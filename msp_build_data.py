# -*- coding: utf-8 -*-
"""
培訓紀錄總資料庫（公開版）- 資料源建置腳本

⚠️ 這個repo是公開的GitHub Pages，教練裁示只公開「姓名、分會、上過哪些培訓」，
   統編/載具/email/電話/應收金額/發票狀態一律不進這個repo，那些放在私有的大腦repo
   （mac-openclaw-workflows/claude-brain/data/training_records_master.py）維護，
   兩邊的出席資料本體(PEOPLE_RAW)要保持同步，改這邊記得也同步改那邊。

來源：knowledges/2026-08-17_培訓出席原始資料_教練提供.md（出席原始資料）
"""
import json
import io

SESSIONS = [
    {"id": "0413", "label": "4/13 進階MSP"},
    {"id": "0511", "label": "5/11 初階MSP"},
    {"id": "0611", "label": "6/11 主題培訓"},
    {"id": "0615", "label": "6/15 進階MSP"},
    {"id": "0720", "label": "7/20 初階MSP"},
    {"id": "0817", "label": "8/17 主題培訓"},
]
SID = [s["id"] for s in SESSIONS]

P, A, T, N = "present", "absent", "teacher0", "nodata"
SH = "share0"


def row(vals):
    return dict(zip(SID, vals))


# ---- 出席資料（61人：姓名 -> (分會, 出席陣列)）----
# 金額/統編/發票欄位不放這裡，公開版不需要，私有版另外維護。
PEOPLE_RAW = {
    "連晧宇": ("真鑫", [A, P, P, P, P, P]),
    "張騰文": ("真鑽", [P, P, P, P, A, P]),
    "康文彬": ("真鑽", [A, P, A, P, A, P]),
    "陳淑玲": ("真鑽", [A, A, A, A, P, P]),
    "蔡珮彤": ("真鑫", [A, A, A, A, P, P]),
    "陳佳玲": ("真鑽", [A, A, A, A, A, P]),

    "買駿航": (None, [A, P, P, P, P, N]),
    "柯朝陽": (None, [P, P, P, P, A, N]),
    "吳亞平": (None, [A, P, P, P, P, N]),
    "古禹澤": (None, [P, A, P, P, A, N]),
    "李美花": (None, [P, A, P, P, A, N]),
    "黃一恭": (None, [P, P, P, A, A, N]),
    "張敬雍": (None, [P, A, P, P, T, N]),
    "張晴晴": (None, [A, P, P, A, A, N]),
    "陳佩君": (None, [P, SH, P, T, T, T]),
    "楊在珍": (None, [P, P, T, T, T, N]),
    "林佳伶": (None, [A, SH, P, T, T, N]),
    "杜亞洛": (None, [A, P, A, P, A, N]),
    "劉彥彬": (None, [A, P, A, P, A, N]),
    "許朝竣": (None, [P, A, A, P, A, N]),
    "蔡瑞穠": (None, [A, A, A, P, P, N]),
    "莊政川": (None, [A, P, A, A, P, N]),
    "楊博丞": (None, [A, P, A, A, P, N]),
    "陳俊源": (None, [A, P, A, A, P, N]),
    "林佳慧": (None, [A, P, A, A, P, N]),
    "陳欣佑": (None, [A, A, P, A, A, N]),
    "陳家煖": (None, [A, A, P, A, A, N]),
    "楊智帆": (None, [A, A, P, A, A, N]),
    "邱南寅": (None, [A, A, P, A, A, N]),

    "宋映璇": (None, [P, N, N, N, N, N]),
    "江紫緹": (None, [P, N, N, N, N, N]),
    "郭展鴻": (None, [P, N, N, N, N, N]),
    "葉建葳": (None, [P, N, N, N, N, N]),
    "陳新典": (None, [P, N, N, N, N, N]),
    "顏淳峯": (None, [P, N, N, N, N, N]),
    "楊仁豪": (None, [P, N, N, N, N, N]),

    "王聖凱": (None, [N, P, N, N, N, N]),
    "吳玫萱": (None, [N, P, N, N, N, N]),
    "黃鑫豊": (None, [N, P, N, N, N, N]),
    "吳志煒": (None, [N, P, N, N, N, N]),
    "林尹渟": (None, [N, P, N, N, N, N]),
    "楊尚儒": (None, [N, P, N, N, N, N]),
    "謝盛峰": (None, [N, P, N, N, N, N]),
    "范郁斌": (None, [N, P, N, N, N, N]),

    "葉彤黎": (None, [N, N, N, P, N, N]),
    "伍芬群": (None, [N, N, N, P, N, N]),
    "吳三貴": (None, [N, N, N, P, N, N]),
    "林宜宏": (None, [N, N, N, P, N, N]),
    "徐偉倫": (None, [N, N, N, P, N, N]),
    "柯炫任": (None, [N, N, N, P, N, N]),
    "楊凱為": (None, [N, N, N, P, N, N]),

    "薛如媛": (None, [N, N, N, N, P, N]),
    "蔡佩彤": (None, [N, N, N, N, P, N]),
    "柯宗佑": (None, [N, N, N, N, P, N]),
    "許超尊": (None, [N, N, N, N, P, N]),
    "林富郎": (None, [N, N, N, N, P, N]),
    "陳穗青": (None, [N, N, N, N, P, N]),
    "洪嘉妘": (None, [N, N, N, N, P, N]),
    "傅恩平": (None, [N, N, N, N, P, N]),
    "杜泱畯": (None, [N, N, N, N, P, N]),
    "郭馨文": (None, [N, N, N, N, P, N]),
}


def main():
    people = []
    for name, (chapter, att) in PEOPLE_RAW.items():
        attended = sum(1 for v in att if v in (P, T, SH))
        people.append({
            "name": name,
            "chapter": chapter,
            "attendance": row(att),
            "attended_count": attended,
        })
    data = {
        "generated_note": "公開版：只含姓名/分會/出席狀態。統編/發票/金額等資料在私有大腦repo維護，不放這裡。",
        "sessions": SESSIONS,
        "people": people,
    }
    with io.open("data_msp.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("data_msp.json done, %d people" % len(people))


if __name__ == "__main__":
    main()
