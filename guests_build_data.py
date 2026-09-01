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
import glob
import json
import os
import xml.etree.ElementTree as ET
from datetime import date

NS = {"ss": "urn:schemas-microsoft-com:office:spreadsheet"}

DOWNLOADS_GLOB = os.path.expanduser("~/Downloads/__-palms-*.xls")
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guests_data.json")

# "今天" 基準：跟教練匯出報表當下的「至」日期一致，避免月數計算隨執行當下日期漂移
TODAY = date(2026, 9, 1)

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


def months_back(from_date_str, chapter):
    y, m, d = (int(x) for x in from_date_str[:10].split("-"))
    from_date = date(y, m, 1)
    founding = CHAPTER_FOUNDING.get(chapter)
    if founding and from_date < founding:
        from_date = founding
    return (TODAY.year - from_date.year) * 12 + (TODAY.month - from_date.month)


def parse_palms_file(path):
    """回傳 (chapter, months, members)，members = [{"name","count"}]，依count降冪排序。"""
    tree = ET.parse(path)
    rows = list(tree.getroot().iter(f"{{{NS['ss']}}}Row"))

    chapter = _row_cells(rows[4]).get(9, "").strip()
    date_from = (_row_cells(rows[5]).get(9, "") or "").strip()
    if not chapter or not date_from:
        return None

    months = months_back(date_from, chapter)

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
        members.append({"name": name, "count": count})

    members.sort(key=lambda m: (-m["count"], m["name"]))
    return chapter, months, members


def main():
    files = sorted(set(glob.glob(DOWNLOADS_GLOB)), key=os.path.getmtime)
    if not files:
        raise SystemExit(f"找不到任何PALMS報表檔案，請確認 {DOWNLOADS_GLOB} 底下有檔案")

    print(f"找到 {len(files)} 份PALMS檔案")

    chapters = {}  # chapter -> {months: members}, 同月數重複匯出取最後一份（mtime較新）
    for f in files:
        parsed = parse_palms_file(f)
        if parsed is None:
            print(f"  跳過（缺分會/從日期）：{os.path.basename(f)}")
            continue
        chapter, months, members = parsed
        chapters.setdefault(chapter, {})[months] = members
        print(f"  {chapter} 近{months}個月：{len(members)}位會員，來源={os.path.basename(f)}")

    output = {"chapters": {}}
    for chapter, snapshots in chapters.items():
        months_available = sorted(snapshots.keys())
        output["chapters"][chapter] = {
            "months_available": months_available,
            "snapshots": {str(m): snapshots[m] for m in months_available},
        }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n=== 完成，寫出 {OUT_PATH} ===")
    for chapter, data in output["chapters"].items():
        print(f"  {chapter}：{len(data['months_available'])}個時間節點 {data['months_available']}")


if __name__ == "__main__":
    main()
