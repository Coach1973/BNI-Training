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
        /* 色系/字型取自 chapters.bymyway.com/sincere（BNI官方Brand Standards Manual指定色） */
        :root {{
            --red: #CF2030; --red-dark: #9B1F27; --ink: #000000; --paper: #FAF7F2;
            --line: #E5DFD3; --gold: #B08D57; --sub: #6B665D; --white: #FFFFFF;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            background-color: var(--paper);
            color: var(--ink);
            font-family: 'Helvetica Neue', Arial, 'PingFang TC', 'Microsoft JhengHei', 'Noto Sans TC', sans-serif;
            margin: 0;
            padding: 0 0 40px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .header-container {{ width: 100%; background: var(--ink); color: var(--white); text-align: center; padding: 48px 20px 40px; margin-bottom: 28px; }}
        h1 {{
            color: var(--white);
            font-size: 2.2rem;
            font-weight: 900;
            letter-spacing: 2px;
            margin: 0;
        }}
        p.subtitle {{ color: var(--line); font-size: 1rem; margin-top: 12px; letter-spacing: 1px; }}

        .stats-row {{
            display: flex; flex-wrap: wrap; gap: 16px; justify-content: center;
            width: 100%; max-width: 1000px; margin: 0 20px 24px; padding: 0 20px;
        }}
        .stat-card {{
            background: var(--white); border: 1px solid var(--line); border-radius: 4px;
            padding: 16px 22px; min-width: 150px; text-align: center;
        }}
        .stat-card .num {{ font-size: 1.7rem; font-weight: 900; color: var(--red); }}
        .stat-card .lbl {{ font-size: .78rem; color: var(--sub); margin-top: 4px; letter-spacing: 1px; }}

        .controls {{
            width: 100%; max-width: 1000px; display: flex; gap: 10px; margin: 0 20px 16px; padding: 0 20px;
        }}
        .controls input[type=text] {{
            flex: 1; background: var(--white); border: 1px solid var(--line);
            color: var(--ink); padding: 10px 14px; border-radius: 4px; font-size: 1rem;
        }}
        .controls input[type=text]:focus {{ outline: none; border-color: var(--red); }}

        .table-wrapper {{
            width: 100%; max-width: 1000px; margin: 0 20px; background: var(--white); border-radius: 4px;
            overflow-x: auto; -webkit-overflow-scrolling: touch; border: 1px solid var(--line);
        }}
        .table-wrapper table {{ min-width: 900px; }}
        table {{ width: 100%; border-collapse: collapse; text-align: center; }}
        thead {{ background: var(--ink); }}
        th {{ padding: 16px 12px; color: var(--white); font-weight: 700; letter-spacing: .5px; white-space: nowrap; font-size: .88rem; }}
        td {{ padding: 14px 12px; border-bottom: 1px solid var(--line); font-size: .95rem; }}
        tbody tr:hover {{ background: var(--paper); }}

        .present {{ color: var(--gold); font-weight: 900; }}
        .absent {{ color: var(--red); font-weight: 900; }}
        .nodata {{ color: var(--sub); }}
        .special {{ color: var(--red-dark); font-weight: 700; font-size: .85rem; }}

        .rank {{ color: var(--sub); font-weight: 700; }}
        .name {{ font-weight: 900; color: var(--ink); text-align: left; padding-left: 16px; white-space: nowrap; }}
        .chapter {{ color: var(--sub); font-size: .9rem; }}
        .total-score {{ color: var(--red); font-weight: 900; font-size: 1.05rem; }}

        .note-panel {{
            width: 100%; max-width: 1000px; margin: 32px 20px 0; background: var(--white);
            border-radius: 4px; border: 1px solid var(--line); padding: 26px 32px; box-sizing: border-box;
        }}
        .note-panel h2 {{ color: var(--ink); font-weight: 900; font-size: 1.05rem; letter-spacing: 1px; margin: 0 0 16px 0; border-bottom: 1px solid var(--line); padding-bottom: 10px; }}
        .note-panel p {{ color: var(--sub); line-height: 1.9; margin: 0 0 12px 0; font-size: .9rem; }}

        @media (max-width: 600px) {{
            .header-container {{ padding: 36px 16px 30px; }}
            h1 {{ font-size: 1.4rem; }}
            .stats-row, .controls, .table-wrapper, .note-panel {{ padding-left: 12px; padding-right: 12px; margin-left: 0; margin-right: 0; }}
        }}
    </style>
</head>
<body>
    <div class="header-container">
        <p style="margin:0 0 10px 0;"><a href="index.html" style="color:var(--gold);text-decoration:none;font-size:.85rem;font-weight:700;letter-spacing:1px;">← 回全區培訓總覽</a></p>
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
