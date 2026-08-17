# -*- coding: utf-8 -*-
"""
BNI大台南南區 全區培訓總覽（公開版）- 資料源建置腳本

來源：BNI Connect官方匯出報表(2026-08-17教練提供)，原始xlsx+完整欄位(含電話/email)
      存在私有大腦repo：mac-openclaw-workflows/claude-brain/data/bni_region_training_raw.json
      （這支腳本讀那份私有檔案，只挑公開安全欄位寫進這個公開repo的data.json，
      電話/email/角色/入會日這些不進來，不對外公開）

更新資料：教練若給新的匯出報表，重新跑一次匯入腳本更新 bni_region_training_raw.json，
再回來跑這支 + region_build_html.py 即可。
"""
import json
import io
import os

RAW_PATH = r"E:\Claude-Data\mac-openclaw-workflows\claude-brain\data\bni_region_training_raw.json"


def main():
    if not os.path.exists(RAW_PATH):
        raise SystemExit("私有原始資料找不到：%s（這份資料含電話/email，只放在私有大腦repo，不會進這個公開repo的git歷史）" % RAW_PATH)

    raw = json.load(io.open(RAW_PATH, encoding="utf-8"))
    public_records = [
        {
            "chapter": r["chapter"],
            "name": r["name"],
            "event_date": r["event_date"],
            "event_type": r["event_type"],
        }
        for r in raw
    ]
    chapters = sorted(set(r["chapter"] for r in public_records))
    event_types = sorted(set(r["event_type"] for r in public_records))
    dates = sorted(r["event_date"] for r in public_records)

    data = {
        "generated_note": "公開版：只含分會/姓名/培訓類型/日期。電話/email/角色等個資在私有大腦repo維護，不放這裡。",
        "chapters": chapters,
        "event_types": event_types,
        "date_range": [dates[0], dates[-1]],
        "records": public_records,
    }
    with io.open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("data.json done, %d records, %d chapters" % (len(public_records), len(chapters)))


if __name__ == "__main__":
    main()
