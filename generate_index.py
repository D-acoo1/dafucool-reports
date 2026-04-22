#!/usr/bin/env python3
"""扫描当前目录下的 .html 报告，生成 Notion 风格的 index.html 目录页（含内嵌预览）。"""
import datetime
import json
from pathlib import Path
from html import escape

HERE = Path(__file__).parent
EXCLUDE = {"index.html"}

def human_size(n):
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"

# 给每份报告挑一个 emoji（按关键词猜，猜不到用默认）
def pick_emoji(name):
    rules = [
        ("分发", "📱"), ("ios", "📱"), ("android", "🤖"),
        ("主播", "🎙️"), ("任务", "✅"), ("产能", "⚡"),
        ("生态", "🌱"), ("长线", "🧭"), ("规划", "🧭"),
        ("用户", "👥"), ("关系", "🔗"),
        ("充值", "💰"), ("问卷", "📝"),
        ("策略", "🎯"), ("方案", "🎯"),
        ("成本", "💸"), ("对比", "⚖️"),
        ("转化", "📈"), ("收礼", "🎁"), ("送礼", "🎁"),
        ("分析", "🔍"), ("报告", "📊"),
    ]
    low = name.lower()
    for kw, emo in rules:
        if kw in low:
            return emo
    return "📄"

reports = []
for p in sorted(HERE.glob("*.html")):
    if p.name in EXCLUDE:
        continue
    stat = p.stat()
    reports.append({
        "name": p.name,
        "title": p.stem,
        "mtime": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
        "mtime_ts": stat.st_mtime,
        "size": human_size(stat.st_size),
        "emoji": pick_emoji(p.stem),
    })
reports.sort(key=lambda r: r["mtime_ts"], reverse=True)

data_json = json.dumps(reports, ensure_ascii=False)
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>可视化数据报告</title>
<style>
  :root {{
    --bg:#ffffff; --panel:#fbfbfa; --border:#ececea;
    --text:#37352f; --sub:#787774; --hover:#f1f1ef; --active:#e8f0fe;
    --accent:#2e75cc;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg:#191919; --panel:#202020; --border:#2d2d2d;
      --text:#e6e6e4; --sub:#999; --hover:#252525; --active:#1f3a5f;
      --accent:#529cff;
    }}
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ height:100%; margin:0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif;
    background: var(--bg); color: var(--text); overflow: hidden;
    -webkit-font-smoothing: antialiased;
  }}
  .app {{ display:flex; height:100vh; }}

  /* 左侧栏 */
  aside {{
    width: 300px; min-width: 240px; background: var(--panel);
    border-right: 1px solid var(--border); display:flex; flex-direction:column;
  }}
  .side-head {{ padding: 16px 18px 10px; }}
  .side-title {{ font-size: 14px; font-weight: 600; display:flex; align-items:center; gap:8px; }}
  .side-sub {{ font-size: 12px; color: var(--sub); margin-top: 4px; }}
  .search {{
    margin: 4px 12px 8px; padding: 7px 10px; border-radius: 6px;
    background: var(--hover); border:1px solid transparent; font-size: 13px;
    color: var(--text); outline: none;
  }}
  .search:focus {{ border-color: var(--accent); background: var(--bg); }}
  .list {{ flex:1; overflow-y:auto; padding: 4px 8px 16px; }}
  .item {{
    display:flex; align-items:flex-start; gap:8px; padding: 8px 10px;
    border-radius: 6px; cursor: pointer; user-select: none; margin-bottom: 2px;
  }}
  .item:hover {{ background: var(--hover); }}
  .item.active {{ background: var(--active); }}
  .item .emo {{ font-size: 16px; line-height: 1.4; flex-shrink:0; }}
  .item .info {{ flex:1; min-width: 0; }}
  .item .name {{
    font-size: 14px; font-weight: 500; line-height: 1.35;
    overflow: hidden; text-overflow: ellipsis; display: -webkit-box;
    -webkit-line-clamp: 2; -webkit-box-orient: vertical; word-break: break-all;
  }}
  .item .meta {{ font-size: 11px; color: var(--sub); margin-top: 3px; }}
  .item .del {{
    opacity: 0; flex-shrink: 0; align-self: center; padding: 4px 6px;
    border-radius: 4px; font-size: 13px; color: var(--sub);
    transition: all .15s ease; background: transparent; border: 0; cursor: pointer;
  }}
  .item:hover .del {{ opacity: 0.6; }}
  .item .del:hover {{ opacity: 1 !important; background: rgba(220,50,50,0.15); color: #e53935; }}
  .empty {{ padding: 24px 16px; color: var(--sub); font-size: 13px; text-align:center; }}

  /* 删除确认弹窗 */
  .modal-mask {{
    display:none; position: fixed; inset:0; background: rgba(0,0,0,0.5);
    z-index: 1000; align-items:center; justify-content:center;
  }}
  .modal-mask.show {{ display: flex; }}
  .modal {{
    background: var(--bg); border-radius: 10px; padding: 24px; width: 420px;
    max-width: calc(100vw - 32px); box-shadow: 0 10px 40px rgba(0,0,0,0.3);
  }}
  .modal h3 {{ margin: 0 0 12px; font-size: 16px; }}
  .modal .target {{
    background: var(--hover); padding: 8px 12px; border-radius: 6px;
    font-size: 13px; margin-bottom: 16px; word-break: break-all;
  }}
  .modal p {{ margin: 10px 0; font-size: 13px; color: var(--sub); line-height: 1.6; }}
  .modal .kbd {{
    font-family: -apple-system, monospace; background: var(--hover); padding: 1px 5px;
    border-radius: 3px; font-size: 12px;
  }}
  .modal .btns {{ display:flex; gap: 8px; justify-content: flex-end; margin-top: 20px; }}
  .modal .btn-danger {{
    background: #e53935; color: #fff; border: 0;
  }}
  .modal .btn-danger:hover {{ background: #c62828; }}

  /* 右侧预览区 */
  main {{ flex:1; display:flex; flex-direction:column; background: var(--bg); }}
  .topbar {{
    height: 48px; padding: 0 18px; border-bottom: 1px solid var(--border);
    display:flex; align-items:center; gap: 12px;
  }}
  .crumb {{ font-size: 13px; color: var(--sub); }}
  .crumb b {{ color: var(--text); font-weight: 600; }}
  .actions {{ margin-left:auto; display:flex; gap:8px; }}
  .btn {{
    font-size: 12px; padding: 6px 12px; border-radius: 6px;
    border:1px solid var(--border); background: var(--bg); color: var(--text);
    cursor:pointer; text-decoration:none; display:inline-flex; align-items:center; gap:4px;
  }}
  .btn:hover {{ background: var(--hover); }}
  .btn.primary {{ background: var(--accent); color:#fff; border-color: var(--accent); }}
  .btn.primary:hover {{ opacity: 0.9; background: var(--accent); }}
  .frame-wrap {{ flex:1; position: relative; background: var(--panel); }}
  iframe {{ width:100%; height:100%; border:0; background:#fff; }}
  .placeholder {{
    position:absolute; inset:0; display:flex; flex-direction:column;
    align-items:center; justify-content:center; color: var(--sub); gap: 12px;
  }}
  .placeholder .big {{ font-size: 56px; }}
  .placeholder .hint {{ font-size: 14px; }}

  /* 移动端 */
  @media (max-width: 720px) {{
    aside {{ width: 100%; min-width: 0; border-right: 0; border-bottom: 1px solid var(--border); height: 45vh; }}
    .app {{ flex-direction: column; }}
    main {{ height: 55vh; }}
  }}
</style>
</head>
<body>
<div class="app">
  <aside>
    <div class="side-head">
      <div class="side-title">📊 可视化数据报告</div>
      <div class="side-sub"><span id="count">{len(reports)}</span> 份报告 · 更新于 {now}</div>
    </div>
    <input class="search" id="q" placeholder="🔎 搜索报告名…" />
    <div class="list" id="list"></div>
  </aside>
  <div class="modal-mask" id="delModal">
    <div class="modal">
      <h3>🗑 删除这份报告？</h3>
      <div class="target" id="delTarget"></div>
      <p>✅ 点下面的按钮会跳转到 GitHub，点 GitHub 页面底部的绿色 <span class="kbd">Commit changes</span> 按钮就删除了。</p>
      <p>⚠️ 提示：如果你本地 <span class="kbd">~/可视化数据报告/</span> 里还有同名文件，下次同步时会<b>再传回来</b>。想彻底删掉的话，记得也去本地文件夹删一份。</p>
      <div class="btns">
        <button class="btn" onclick="closeModal()">取消</button>
        <a class="btn btn-danger" id="delConfirm" target="_blank" rel="noopener" onclick="setTimeout(closeModal, 200)">去 GitHub 删除 →</a>
      </div>
    </div>
  </div>
  <main>
    <div class="topbar">
      <div class="crumb">可视化数据报告 / <b id="current">请选择一份报告</b></div>
      <div class="actions" id="actions" style="display:none;">
        <a class="btn" id="openNew" target="_blank" rel="noopener">↗ 新窗口打开</a>
        <a class="btn primary" id="download" download>⬇ 下载</a>
      </div>
    </div>
    <div class="frame-wrap">
      <div class="placeholder" id="placeholder">
        <div class="big">👈</div>
        <div class="hint">从左边选一份报告开始预览</div>
      </div>
      <iframe id="frame" style="display:none;" sandbox="allow-scripts allow-same-origin allow-popups allow-forms"></iframe>
    </div>
  </main>
</div>
<script>
  const reports = {data_json};
  const listEl = document.getElementById('list');
  const searchEl = document.getElementById('q');
  const frame = document.getElementById('frame');
  const placeholder = document.getElementById('placeholder');
  const currentEl = document.getElementById('current');
  const actionsEl = document.getElementById('actions');
  const openNew = document.getElementById('openNew');
  const download = document.getElementById('download');
  const countEl = document.getElementById('count');

  let activeIdx = -1;

  function render(filter) {{
    listEl.innerHTML = '';
    const f = (filter || '').trim().toLowerCase();
    const matched = reports.filter(r => !f || r.title.toLowerCase().includes(f));
    countEl.textContent = matched.length;
    if (matched.length === 0) {{
      listEl.innerHTML = '<div class="empty">没有匹配的报告</div>';
      return;
    }}
    matched.forEach((r) => {{
      const realIdx = reports.indexOf(r);
      const div = document.createElement('div');
      div.className = 'item' + (realIdx === activeIdx ? ' active' : '');
      div.innerHTML = `
        <div class="emo">${{r.emoji}}</div>
        <div class="info">
          <div class="name">${{r.title}}</div>
          <div class="meta">🕒 ${{r.mtime}} · ${{r.size}}</div>
        </div>
        <button class="del" title="从云端删除" aria-label="删除">🗑</button>`;
      div.onclick = () => select(realIdx);
      div.querySelector('.del').onclick = (e) => {{ e.stopPropagation(); askDelete(r); }};
      listEl.appendChild(div);
    }});
  }}

  function select(i) {{
    activeIdx = i;
    const r = reports[i];
    frame.src = './' + encodeURIComponent(r.name);
    frame.style.display = 'block';
    placeholder.style.display = 'none';
    currentEl.textContent = r.title;
    actionsEl.style.display = 'flex';
    openNew.href = './' + encodeURIComponent(r.name);
    download.href = './' + encodeURIComponent(r.name);
    render(searchEl.value);
    // URL hash 便于分享
    history.replaceState(null, '', '#' + encodeURIComponent(r.name));
  }}

  // 删除流程
  const delModal = document.getElementById('delModal');
  const delTarget = document.getElementById('delTarget');
  const delConfirm = document.getElementById('delConfirm');
  const REPO = 'D-acoo1/dafucool-reports';
  function askDelete(r) {{
    delTarget.textContent = r.name;
    delConfirm.href = `https://github.com/${{REPO}}/delete/main/${{encodeURIComponent(r.name)}}`;
    delModal.classList.add('show');
  }}
  function closeModal() {{ delModal.classList.remove('show'); }}
  delModal.addEventListener('click', (e) => {{ if (e.target === delModal) closeModal(); }});
  document.addEventListener('keydown', (e) => {{ if (e.key === 'Escape') closeModal(); }});

  searchEl.addEventListener('input', () => render(searchEl.value));
  render('');

  // 打开页面时若 URL 有 hash，自动选中
  if (location.hash) {{
    const want = decodeURIComponent(location.hash.slice(1));
    const i = reports.findIndex(r => r.name === want);
    if (i >= 0) select(i);
  }}
</script>
</body>
</html>
"""

(HERE / "index.html").write_text(html, encoding="utf-8")
print(f"index.html generated with {len(reports)} reports")
