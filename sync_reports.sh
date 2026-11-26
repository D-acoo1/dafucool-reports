#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf "%s\n" "用法：./sync_reports.sh /绝对路径/公开报告.html 原地址.html [报告标题] [内容更新时间]"
}

case "$#" in
  0) usage; exit 0 ;;
  2|3|4) ;;
  *) usage >&2; exit 2 ;;
esac

source_report=$1
report=$2
if [[ "$source_report" != /* || ! -f "$source_report" ]]; then
  printf "%s\n" "请指定已核验的公开版 HTML 绝对路径。" >&2
  exit 2
fi
if [[ "$report" = */* || "$report" = index.html || "$report" != *.html ]]; then
  printf "%s\n" "请填写站内报告的 HTML 文件名。" >&2
  exit 2
fi

cd "$(dirname -- "$0")"
lock_dir=$(git rev-parse --git-path report-sync.lock)
if ! mkdir "$lock_dir" 2>/dev/null; then
  printf "%s\n" "报告仓库正在发布，请在本次发布完成后重试。" >&2
  exit 1
fi
trap 'rmdir "$lock_dir"' EXIT

if [[ "$(git branch --show-current)" != main || -n "$(git status --porcelain)" ]]; then
  printf "%s\n" "请在干净的 main 工作区发布，以免夹带其他改动。" >&2
  exit 1
fi

git pull --ff-only origin main

args=(--report "$report")
if [[ -n "${3:-}" ]]; then args+=(--title "$3"); fi
if [[ -n "${4:-}" ]]; then args+=(--updated-at "$4"); fi

python3 - "$source_report" "$report" "${3:-}" "${4:-}" <<'PY'
import datetime
import json
from pathlib import Path
import re
import sys

source, report, title, timestamp = sys.argv[1:]
catalog = json.loads(Path("reports.json").read_text(encoding="utf-8"))
alias = catalog["aliases"].get(report)
if alias:
    sys.exit(f"请沿用原地址 {alias}")
current = catalog["reports"].get(report)
if not current and not title:
    sys.exit("首次发布请填写报告标题。")
if timestamp:
    updated = datetime.datetime.fromisoformat(timestamp)
    if updated.tzinfo is None:
        sys.exit("更新时间需包含时区。")
    if current and updated < datetime.datetime.fromisoformat(current["updated_at"]):
        sys.exit("此次报告时间早于站点已有版本。")
text = Path(source).read_text(encoding="utf-8")
if not re.search(r"<html\b", text, re.I) or re.search(r"/Users/|file:///|ghp_[a-zA-Z0-9]{30,}", text):
    sys.exit("待发布文件需要是完整网页，且需清理本地路径或凭据。")
PY

if [[ ! -f "$report" ]] || ! cmp -s "$source_report" "$report"; then
  cp "$source_report" "./$report"
  python3 generate_index.py "${args[@]}"
  git add -- "$report" reports.json index.html
  git commit -m "Update report: $report"
fi

# 前一次推送中断时，重试可补推已提交的同一版本。
git push origin main
printf "%s\n" "报告已推送，等待 GitHub Pages 更新。"
