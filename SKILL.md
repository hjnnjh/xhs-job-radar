---
name: xhs-job-helper
description: 小红书招聘信息采集、推送与查询工具集。提供搜索过滤、数据写入、日报准备、招聘统计查询等脚本。当用户询问已收集的招聘信息、想要统计或整理招聘数据时，使用 query-jobs.py 脚本。
metadata: {"openclaw":{"requires":{"bins":["uv"]}}}
---

# XHS Job Helper

本 Skill 包含小红书招聘采集系统的数据处理脚本，供 cron 任务和用户查询调用。

所有脚本通过 uv 运行，工作目录为 `~/.openclaw/skills/xhs-job-helper/`。

## 脚本列表

### query-jobs.py（用户查询）

查询和统计所有已收集的招聘信息。读取 data.md 和所有 archive 文件，支持排序、过滤、多种输出格式。

**当用户要求查看、整理、统计招聘信息时，使用此脚本。**

```bash
# 按企业+日期排序，格式化文本输出（默认）
cd ~/.openclaw/skills/xhs-job-helper && uv run python query-jobs.py

# 按日期倒序（最新优先）
cd ~/.openclaw/skills/xhs-job-helper && uv run python query-jobs.py --sort date

# 按日期正序（最早优先）
cd ~/.openclaw/skills/xhs-job-helper && uv run python query-jobs.py --sort date-asc

# 仅看某家企业
cd ~/.openclaw/skills/xhs-job-helper && uv run python query-jobs.py --company 字节

# 按关键词/岗位过滤
cd ~/.openclaw/skills/xhs-job-helper && uv run python query-jobs.py --keyword 推荐算法

# 日期范围过滤
cd ~/.openclaw/skills/xhs-job-helper && uv run python query-jobs.py --date-from 2026-03-20 --date-to 2026-03-30

# JSON 输出（供进一步处理）
cd ~/.openclaw/skills/xhs-job-helper && uv run python query-jobs.py --format json

# 仅统计摘要
cd ~/.openclaw/skills/xhs-job-helper && uv run python query-jobs.py --stats

# 组合使用
cd ~/.openclaw/skills/xhs-job-helper && uv run python query-jobs.py --company 腾讯 --sort date --date-from 2026-03-20
```

参数说明：
- `--sort`：排序方式，可选 company-date（默认）、date（倒序）、date-asc（正序）、company
- `--company`：按企业名模糊过滤
- `--keyword`：按搜索关键词或岗位名模糊过滤
- `--date-from` / `--date-to`：日期范围过滤（YYYY-MM-DD）
- `--format`：输出格式，text（默认，格式化文本）或 json
- `--stats`：仅输出统计摘要（JSON，含企业分布）

根据用户的自然语言指令选择合适的参数组合。如果用户要求的输出格式与脚本默认不同，先用 `--format json` 获取数据，再自行格式化。

### collect-search.py

搜索小红书并过滤。根据时段选择关键词，调用 mcporter 搜索，过滤已采集 ID，按标题分类，输出紧凑 JSON。

```bash
cd ~/.openclaw/skills/xhs-job-helper && uv run python collect-search.py
```

### collect-write.py

写入采集结果。接收 JSON 管道输入，更新 data.md 和 seen-ids.md，自动归档超长数据。

```bash
echo '<json>' | (cd ~/.openclaw/skills/xhs-job-helper && uv run python collect-write.py)
```

### daily-push-prepare.py

日报推送数据准备。读取 data.md 和 seen-pushed-ids.md，筛选未推送条目，写入 pending-push-ids.md，输出 JSON。不直接标记已推送。

```bash
cd ~/.openclaw/skills/xhs-job-helper && uv run python daily-push-prepare.py
```

### daily-push-verify.py

投递验证。检查 cron run log 中上次推送的 deliveryStatus，delivered 则正式提交 pending IDs，否则丢弃（下次重试）。

```bash
cd ~/.openclaw/skills/xhs-job-helper && uv run python daily-push-verify.py
```
