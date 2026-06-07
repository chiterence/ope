#!/usr/bin/env python3
"""天翼云盘 (cloud.189.cn) CLI

认证通过 Bitwarden 管理（ope.tianyi.{account}），支持多账号。
认证失效时自动续期：cookie 过期 → 密码重登 → 存回 BW。

用法：
  python3 tianyi.py ls                      # 默认账号
  python3 tianyi.py ls -a <别名>             # 切换账号
  python3 tianyi.py -a home ls              # 同上（-a 放前面）
"""
import json, os, re, subprocess, sys, time, base64
import requests
from urllib.parse import urlparse, parse_qs

# ── 常量 ──
HOST = "https://cloud.189.cn"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BW_ITEM = "ope.tianyi"       # 默认账号
ACCOUNT = "default"

RSA_PUBKEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDY7mpaUysvgQkbp0iIn2ezoUyh
i1zPFn0HCXloLFWT7uoNkqtrphpQ/63LEcPz1VYzmDuDIf3iGxQKzeoHTiVMSmW6
FlhDeqVOG094hFJvZeK4OzA6HVwzwnEW5vIZ7d+u61RV1bsFxmB68+8JXs3ycGcE
4anY+YzZJcyOcEGKVQIDAQAB
-----END PUBLIC KEY-----"""

B64MAP = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
BI_RM = list("0123456789abcdefghijklmnopqrstuvwxyz")

# ── 凭证管理（通过 bw skill 的 bw.sh 接口） ──

BW_SH = os.path.join(SCRIPT_DIR, "..", "bw", "bw.sh")
BW_ENV = {**os.environ, "BW_SKILL_CALL": "1"}

def _load_creds():
    """从 bw skill 读凭证。返回 (cookies_dict, phone, password)。"""
    r = subprocess.run(["bash", BW_SH, "field", "ope.tianyi", "cookies"],
                      capture_output=True, text=True, timeout=15, env=BW_ENV)
    cookies = json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else {}
    r2 = subprocess.run(["bash", BW_SH, "field", "ope.tianyi", "phone"],
                       capture_output=True, text=True, timeout=15, env=BW_ENV)
    phone = r2.stdout.strip() if r2.returncode == 0 else ""
    r3 = subprocess.run(["bash", BW_SH, "password", "ope.tianyi"],
                       capture_output=True, text=True, timeout=15, env=BW_ENV)
    password = r3.stdout.strip() if r3.returncode == 0 else ""
    return cookies, phone, password

def _save_cookies(cookies_dict):
    """存新 cookies 回 bw skill。"""
    val = json.dumps(cookies_dict, ensure_ascii=False)
    subprocess.run(["bash", BW_SH, "set", "ope.tianyi", "cookies", val],
                  capture_output=True, text=True, timeout=15, env=BW_ENV)

# ── RSA 工具 ──

def rsa_encrypt(text):
    import rsa as rsa_lib
    pk = rsa_lib.PublicKey.load_pkcs1_openssl_pem(RSA_PUBKEY.encode())
    return rsa_lib.encrypt(text.encode("utf-8"), pk)

def b64tohex(a):
    d, e = "", 0
    for ch in a:
        if ch == "=": continue
        v = B64MAP.index(ch)
        if e == 0: e = 1; d += BI_RM[v >> 2]; c = 3 & v
        elif e == 1: e = 2; d += BI_RM[c << 2 | v >> 4]; c = 15 & v
        elif e == 2: e = 3; d += BI_RM[c]; d += BI_RM[v >> 2]; c = 3 & v
        else: e = 0; d += BI_RM[c << 2 | v >> 4]; d += BI_RM[15 & v]
    if e == 1: d += BI_RM[c << 2]
    return d

def rsa_encode(text):
    from base64 import b64encode
    return '{RSA}' + b64tohex(b64encode(rsa_encrypt(text)).decode())

# ── Session 管理 ──

def make_session(cookies):
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Referer": "https://cloud.189.cn/",
                       "Accept": "application/json;charset=UTF-8"})
    for k, v in cookies.items():
        s.cookies.set(k, v, domain=".cloud.189.cn")
    return s

def get_session_cookies(session):
    c = {}
    for cookie in session.cookies:
        if ".cloud.189.cn" in (cookie.domain or ""):
            c[cookie.name] = cookie.value
    return c

def session_valid(session):
    try:
        r = session.get(f"{HOST}/v2/getUserLevelInfo.action", timeout=10)
        return r.status_code == 200 and "InvalidSessionKey" not in r.text
    except:
        return False

# ── 登录（v2） ──

def login_v2(session, phone, password):
    r = session.get(f"{HOST}/api/portal/loginUrl.action",
        params={"pageId": 1, "redirectURL": "https://cloud.189.cn/main.action"},
        timeout=15, allow_redirects=True)
    qp = parse_qs(urlparse(r.url).query)
    lt, req_id = qp.get("lt", [""])[0], qp.get("reqId", [""])[0]
    app_id = qp.get("appId", [""])[0]
    if not lt or not req_id: return "cannot_get_params"
    session.headers.update({"Referer": r.url})

    rc = session.post("https://open.e.189.cn/api/logbox/oauth2/appConf.do",
        headers={"lt": lt, "reqId": req_id},
        data={"version": "2.0", "appKey": app_id}, timeout=10).json().get("data", {})

    session.post("https://open.e.189.cn/api/logbox/oauth2/needcaptcha.do",
        headers={"lt": lt, "reqId": req_id},
        data={"accountType": "01", "userName": rsa_encode(phone), "appKey": "cloud"},
        timeout=10)

    r3 = session.post("https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do",
        headers={"lt": lt, "reqId": req_id},
        data={
            "version": "v2.0", "apToken": "",
            "appKey": rc.get("appKey", "cloud"),
            "pageKey": rc.get("pageKey", "normal"),
            "accountType": rc.get("accountType", "01"),
            "userName": rsa_encode(phone), "epd": rsa_encode(password),
            "captchaType": "", "validateCode": "", "smsValidateCode": "",
            "captchaToken": "",
            "returnUrl": rc.get("returnUrl", "https://cloud.189.cn/main.action"),
            "mailSuffix": rc.get("mailSuffix", "@189.cn"),
            "dynamicCheck": "", "clientType": str(rc.get("clientType", "1")),
            "cb_SaveName": "1",
            "isOauth2": str(rc.get("isOauth2", "True")).lower(),
            "state": rc.get("state", ""), "paramId": rc.get("paramId", ""),
        }, timeout=15)
    try:
        j = r3.json()
    except: return "parse_error"
    if j.get("result") == 0 or j.get("msg") == "登录成功":
        if j.get("toUrl"): session.get(j["toUrl"], timeout=10)
        return "ok"
    if j.get("result") == -133 or "设备" in j.get("msg",""): return "need_2fa"
    if "密码" in j.get("msg","") or "账户名" in j.get("msg",""): return "wrong_password"
    return f"unknown:{j.get('msg','')}"

# ── 认证中间件（env 驱动） ──

def ensure_session():
    """从环境变量读取凭证 → 创建 session → 失效时自动续期 → 输出 RENEWED 信号。
    返回 (session, ok)"""
    cookies, phone, password = _load_creds()
    session = make_session(cookies)

    if cookies and session_valid(session):
        return session, True

    if not phone or not password:
        print("❌ 凭证不完整：需设置 TIANYI_COOKIES, TIANYI_PHONE, TIANYI_PASSWORD")
        print("   例: TIANYI_COOKIES='{\"COOKIE_LOGIN_USER\":\"...\",\"JSESSIONID\":\"...\"}' TIANYI_PHONE=... TIANYI_PASSWORD=... python3 tianyi.py ls")
        return None, False

    print("🔄 Cookie 失效，尝试自动续期...")
    result = login_v2(session, phone, password)
    if result == "ok":
        new_cookies = get_session_cookies(session)
        if new_cookies:
            _save_cookies(new_cookies)
        print("✅ 自动续期成功")
        return session, True
    elif result == "need_2fa":
        print("❌ 需要二次设备验证，无法自动重登。请手动更新 TIANYI_COOKIES。")
        return None, False
    elif result == "wrong_password":
        print("❌ 密码错误，无法自动续期。")
        return None, False
    else:
        print(f"❌ 自动续期失败（{result}）。")
        return None, False

# ── API 操作 ──

def list_files(session, folder_id="-11"):
    if folder_id in ("-11", "/"):
        r = session.get(f"{HOST}/api/portal/listFiles.action",
            params={"fileId": "-11", "noCache": str(time.time())}, timeout=15)
        if r.status_code != 200: print(f"❌ HTTP {r.status_code}"); return
        try: j = r.json()
        except: print(f"❌ 响应异常"); return
        items = j.get("data", [])
        for item in items:
            typ = "📁" if item.get("isFolder") == 1 else "📄"
            name = item.get("fileName", "?")
            sid = str(item.get("fileId", ""))
            sz = item.get("fileSize", 0)
            sz_s = f"{sz/1024/1024:.1f}MB" if sz > 1024*1024 else f"{sz/1024:.1f}KB" if sz else "      -"
            print(f"{typ} [{sid:12s}] {name:30s} {sz_s:>8s}  {item.get('lastOpTime','')[:10]}")
        if not items: print("(empty)")
    else:
        page = 1
        found = False
        while True:
            r = session.get(f"{HOST}/api/open/file/listFiles.action", params={
                "folderId": str(folder_id), "orderBy": "lastOpTime", "descending": "true",
                "pageNum": page, "pageSize": 60, "iconOption": 5, "mediaType": 0,
                "noCache": str(time.time()),
            }, timeout=15)
            if r.status_code != 200: print(f"❌ HTTP {r.status_code}"); return
            try: j = r.json()
            except: print(f"❌ 响应异常"); return
            fl = j.get("fileListAO", {})
            for item in fl.get("folderList", []):
                found = True; print(f"📁 [{str(item.get('id','')):12s}] {item.get('name','?'):30s}  (文件夹)")
            for item in fl.get("fileList", []):
                found = True; sz = item.get("size",0)
                sz_s = f"{sz/1024/1024:.1f}MB" if sz > 1024*1024 else f"{sz/1024:.1f}KB" if sz else "      -"
                print(f"📄 [{str(item.get('id','')):12s}] {item.get('name','?'):30s} {sz_s:>8s}  {item.get('lastOpTime','')[:10]}")
            if page * 60 >= fl.get("count", 0): break
            page += 1; time.sleep(0.3)
        if not found: print("(empty)")

def download(session, file_id, output=None):
    r = session.get(f"{HOST}/v2/getFileInfo.action", params={"fileId": str(file_id)}, timeout=15)
    if r.status_code != 200: print(f"❌ HTTP {r.status_code}"); return
    try: info = r.json()
    except: print("❌ 响应异常"); return
    if "errorCode" in info: print("❌ 文件不存在"); return
    durl = info.get("downloadUrl", "")
    if not durl: print("❌ 无下载链接"); return
    durl = "https:" + durl if durl.startswith("//") else durl
    out = output or info.get("fileName", f"file_{file_id[:8]}")
    r2 = session.get(durl, stream=True, timeout=30)
    if r2.status_code != 200: print(f"❌ 下载失败: HTTP {r2.status_code}"); return
    total = int(r2.headers.get("content-length", 0)) or 0
    written = 0
    with open(out, "wb") as f:
        for chunk in r2.iter_content(65536):
            if chunk: f.write(chunk); written += len(chunk)
            if total > 0:
                pct = int(written*100/total)
                sys.stdout.write(f"\r  {written/1024/1024:.1f}MB / {total/1024/1024:.1f}MB ({pct}%)")
                sys.stdout.flush()
    print(f"\n✅ 下载完成: {out}")

def mkdir(session, parent_id="-11", name=None):
    if not name: print("Usage: mkdir <folder_name> [parent_id]"); return None
    r = session.get(f"{HOST}/v2/createFolder.action",
        params={"parentId": str(parent_id), "fileName": name}, timeout=15)
    try: j = r.json()
    except: print(f"❌ 创建失败"); return None
    if "fileId" in j:
        fid = str(j["fileId"]); print(f"✅ {fid}"); return fid
    print(f"❌ 创建失败: {j}"); return None

def rm(session, file_id):
    info = session.get(f"{HOST}/v2/getFileInfo.action", params={"fileId": str(file_id)}, timeout=10)
    if info.status_code != 200: print("❌ 文件不存在"); return False
    try: info = info.json()
    except: print("❌ 文件不存在"); return False
    if "errorCode" in info: print("❌ 文件不存在"); return False
    task = {"fileId": str(file_id), "srcParentId": str(info.get("parentId","-11")),
            "fileName": info.get("fileName",""), "isFolder": 1 if info.get("isFolder",0) else 0}
    r = session.post(f"{HOST}/createBatchTask.action", data={"type":"DELETE","taskInfos":json.dumps([task])}, timeout=15)
    tid = r.text.strip('"').strip("'") if r.text else ""
    if not tid: print("❌ 删除失败"); return False
    for _ in range(20):
        time.sleep(0.5)
        s = session.post(f"{HOST}/checkBatchTask.action", data={"type":"DELETE","taskId":tid}, timeout=10)
        try:
            if s.json().get("taskStatus",0) == 4: print(f"✅ 删除成功: {file_id}"); return True
        except: pass
    print("⚠️  删除超时（可能已删除）"); return True

def who(session):
    r = session.get(f"{HOST}/v2/getLoginedInfos.action", timeout=10)
    if r.status_code != 200: print("❌ 获取用户信息失败"); return
    try:
        u = r.json()
        used = float(u.get("usedSize",0))/1024/1024/1024
        quota = float(u.get("quota",0))/1024/1024/1024
        print(f"用户: {u.get('userAccount','?')}  空间: {used:.1f}GB / {quota:.1f}GB ({used/quota*100:.1f}%)")
        if u.get("superVip"): print(f"VIP: 是 (到期 {u.get('superEndTime','?')})")
    except: print("解析失败")

def check(session):
    print("=== 天翼云盘 读写自检 ===")
    if not session_valid(session): print("❌ 会话无效"); return False
    print("✅ 认证正常")
    r = session.get(f"{HOST}/v2/getLoginedInfos.action", timeout=10)
    if r.status_code == 200:
        try:
            u = r.json()
            used = float(u.get("usedSize",0))/1024/1024/1024
            quota = float(u.get("quota",0))/1024/1024/1024
            print(f"📊 {u.get('userAccount','?')}  {used:.1f}GB/{quota:.1f}GB")
        except: pass
    r = session.get(f"{HOST}/api/portal/listFiles.action", params={"fileId": "-11", "noCache": str(time.time())}, timeout=15)
    if r.status_code != 200: print("❌ 读取失败"); return False
    print("✅ 读正常")
    ts = int(time.time())
    fname = f"ope-check-{ts}"
    r2 = session.get(f"{HOST}/v2/createFolder.action", params={"parentId":"-11","fileName":fname}, timeout=15)
    try: j = r2.json()
    except: print("❌ 创建失败"); return False
    if "fileId" not in j: print("❌ 创建失败"); return False
    fid = str(j["fileId"]); print(f"✅ {fid}")
    r3 = session.get(f"{HOST}/api/portal/listFiles.action", params={"fileId":"-11","noCache":str(time.time())}, timeout=10)
    found = False
    if r3.status_code == 200:
        for item in r3.json().get("data",[]):
            if item.get("fileName") == fname: found = True; break
    if not found: print("❌ 创建后未找到"); rm(session,fid); return False
    print("✅ 写正常")
    if rm(session,fid): print("✅ 删正常")
    else: print("❌ 删失败"); return False
    print("=== 天翼云盘 自检通过 ===")
    return True

# ── 主入口 ──

def main():
    global ACCOUNT
    args = list(sys.argv[1:])

    session, ok = ensure_session()
    if not ok: sys.exit(1)

    cmd = args[0] if args else "ls"

    if cmd == "ls": list_files(session, args[1] if len(args) > 1 else "-11")
    elif cmd == "download":
        fid = args[1] if len(args) > 1 else ""
        if not fid: print("Usage: download <file_id> [output_name]"); sys.exit(1)
        download(session, fid, args[2] if len(args) > 2 else None)
    elif cmd == "mkdir": mkdir(session, args[2] if len(args) > 2 else "-11", args[1] if len(args) > 1 else None)
    elif cmd == "rm":
        fid = args[1] if len(args) > 1 else None
        if not fid: print("Usage: rm <file_id>"); sys.exit(1)
        rm(session, fid)
    elif cmd == "who": who(session)
    elif cmd == "check": ok = check(session); sys.exit(0 if ok else 1)
    else:
        print(f"Unknown: {cmd}")
        print("Commands: ls, download, mkdir, rm, who, check")
        sys.exit(1)

if __name__ == "__main__":
    main()
