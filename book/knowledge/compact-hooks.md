# PreCompact / PostCompact Hooks

Claude Code 的 `/compact` 命令相关 hook 机制。

## PreCompact

压缩前触发。支持 matcher：
- `"manual"` — 手动 `/compact` 时触发
- `"auto"` — 自动压缩时触发

配置在 settings.json 的 `hooks.PreCompact` 下。支持 command（shell）、prompt（LLM）、agent（子 agent）、http（POST）四种类型。

**已知问题：** v2.1.105–v2.1.114 的 auto-compaction 不触发 PreCompact。

## PostCompact

不是官方事件。替代方案：`SessionStart` hook 的 `matcher: "compact"`。

## 当前状态

ope 没有配置任何 hooks。不确定是否需要用——目前走手动写日记 + 蒸馏的路。
