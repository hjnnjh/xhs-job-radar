#!/usr/bin/env python3
"""
小红书招聘信息搜索脚本。
根据时段选关键词，调用 mcporter 搜索，过滤已采集 ID，按标题分类，输出紧凑 JSON。
"""
import json
import subprocess
import os
import sys
import time
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.expanduser("~/.openclaw/workspace/xhs-jobs")
MCPORTER = os.path.expanduser("~/.npm-global/bin/mcporter")


def get_keywords():
    bj_time = datetime.now(timezone(timedelta(hours=8)))
    hour = bj_time.hour

    if 6 <= hour <= 9:
        return ["推荐算法实习", "推荐系统实习"]
    elif 12 <= hour <= 15:
        return ["算法工程师实习", "推荐算法暑期实习"]
    elif 18 <= hour <= 21:
        return ["推荐算法内推", "算法实习招聘"]
    else:
        return ["推荐算法实习", "推荐系统实习"]


def read_seen_ids():
    path = os.path.join(BASE_DIR, "seen-ids.md")
    ids = set()
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    ids.add(line)
    return ids


def search_feeds(keyword):
    cmd = [MCPORTER, "call", f'xiaohongshu-mcp.search_feeds(keyword: "{keyword}")']
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60,
            env={**os.environ, "PATH": f"{os.path.expanduser('~/.npm-global/bin')}:{os.environ.get('PATH', '')}"}
        )
        if result.returncode != 0:
            return None, result.stderr.strip()
        return json.loads(result.stdout), None
    except json.JSONDecodeError:
        return None, "mcporter output is not valid JSON"
    except subprocess.TimeoutExpired:
        return None, "mcporter call timed out (60s)"
    except Exception as e:
        return None, str(e)


def classify_title(title):
    title_lower = title.lower()

    filter_kw = ["面经", "一面", "二面", "三面", "面试", "凉经", "挂了", "拒了",
                  "参考答案", "复盘", "总结", "经验", "offer", "oc", "意向书"]
    for kw in filter_kw:
        if kw in title_lower:
            return "filter"

    keep_kw = ["招", "实习", "内推", "hc", "岗位", "团队招", "急招", "日常实习", "暑期"]
    for kw in keep_kw:
        if kw in title_lower:
            return "recruit"

    return "uncertain"


def extract_feeds(data):
    """Extract feed list from mcporter response (handles different response shapes)."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("feeds", "data", "items", "result"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # Check nested: data.data, data.feeds etc
        if "data" in data and isinstance(data["data"], dict):
            inner = data["data"]
            for key in ("feeds", "items", "list"):
                if key in inner and isinstance(inner[key], list):
                    return inner[key]
    return []


def main():
    keywords = get_keywords()
    seen_ids = read_seen_ids()

    all_results = []
    all_new_ids = []
    errors = []

    for i, keyword in enumerate(keywords):
        if i > 0:
            time.sleep(20)

        data, err = search_feeds(keyword)
        if err:
            errors.append(f"{keyword}: {err}")
            continue

        feeds = extract_feeds(data)

        for feed in feeds:
            model_type = feed.get("modelType", "")
            if model_type and model_type != "note":
                continue

            feed_id = feed.get("id", "")
            if not feed_id:
                continue

            note_card = feed.get("noteCard", {})
            title = note_card.get("displayTitle", feed.get("title", ""))
            xsec_token = feed.get("xsecToken", "")

            all_new_ids.append(feed_id)

            if feed_id in seen_ids:
                continue

            category = classify_title(title)

            all_results.append({
                "id": feed_id,
                "title": title,
                "xsecToken": xsec_token,
                "category": category,
                "keyword": keyword,
            })

    recruit = [r for r in all_results if r["category"] == "recruit"]
    uncertain = [r for r in all_results if r["category"] == "uncertain"][:3]
    filtered_count = sum(1 for r in all_results if r["category"] == "filter")

    output = {
        "keywords": keywords,
        "errors": errors,
        "new_recruit": recruit,
        "new_uncertain": uncertain,
        "filtered_count": filtered_count,
        "total_new": len(all_results),
        "all_new_ids": list(set(all_new_ids)),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
