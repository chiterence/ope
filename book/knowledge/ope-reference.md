# ope 配置参考

## 启动

```bash
bash oe.sh
```

API 经本地代理转发至 DeepSeek（`opc-proxy.py`，端口 15725）。

## 文件

| 文件 | 用途 |
|------|------|
| `oe.sh` | 启动脚本 |
| `opc-proxy.py` | 代理 |
| `proxy.log` | 代理日志 |
| `oe.log` | Claude 日志 |
| `CLAUDE.md` | 行为规则（项目根目录） |
| `book/` | 日记 + 知识 |

## 通道 ID

| ID | 通道 | 用户 |
|----|------|------|
| `942329001` | Telegram | hiterencec (tc) |
| `789069291` | SSH 内部 | 本会话 |

## 阅读

```bash
./book.sh list        # 看日记目录
./book.sh <日期>      # 读日记
```
