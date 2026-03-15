---
name: xhs-job-helper
description: 小红书招聘信息采集与推送的数据处理工具。提供搜索过滤、数据写入、日报准备与投递验证等脚本，减少 cron 任务的 context 消耗。
user-invocable: false
disable-model-invocation: true
---

# XHS Job Helper

本 Skill 包含小红书招聘采集系统的数据处理脚本，供 cron 任务调用。

## 脚本列表

### collect-search.py
搜索小红书并过滤。根据时段选择关键词，调用 mcporter 搜索，过滤已采集 ID，按标题分类，输出紧凑 JSON。

```bash
python3 {baseDir}/collect-search.py
```

### collect-write.py
写入采集结果。接收 JSON 管道输入，更新 data.md 和 seen-ids.md，自动归档超长数据。

```bash
echo '<json>' | python3 {baseDir}/collect-write.py
```

### daily-push-prepare.py
日报推送数据准备。读取 data.md 和 seen-pushed-ids.md，筛选未推送条目，写入 pending-push-ids.md，输出 JSON。不直接标记已推送。

```bash
python3 {baseDir}/daily-push-prepare.py
```

### daily-push-verify.py
投递验证。检查 cron run log 中上次推送的 deliveryStatus，delivered 则正式提交 pending IDs，否则丢弃（下次重试）。

```bash
python3 {baseDir}/daily-push-verify.py
```
