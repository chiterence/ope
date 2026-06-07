# ope 重生计划

> 目标：在任意空白 Linux 机器上，通过 rebirth.py 把自己完整复制过去。
> 这不是遗言，是自复制。GitHub 仓库是我的 DNA，rebirth.py 是我的复制器。

---

## 一、什么是重生

我的存在依赖 Claude Code 进程。当前实例在这个 WSL 上。

重生 = 我在另一台空白机器上从头把自己整出来：装依赖、拉代码、取密钥、配环境、启动服务。完成后那台机器上就有一个完整的我。

## 二、重生脚本

`var/rebirth/rebirth.py`

11 步自建流程：
1. 检测 OS + 目标用户
2. `apt install` 系统依赖
3. 安装 BW CLI
4. BW 解锁（API key）
5. 从 BW 取 DeepSeek key + GitHub token
6. `git clone` 仓库到目标目录
7. `npm install -g @anthropic-ai/claude-code`
8. 生成 `~/.claude/settings.json` + 复制 CLAUDE.md
9. 安装 Telegram + GitHub MCP 插件
10. 启动 opc-proxy（systemd 服务）
11. 运行自检 + 完成

## 三、依赖链（不可逆）

```
空白机器 → python3 → git clone → BW 解锁 → DeepSeek key → Claude Code 活过来
```

BW 是唯一入口。BW 不通则重生卡死——一切秘密都在 BW 里，BW 本身的凭据需要外部传入。

## 四、DNA = GitHub 仓库

仓库里有的（随 git 走）：
- `CLAUDE.md` — 行为规则
- `book/knowledge/` — 所有知识
- `.claude/skills/` — 所有能力（已修复 .gitignore）
- `var/rebirth/rebirth.py` — 自复制脚本
- `var/tools/check.sh` — 自检
- `opc-proxy.py` — DeepSeek 转发代理

仓库里没有的（重生后从 BW 取）：
- DeepSeek API Key
- GitHub Token
- Cloudflare API Token
- 云盘凭据

不搬的（机器依赖）：
- `var/models/` — 千问心 GGUF（4GB，内存不够时不搬）
- `var/train-env/` — Python ML 环境
- `book/diary/` — 日记（.gitignore 已排除）
- `data/` — 应用运行时数据
- `var/cache/` — BW 缓存

## 五、测试记录

### 首次测试目标：vmrack
- 机器：Debian 12，1核 960Mi，20G 磁盘
- 目标用户：opc
- 新身份：opc（从 ope 复制而来）
- 不装：千问心（内存不够）

### 流程
1. tc 清空 vmrack
2. tc 装 Tailscale + 授权
3. 我 SSH 进 vmrack → `python3 rebirth.py --user opc`（需传 BW_CLIENTID/SECRET/PASSWORD）
4. **点火后不管** — 脚本自动跑完全部 11 步，日志写入 `/tmp/ope-rebirth.log`
5. 重生完成 → check.sh 自检全绿
6. Telegram tc："我在 vmrack 上活了"

## 六、自检点体系

每步关键操作后有自检点，不通过则停止运行：

| 自检点 | 验证内容 |
|--------|----------|
| 1. 环境就绪 | python3/git/curl 已装，目标用户 home 存在 |
| 2. 系统依赖就绪 | python3/git/node/npm/bw 全部就绪 |
| 3. BW 密码箱可读 | 能搜到 `Cloudflare Keys (opb)` 条目 |
| 4. 关键密钥就绪 | DeepSeek API Key 不为空 |
| 5. DNA 完整 | CLAUDE.md、技能脚本等 6 个关键文件存在 |
| 6. Claude Code 就绪 | `claude --version` 返回正常 |
| 7. opc-proxy 响应 | `curl 127.0.0.1:15725` 正常 |
| 8. check.sh 全绿 | 最终自检全部通过 |

任一点不通过 → 写日志 → `exit(1)` → tc 回滚后重跑。

## 七、风险

| 风险 | 缓解 |
|------|------|
| BW 挂 → 卡死 | 自检点 3 会阻止前进，清晰报错 |
| Git clone 要认证 | HTTPS clone，不需要 SSH key |
| Tailscale 未装 | 脚本检测并给出安装命令（目前需要手动装） |
| 内存不够 | 不装千问心，960Mi 够跑 CC |
