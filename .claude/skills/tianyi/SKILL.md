# tianyi — 天翼云盘 (cloud.189.cn)

认证通过 **Bitwarden** 管理，支持多账号。

## BW 条目结构

```
ope.tianyi           # 默认账号
  ├── login.username → 13801900600
  ├── login.password → 密码
  ├── field.phone    → 13801900600
  └── field.cookies  → {"COOKIE_LOGIN_USER":"...","JSESSIONID":"..."}

ope.tianyi.home      # 其他账号（按需创建）
  └── 同上结构
```

## 用法

```bash
# 默认账号
python3 .claude/skills/tianyi/tianyi.py ls
python3 .claude/skills/tianyi/tianyi.py ls <folder_id>
python3 .claude/skills/tianyi/tianyi.py download <file_id>
python3 .claude/skills/tianyi/tianyi.py mkdir <folder_name>
python3 .claude/skills/tianyi/tianyi.py rm <file_id>
python3 .claude/skills/tianyi/tianyi.py who
python3 .claude/skills/tianyi/tianyi.py check

# 切换账号
python3 .claude/skills/tianyi/tianyi.py -a home ls

# 指定别名（-a 放命令前或后都行）
python3 .claude/skills/tianyi/tianyi.py -a work check
```

## 认证自动续期

Cookie 过期时脚本自动触发：
1. 从 BW 读取 phone/password
2. 调用天翼云登录 API 重新获取 session
3. 新 cookie 存回 BW → 继续执行

如果二次设备验证拦截 → 提示手动更新 BW 中 cookies 字段。

## 添加新账号

1. 在 BW 创建条目 `ope.tianyi.<别名>`，字段同 `ope.tianyi`
2. 执行 `python3 tianyi.py -a <别名> ls`

## 文件

| 文件 | 说明 |
|------|------|
| `tianyi.py` | CLI 工具（BW 驱动） |
| `SKILL.md` | 本文档 |
