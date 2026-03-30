#!/usr/bin/env python3
"""
招聘信息查询统计脚本。
读取 data.md + archive-*.md，解析所有条目，支持排序和过滤，输出格式化文本或 JSON。
"""
import argparse
import glob
import json
import os
import re
import sys

BASE_DIR = os.path.expanduser("~/.openclaw/workspace/xhs-jobs")


def parse_md_file(filepath):
    """解析单个 MD 文件，返回条目列表（含日期）。"""
    entries = []
    current_date = None

    with open(filepath) as f:
        for line in f:
            line = line.strip()

            date_match = re.match(r"^## (\d{4}-\d{2}-\d{2})", line)
            if date_match:
                current_date = date_match.group(1)
                continue

            if not line.startswith("|") or line.startswith("|---") or ("企业" in line and "部门" in line):
                continue

            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) < 6:
                continue

            company = cols[0]
            department = cols[1]
            position = cols[2]
            contact = cols[3]
            url = cols[4]
            keyword = cols[5]

            # 提取 note_id
            match = re.search(r"/explore/([a-f0-9]+)", url)
            note_id = match.group(1) if match else ""

            # 确保 URL 完整
            if url and not url.startswith("http"):
                url = "https://www.xiaohongshu.com/explore/" + url

            entries.append({
                "date": current_date or "未知",
                "company": company,
                "department": department,
                "position": position,
                "contact": contact,
                "url": url,
                "keyword": keyword,
                "note_id": note_id,
            })

    return entries


def load_all_entries():
    """加载所有数据文件。"""
    entries = []

    # 加载 archive 文件
    archive_pattern = os.path.join(BASE_DIR, "archive-*.md")
    for path in sorted(glob.glob(archive_pattern)):
        entries.extend(parse_md_file(path))

    # 加载 data.md（当前数据）
    data_path = os.path.join(BASE_DIR, "data.md")
    if os.path.exists(data_path):
        entries.extend(parse_md_file(data_path))

    return entries


def filter_entries(entries, company=None, keyword=None, date_from=None, date_to=None):
    """按条件过滤。"""
    result = entries

    if company:
        kw = company.lower()
        result = [e for e in result if kw in e["company"].lower()]

    if keyword:
        kw = keyword.lower()
        result = [e for e in result if kw in e["keyword"].lower() or kw in e["position"].lower()]

    if date_from:
        result = [e for e in result if e["date"] >= date_from]

    if date_to:
        result = [e for e in result if e["date"] <= date_to]

    return result


def sort_entries(entries, sort_mode):
    """排序。"""
    if sort_mode == "company-date":
        return sorted(entries, key=lambda e: (e["company"], e["date"]))
    elif sort_mode == "date":
        return sorted(entries, key=lambda e: e["date"], reverse=True)
    elif sort_mode == "date-asc":
        return sorted(entries, key=lambda e: e["date"])
    elif sort_mode == "company":
        return sorted(entries, key=lambda e: e["company"])
    else:
        return entries


def format_text(entries, sort_mode):
    """格式化为类似每日推送的文本格式。"""
    if not entries:
        return "未找到匹配的招聘信息。"

    lines = []
    total = len(entries)
    companies = len(set(e["company"] for e in entries))
    date_range = sorted(set(e["date"] for e in entries))

    lines.append(f"📋 招聘信息统计")
    lines.append(f"共 {total} 条，涉及 {companies} 家企业")
    if date_range:
        lines.append(f"📅 {date_range[0]} ~ {date_range[-1]}")
    lines.append("")

    if sort_mode in ("company-date", "company"):
        # 按企业分组
        grouped = {}
        for e in entries:
            grouped.setdefault(e["company"], []).append(e)

        for company in sorted(grouped.keys()):
            group = grouped[company]
            lines.append(f"🏢 {company}（{len(group)} 条）")
            for e in sorted(group, key=lambda x: x["date"]):
                dept = f" | {e['department']}" if e["department"] and e["department"] != "-" else ""
                lines.append(f"  · {e['position']}{dept}")
                lines.append(f"    📅 {e['date']}")
                if e["contact"] and e["contact"] not in ("-", "", "—"):
                    lines.append(f"    📮 {e['contact']}")
                lines.append(f"    🔗 {e['url']}")
                lines.append(f"    🏷 {e['keyword']}")
            lines.append("")
    else:
        # 按日期分组
        grouped = {}
        for e in entries:
            grouped.setdefault(e["date"], []).append(e)

        date_keys = sorted(grouped.keys(), reverse=(sort_mode == "date"))
        for date in date_keys:
            group = grouped[date]
            lines.append(f"📅 {date}（{len(group)} 条）")
            for e in sorted(group, key=lambda x: x["company"]):
                dept = f" | {e['department']}" if e["department"] and e["department"] != "-" else ""
                lines.append(f"  🏢 {e['company']}")
                lines.append(f"  · {e['position']}{dept}")
                if e["contact"] and e["contact"] not in ("-", "", "—"):
                    lines.append(f"    📮 {e['contact']}")
                lines.append(f"    🔗 {e['url']}")
                lines.append(f"    🏷 {e['keyword']}")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="查询招聘信息")
    parser.add_argument("--sort", choices=["company-date", "date", "date-asc", "company"],
                        default="company-date", help="排序方式（默认: company-date）")
    parser.add_argument("--company", help="按企业名称过滤（模糊匹配）")
    parser.add_argument("--keyword", help="按关键词/岗位过滤（模糊匹配）")
    parser.add_argument("--date-from", help="起始日期（YYYY-MM-DD）")
    parser.add_argument("--date-to", help="截止日期（YYYY-MM-DD）")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="输出格式（默认: text）")
    parser.add_argument("--stats", action="store_true",
                        help="仅输出统计摘要")
    args = parser.parse_args()

    entries = load_all_entries()
    entries = filter_entries(entries,
                            company=args.company,
                            keyword=args.keyword,
                            date_from=args.date_from,
                            date_to=args.date_to)
    entries = sort_entries(entries, args.sort)

    if args.stats:
        companies = {}
        for e in entries:
            companies.setdefault(e["company"], 0)
            companies[e["company"]] += 1
        dates = sorted(set(e["date"] for e in entries))
        stats = {
            "total": len(entries),
            "companies": len(companies),
            "date_range": [dates[0], dates[-1]] if dates else [],
            "by_company": dict(sorted(companies.items(), key=lambda x: -x[1])),
        }
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return

    if args.format == "json":
        print(json.dumps(entries, ensure_ascii=False, indent=2))
    else:
        print(format_text(entries, args.sort))


if __name__ == "__main__":
    main()
