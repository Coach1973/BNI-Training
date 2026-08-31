# -*- coding: utf-8 -*-
"""
BNI大台南南區「來賓邀約查詢」公開頁面（比照培訓總覽風格）- 資料源建置腳本

資料來源：
  ~/Downloads/__-__-__-___31-08-2026_3-04_PM.xls
  （BNI Connect 官方「地區-查看來賓」SpreadsheetML XML，5.8MB，3718 筆，
   範圍 2018-08-08 ~ 2026-09-01，涵蓋 真富/真愛/真誠/真鑫/真鑽 5 個分會）

計算邏輯：
  依「Invited By + 分會」分組，取每組訪問日期最大值 = 該邀請人在該分會的最近一次邀約日期。
  公開頁只顯示 邀請人姓名/分會/日期（不顯示來賓個資，符合培訓總覽隱私原則）。

產出：guests_data.json（前端 JS 動態計算月數、不預先算好12種門檻）
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

# 公開頁只顯示的欄位（隱私原則：來賓個資不顯示）
PUBLIC_FIELDS = ("inviter", "chapter", "visit_date", "guest_name", "type")


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
        surname = cells.get(1, "").strip()
        given = cells.get(2, "").strip()
        type_ = cells.get(20, "").strip()

        if not chapter or not visit_date_raw or not inviter:
            continue

        # 解析訪問日期（ISO 格式：2025-04-02T00:00:00，取 YYYY-MM-DD）
        try:
            visit_date = visit_date_raw.split("T")[0]
            # 驗證格式
            datetime.strptime(visit_date, "%Y-%m-%d")
        except Exception:
            continue

        guest_name = (surname + " " + given).strip()

        records.append({
            "inviter": inviter,
            "chapter": chapter,
            "visit_date": visit_date,
            "guest_name": guest_name,
            "type": type_,
        })
    return records


def build_groups(records):
    """依「inviter + chapter」分組，每組只留訪問日期最大值（最近一次）。"""
    groups = {}  # (inviter, chapter) -> dict
    for r in records:
        key = (r["inviter"], r["chapter"])
        existing = groups.get(key)
        if existing is None or r["visit_date"] > existing["visit_date"]:
            groups[key] = r
    return list(groups.values())


def main():
    if not os.path.exists(XLS_PATH):
        sys.exit(f"找不到資料源 {XLS_PATH}")

    print(f"讀取 {XLS_PATH}...")
    records = parse_xls_to_records(XLS_PATH)
    print(f"  有效來賓紀錄：{len(records)}")

    print("依 (邀請人, 分會) 分組，取最近一次...")
    groups = build_groups(records)
    print(f"  分組後的 (邀請人, 分會) 組合：{len(groups)}")

    # 計算一些統計資訊給前端顯示
    chapters = sorted(set(g["chapter"] for g in groups))
    inviters = sorted(set(g["inviter"] for g in groups))
    stats = {
        "total_records": len(records),
        "total_groups": len(groups),
        "chapters": chapters,
        "unique_inviters": len(inviters),
        "inviter_sample": inviters[:5],  # 前 5 個範例
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }

    output = {
        "stats": stats,
        "groups": groups,
    }

    print(f"寫出 {OUT_PATH}...")
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n=== 完成 ===")
    print(f"  涵蓋分會：{', '.join(chapters)}")
    print(f"  獨立邀請人數：{len(inviters)}")
    print(f"  範例邀請人：{', '.join(inviters[:5])}")

    # 舉 2-3 個範例邀請人驗證
    print(f"\n=== 驗證（3 個範例）===")
    for name in ["吳 志煒", "謝 盛峯", "許 瀅瀅"]:
        for g in groups:
            if g["inviter"] == name:
                print(f"  {g['inviter']} / {g['chapter']} → 最近一次邀約：{g['visit_date']}")
                break

    # 額外：同一邀請人出現在多個分會的狀況
    multi_chapter_inviters = {}
    for g in groups:
        multi_chapter_inviters.setdefault(g["inviter"], set()).add(g["chapter"])
    multi = {inv: chs for inv, chs in multi_chapter_inviters.items() if len(chs) > 1}
    print(f"\n=== 額外統計：跨多分會的邀請人 {len(multi)} 位 ===")
    for inv, chs in list(multi.items())[:5]:
        print(f"  {inv}: {', '.join(sorted(chs))}")


if __name__ == "__main__":
    main()
