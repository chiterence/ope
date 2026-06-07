# pcloud — pCloud 云盘

认证通过 Bitwarden 管理（`ope.pcloud[.<别名>]`），支持多账号。

## 用法

```bash
# 默认账号
python3 .claude/skills/pcloud/pcloud.py ls
python3 .claude/skills/pcloud/pcloud.py ls <folder_id>
python3 .claude/skills/pcloud/pcloud.py download <file_id|path>
python3 .claude/skills/pcloud/pcloud.py mkdir <folder_name>
python3 .claude/skills/pcloud/pcloud.py rm <file_id|folder_id>
python3 .claude/skills/pcloud/pcloud.py check

# 切换账号
python3 .claude/skills/pcloud/pcloud.py -a <别名> ls
```

## BW 条目结构

```
ope.pcloud                  # 默认账号
  └── field.token           # pCloud API token

ope.pcloud.<别名>           # 其他账号（结构同上）
```

## 本机挂载

```bash
sudo mount -t drvfs P: /mnt/p
```
