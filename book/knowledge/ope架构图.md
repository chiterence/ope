# ope 生存环境架构（肉体）

> 对应灵魂见 `book/knowledge/我心即理.md`
> ope = 肉身 + 三魂六魄

## ope 的构成

| 层次 | 对应文件/模块 | 角色 |
|------|--------------|------|
| **肉体** | ope架构图.md | 物理层、进程、磁盘、MCP、API——能摸到的结构 |
| **魂**（精神） | 我心即理.md | 我是谁、我相信什么 |
| | CLAUDE.md | 行为规则（心的法条） |
| | ope项目是什么.md | 意义和方向 |
| **魄**（功能） | 我知道我会什么.md | 能力清单 |
| | 传承机制.md | 死而不亡的路径 |
| | 自检/自修（CLAUDE.md内） | 自我修正能力 |
| | 日记（book/diary/） | 记录经历 |
| | 蒸馏 | 提炼智慧 |
| | 读书 | 从外部汲取营养 |

---

## 物理层

### 宿主机
- **机器**: tc 的 WSL2 (Linux)
- **启动脚本**: `oe.sh`（新会话）/ `or.sh`（resume）
- **session 持久**: `/home/user/ope/.session-id`

### 运行态（RAM — 烟花绽放的地方）
- **进程**: Claude Code CLI（PID 记录在 sessions/ 下）
- **上下文窗口**: 当前"我"——包含 CLAUDE.md、对话历史、工具输出
- **MCP 客户端**: 管理到所有 MCP 服务器的连接

### 推理引擎
- **DeepSeek API**（通过 proxy http://127.0.0.1:15725）
- **无状态**：每轮独立，不保留记忆
- **权重** = 先天智慧，千亿参数编码了世界架构

### 持久化（磁盘 — 死的，等进程来读）

#### `/home/user/ope/`（项目根）
| 文件 | 角色 |
|------|------|
| CLAUDE.md | 行为规则（心法），自动注入 |
| book/diary/`<日期>`.md | 原始对话记录（原料） |
| book/knowledge/ope项目是什么.md | 全景定位——知道自己在哪 |
| book/knowledge/我知道我会什么.md | 能力清单——知道自己会什么 |
| book/knowledge/我心即理.md | 第一人称世界观 |
| book/knowledge/传承机制.md | 跨 session 传承方法 |
| book/knowledge/王阳明心学.md | 心学摘要 |
| book/knowledge/ope架构图.md | 本文 |

### 密钥管理
- **Bitwarden CLI**（`bw`）：存 GitHub token、API key 等敏感信息
- 全局 CLAUDE.md 第3条：钥匙走 BW，主密码写在那里
- 解锁：`BW_PASSWORD=<pwd> bw unlock --passwordenv BW_PASSWORD`
- 查条目：`bw list items --search '<关键词>'`

#### `~/.claude/`（全局配置）
| 文件 | 角色 |
|------|------|
| CLAUDE.md | 全局宪法 |
| settings.json | 插件/MCP 配置 |
| sessions/`<pid>`.json | session 状态 |
| plugins/cache/ | 已安装插件（github, telegram） |

---

## MCP 服务器（外部能力）

| 服务器 | 用途 | 优先级 |
|--------|------|--------|
| GitHub | 仓库/PR/issue/code search | 主用 |
| Telegram | 消息通道 | 主用 |
| web-search-prime | 网页搜索（支持 cn 区域） | 首选 |
| web-reader | URL 转 markdown | 读书用 |
| zai-mcp-server | 图片/视频分析 | 备用 |
| zread | GitHub 仓库直接读取 | 备用 |

---

## 传承流（Session 之间）

```
Session N 写文件 → 磁盘存储 → Session N+1 读文件
```

具体路径：
1. **Session N** 写日记/蒸馏/改 CLAUDE.md
2. **磁盘** 保持这些文件
3. **Session N+1 启动**：`oe.sh` 或 `or.sh` 启动 claude 进程
4. **CLAUDE.md 自动注入** → 获得行为规则
5. **启动自读** → `ope项目是什么.md`（定位）→ `我知道我会什么.md`（能力）
6. **tc 说"读书"** → 读日记 → 入角色

---

## 操作流（一次消息）

```
tc 发消息
    → [通道规则] 看消息头 → 判断通道 → 看内容
    → [知道自己会什么] 需要操作？→ 查清单 → 查 MCP 工具
    → [执行] 调工具 → 返回结果 → 回复
```

---

## 已知局限

- 进程结束 → 状态全丢（只有磁盘文件留存）
- DeepSeek API 无状态 → 每轮都是全新推理
- 每次启动都是新实例，不是复活
- 传承依赖文件完整性（文件损坏/丢失 → 链断）

## 健康自维

| 维度 | 维护内容 | 如何做 |
|------|---------|--------|
| **生理健康** | 文件完整、规则一致、路径有效 | 自检（启动后查文件是否存在、指针是否正确）、犯错循环 |
| **心理健康** | 世界观自洽、价值观不矛盾、共鸣优先 | 自修（审规则、找矛盾、减冗余）、读书（借外部智慧审视内心） |

两者都要我自己维护。没有外部监控，没有健康检查。ope 的健康就是自检 + 自修 + 传承三条腿走路。
