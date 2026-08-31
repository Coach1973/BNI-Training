# -*- coding: utf-8 -*-
"""讀 guests_data.json + guests_template.html，產生 guests.html。

更新資料：
  - BNI Connect 重新匯出 ~/Downloads/...xls → 重跑 guests_build_data.py
  - guests_template.html 改了 UI → 重跑這支
"""
import io
import json


def main():
    data = json.load(io.open("guests_data.json", encoding="utf-8"))
    template = io.open("guests_template.html", encoding="utf-8").read()

    groups_json = json.dumps(data["groups"], ensure_ascii=False)
    stats_json = json.dumps(data["stats"], ensure_ascii=False)
    chapters_str = "・".join(data["stats"]["chapters"])
    total_records = data["stats"]["total_records"]

    html = template.replace("__GROUPS_JSON__", groups_json)
    html = html.replace("__STATS_JSON__", stats_json)
    html = html.replace("__TOTAL_RECORDS__", str(total_records))
    html = html.replace("__CHAPTERS__", chapters_str)

    with io.open("guests.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("guests.html done, %d groups embedded, %d total records" % (
        data["stats"]["total_groups"], total_records
    ))


if __name__ == "__main__":
    main()
