#!/usr/bin/env bash
# 增量同步：~/可视化数据报告/*.html → dafucool-reports 仓库
# - 本地新增 → 云端新增
# - 本地修改 → 云端覆盖（同名视为同一报告）
# - 本地删除 → 云端保留（用户自行在云端管理删除）
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

# 先和远端对齐（避免云端手动删除的文件被本地再推回去）
cd "$DST"
git stash --quiet 2>/dev/null || true
git pull --rebase --quiet origin main 2>&1 | grep -v "up to date" || true
git stash pop --quiet 2>/dev/null || true

# 从源拷贝最新的所有 HTML（同名覆盖；不删除目标里已有的其他报告）
shopt -s nullglob
html_files=("$SRC"/*.html)
shopt -u nullglob
if [ ${#html_files[@]} -gt 0 ]; then
  # -p 保留原始修改时间（报告的真实生成时间），避免每次同步都刷新成"现在"
  cp -pf "${html_files[@]}" "$DST"/
  echo "复制/覆盖了 ${#html_files[@]} 份报告（保留原始时间）"
else
  echo "源目录无 HTML 报告"
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
