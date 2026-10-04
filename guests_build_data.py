# -*- coding: utf-8 -*-
"""
BNI大台南南區「來賓邀約排行榜」公開頁面 - 資料源建置腳本（PALMS版）

2026-09-01教練親口拍板：改用官方「分會 - PALMS摘要報告」當資料源，
不再用「地區-查看來賓」/「分會訪問報告」明細報表——後者的「Invited By」
自由文字欄位統計出的來賓次數，跟PALMS「來賓」欄位官方數字對不上
（真鑽分會實測：郭政輝明細報表只有106筆，PALMS官方認證是303筆，
落差原因不明，但PALMS是BNI官方績效指標，以它為準）。

資料來源：
  ~/Downloads/__-palms-*.xls （檔名為 BNI Connect 匯出時的亂碼格式，
   無法從檔名判斷分會/時間範圍，一律讀檔案內容第4~6列「分會:/從:/至:」
   參數列自動判斷，不需要教練額外註記）

PALMS報表性質：每一份是「某個固定期間」的累積總數快照（非逐筆明細），
教練用同一個「至」（今天）、不同「從」，匯出多份巢狀（nested）快照
——近N個月的快照，天生就包含近N-1個月的全部資料，因為都是「從某天到
今天」，不是互斥的分段。前端直接依「快照可用的月數清單」動態產生
查詢按鈕，不支援任意月數自訂輸入（哪個月數要看教練有沒有匯出那份快照）。

產出：guests_data.json
  { "chapters": {
      "真鑽": { "months_available": [1,2,3,...], "snapshots": { "1": [{"name","count"}...], ... } },
      ...
  } }
"""
import csv
import glob
import json
import os
import re
import sqlite3
import xml.etree.ElementTree as ET
from datetime import date

NS = {"ss": "urn:schemas-microsoft-com:office:spreadsheet"}

DOWNLOADS_GLOB = os.path.expanduser("~/Downloads/__-palms-*.xls")
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guests_data.json")

# 「沒有邀約來賓的名單」要知道分會現在有誰（2026-10-05 教練交辦）：用 BNI Connect「會員資格會期報告」，
# 扣掉教練確認已離會、但報告還留著的人。只取姓名＋最近會齡（月），電話等個資不進公開頁
TENURE_CSV = os.path.expanduser("~/.openclaw/workspace/claude-brain/data/bni_membership_tenure_report_2026-10-04.csv")
DEPARTED = {"真誠": {"郭素玲", "盧尚政"}}  # 教練 2026-10-05 00:23 確認已離會

# PALMS 報表只匯出到 8/31；9/1 以後的來賓，用各分會戰情表每週填的來賓名單（誰邀的）補上
# （教練 2026-10-05：「從戰情表裡面最新的資訊，更新回來賓總表，這樣你就不用進 connect 裡面查」）。
# 只取「邀請人→人數」，來賓姓名不進公開頁。
GITHUB = os.path.expanduser("~/github_repos")
DASHBOARDS = {
    "真鑽": os.path.join(GITHUB, "zhenzuan-guests", "zhenzuan_guests.db"),
    "真鑫": os.path.join(GITHUB, "zhenxin-guests", "zhenxin_guests.db"),
    "真誠": os.path.join(GITHUB, "zhencheng-guests", "zhencheng_guests.db"),
}

# 各分會實際成立月（2026-09-01教練親口逐一確認+資料本身交叉驗證）。有些PALMS
# 報表的「從」日期比分會實際成立還早（例如真鑽報表填2018-01-01，但真鑽
# 2018-08才成立），這種情況月數要以成立月封頂，不能照報表「從」日期機械算出
# 虛高的月數。真鑽已用資料交叉驗證：97個月(從2018-08-01)與104個月
# (從2018-01-01)總計皆為1624，證明2018-01~08這段本來就沒有資料，
# 跟教練親口「2018年8月成立」完全吻合。
CHAPTER_FOUNDING = {
    "真鑽": date(2018, 8, 1),
    "真誠": date(2020, 9, 1),
    "真鑫": date(2026, 4, 1),
}


def _row_cells(row):
    cells = {}
    for cell in row.findall(f"{{{NS['ss']}}}Cell"):
        idx = cell.get(f"{{{NS['ss']}}}Index")
        data = cell.find(f"{{{NS['ss']}}}Data")
        if idx and data is not None:
            cells[int(idx)] = data.text or ""
    return cells


def _date(s):
    y, m, d = (int(x) for x in s[:10].split("-"))
    return date(y, m, d)


def months_back(date_from, date_to, chapter):
    """「從～至」實際涵蓋幾個月（照天數換算再四捨五入）：2025-08-31～2026-08-31＝12、2026-03-01～2026-08-31＝6。
    2026-10-05 前是用「從」的月份硬減固定的今天，從 8/31 起算的報表會多算一個月（近 12 個月變成 13）。"""
    start = _date(date_from)
    founding = CHAPTER_FOUNDING.get(chapter)
    if founding and start < founding:
        start = founding
    return round((_date(date_to) - start).days / 30.44)


def _key(name):
    """比對用：去掉空白、括號註記、英文名（「林佳伶 Lavi」＝「林佳伶」）。"""
    return re.sub(r"[\sA-Za-z]", "", re.sub(r"[（(].*?[）)]", "", name or ""))


def load_dashboard_guests(chapter, after):
    """回傳（{邀請人: 戰情表在 after 之後記的來賓數}, 戰情表最新有資料的週）；沒有這個分會的戰情表就回 ({}, None)。"""
    path = DASHBOARDS.get(chapter)
    if not path or not os.path.exists(path):
        return {}, None
    conn = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    counts = {}
    for inviter, n in conn.execute(
        "SELECT inviter, COUNT(*) FROM guest_list WHERE week_date > ? AND inviter IS NOT NULL AND inviter != '' GROUP BY inviter",
        (after,),
    ):
        counts[inviter] = n
    # 最新有填資料的週（出席或早鳥或來賓任一有值），比「週次表」最後一週可靠（週次會先開好）
    last = conn.execute(
        "SELECT MAX(week_date) FROM weekly_data WHERE attendance IS NOT NULL OR early_bird IS NOT NULL OR guests IS NOT NULL"
    ).fetchone()[0]
    conn.close()
    return counts, last


def load_rosters():
    rosters = {}
    with open(TENURE_CSV, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            ch, name = r["分會"], r["姓名"].strip()
            if name in DEPARTED.get(ch, ()):
                continue
            rosters.setdefault(ch, []).append({
                "name": name, "key": _key(name),
                "tenure_months": int(r["最近會齡_年"]) * 12 + int(r["最近會齡_月"]),
            })
    return rosters


def parse_palms_file(path):
    """回傳 (chapter, months, members)，members = [{"name","count"}]，依count降冪排序。"""
    tree = ET.parse(path)
    rows = list(tree.getroot().iter(f"{{{NS['ss']}}}Row"))

    chapter = _row_cells(rows[4]).get(9, "").strip()
    date_from = (_row_cells(rows[5]).get(9, "") or "").strip()
    date_to = (_row_cells(rows[6]).get(9, "") or "").strip()
    if not chapter or not date_from or not date_to:
        return None

    months = months_back(date_from, date_to, chapter)

    members = []
    for row in rows[8:]:
        cells = _row_cells(row)
        surname = (cells.get(1) or "").strip()
        given = (cells.get(2) or "").strip()
        name = (surname + given).strip()
        guest_raw = cells.get(13)
        # 跳過「總數」彙總列，跳過已知的非會員雜項佔位列（來賓/BNI，查證見真鑽PALMS報表第57~58列，
        # 不是真實會員姓名），跳過沒有姓名或沒有來賓數字的空列
        if not name or name in ("總數", "來賓", "BNI") or not guest_raw:
            continue
        try:
            count = int(float(guest_raw))
        except ValueError:
            continue
        members.append({"name": name, "key": _key(name), "count": count})

    members.sort(key=lambda m: (-m["count"], m["name"]))
    return chapter, months, members, date_to[:10]


def main():
    files = sorted(set(glob.glob(DOWNLOADS_GLOB)), key=os.path.getmtime)
    if not files:
        raise SystemExit(f"找不到任何PALMS報表檔案，請確認 {DOWNLOADS_GLOB} 底下有檔案")

    print(f"找到 {len(files)} 份PALMS檔案")

    parsed_files = []
    for f in files:
        parsed = parse_palms_file(f)
        if parsed is None:
            print(f"  跳過（缺分會/從日期）：{os.path.basename(f)}")
            continue
        parsed_files.append((f, *parsed))

    # 「近 N 個月」必須是「從 N 個月前到最新匯出日」：每個分會只用「至」＝最新那一天的報表，
    # 其他區間的報表（例如只匯出 4 月一個月、或 2023-09～2024-05）不是近 N 個月，跳過（2026-10-05 修）
    latest_to = {}
    for _, chapter, _, _, date_to in parsed_files:
        latest_to[chapter] = max(latest_to.get(chapter, ""), date_to)

    chapters = {}  # chapter -> {months: members}, 同月數重複匯出取最後一份（mtime較新）
    for f, chapter, months, members, date_to in parsed_files:
        if date_to != latest_to[chapter]:
            print(f"  跳過（不是近N個月，至 {date_to}）：{chapter} {os.path.basename(f)}")
            continue
        chapters.setdefault(chapter, {})[months] = members
        print(f"  {chapter} 近{months}個月：{len(members)}位會員，來源={os.path.basename(f)}")

    rosters = load_rosters()
    output = {"chapters": {}}
    for chapter, snapshots in chapters.items():
        # BNI Connect 偶爾把姓放到最後（PALMS「姵彤蔡」＝會期報告「蔡姵彤」），對不到時試著把最後一個字移到前面
        roster_keys = {m["key"] for m in rosters.get(chapter, [])}
        for members in snapshots.values():
            for m in members:
                if m["key"] not in roster_keys and m["key"][-1:] + m["key"][:-1] in roster_keys:
                    m["key"] = m["key"][-1:] + m["key"][:-1]
        months_available = sorted(snapshots.keys())
        # 9/1 以後的來賓：戰情表每週填的邀請人名單，每份快照都加上（快照都是「到 8/31 為止」，加上之後就是「到最新一週為止」）
        dash_counts, dash_last = load_dashboard_guests(chapter, latest_to[chapter])
        extra = {}
        roster_name = {m["key"]: m["name"] for m in rosters.get(chapter, [])}
        for inviter, n in dash_counts.items():
            extra[_key(inviter)] = extra.get(_key(inviter), 0) + n
        if extra:
            for members in snapshots.values():
                by_key = {m["key"]: m for m in members}
                for key, n in extra.items():
                    if key in by_key:
                        by_key[key]["count"] += n
                    else:
                        members.append({"name": roster_name.get(key, key), "key": key, "count": n})
                members.sort(key=lambda m: (-m["count"], m["name"]))
        output["chapters"][chapter] = {
            "as_of": max(latest_to[chapter], dash_last or ""),
            "palms_to": latest_to[chapter],
            "extra_counts": extra,
            "months_available": months_available,
            "snapshots": {str(m): snapshots[m] for m in months_available},
            "roster": rosters.get(chapter, []),
        }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n=== 完成，寫出 {OUT_PATH} ===")
    for chapter, data in output["chapters"].items():
        print(f"  {chapter}：{len(data['months_available'])}個時間節點 {data['months_available']}，截至 {data['as_of']}（官方報表到 {data['palms_to']}，戰情表補 {sum(data['extra_counts'].values())} 位），現任名單 {len(data['roster'])} 位")


if __name__ == "__main__":
    main()
