#!/usr/bin/env python3
"""
日报推送投递验证脚本。
检查 xhs-job-daily-push 最近一次运行的 deliveryStatus：
- delivered → 将 pending IDs 正式写入 seen-pushed-ids.md
- 其他状态 → 丢弃 pending IDs（下次推送会重试）
"""
import json
import os
import re

BASE_DIR = os.path.expanduser("~/.openclaw/workspace/xhs-jobs")
CRON_RUNS_DIR = os.path.expanduser("~/.openclaw/cron/runs")
PUSH_JOB_ID = "YOUR_DAILY_PUSH_JOB_ID"  # 部署后替换为实际的 xhs-job-daily-push Job ID
NOTE_ID_RE = re.compile(r"^[a-f0-9]{24}$")


def get_last_run_status():
    """从 run log 读取最近一次运行的 deliveryStatus。"""
    log_path = os.path.join(CRON_RUNS_DIR, PUSH_JOB_ID + ".jsonl")
    if not os.path.exists(log_path):
        return None

    last_line = None
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if line:
                last_line = line

    if not last_line:
        return None

    try:
        entry = json.loads(last_line)
        return entry.get("deliveryStatus")
    except json.JSONDecodeError:
        return None


def read_pending_ids():
    path = os.path.join(BASE_DIR, "pending-push-ids.md")
    ids = []
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                stripped = line.strip()
                if stripped and NOTE_ID_RE.match(stripped):
                    ids.append(stripped)
    return ids


def clear_pending():
    path = os.path.join(BASE_DIR, "pending-push-ids.md")
    if os.path.exists(path):
        with open(path, "w") as f:
            f.write("")


def commit_ids(ids):
    """将 ID 追加到 seen-pushed-ids.md（去重）。"""
    seen_path = os.path.join(BASE_DIR, "seen-pushed-ids.md")
    existing = set()
    if os.path.exists(seen_path):
        with open(seen_path) as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    existing.add(stripped)

    new_ids = [nid for nid in ids if nid not in existing]
    if new_ids:
        with open(seen_path, "a") as f:
            for nid in new_ids:
                f.write(nid + "\n")

    return new_ids


def main():
    pending = read_pending_ids()
    if not pending:
        print("No pending IDs to verify.")
        return

    status = get_last_run_status()
    print("Last push deliveryStatus: %s" % status)
    print("Pending IDs: %d" % len(pending))

    if status == "delivered":
        committed = commit_ids(pending)
        clear_pending()
        print("Committed %d IDs (delivery confirmed)." % len(committed))
    else:
        clear_pending()
        print("Discarded pending IDs (delivery failed/unknown). Will retry next push.")


if __name__ == "__main__":
    main()
