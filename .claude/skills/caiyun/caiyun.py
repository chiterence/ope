#!/usr/bin/env python3
"""和彩云 (139云盘) CLI

认证通过 Bitwarden 管理（ope.caiyun.{account}），支持多账号。
Token 失效时自动续期。
"""
import base64, hashlib, json, os, random, string, subprocess, sys, time, urllib.parse
import requests

AUTH_ENV_NAME = "CAIYUN_AUTH"  # 兼容旧环境变量
HOST_DISCOVER = "https://user-njs.yun.139.com"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BW_DIR = os.path.join(SCRIPT_DIR, "..", "bw")

# ── 凭证管理（只从环境变量读） ──

BW_SH = os.path.join(SCRIPT_DIR, "..", "bw", "bw.sh")
BW_ENV = {**os.environ, "BW_SKILL_CALL": "1"}

def _ensure_token():
    """从 bw skill 读 token，失效时自动续期并存回。"""
    # token 优先 CAIYUN_AUTH env（兼容旧用法），否则从 bw skill 取
    token = os.environ.get(AUTH_ENV_NAME, "")
    if not token:
        r = subprocess.run(["bash", BW_SH, "field", "ope.caiyun", "token"],
                          capture_output=True, text=True, timeout=15, env=BW_ENV)
        token = r.stdout.strip() if r.returncode == 0 else ""
    if not token:
        print("❌ 无 token。设 CAIYUN_AUTH env 或通过 bw skill 添加 ope.caiyun token 字段")
        return None

    # phone/password 用于自动续期
    phone = os.environ.get("CAIYUN_PHONE", "")
    password = os.environ.get("CAIYUN_PASSWORD", "")
    if not phone:
        r = subprocess.run(["bash", BW_SH, "field", "ope.caiyun", "phone"],
                          capture_output=True, text=True, timeout=15, env=BW_ENV)
        phone = r.stdout.strip() if r.returncode == 0 else ""
    if not password:
        r = subprocess.run(["bash", BW_SH, "password", "ope.caiyun"],
                          capture_output=True, text=True, timeout=15, env=BW_ENV)
        password = r.stdout.strip() if r.returncode == 0 else ""

    try:
        dec = base64.b64decode(token).decode()
        parts = dec.split(":")
        if len(parts) >= 3:
            token_parts = parts[2].split("|")
            if len(token_parts) >= 4:
                expiry_ms = int(token_parts[3])
                remaining = expiry_ms - int(time.time() * 1000)
                if remaining < 1000 * 60 * 60 * 24 * 15:  # < 15 天，刷新
                    new_token = _refresh_token_impl(token, parts[1])
                    if new_token:
                        subprocess.run(["bash", BW_SH, "set", "ope.caiyun", "token", new_token],
                                      capture_output=True, text=True, timeout=15, env=BW_ENV)
                        return new_token
                    if remaining < 0:
                        print(f"❌ Token 已过期，尝试密码重登...")
                        if password:
                            new_token = _login_renew(parts[1], password)
                            if new_token:
                                subprocess.run(["bash", BW_SH, "set", "ope.caiyun", "token", new_token],
                                              capture_output=True, text=True, timeout=15, env=BW_ENV)
                                return new_token
                        print("❌ 无法续期，请手动更新 bw skill 中 ope.caiyun 的 token 字段")
                        return None
    except:
        pass
    return token

def _refresh_token_impl(old_token, phone):
    """调用刷新 API。"""
    try:
        dec = base64.b64decode(old_token).decode()
        session_token = dec.split("|")[0] if "|" in dec else dec.split(":")[2].split("|")[0]
    except:
        return None
    xml = f"<root><token>{session_token}</token><account>{phone}</account><clienttype>656</clienttype></root>"
    try:
        r = requests.post("https://aas.caiyun.feixin.10086.cn:443/tellin/authTokenRefresh.do",
                         data=xml, headers={"Content-Type": "application/xml"}, timeout=15)
        import xml.etree.ElementTree as ET
        root = ET.fromstring(r.content)
        ret = root.findtext("return", "")
        if ret != "0":
            return None
        new_token = root.findtext("token", "")
        if not new_token:
            return None
        prefix = dec.split(":")[0]
        return base64.b64encode(f"{prefix}:{phone}:{new_token}".encode()).decode()
    except:
        return None

def _login_renew(phone, password, account=""):
    """密码重登（刷新长期 token）。"""
    try:
        from caiyun_api import login
        # 简单实现：用旧格式的 discover_host + api_post 拿新 token
        # 目前暂不支持——需要和彩云密码登录流程
        pass
    except:
        pass
    return None

# ── 签名工具（复用现有逻辑） ──

def cal_sign(body, ts, rand_str):
    body = urllib.parse.quote(body, safe='~')
    body = body.replace('+', '%20').replace('%21', '!').replace('%27', "'")
    body = body.replace('%28', '(').replace('%29', ')').replace('%2A', '*')
    body = ''.join(sorted(body))
    body = base64.b64encode(body.encode()).decode()
    h1 = hashlib.md5(body.encode()).hexdigest()
    h2 = hashlib.md5((ts + ':' + rand_str).encode()).hexdigest()
    return hashlib.md5((h1 + h2).encode()).hexdigest().upper()

def discover_host(auth):
    phone, session_token = decode_auth(auth)
    data = {"userInfo": {"userType": 1, "accountType": 1, "accountName": phone},
            "modAddrType": 1}
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
    body = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    sig = cal_sign(body, ts, rand)
    headers = {"Accept": "application/json, text/plain, */*", "CMS-DEVICE": "default",
               "Authorization": f"Basic {auth}", "mcloud-channel": "1000101",
               "mcloud-client": "10701", "mcloud-sign": f"{ts},{rand},{sig}",
               "mcloud-version": "7.14.0", "Origin": "https://yun.139.com",
               "Referer": "https://yun.139.com/w/",
               "x-DeviceInfo": "||9|7.14.0|chrome|120.0.0.0|||windows 10||zh-CN|||",
               "x-huawei-channelSrc": "10000034", "x-inner-ntwk": "2",
               "x-m4c-caller": "PC", "x-m4c-src": "10002", "x-SvcType": "1",
               "Inner-Hcy-Router-Https": "1"}
    r = requests.post("https://user-njs.yun.139.com/user/route/qryRoutePolicy",
                      headers=headers, json=data, timeout=10)
    j = r.json()
    if not j.get("success"):
        print("Route discovery failed:", j.get("message"))
        return None
    for p in j.get("data", {}).get("routePolicyList", []):
        if p.get("modName") == "personal" and p.get("httpsUrl"):
            return p["httpsUrl"].rstrip("/")
    return None

def decode_auth(auth):
    try:
        dec = base64.b64decode(auth).decode()
        parts = dec.split(":")
        if parts[0] == "pc":
            return parts[1], parts[2]
        return parts[0], parts[1]
    except:
        return "", ""

def api_post(host, path, data, auth):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
    body = json.dumps(data, separators=(",", ":"), ensure_ascii=False) if data else ""
    sig = cal_sign(body, ts, rand)
    headers = {"Accept": "application/json, text/plain, */*",
               "Authorization": f"Basic {auth}",
               "Caller": "web", "Cms-Device": "default",
               "Mcloud-Channel": "1000101", "Mcloud-Client": "10701",
               "Mcloud-Route": "001", "Mcloud-Sign": f"{ts},{rand},{sig}",
               "Mcloud-Version": "7.14.0",
               "x-DeviceInfo": "||9|7.14.0|chrome|120.0.0.0|||windows 10||zh-CN|||",
               "x-huawei-channelSrc": "10000034", "x-inner-ntwk": "2",
               "x-m4c-caller": "PC", "x-m4c-src": "10002", "x-SvcType": "1",
               "X-Yun-Api-Version": "v1", "X-Yun-App-Channel": "10000034",
               "X-Yun-Channel-Source": "10000034",
               "X-Yun-Client-Info": "||9|7.14.0|chrome|120.0.0.0|||windows 10||zh-CN|||dW5kZWZpbmVk||",
               "X-Yun-Module-Type": "100", "X-Yun-Svc-Type": "1"}
    r = requests.post(f"{host}{path}", headers=headers, json=data, timeout=15)
    try:
        j = r.json()
    except:
        print(f"API error: {r.text[:200]}")
        return None
    if not j.get("success"):
        print(f"API error: {j.get('message','')}")
        return None
    return j

# ── API 操作 ──

def cmd_ls(auth, file_id="/"):
    host = discover_host(auth)
    if not host: return
    data = {"parentFileId": file_id, "orderBy": "updated_at", "orderDirection": "DESC",
            "imageThumbnailStyleList": ["Small", "Large"],
            "pageInfo": {"pageCursor": "", "pageSize": 100}}
    j = api_post(host, "/file/list", data, auth)
    if not j: return
    for item in j.get("data", {}).get("items", []):
        typ = "📁" if item["type"] == "folder" else "📄"
        sz = item.get("size") or 0
        sz_s = f"{sz/1024/1024:.1f}MB" if sz > 1024*1024 else f"{sz/1024:.1f}KB" if sz else "      -"
        print(f"{typ} {item['name']:30s} {sz_s:>8s}  {item.get('updatedAt','')[:10]}")
    if not j.get("data", {}).get("items"): print("(empty)")

def cmd_download(auth, file_id, output=None):
    host = discover_host(auth)
    if not host: return
    j = api_post(host, "/file/getDownloadUrl", {"fileId": file_id}, auth)
    if not j: return
    url = j.get("data", {}).get("cdnUrl") or j.get("data", {}).get("url", "")
    if not url: print("No download URL"); return
    name = output or f"download_{file_id[:8]}"
    r = requests.get(url, stream=True, timeout=30)
    with open(name, "wb") as f:
        for c in r.iter_content(8192): f.write(c)
    print(f"Downloaded to {name}")

def cmd_mkdir(auth, parent_id="/", name=None):
    if not name: print("Usage: mkdir <folder_name> [parent_id]"); return None
    host = discover_host(auth)
    if not host: return None
    data = {"parentFileId": parent_id, "name": name, "description": "",
            "type": "folder", "fileRenameMode": "force_rename"}
    j = api_post(host, "/file/create", data, auth)
    if not j: return None
    fid = j.get("data", {}).get("fileId", "")
    if fid: print(f"Created: {fid}"); return fid
    print(f"mkdir failed: {j.get('message','')}"); return None

def cmd_rm(auth, file_id):
    host = discover_host(auth)
    if not host: return False
    data = {"fileIds": [file_id]}
    j = api_post(host, "/recyclebin/batchTrash", data, auth)
    if j: print(f"Deleted: {file_id}"); return True
    return False

def cmd_check(auth):
    print("=== 和彩云 读写自检 ===")
    host = discover_host(auth)
    if not host: return False
    r = api_post(host, "/file/list", {"parentFileId": "/", "orderBy": "updated_at",
        "orderDirection": "DESC", "pageInfo": {"pageCursor": "", "pageSize": 5}}, auth)
    if not r: print("❌ 读取根目录失败"); return False
    print("✅ 读操作正常")
    ts = int(time.time())
    fname = f"ope-check-{ts}"
    fid = cmd_mkdir(auth, "/", fname)
    if not fid: print("❌ 创建文件夹失败"); return False
    r2 = api_post(host, "/file/list", {"parentFileId": "/", "orderBy": "updated_at",
        "orderDirection": "DESC", "pageInfo": {"pageCursor": "", "pageSize": 100}}, auth)
    found = False
    if r2:
        for item in r2.get("data", {}).get("items", []):
            if item.get("name") == fname: found = True; break
    if not found: cmd_rm(auth, fid); print("❌ 创建后未找到"); return False
    print("✅ 写操作正常")
    if cmd_rm(auth, fid): print("✅ 删除操作正常")
    else: print("❌ 删除失败"); return False
    print("=== 和彩云 读写自检通过 ===")
    return True

# ── 主入口 ──

def main():
    args = list(sys.argv[1:])
    auth = _ensure_token()
    if not auth:
        sys.exit(1)

    cmd = args[0] if args else "ls"
    if cmd == "ls": cmd_ls(auth, args[1] if len(args) > 1 else "/")
    elif cmd == "download": cmd_download(auth, args[1], args[2] if len(args) > 2 else None)
    elif cmd == "mkdir": cmd_mkdir(auth, args[2] if len(args) > 2 else "/", args[1] if len(args) > 1 else None)
    elif cmd == "rm":
        if not args[1:]: print("Usage: rm <file_id>"); sys.exit(1)
        cmd_rm(auth, args[1])
    elif cmd == "check": sys.exit(0 if cmd_check(auth) else 1)
    else: print(f"Unknown: {cmd}"); print("Commands: ls, download, mkdir, rm, check"); sys.exit(1)

if __name__ == "__main__":
    main()
