#!/usr/bin/env python3
"""
日报推送数据准备脚本。
读取 data.md + seen-pushed-ids.md，筛选未推送条目，输出 JSON。
同时将本次新 ID 写入 pending-push-ids.md，等待投递确认后再正式提交。
"""
import json
import re
import os

BASE_DIR = os.path.expanduser("~/.openclaw/workspace/xhs-jobs")


def read_pushed_ids():
    path = os.path.join(BASE_DIR, "seen-pushed-ids.md")
    ids = set()
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    ids.add(line)
    return ids


def parse_data_md():
    path = os.path.join(BASE_DIR, "data.md")
    if not os.path.exists(path):
        return []

    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|") or line.startswith("|---") or ("企业" in line and "部门" in line):
                continue

            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) >= 6:
                company = cols[0]
                department = cols[1]
                position = cols[2]
                contact = cols[3]
                url = cols[4]
                keyword = cols[5]

                match = re.search(r"/explore/([a-f0-9]+)", url)
                note_id = match.group(1) if match else url.strip()

                entries.append({
                    "company": company,
                    "department": department,
                    "position": position,
                    "contact": contact,
                    "link": url if url.startswith("http") else "https://www.xiaohongshu.com/explore/" + url,
                    "keyword": keyword,
                    "note_id": note_id,
                })
    return entries


def write_pending_ids(new_ids):
    """写入待确认 ID 文件（覆盖），等 verify 脚本根据投递状态决定是否正式提交。"""
    path = os.path.join(BASE_DIR, "pending-push-ids.md")
    with open(path, "w") as f:
        for nid in new_ids:
            f.write(nid + "\n")


def main():
    pushed_ids = read_pushed_ids()
    entries = parse_data_md()

    new_entries = [e for e in entries if e["note_id"] not in pushed_ids]

    if not new_entries:
        print(json.dumps({"no_new": True, "new_count": 0, "entries": []}, ensure_ascii=False))
        return

    with_contact = [e for e in new_entries if e["contact"] not in ("-", "", "\u2014")]
    without_contact = [e for e in new_entries if e["contact"] in ("-", "", "\u2014")]

    new_ids = [e["note_id"] for e in new_entries]

    # 写入 pending 文件，等待投递确认
    write_pending_ids(new_ids)

    result = {
        "no_new": False,
        "new_count": len(new_entries),
        "new_ids": new_ids,
        "with_contact": with_contact,
        "without_contact": without_contact,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
