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
import os

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
    "許朝竣": ("真鑽", [P, A, A, P, P, N]),  # 7/20原批次2標缺席，但同一人在批次3(當時誤植為「許超尊」)明確標出席，採信出席
    "蔡瑞穠": (None, [A, A, A, P, P, N]),
    "莊政川": (None, [A, P, A, A, P, N]),
    "楊博丞": (None, [A, P, A, A, P, N]),
    "陳俊源": (None, [A, P, A, A, P, N]),
    "林佳慧": (None, [A, P, A, A, P, N]),
    "楊智帆": (None, [A, A, P, A, A, N]),
    "邱南寅": (None, [A, A, P, A, A, N]),

    "宋映璇": (None, [P, N, N, N, N, N]),
    "郭展鴻": (None, [P, N, N, N, N, N]),
    "葉建葳": (None, [P, N, N, N, N, N]),
    "陳新典": (None, [P, N, N, N, N, N]),
    "顏淳峯": (None, [P, N, N, N, N, N]),
    "楊仁豪": (None, [P, A, A, T, T, T]),  # 教練2026-08-18提供4-8月開票總清冊：6/15、7/20、8/17皆擔任講師

    "王聖凱": (None, [N, P, N, N, N, N]),
    "吳玫萱": (None, [N, P, N, N, N, N]),
    "黃鑫豊": (None, [N, P, N, N, N, N]),
    "吳志煒": (None, [N, P, N, N, N, N]),
    "林尹渟": ("真鑫", [N, P, N, N, N, N]),
    "楊尚儒": (None, [A, P, A, T, A, A]),  # 教練2026-08-18提供4-8月開票總清冊：6/15擔任講師
    "謝盛峰": ("真鑫", [N, P, N, N, N, N]),
    "范郁琪": ("真鑫", [N, P, N, N, N, N]),  # 教練更正原「范郁斌」姓名有誤

    "葉彤黎": ("真鑽", [N, N, N, P, N, N]),
    "伍芬群": ("真鑽", [N, N, N, P, N, N]),
    "吳三貴": ("真鑽", [N, N, N, P, N, N]),
    "林宜宏": (None, [N, N, N, P, N, N]),
    "徐偉倫": ("真鑫", [N, N, N, P, N, N]),
    "柯炫任": (None, [N, N, N, P, N, N]),
    "楊凱為": ("真鑫", [N, N, N, P, N, N]),

    "薛如媛": (None, [N, N, N, N, P, N]),
    "柯宗佑": (None, [N, N, N, N, P, N]),
    "林富郎": (None, [N, N, N, N, P, N]),
    "陳穗青": (None, [N, N, N, N, P, N]),
    "洪嘉妘": (None, [N, N, N, N, P, N]),
    "傅恩平": (None, [N, N, N, N, P, N]),
    "杜泱峻": ("真鑽", [N, N, N, N, P, N]),  # 教練2026-08-18更正：原「杜泱畯」姓名有誤
    "郭馨文": (None, [N, N, N, N, P, N]),

    # 教練2026-08-18提供4-8月開票總清冊，這兩人MSP名單原本完全沒有，全程0元免收費(講師/分享人)
    "王彤": ("真誠", [T, SH, N, T, T, T]),  # 4/13講者不收、5/11分享人，6/11清冊未提及
    "張羽家": ("真誠", [N, N, N, T, N, T]),  # 6/15、8/17擔任講師
}


RAW_PATH = r"E:\Claude-Data\mac-openclaw-workflows\claude-brain\data\bni_region_training_raw.json"


def load_official_chapter():
    """姓名→分會對照，來源是官方BNI Connect報表(全5分會，不受region app的3分會白名單限制，
    因為msp.html從來就沒有教練指示要排除真愛/真富)。"""
    if not os.path.exists(RAW_PATH):
        return {}
    raw = json.load(io.open(RAW_PATH, encoding="utf-8"))
    return {r["name"]: r["chapter"] for r in raw if r["chapter"]}


def backfill_chapter(name, official_chapter):
    if name in official_chapter:
        return official_chapter[name]
    for oname, ochapter in official_chapter.items():
        if oname.startswith(name) or name.startswith(oname):
            return ochapter
    return None


def main():
    official_chapter = load_official_chapter()
    people = []
    still_unknown = []
    for name, (chapter, att) in PEOPLE_RAW.items():
        if not chapter:
            chapter = backfill_chapter(name, official_chapter)
        if not chapter:
            still_unknown.append(name)
        attended = sum(1 for v in att if v in (P, T, SH))
        people.append({
            "name": name,
            "chapter": chapter,
            "attendance": row(att),
            "attended_count": attended,
        })
    data = {
        "generated_note": "公開版：只含姓名/分會/出席狀態。統編/發票/金額等資料在私有大腦repo維護，不放這裡。分會優先用教練原始資料，缺的用官方BNI Connect報表姓名比對回填。",
        "sessions": SESSIONS,
        "people": people,
    }
    with io.open("data_msp.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("data_msp.json done, %d people, %d still unknown chapter: %s" % (
        len(people), len(still_unknown), ", ".join(still_unknown)))


if __name__ == "__main__":
    main()
