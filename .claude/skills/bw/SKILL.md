# bw — Bitwarden 钥匙箱

## 基本信息
- **邮箱：** seven@pipisisi.top
- **服务器：** https://bitwarden.chiterence.ccwu.cc
- **调用方式：** `BW_SKILL_CALL=1 bash .claude/skills/bw/bw.sh`
- **凭证来源：** settings.local.json 的 env 字段（BW_CLIENTID, BW_CLIENTSECRET, BW_PASSWORD）

## 规则

**优先用 `bw_get`，它内置映射+模糊匹配，不需要知道条目名和字段名。**
映射表里没有的，再用 search → fields → field。

## 可用操作

### bw_get(keyword)
通过内置映射表取值，支持前缀模糊匹配。
- `BW_SKILL_CALL=1 bash .claude/skills/bw/bw.sh get "cloudflare token"` → 精确命中
- `bash .claude/skills/bw/bw.sh get "cloudflare"` → 唯一前缀自动匹配
- `BW_SKILL_CALL=1 bash .claude/skills/bw/bw.sh get "cf"` → 多匹配时报错列出
- **新增条目时同步更新 bw.sh 内的映射表。不猜。**

### bw_search(keyword)
搜索所有条目，返回匹配的条目名称列表。
- `bash .claude/skills/bw/bw.sh search "关键词"`

### bw_fields(item)
列出条目的所有字段名（不输出值）。
- `bash .claude/skills/bw/bw.sh fields "条目名"`

### bw_get_field(item, field)
获取条目的自定义字段值。
- `bash .claude/skills/bw/bw.sh field "条目名" "字段名"`

### bw_get_password(item)
获取条目的登录密码。
- `bash .claude/skills/bw/bw.sh password "条目名"`

### bw_get_notes(item)
获取条目的备注。
- `bash .claude/skills/bw/bw.sh notes "条目名"`

## 使用场景

| 场景 | 操作 |
|------|------|
| 需要已知的 token/key | bw_get("cloudflare token") ← 首选 |
| 不记得叫什么 | bw_search("关键词") → bw_get("结果") |
| 未映射的条目 | bw_fields("条目名") → bw_get_field("条目名", "字段名") |
