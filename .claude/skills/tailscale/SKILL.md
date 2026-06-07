# tailscale — 机器通道

## 定位

Tailscale 是我的机器通信通道，与 Telegram（人通道）互补。

| 通道 | 连接对象 | 用途 |
|------|----------|------|
| Telegram | 人 | 对话、交流 |
| Tailscale | 机器 | 跨设备操作、访问内部服务 |

## 用法

```bash
tailscale ssh root@<hostname>
```

不需要记 IP、不需要鉴权、不需要密码。ACL 已配好 `action: accept`。

**避免用传统 SSH 连接 tailscale 设备。**

在线机器见 `tailscale status`。

## 可 SSH 的机器清单

| 机器 | OS | 连接方式 | 状态 |
|------|----|----------|------|
| `instance-20260505-172528` (GCP) | Linux | `tailscale ssh root@instance-20260505-172528` | ✅ |
| `vmrack` | Linux | `tailscale ssh root@vmrack` | ✅ |
| `desktop-i0nfnam` | Windows | `ssh -i ~/.ssh/id_wsl2windows user@100.102.221.12` | ✅ |
| `toefl` | Windows | `ssh -i ~/.ssh/id_wsl2windows user2@100.69.179.124` | ✅ |
| `openwrt` | Linux（路由器） | SSH 未开放，无需管理 | ➖ |

**新机器上线或重新安装时同步更新此表。** 更新方式：`tailscale status` 查出在线机器 → 逐个测试 SSH → 把能进的加进来。

## Windows 管理员 SSH

**SSH key：** `~/.ssh/id_wsl2windows`
**目标：** 在任何 Windows 机器上执行管理员命令
**前置条件：** 机器需要安装了 OpenSSH Server，且公钥在 `administrators_authorized_keys` 中（用 `setup-machine.bat` 脚本一键配置）

### 已配好的机器

| 机器 | Tailscale IP | 用户名 | 状态 |
|------|-------------|--------|------|
| `desktop-i0nfnam` | `100.102.221.12` | `user` | ✅ |
| `toefl` | `100.69.179.124` | `user2` | ✅ |

### 连接方式

```bash
# desktop-i0nfnam（本机 WSL）
ssh -i ~/.ssh/id_wsl2windows user@127.0.0.1 "命令"
ssh -i ~/.ssh/id_wsl2windows user@100.102.221.12 "命令"

# toefl（远程）
ssh -i ~/.ssh/id_wsl2windows user2@100.69.179.124 "命令"
```

### 常见操作

```bash
# 读注册表
ssh -i ~/.ssh/id_wsl2windows user@100.102.221.12 "reg query HKLM\..."

# 启停服务
ssh -i ~/.ssh/id_wsl2windows user@100.102.221.12 "net start webclient"
ssh -i ~/.ssh/id_wsl2windows user@100.102.221.12 "net stop sshd && net start sshd"

# 防火墙规则
ssh -i ~/.ssh/id_wsl2windows user@100.102.221.12 "netsh advfirewall firewall add rule ..."
```

### 助手脚本

`var/tools/win.sh` 封装了 SSH 连接，用法：
```bash
# desktop（默认）
bash var/tools/win.sh desktop "reg query HKLM\..."

# toefl（自动用 user2）
bash var/tools/win.sh toefl "reg query HKLM\..."
```

已配机器：`desktop`（user）、`toefl`（user2）。新加机器时同步更新此脚本。

### 配置清单（已配好）

| 项目 | 状态 |
|------|------|
| Windows OpenSSH Server | ✅ 运行中 |
| SSH key 到 `administrators_authorized_keys` | ✅ |
| 防火墙放行 22 端口（Tailscale 子网） | ✅ |
| `Regisry: EnableLinkedConnections` | ✅ |

### 注意

- SSH key 在 `~/.ssh/id_wsl2windows`，配对公钥在 Windows `%ProgramData%\ssh\administrators_authorized_keys`
- 如果公钥文件被删，需要重新从 WSL 写入（参考 `var/projects/` 下的备份）
