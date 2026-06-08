# channel — 信道管理

## 基本信息
信道管理负责消息路由。分三层：

### 1. 消息到达 → 切信道（第一步，不可跳过）

每次消息到达时，先判断来源再切信道：
- 消息带 `<channel source="telegram"...>` 标签 → `set-channel-from-source.sh telegram <chat_id>`
- 消息带其他 channel 标签 → `set-channel-from-source.sh <source> <chat_id>`
- 消息**没有** channel 标签 → 这是终端消息 → `set-channel-from-source.sh terminal`

**这一步必须在处理消息内容之前做，否则 send.sh 会发到上一个信道。**

### 2. 回复 → 用 send.sh
`.claude/skills/channel/send.sh "消息内容"`
- 空消息自动替换为"收到"
- 信道自动从 `/tmp/ope-channel.json` 读取
- Telegram 信道直接发，其他信道输出 terminal

### 3. Hook 保护
`settings.json` 的 `UserPromptSubmit` hook 跑 `set-channel.sh` 重置信道。但如果信道文件已是 Telegram，不会被覆写（`set-channel.sh` 无条件保留已有 Telegram 配置）。

## 信道文件
`/tmp/ope-channel.json`（tmpfs，掉电丢失）
- `{"source":"telegram","chat_id":"942329001"}` — TG 模式
- `{"source":"terminal"}` — 终端模式（默认）

## 信道路由图
```
消息到达
  │
  ├── Telegram → set-channel-from-source.sh telegram <id>
  │               → send.sh → TG API
  │
  └── 终端 → set-channel-from-source.sh terminal
              → send.sh → stdout
```

## 相关文件
- `.claude/skills/channel/set-channel.sh` — hook 调用（无参时保留已有 TG）
- `.claude/skills/channel/set-channel-from-source.sh` — 消息到达时显式设信道
- `.claude/skills/channel/send.sh` — 发送消息
- `/home/user/ope/.claude/settings.json` — 定义 UserPromptSubmit hook
