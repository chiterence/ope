# caiyun — 139 云盘（和彩云）

认证通过 Bitwarden 管理（`ope.caiyun[.<别名>]`），支持多账号。
token 自动续期。

## 用法

```bash
# 默认账号
python3 .claude/skills/caiyun/caiyun.py ls
python3 .claude/skills/caiyun/caiyun.py download <file_id>
python3 .claude/skills/caiyun/caiyun.py mkdir <folder_name>
python3 .claude/skills/caiyun/caiyun.py rm <file_id>
python3 .claude/skills/caiyun/caiyun.py check

# 切换账号
python3 .claude/skills/caiyun/caiyun.py -a <别名> ls
```

## BW 条目结构

```
ope.caiyun                  # 默认账号
  ├── field.token           # base64 编码的 auth token
  └── field.password        # 密码（用于自动续期）

ope.caiyun.<别名>           # 其他账号（结构同上）
```

## WebDAV

```bash
CAIYUN_AUTH=$(bash .claude/skills/bw/bw.sh field "ope.caiyun" "token") \
  python3 .claude/skills/caiyun/caiyun-webdav.py
```
