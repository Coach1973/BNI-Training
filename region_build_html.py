# -*- coding: utf-8 -*-
"""讀 data.json + region_template.html，產生 index.html（全區培訓總覽App）。
更新資料：改 region_build_data.py 重跑，再跑這支。
"""
import json
import io


def main():
    data = json.load(io.open("data.json", encoding="utf-8"))
    template = io.open("region_template.html", encoding="utf-8").read()

    records_json = json.dumps(data["records"], ensure_ascii=False)
    roster_json = json.dumps(data["roster"], ensure_ascii=False)
    date_range = "%s ~ %s" % tuple(data["date_range"])

    html = template.replace("__RECORDS_JSON__", records_json)
    html = html.replace("__ROSTER_JSON__", roster_json)
    html = html.replace("__DATE_RANGE__", date_range)
    html = html.replace("__TOTAL_RECORDS__", str(len(data["records"])))

    with io.open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("index.html done, %d records embedded" % len(data["records"]))


if __name__ == "__main__":
    main()
