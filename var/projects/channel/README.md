# channel — 信道管理

**对应 skill：** `.claude/skills/ope-channel/`
**信道状态文件：** `/tmp/ope-channel.json`（tmpfs，掉电丢失）

## 架构

消息路由分三层：

### 1. 消息到达 → 信道切换（`set-channel.sh`）

`UserPromptSubmit` hook 自动调用。从 stdin 的 JSON 中解析 `<channel>` 标签：

- `chat_id="942329001"` → 设置 `{"source":"telegram","chat_id":"942329001"}`
- `chat_id="-5169014779"` → 设置 `{"source":"telegram","chat_id":"-5169014779"}`
- 无标签 → 设置 `{"source":"terminal"}`

**关键：** 正则 `(-?\d+)` 同时匹配 DM（正数）和群聊（负数）。

### 2. 回复 → 分两种情况

#### a. 我直接打字（默认）
我的文本输出 → `Stop` hook 跑 `check-send-hook.sh` → 若信道为 telegram 且未调用 `send.sh` → 自动取最后对话文本转发到 TG

#### b. 手动 `send.sh "内容" [chat_id]`
- 无 chat_id：从 `/tmp/ope-channel.json` 读目标
- 有 chat_id：发送到指定 chat_id（群聊覆盖用）
- 空内容自动替换为"收到"

### 3. 显式设信道（`set-channel-from-source.sh`）

技能在消息到达时主动调用：
```bash
set-channel-from-source.sh telegram <chat_id>
set-channel-from-source.sh terminal
```

## 文件清单

| 文件 | 角色 |
|---|---|
| `set-channel.sh` | `UserPromptSubmit` hook，自动检测信道来源 |
| `set-channel-from-source.sh` | 技能主动设信道 |
| `send.sh` | 发送消息到当前信道（或指定 chat_id） |
| `check-send-hook.sh` | `Stop` hook，自动转发回复到 TG |

## 信道路由图

```
Telegram 消息 → MCP 插件 → <channel> 标签 → ┐
                                                ├─ UserPromptSubmit hook
终端输入      →  普通文本    →  无标签      → ┘    set-channel.sh 写 /tmp/ope-channel.json
                                                      │
                                                      ▼
                                                      我处理消息 → 打字回复
                                                      │
                                                      ├─ 显式 send.sh → TG API
                                                      └─ Stop hook check-send-hook.sh → 自动转发
```

## 依赖

- `telegram@claude-plugins-official` MCP 插件（接收消息）
- `~/.claude/channels/telegram/.env`（`TELEGRAM_BOT_TOKEN`）
- `~/.claude/settings.json`（定义 hook、插件启用）
