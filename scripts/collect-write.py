#!/usr/bin/env python3
"""
写入采集结果到 data.md 和 seen-ids.md。
通过管道接收 JSON 输入。

输入格式:
{
  "entries": [{"id": "xxx", "company": "...", "department": "...", "position": "...", "contact": "...", "keyword": "..."}],
  "all_new_ids": ["id1", "id2"]
}
"""
import json
import re
import sys
import os
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.expanduser("~/.openclaw/workspace/xhs-jobs")


def main():
    input_data = json.loads(sys.stdin.read())
    entries = input_data.get("entries", [])
    all_new_ids = input_data.get("all_new_ids", [])

    # --- Update seen-ids.md ---
    seen_path = os.path.join(BASE_DIR, "seen-ids.md")
    existing_ids = set()
    if os.path.exists(seen_path):
        with open(seen_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    existing_ids.add(line)

    with open(seen_path, "a") as f:
        for nid in all_new_ids:
            if nid not in existing_ids:
                f.write(f"{nid}\n")

    if not entries:
        print(json.dumps({"written": 0}, ensure_ascii=False))
        return

    # --- Update data.md ---
    data_path = os.path.join(BASE_DIR, "data.md")
    bj_time = datetime.now(timezone(timedelta(hours=8)))
    today = bj_time.strftime("%Y-%m-%d")

    existing_content = ""
    if os.path.exists(data_path):
        with open(data_path) as f:
            existing_content = f.read()

    # Build new rows
    new_rows = []
    for e in entries:
        link = f"https://www.xiaohongshu.com/explore/{e['id']}"
        company = e.get("company", "未知")
        department = e.get("department", "-")
        position = e.get("position", "-")
        contact = e.get("contact", "-")
        keyword = e.get("keyword", "-")
        row = f"| {company} | {department} | {position} | {contact} | {link} | {keyword} |"
        new_rows.append(row)

    table_header = "| 企业 | 部门 | 岗位 | 联系方式 | 笔记ID | 关键词 |\n|------|------|------|---------|--------|--------|"

    if f"## {today}" in existing_content:
        # Append to existing today section
        sections = existing_content.split(f"## {today}", 1)
        before = sections[0]
        after = sections[1]

        next_section = after.find("\n## ")
        if next_section == -1:
            today_section = after
            rest = ""
        else:
            today_section = after[:next_section]
            rest = after[next_section:]

        today_section = today_section.rstrip() + "\n" + "\n".join(new_rows) + "\n"
        new_content = before + f"## {today}" + today_section + rest
    else:
        new_section = f"\n## {today}\n\n{table_header}\n" + "\n".join(new_rows) + "\n"
        new_content = existing_content.rstrip() + "\n" + new_section

    # Archive if too large
    if len(new_content) > 15000:
        dates = re.findall(r"## (\d{4}-\d{2}-\d{2})", new_content)
        if len(dates) > 1:
            oldest_date = dates[0]
            oldest_start = new_content.find(f"## {oldest_date}")
            next_start = new_content.find(f"## {dates[1]}")
            oldest_section = new_content[oldest_start:next_start]

            archive_month = oldest_date[:7]
            archive_path = os.path.join(BASE_DIR, f"archive-{archive_month}.md")
            with open(archive_path, "a") as f:
                f.write(oldest_section + "\n")

            new_content = new_content[:oldest_start] + new_content[next_start:]

    with open(data_path, "w") as f:
        f.write(new_content)

    print(json.dumps({"written": len(entries), "date": today}, ensure_ascii=False))


if __name__ == "__main__":
    main()
