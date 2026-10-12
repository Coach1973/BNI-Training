# -*- coding: utf-8 -*-
"""
離會會員過濾（2026-10-13 教練交辦）：培訓總覽、來賓總覽都不要留下已離會的人。

怎麼判斷離會（教練原話：「看戰情表，只要沒在名單上的都代表離會」）：
  在籍名單 ＝ 真鑽／真鑫／真誠三個戰情表 members 表裡 left_chapter=0 的人
  不在在籍名單裡的人 ＝ 離會
  戰情表還沒標離會、但教練已確認離會的人，寫在下面 EXPLICIT_DEPARTED（例如柯朝陽、徐偉倫）

戰情表在這台電腦才讀得到；讀得到時順便把在籍名單存成 active_roster_snapshot.json，
讀不到（例如在別台機器重建）就用那份存檔，不會因為少了戰情表就讓離會的人冒出來。

用法：
  python3 departed.py          # 直接過濾 data.json、guests_data.json 並印出被拿掉的人
  被 region_build_data.py、guests_build_data.py 在寫檔前呼叫（filter_training／filter_guests）
"""
import io
import json
import os
import re
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
GITHUB = os.path.expanduser("~/github_repos")
DASHBOARDS = {
    "真鑽": os.path.join(GITHUB, "zhenzuan-guests", "zhenzuan_guests.db"),
    "真鑫": os.path.join(GITHUB, "zhenxin-guests", "zhenxin_guests.db"),
    "真誠": os.path.join(GITHUB, "zhencheng-guests", "zhencheng_guests.db"),
}
SNAPSHOT = os.path.join(HERE, "active_roster_snapshot.json")

# 教練確認已離會、但戰情表還沒標的人（日期＝會籍結束日）。信用證有開的離會者也列在這裡，
# 避免戰情表日後又把名字加回來。
EXPLICIT_DEPARTED = {
    "柯朝陽",  # 真鑽，2026-10-01 離會（教練 10/13：培訓 Top10 第 5 名要拿掉）
    "徐偉倫",  # 真鑫，2026-10-08 離會（教練 10/13：近 6 個月來賓總覽要拿掉）
    "蘇志揚",  # 真鑽，2026-08-31 離會
    "范郁琪", "薛如媛",  # 真鑫，2026-10-08 離會
    "杜亞洛", "劉彥彬", "謝盛峯", "柯炫任", "張晴晴", "陳俊源",  # 真鑫，9 月底離會（信用證 10/02 開立）
    "盧尚政", "趙世穎", "郭素玲",  # 真誠
}

# 同一個人在報表裡的不同寫法（姓放最後、同音字），算同一個人，不能因為寫法不同被當成離會
ALIASES = {
    "姵彤蔡": "蔡姵彤", "蔡珮彤": "蔡姵彤",  # 真鑫在籍，PALMS 把姓放最後／MSP 名單寫同音字
    "連晧宇": "連皓宇", "楊為凱": "楊凱為", "林尹渟": "林尹渰",  # 真鑫在籍，MSP 名單與官方報表寫法不同（10/13 逐人核對出席日期確認是同一人）
    "謝盛峰": "謝盛峯",  # 真鑫離會者的另一種寫法
}


def _key(name):
    """比對用：去掉空白、括號註記、英文名（「林佳伶 Lavi」＝「林佳伶」）。"""
    return re.sub(r"[\sA-Za-z]", "", re.sub(r"[（(].*?[）)]", "", name or ""))


def _canon(name):
    k = _key(name)
    return ALIASES.get(k, k)


def _read_dashboards():
    keys = set()
    for path in DASHBOARDS.values():
        if not os.path.exists(path):
            return None
        conn = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
        for (name,) in conn.execute("SELECT name FROM members WHERE left_chapter = 0"):
            keys.add(_canon(name))
        conn.close()
    return keys


def active_keys():
    keys = _read_dashboards()
    if keys is not None:
        with io.open(SNAPSHOT, "w", encoding="utf-8") as f:
            json.dump({"說明": "三個戰情表 members（left_chapter=0）的在籍姓名，departed.py 自動產生", "names": sorted(keys)},
                      f, ensure_ascii=False, indent=1)
        return keys
    with io.open(SNAPSHOT, encoding="utf-8") as f:
        return set(json.load(f)["names"])


class Filter:
    def __init__(self):
        self.active = active_keys()
        self.explicit = {_canon(n) for n in EXPLICIT_DEPARTED}
        self.removed = set()

    def departed(self, name):
        k = _canon(name)
        gone = k in self.explicit or k not in self.active
        if gone:
            self.removed.add(name)
        return gone


# 同一個人兩種寫法時，培訓總覽只留一個（教練 2026-10-13：「林佳伶 Lavi」就留這一個）
MERGE_NAMES = {"林佳伶": "林佳伶 Lavi"}


def merge_names(records):
    """把舊寫法改成保留的寫法；合併後同一天重複的（官方報表與 MSP 名單各記一次）只留原本就用保留寫法的那筆。"""
    keep = {(r["name"], r["event_date"]) for r in records if r["name"] in MERGE_NAMES.values()}
    out = []
    for r in records:
        new = MERGE_NAMES.get(r["name"])
        if new:
            if (new, r["event_date"]) in keep:
                continue
            keep.add((new, r["event_date"]))
            r = dict(r, name=new)
        out.append(r)
    return out


def clean_training_records(records, f=None):
    f = f or Filter()
    return [r for r in merge_names(records) if not f.departed(r["name"])]


def filter_training(data, f=None):
    """培訓總覽 data.json：拿掉離會者的出席紀錄與名冊，同人兩種寫法合併。"""
    f = f or Filter()
    data["records"] = clean_training_records(data["records"], f)
    seen, roster = set(), []
    for r in data["roster"]:
        name = MERGE_NAMES.get(r["name"], r["name"])
        if f.departed(name) or name in seen:
            continue
        seen.add(name)
        roster.append(dict(r, name=name))
    data["roster"] = roster
    return f


def filter_guests(data, f=None):
    """來賓總覽 guests_data.json：拿掉離會者的邀約排行與現任名單。"""
    f = f or Filter()
    for ch in data["chapters"].values():
        for months, members in ch["snapshots"].items():
            ch["snapshots"][months] = [m for m in members if not f.departed(m["name"])]
        ch["roster"] = [m for m in ch.get("roster", []) if not f.departed(m["name"])]
        ch["extra_counts"] = {k: v for k, v in ch.get("extra_counts", {}).items() if not f.departed(k)}
    return f


def _apply(path, fn, indent):
    p = os.path.join(HERE, path)
    with io.open(p, encoding="utf-8") as fh:
        data = json.load(fh)
    f = fn(data)
    with io.open(p, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=indent)
    print("%s：拿掉 %d 人 %s" % (path, len(f.removed), sorted(f.removed)))


if __name__ == "__main__":
    _apply("data.json", filter_training, 1)
    _apply("guests_data.json", filter_guests, 2)
