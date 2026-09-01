# -*- coding: utf-8 -*-
"""
BNI大台南南區「來賓邀約排行榜」公開頁面（比照培訓總覽 index.html 排行榜邏輯）- 資料源建置腳本

資料來源：
  ~/Downloads/__-__-__-___31-08-2026_3-04_PM.xls
  （BNI Connect 官方「地區-查看來賓」SpreadsheetML XML，5.8MB，原始 3718 筆，
   範圍 2018-08-08 ~ 2026-09-01，原始資料涵蓋 真富/真愛/真誠/真鑫/真鑽 5 個分會，
   但只留目前有在營運的 真誠/真鑫/真鑽 3 分會，跟培訓總覽(index.html)範圍一致）

計算邏輯（2026-09-01教練親口指示：跟 index.html 一模一樣，不要自己另外發明邏輯）：
  輸出每一筆原始造訪紀錄（不預先分組/不預先算最近一次），前端依「所選時間範圍」
  篩選出落在範圍內的紀錄，再依「邀請人」統計次數排名，邏輯逐字對照
  index.html 的 RECORDS → filterByWindow → renderRanking 這條路徑。

產出：guests_data.json（前端 JS 動態依時間窗篩選並統計次數，不預先分組）
"""
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

# 資料源（BNI Connect 官方匯出，SpreadsheetML XML 格式）
XLS_PATH = os.path.expanduser("~/Downloads/__-__-__-___31-08-2026_3-04_PM.xls")

# 輸出位置（跟 region_build_data.py 的 data.json 同層）
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guests_data.json")

# 公開頁只輸出的欄位（隱私原則：來賓姓名/公司/職業/電話/Email/地址一律不輸出）
PUBLIC_FIELDS = ("inviter", "chapter", "visit_date")

# 2026-09-01教練親口指示：只留目前有在營運的分會，跟培訓總覽(index.html)範圍一致。
# 真富/真愛目前翻轉中、連正式例會都沒有，不列入。
OPERATING_CHAPTERS = {"真誠", "真鑫", "真鑽"}


def parse_xls_to_records(xls_path):
    """讀 SpreadsheetML XML 格式 .xls 檔，吐出每筆來賓造訪紀錄 dict。

    欄位 Index（從 1 起算）：
      1:姓氏 2:名字 3:公司 4:職業 6:Email 7:電話 8~9:地址 10:城市 11:狀態
      14:郵編 15:國家 16:分會 18:訪問日期 19:Invited By 20:Type
    """
    if not os.path.exists(xls_path):
        sys.exit(f"找不到資料源 {xls_path}，請確認檔案還在 ~/Downloads/")

    ns = {
        "ss": "urn:schemas-microsoft-com:office:spreadsheet",
    }

    tree = ET.parse(xls_path)
    root = tree.getroot()

    records = []
    for row_idx, row in enumerate(root.iter(f"{{{ns['ss']}}}Row")):
        # 跳過頁首/欄位標題列（前 11 列是 header）
        if row_idx < 11:
            continue

        cells = {}  # Index 1-based -> text
        for cell in row.findall(f"{{{ns['ss']}}}Cell"):
            idx_str = cell.get(f"{{{ns['ss']}}}Index")
            idx = int(idx_str) if idx_str else None
            data = cell.find(f"{{{ns['ss']}}}Data")
            if data is not None and idx is not None:
                cells[idx] = data.text or ""

        # 必要欄位：分會(16) / 訪問日期(18) / Invited By(19)
        chapter = cells.get(16, "").strip()
        visit_date_raw = cells.get(18, "").strip()
        inviter = cells.get(19, "").strip()

        if not chapter or not visit_date_raw or not inviter:
            continue

        # 解析訪問日期（ISO 格式：2025-04-02T00:00:00，取 YYYY-MM-DD）
        try:
            visit_date = visit_date_raw.split("T")[0]
            # 驗證格式
            datetime.strptime(visit_date, "%Y-%m-%d")
        except Exception:
            continue

        records.append({
            "inviter": inviter,
            "chapter": chapter,
            "visit_date": visit_date,
        })
    return records


def main():
    if not os.path.exists(XLS_PATH):
        sys.exit(f"找不到資料源 {XLS_PATH}")

    print(f"讀取 {XLS_PATH}...")
    records = parse_xls_to_records(XLS_PATH)
    print(f"  有效來賓紀錄：{len(records)}")

    records = [r for r in records if r["chapter"] in OPERATING_CHAPTERS]
    print(f"  只留營運中分會（{'/'.join(sorted(OPERATING_CHAPTERS))}）後：{len(records)}")

    # 計算一些統計資訊給前端顯示（全期間，不受時間窗篩選影響）
    chapters = sorted(set(r["chapter"] for r in records))
    inviters = sorted(set(r["inviter"] for r in records))
    stats = {
        "total_records": len(records),
        "chapters": chapters,
        "unique_inviters": len(inviters),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }

    output = {
        "stats": stats,
        "records": records,
    }

    print(f"寫出 {OUT_PATH}...")
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n=== 完成 ===")
    print(f"  涵蓋分會：{', '.join(chapters)}")
    print(f"  獨立邀請人數：{len(inviters)}")

    # 驗證：模擬前端「近6個月」邏輯，看排行榜前3名是誰
    print(f"\n=== 驗證（比照 index.html renderRanking 邏輯，近6個月TOP3）===")
    from datetime import date
    today = date.today()
    y, m = today.year, today.month - 6
    while m <= 0:
        m += 12
        y -= 1
    cutoff = f"{y:04d}-{m:02d}-{today.day:02d}"
    counts = {}
    for r in records:
        if r["visit_date"] >= cutoff:
            key = r["inviter"]
            counts.setdefault(key, {"chapter": r["chapter"], "count": 0})
            counts[key]["count"] += 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1]["count"], kv[0]))
    for name, info in ranked[:3]:
        print(f"  {name}（{info['chapter']}）→ {info['count']} 位來賓")


if __name__ == "__main__":
    main()
