# -*- coding: utf-8 -*-
"""讀 data.json，產生 index.html（公開版，只有姓名/分會/出席狀態）。
更新資料：改 build_data.py 裡的 PEOPLE_RAW，重跑
    python build_data.py && python build_html.py
兩個檔案一起 commit + push。
"""
import json
import io

STATUS_MAP = {
    "present": ("present", "出席"),
    "absent": ("absent", "缺席"),
    "nodata": ("nodata", "-"),
    "teacher0": ("special", "🎤講師"),
    "share0": ("special", "🎤分享"),
}


def render_row(rank, p, sessions):
    cells = []
    cells.append('<td class="rank">%d</td>' % rank)
    cells.append('<td class="name">%s</td>' % p["name"])
    cells.append('<td class="chapter">%s</td>' % (p["chapter"] or '<span class="nodata">-</span>'))
    for s in sessions:
        cls, label = STATUS_MAP[p["attendance"][s["id"]]]
        cells.append('<td class="%s">%s</td>' % (cls, label))
    cells.append('<td class="total-score">%d 次</td>' % p["attended_count"])
    return '<tr class="data-row" data-name="%s">%s</tr>' % (p["name"], "".join(cells))


def main():
    data = json.load(io.open("data_msp.json", encoding="utf-8"))
    sessions = data["sessions"]
    people = sorted(data["people"], key=lambda p: (-p["attended_count"], p["name"]))

    header_ths = "".join('<th>%s</th>' % s["label"] for s in sessions)
    rows_html = "\n".join(render_row(i + 1, p, sessions) for i, p in enumerate(people))

    html = HTML_TEMPLATE.format(
        header_ths=header_ths,
        rows_html=rows_html,
        total_people=len(people),
    )
    with io.open("msp.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("msp.html done")


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BNI 培訓紀錄總資料庫</title>
    <style>
        :root {{
            --bg-color: #0b0f19;
            --panel-bg: #1a2333;
            --text-main: #e2e8f0;
            --text-muted: #64748b;
            --neon-blue: #00f0ff;
            --neon-green: #10b981;
            --neon-red: #ff2a2a;
            --neon-gold: #f59e0b;
        }}
        body {{
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: 'Helvetica Neue', 'PingFang TC', 'Microsoft JhengHei', sans-serif;
            margin: 0;
            padding: 40px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .header-container {{ text-align: center; margin-bottom: 28px; }}
        h1 {{
            color: var(--neon-blue);
            font-size: 2.2rem;
            letter-spacing: 2px;
            margin: 0;
            text-shadow: 0 0 15px rgba(0, 240, 255, 0.5);
        }}
        p.subtitle {{ color: var(--text-muted); font-size: 1.05rem; margin-top: 10px; letter-spacing: 1px; }}

        .stats-row {{
            display: flex; flex-wrap: wrap; gap: 16px; justify-content: center;
            width: 100%; max-width: 1000px; margin-bottom: 24px;
        }}
        .stat-card {{
            background: var(--panel-bg); border: 1px solid #2d3748; border-radius: 10px;
            padding: 16px 22px; min-width: 150px; text-align: center;
        }}
        .stat-card .num {{ font-size: 1.6rem; font-weight: bold; color: var(--neon-blue); text-shadow: 0 0 10px rgba(0,240,255,.4); }}
        .stat-card .lbl {{ font-size: .8rem; color: var(--text-muted); margin-top: 4px; letter-spacing: 1px; }}

        .controls {{
            width: 100%; max-width: 1000px; display: flex; gap: 10px; margin-bottom: 16px;
        }}
        .controls input[type=text] {{
            flex: 1; background: var(--panel-bg); border: 1px solid #2d3748;
            color: var(--text-main); padding: 10px 14px; border-radius: 8px; font-size: 1rem;
        }}

        .table-wrapper {{
            width: 100%; max-width: 1000px; background: var(--panel-bg); border-radius: 12px;
            box-shadow: 0 0 30px rgba(0, 240, 255, 0.1); overflow-x: auto;
            -webkit-overflow-scrolling: touch; border: 1px solid #2d3748;
        }}
        .table-wrapper table {{ min-width: 900px; }}
        table {{ width: 100%; border-collapse: collapse; text-align: center; }}
        thead {{ background: #0f172a; border-bottom: 2px solid var(--neon-blue); }}
        th {{ padding: 16px 12px; color: var(--neon-blue); font-weight: 600; letter-spacing: .5px; white-space: nowrap; font-size: .9rem; }}
        td {{ padding: 14px 12px; border-bottom: 1px solid #2d3748; font-size: .95rem; }}
        tbody tr:hover {{ background: rgba(0, 240, 255, 0.05); }}

        .present {{ color: var(--neon-green); font-weight: bold; }}
        .absent {{ color: var(--neon-red); font-weight: bold; }}
        .nodata {{ color: #475569; }}
        .special {{ color: var(--neon-gold); font-weight: bold; font-size: .85rem; }}

        .rank {{ color: #94a3b8; font-weight: bold; }}
        .name {{ font-weight: bold; color: #fff; text-align: left; padding-left: 16px; white-space: nowrap; }}
        .chapter {{ color: #94a3b8; font-size: .9rem; }}
        .total-score {{ color: var(--neon-gold); font-weight: bold; font-size: 1.05rem; }}

        .note-panel {{
            width: 100%; max-width: 1000px; margin-top: 32px; background: #1a2333;
            border-radius: 12px; border: 1px solid #2d3748; padding: 26px 32px; box-sizing: border-box;
        }}
        .note-panel h2 {{ color: var(--neon-gold); font-size: 1.05rem; letter-spacing: 2px; margin: 0 0 16px 0; border-bottom: 1px dashed #475569; padding-bottom: 10px; }}
        .note-panel p {{ color: #e2e8f0; line-height: 1.9; margin: 0 0 12px 0; font-size: .92rem; }}

        @media (max-width: 600px) {{
            body {{ padding: 20px 8px; }}
            h1 {{ font-size: 1.3rem; }}
        }}
    </style>
</head>
<body>
    <div class="header-container">
        <p style="margin:0 0 10px 0;"><a href="index.html" style="color:#00f0ff;text-decoration:none;font-size:.9rem;">← 回全區培訓總覽</a></p>
        <h1>BNI 培訓紀錄總資料庫</h1>
        <p class="subtitle">大樹教練 MSP初階/進階培訓出席戰情儀表板　2026年1月起｜共6場次</p>
    </div>

    <div class="stats-row">
        <div class="stat-card"><div class="num">{total_people}</div><div class="lbl">出席人次總計</div></div>
    </div>

    <div class="controls">
        <input type="text" id="searchBox" placeholder="搜尋姓名...">
    </div>

    <div class="table-wrapper">
        <table>
            <thead>
                <tr>
                    <th>排名</th>
                    <th style="text-align:left;padding-left:16px;">姓名</th>
                    <th>分會</th>
                    {header_ths}
                    <th>出席次數</th>
                </tr>
            </thead>
            <tbody id="tbody">
{rows_html}
            </tbody>
        </table>
    </div>

    <div class="note-panel">
        <h2>📋 資料說明</h2>
        <p>出席狀態：✅出席／🚫缺席／🎤講師・分享(擔任講師或分享人身份出席)／- 代表無資料(非確認缺席，例如僅在單場出席名單中出現的人，其餘場次未被記錄)。</p>
        <p>8/17資料以最新為準：若同一人在多批資料重複出現，一律採用含8/17的最新版本。</p>
    </div>

    <script>
        const searchBox = document.getElementById('searchBox');
        const rows = Array.from(document.querySelectorAll('.data-row'));
        searchBox.addEventListener('input', () => {{
            const q = searchBox.value.trim();
            rows.forEach(r => {{
                r.style.display = (!q || r.dataset.name.includes(q)) ? '' : 'none';
            }});
        }});
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
