#!/usr/bin/env bash
# 真·镜像同步：~/Desktop/可视化数据报告/*.html ↔ dafucool-reports 仓库
# - 本地新增 → 云端新增
# - 本地修改 → 云端覆盖（同名视为同一报告）
# - 本地删除 → 云端也删除
set -e

# launchd 启动时环境变量很少，显式设 PATH
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

SRC="$HOME/可视化数据报告"
DST="$HOME/dafucool-reports"
LOG="$HOME/dafucool-reports/.sync.log"

exec >>"$LOG" 2>&1
echo "==== $(date '+%Y-%m-%d %H:%M:%S') 开始同步 ===="

[ -d "$SRC" ] || { echo "⚠ 源目录不存在: $SRC"; exit 0; }
[ -d "$DST/.git" ] || { echo "⚠ 目标仓库不存在: $DST"; exit 1; }

# 1. 先清掉目标里的所有 HTML 报告（保留 index.html、README.md、脚本、.git 等）
find "$DST" -maxdepth 1 -name "*.html" ! -name "index.html" -delete

# 2. 从源拷贝最新的所有 HTML（真镜像）
shopt -s nullglob
html_files=("$SRC"/*.html)
shopt -u nullglob
if [ ${#html_files[@]} -gt 0 ]; then
  cp -f "${html_files[@]}" "$DST"/
  echo "同步了 ${#html_files[@]} 份报告"
else
  echo "源目录无 HTML 报告（将只保留一个空目录页）"
fi

# 3. 重建目录页
/usr/bin/env python3 "$DST/generate_index.py"

# 4. 提交并推送
cd "$DST"
git add -A
if git diff --cached --quiet; then
  echo "✓ 无变更，跳过推送"
  exit 0
fi
git commit -m "sync $(date +%Y-%m-%d\ %H:%M)" >/dev/null
git push origin main && echo "✅ 推送成功 → https://d-acoo1.github.io/dafucool-reports/"
