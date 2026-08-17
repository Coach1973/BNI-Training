# -*- coding: utf-8 -*-
"""
BNI大台南南區 全區培訓總覽（公開版）- 資料源建置腳本

兩條資料來源合併(2026-08-17教練點出這兩份是平行資料，官方報表沒收錄教練自己開的MSP課)：
1. BNI Connect官方匯出報表 → 私有大腦repo：
   mac-openclaw-workflows/claude-brain/data/bni_region_training_raw.json
   （這支腳本讀那份私有檔案，只挑公開安全欄位，電話/email/角色/入會日不進來，不對外公開）
2. 教練自己追蹤的MSP初階/進階/主題培訓6場次 → 讀本repo內 msp_build_data.py 的 PEOPLE_RAW
   （官方報表完全沒有這6場，缺這塊首頁的時間窗/排名就不完整）

更新資料：
  - 官方報表有新的匯出，重新跑一次匯入腳本更新 bni_region_training_raw.json
  - MSP新場次，改 msp_build_data.py 的 PEOPLE_RAW/SESSIONS
再回來跑這支 + region_build_html.py 即可。
"""
import json
import io
import os
import sys

RAW_PATH = r"E:\Claude-Data\mac-openclaw-workflows\claude-brain\data\bni_region_training_raw.json"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import msp_build_data as msp

# session id -> 實際西元日期（msp_build_data.py的label是"4/13 進階MSP"這種日期+類型混合字串，
# 這裡拆開成獨立的date跟type，才能跟官方報表的event_date/event_type同格式合併）
MSP_SESSION_DATE = {
    "0413": "2026-04-13",
    "0511": "2026-05-11",
    "0611": "2026-06-11",
    "0615": "2026-06-15",
    "0720": "2026-07-20",
    "0817": "2026-08-17",
}
MSP_SESSION_TYPE = {
    "0413": "進階MSP",
    "0511": "初階MSP",
    "0611": "主題培訓",
    "0615": "進階MSP",
    "0720": "初階MSP",
    "0817": "主題培訓",
}
MSP_ATTENDED_STATUS = (msp.P, msp.T, msp.SH)  # 出席／講師0元／分享0元都算真的有到場受訓

# 教練2026-08-17裁示：只留真鑫/真誠/真鑽3分會，真愛/真富資料整個拿掉
CHAPTER_ALLOWLIST = {"真鑫", "真誠", "真鑽"}

# 已離會會員，教練口述指定不列入計算（陸續補充，姓名須完全比對官方報表用字）
DEPARTED_MEMBERS = {
    "江維宣",  # 真誠分會，教練2026-08-17指定
    "陳家煖", "陳欣佑", "江紫緹",  # 教練2026-08-18指定，MSP名單已刪除，這裡是防未來官方報表補進他們的舊紀錄
}


def build_msp_records():
    records = []
    for name, (chapter, att) in msp.PEOPLE_RAW.items():
        for sid, status in zip(msp.SID, att):
            if status in MSP_ATTENDED_STATUS:
                records.append({
                    "chapter": chapter,
                    "name": name,
                    "event_date": MSP_SESSION_DATE[sid],
                    "event_type": MSP_SESSION_TYPE[sid],
                })
    return records


# ---- 種子講師歷史補值(2026-08-17教練裁示) ----
# 教練說明：陳佩君(真誠分會種子講師)從入會以來每月都有上MSP/進階MSP，但只有今年4月起6場
# 有留下逐場紀錄。教練的規則：「Excel裡本來就有標註MSP/進階MSP的月份不重複計算，沒寫的月份才補」。
# MSP=BNI官方「Member Success Program」，對應官方報表裡的「會員成功專案」事件類型——
# 這個推論是本次判斷，非教練逐字確認，若跟教練理解不同要再對一次。
# 做法：以「會員成功專案」(官方) + MSP初階/進階(教練自訂6場) 兩邊合起來算「已覆蓋的月份」，
# 只在真的沒有任何來源覆蓋的月份，才補1筆估算值(每月15日，標「MSP(估算)」跟真實日期做區隔)。
SEED_TEACHER_FILL = {
    "陳佩君": {
        "chapter": "真誠",
        "start": "2025-05",  # 教練提供的入會月份(BNI Connect Induction Date=2025-05-08)
        "end": "2026-08",    # 涵蓋到資料最新月份
        "covered_event_type": "會員成功專案",  # 官方報表裡視同MSP的類別
    },
}


# ---- 教練逐月核對月曆後更正：楊在珍自己key單類別選錯+官方報表沒有的真實出席(2026-08-17) ----
# 教練親自比對 https://tainan-calender.netlify.app/ 全年度行事曆後確認：
# 這不是官方報表漏登記，是楊在珍key單時類別選錯，佩君這幾場其實都有出席，只是完全沒被登記。
# 教練並補充規則：①M1/M2培訓在系統上官方類別就叫「董事培訓」②LTRT沒有分數，不能算培訓。
#
# 楊在珍原始記錄類別更正(官方報表裡她自己key的類別是錯的)：
# - 2026-02-13 原key「領導團隊培訓」，教練確認當天其實是「LTRT」(過年提前1週場)，LTRT不計分，整筆移除
# - 2026-03-12 原key「Workshop」，行事曆真實場次是「曜董主題培訓」14:00-17:00 @安平路176號
# - 2026-07-06 原key「董事培訓 - Taiwan」，行事曆真實場次是「引薦+1對1工作坊(台北)」@集思北科大
# - 2026-07-17 原key「領導團隊培訓」，行事曆當天是「LTRT」20:00-21:30 @ZOOM，LTRT不計分，整筆移除不算培訓
# (2026-03-14 原key「董事培訓 - Taiwan」保留不動：行事曆當天是M2培訓，M2官方類別本來就是「董事培訓」，這筆本來就沒錯)
RECORD_TYPE_CORRECTIONS = {
    ("楊在珍", "2026-02-13", "領導團隊培訓"): None,  # LTRT無分數，教練確認不能算培訓，整筆排除
    ("楊在珍", "2026-03-12", "Workshop"): "曜董主題培訓",
    ("楊在珍", "2026-07-06", "董事培訓 - Taiwan"): "引薦+1對1工作坊",
    ("楊在珍", "2026-07-17", "領導團隊培訓"): None,  # LTRT無分數，不能算培訓，整筆排除
}

# 教練通則(2026-08-17)：從2月起，只要地點是「安平路176號」的場次，佩君每一場都有出席(她是種子講師)，
# 但在珍不一定每場都有去；比對月曆後找出「地點=安平路176號、但佩君官方報表完全沒被登記」的場次逐筆補上。
# event_type採官方對應類別(M1/M2→董事培訓)，無對應官方類別的場次(曜董系列)用行事曆原始名稱。
# (3/13、6/12「曜董DnA季度培訓」改用下方DNA_QUARTERLY_ATTENDANCE整個DnA團隊的真實名單處理，不在這裡重複列)
MANUAL_ATTENDANCE_CORRECTIONS = [
    {"name": "陳佩君", "chapter": "真誠", "event_date": "2026-03-12", "event_type": "曜董主題培訓"},
    {"name": "陳佩君", "chapter": "真誠", "event_date": "2026-03-14", "event_type": "董事培訓 - Taiwan"},
    {"name": "陳佩君", "chapter": "真誠", "event_date": "2026-07-06", "event_type": "引薦+1對1工作坊"},
]

# ---- DnA團隊季度培訓真實出席名單(2026-08-17，教練指定對照 https://coach1973.github.io/bni-dna/) ----
# 「曜董季度培訓」＝DnA團隊戰情儀表板裡3/6/9/12月那一次(該月剛好是安平路176號實體場，其餘月份是ZOOM月例會)。
# 教練原話：「這個網址上面有出現的人，都要算培訓」——不限佩君/在珍，DnA團隊19人只要當月標「出席」就算。
# 9月/12月尚未發生(資料範圍到今天2026-08-17)，故只處理3/13、6/12兩場已發生的。
DNA_TEAM_CHAPTER = {
    "郭政輝": "真鑽", "邱南寅": "真鑽", "陳佩君": "真誠", "李孟哲": "真鑽",
    "傅恩平": "真鑽", "林佳伶": "真誠", "柯朝陽": "真鑽", "蔡丞弘": "真鑽",
    "楊仁豪": "真鑽", "許朝竣": "真鑽", "羅琳": "真鑽", "謝緯翔": "真鑽",
    "顏淳峯": "真鑽", "楊尚儒": "真鑽", "楊在珍": "真誠", "張敬雍": "真鑽",
    "王彤": "真誠", "莊弼翔": "真鑽", "張騰文": "真鑽",
}
DNA_QUARTERLY_ATTENDANCE = {
    "2026-03-13": [  # 謝緯翔、顏淳峯該月缺席，莊弼翔/張騰文8月才入隊尚未存在
        "郭政輝", "邱南寅", "陳佩君", "李孟哲", "傅恩平", "林佳伶", "柯朝陽", "蔡丞弘",
        "楊仁豪", "許朝竣", "羅琳", "楊尚儒", "楊在珍", "張敬雍", "王彤",
    ],
    "2026-06-12": [  # 蔡丞弘、許朝竣該月缺席
        "郭政輝", "邱南寅", "陳佩君", "李孟哲", "傅恩平", "林佳伶", "柯朝陽",
        "楊仁豪", "羅琳", "謝緯翔", "顏淳峯", "楊尚儒", "楊在珍", "張敬雍", "王彤",
    ],
}


def build_dna_quarterly_records(existing_records):
    covered = set((r["name"], r["event_date"]) for r in existing_records)
    records = []
    for date, names in DNA_QUARTERLY_ATTENDANCE.items():
        for name in names:
            if (name, date) in covered:
                continue
            records.append({
                "chapter": DNA_TEAM_CHAPTER[name],
                "name": name,
                "event_date": date,
                "event_type": "曜董DnA季度培訓",
            })
    return records


# ---- 教練另一對話框統計1-3月MSP培訓費發票總次數，回頭補進系統(2026-08-18) ----
# 教練原話：「保證次數一定是正確的」(依$300/場發票金額換算)，但不知道每個月確切幾場。
# 教練給的月份分配規則：1場→1月；2場→1、2月各一場；3場→1、2、3月各一場；4場→1、2月各一場、3月兩場。
# 教練同時裁示：「如果Excel表裡面出現重複的，那就不用算；沒有的，才幫我加上去」——
# 逐月比對該人在該月是否已有任何記錄(來自官方報表/DnA/MSP等其他來源)，已有就跳過不重複加，
# 只在真的缺口的月份才補一筆。2月/3月有真實對應的MSP場次(2/9進階MSP、3/9初階MSP)，
# 用真實日期+類型；1月月曆資料遺失查無實際日期，教練確認「1月份就是一堂課」，用估算日期補上。
INVOICE_JAN_MAR_TOTALS = {
    "張敬雍": 4, "楊智帆": 4, "蔡丞弘": 4, "郭展鴻": 4, "張羽家": 4,
    "傅恩平": 3, "林尹渰": 3, "張騰文": 3, "康文彬": 3,
    "鄭綉美": 2, "李美花": 2, "陳佳玲": 2, "陳穗青": 2,
    "林宜宏": 1,
}


def invoice_month_targets(total):
    if total == 1:
        return {1: 1, 2: 0, 3: 0}
    if total == 2:
        return {1: 1, 2: 1, 3: 0}
    if total == 3:
        return {1: 1, 2: 1, 3: 1}
    if total == 4:
        return {1: 1, 2: 1, 3: 2}
    raise ValueError("教練的月份分配規則只定義到4場：%r" % total)


def build_invoice_jan_mar_records(existing_records, roster_chapter):
    existing_month_count = {}
    for r in existing_records:
        if r["name"] not in INVOICE_JAN_MAR_TOTALS:
            continue
        ym = r["event_date"][:7]
        if ym in ("2026-01", "2026-02", "2026-03"):
            m = int(ym[5:7])
            key = (r["name"], m)
            existing_month_count[key] = existing_month_count.get(key, 0) + 1

    records = []
    for name, total in INVOICE_JAN_MAR_TOTALS.items():
        chapter = roster_chapter.get(name)
        need = invoice_month_targets(total)
        for m in (1, 2, 3):
            have = existing_month_count.get((name, m), 0)
            to_add = max(0, need[m] - have)
            if to_add == 0:
                continue
            if m == 1:
                date, etype = "2026-01-15", "MSP(估算)"  # 行事曆1月資料遺失，教練確認1月就是1場
            elif m == 2:
                date, etype = "2026-02-09", "進階MSP"  # 行事曆真實場次
            else:
                date, etype = "2026-03-09", "初階MSP"  # 行事曆真實場次
            for _ in range(to_add):
                records.append({
                    "chapter": chapter, "name": name, "event_date": date, "event_type": etype,
                })
    return records


def month_range(start_ym, end_ym):
    y, m = map(int, start_ym.split("-"))
    ey, em = map(int, end_ym.split("-"))
    out = []
    while (y, m) <= (ey, em):
        out.append("%04d-%02d" % (y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


def build_seed_teacher_fill(official_records, msp_records):
    records = []
    for name, cfg in SEED_TEACHER_FILL.items():
        covered_months = set()
        for r in official_records:
            if r["name"] == name and r["event_type"] == cfg["covered_event_type"]:
                covered_months.add(r["event_date"][:7])
        for r in msp_records:
            if r["name"] == name:
                covered_months.add(r["event_date"][:7])
        for ym in month_range(cfg["start"], cfg["end"]):
            if ym in covered_months:
                continue
            records.append({
                "chapter": cfg["chapter"],
                "name": name,
                "event_date": "%s-15" % ym,
                "event_type": "MSP(估算)",
            })
    return records


def main():
    if not os.path.exists(RAW_PATH):
        raise SystemExit("私有原始資料找不到：%s（這份資料含電話/email，只放在私有大腦repo，不會進這個公開repo的git歷史）" % RAW_PATH)

    raw = json.load(io.open(RAW_PATH, encoding="utf-8"))
    official_records = [
        {
            "chapter": r["chapter"],
            "name": r["name"],
            "event_date": r["event_date"],
            "event_type": r["event_type"],
        }
        for r in raw
    ]

    # 套用楊在珍key單類別更正：對到(姓名,日期,原類別)就改類別，改成None代表整筆移除(LTRT不計分)
    corrected_records = []
    for r in official_records:
        key = (r["name"], r["event_date"], r["event_type"])
        if key in RECORD_TYPE_CORRECTIONS:
            new_type = RECORD_TYPE_CORRECTIONS[key]
            if new_type is None:
                continue  # 整筆排除，不算培訓
            r = dict(r, event_type=new_type)
        corrected_records.append(r)
    official_records = corrected_records

    msp_records = build_msp_records()

    # MSP名單裡分會欄位大多是None(教練原始資料只標了6人的分會)，
    # 用官方報表的姓名→分會對照回填，讓同一個人不會因為紀錄來源不同、分會欄位時有時無。
    # 先試完全比對，比對不到再試前綴(例如MSP名單的"林佳伶"要對到官方報表的"林佳伶 Lavi")。
    official_chapter = {r["name"]: r["chapter"] for r in official_records if r["chapter"]}
    for r in msp_records:
        if r["chapter"]:
            continue
        if r["name"] in official_chapter:
            r["chapter"] = official_chapter[r["name"]]
            continue
        for oname, ochapter in official_chapter.items():
            if oname.startswith(r["name"]) or r["name"].startswith(oname):
                r["chapter"] = ochapter
                break

    seed_fill_records = build_seed_teacher_fill(official_records, msp_records)
    dna_quarterly_records = build_dna_quarterly_records(
        official_records + msp_records + seed_fill_records + MANUAL_ATTENDANCE_CORRECTIONS
    )
    invoice_jan_mar_records = build_invoice_jan_mar_records(
        official_records + msp_records + seed_fill_records
        + MANUAL_ATTENDANCE_CORRECTIONS + dna_quarterly_records,
        official_chapter,
    )
    all_records = (
        official_records + msp_records + seed_fill_records
        + MANUAL_ATTENDANCE_CORRECTIONS + dna_quarterly_records + invoice_jan_mar_records
    )

    # 已離會會員先拿掉，再套分會白名單——分會不明(兩邊資料都對不到)的紀錄也一併排除，
    # 因為沒辦法確認他是不是真鑫/真誠/真鑽，寧可不顯示也不要顯示錯分會
    public_records = [
        r for r in all_records
        if r["name"] not in DEPARTED_MEMBERS and r["chapter"] in CHAPTER_ALLOWLIST
    ]

    chapters = sorted(set(r["chapter"] for r in public_records if r["chapter"]))
    event_types = sorted(set(r["event_type"] for r in public_records))
    dates = sorted(r["event_date"] for r in public_records)

    # 完整名冊(兩份來源合併去重)，給「近N個月沒上課的人」反向查詢用——
    # 這份名單一定要獨立存，不能只從filtered records反推，
    # 不然某人在選定時間窗內剛好0筆紀錄時，反向查詢會找不到這個人本身。
    roster = {}
    for r in public_records:
        name = r["name"]
        if name not in roster or (not roster[name] and r["chapter"]):
            roster[name] = r["chapter"]
    roster_list = sorted(
        [{"name": n, "chapter": c} for n, c in roster.items()],
        key=lambda x: (x["chapter"] or "zzz", x["name"])
    )

    data = {
        "generated_note": "公開版：官方BNI Connect報表 + 教練自訂MSP初階/進階/主題培訓 兩條資料源合併，只含分會/姓名/培訓類型/日期。電話/email/角色等個資在私有大腦repo維護，不放這裡。",
        "chapters": chapters,
        "event_types": event_types,
        "date_range": [dates[0], dates[-1]],
        "records": public_records,
        "roster": roster_list,
    }
    with io.open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("data.json done, %d records (%d official + %d MSP + %d seed-teacher-fill + %d manual-correction + %d dna-quarterly + %d invoice-jan-mar), %d chapters" % (
        len(public_records), len(official_records), len(msp_records), len(seed_fill_records),
        len(MANUAL_ATTENDANCE_CORRECTIONS), len(dna_quarterly_records), len(invoice_jan_mar_records), len(chapters)))


if __name__ == "__main__":
    main()
