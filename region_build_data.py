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
# - 2026-03-12 原key「Workshop」，行事曆真實場次是「曜董主題培訓」14:00-17:00 @安平路176號
# - 2026-07-06 原key「董事培訓 - Taiwan」，行事曆真實場次是「引薦+1對1工作坊(台北)」@集思北科大
# - 2026-07-17 原key「領導團隊培訓」，行事曆當天是「LTRT」20:00-21:30 @ZOOM，LTRT不計分，整筆移除不算培訓
# (2026-03-14 原key「董事培訓 - Taiwan」保留不動：行事曆當天是M2培訓，M2官方類別本來就是「董事培訓」，這筆本來就沒錯)
RECORD_TYPE_CORRECTIONS = {
    ("楊在珍", "2026-03-12", "Workshop"): "曜董主題培訓",
    ("楊在珍", "2026-07-06", "董事培訓 - Taiwan"): "引薦+1對1工作坊",
    ("楊在珍", "2026-07-17", "領導團隊培訓"): None,  # LTRT無分數，不能算培訓，整筆排除
}

# 教練通則(2026-08-17)：從2月起，只要地點是「安平路176號」的場次，佩君每一場都有出席(她是種子講師)，
# 但在珍不一定每場都有去；比對月曆後找出「地點=安平路176號、但佩君官方報表完全沒被登記」的場次逐筆補上。
# event_type採官方對應類別(M1/M2→董事培訓)，無對應官方類別的場次(曜董系列)用行事曆原始名稱。
MANUAL_ATTENDANCE_CORRECTIONS = [
    {"name": "陳佩君", "chapter": "真誠", "event_date": "2026-03-12", "event_type": "曜董主題培訓"},
    {"name": "陳佩君", "chapter": "真誠", "event_date": "2026-03-13", "event_type": "曜董DnA季度培訓"},
    {"name": "陳佩君", "chapter": "真誠", "event_date": "2026-03-14", "event_type": "董事培訓 - Taiwan"},
    {"name": "陳佩君", "chapter": "真誠", "event_date": "2026-06-12", "event_type": "曜董DnA季度培訓"},
    {"name": "陳佩君", "chapter": "真誠", "event_date": "2026-07-06", "event_type": "引薦+1對1工作坊"},
]


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
    all_records = official_records + msp_records + seed_fill_records + MANUAL_ATTENDANCE_CORRECTIONS

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
    print("data.json done, %d records (%d official + %d MSP + %d seed-teacher-fill + %d manual-correction), %d chapters" % (
        len(public_records), len(official_records), len(msp_records), len(seed_fill_records),
        len(MANUAL_ATTENDANCE_CORRECTIONS), len(chapters)))


if __name__ == "__main__":
    main()
