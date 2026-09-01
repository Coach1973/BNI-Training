# -*- coding: utf-8 -*-
"""讀 guests_data.json + guests_template.html，產生 guests.html。

更新資料：
  - 教練匯出新的PALMS報表到 ~/Downloads/ → 重跑 guests_build_data.py
  - guests_template.html 改了 UI → 重跑這支
"""
import io
import json


def main():
    data = json.load(io.open("guests_data.json", encoding="utf-8"))
    template = io.open("guests_template.html", encoding="utf-8").read()

    chapters_json = json.dumps(data["chapters"], ensure_ascii=False)
    chapter_names = "・".join(sorted(data["chapters"].keys()))

    html = template.replace("__CHAPTERS_DATA_JSON__", chapters_json)
    html = html.replace("__CHAPTERS__", chapter_names)

    with io.open("guests.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("guests.html done, chapters embedded: %s" % ", ".join(sorted(data["chapters"].keys())))


if __name__ == "__main__":
    main()
