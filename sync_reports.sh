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

# 智能复制：只在"新增 / 修改"时往云端推，云端已删除的文件不会被本地"还魂"
shopt -s nullglob
html_files=("$SRC"/*.html)
shopt -u nullglob

copied=0
skipped_deleted=0
for f in "${html_files[@]}"; do
  name=$(basename "$f")
  if [ -f "$DST/$name" ]; then
    # 云端有这份文件，若内容不同就覆盖（同名更新）
    if ! cmp -s "$f" "$DST/$name"; then
      cp -pf "$f" "$DST/$name"
      ((copied++)) || true
    fi
  else
    # 云端没这份文件，要分两种情况：
    # 1) 这是全新报告 → 上传
    # 2) 这是"云端刚删过"的报告 → 不再往回推（除非本地修改时间晚于删除时间，说明用户又改过了）
    delete_ts=$(git log --diff-filter=D --format="%ct" -1 -- "$name" 2>/dev/null)
    if [ -z "$delete_ts" ]; then
      # 从未在云端出现过 → 新报告，上传
      cp -pf "$f" "$DST/$name"
      ((copied++)) || true
    else
      # 云端曾有被删过；对比本地修改时间和删除时间
      src_mtime=$(stat -f %m "$f")
      if [ "$src_mtime" -gt "$delete_ts" ]; then
        # 本地这份在云端删除之后被修改过 → 说明用户想重新上传，推
        cp -pf "$f" "$DST/$name"
        ((copied++)) || true
      else
        # 本地没动过，尊重云端的删除
        ((skipped_deleted++)) || true
      fi
    fi
  fi
done
echo "新增/更新 $copied 份；跳过被云端删除的 $skipped_deleted 份"

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
