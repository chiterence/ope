#!/usr/bin/env python3
"""pCloud 云盘 CLI

认证通过 Bitwarden 管理（ope.pcloud.{account}），支持多账号。
"""
import json, os, subprocess, sys, time, urllib.parse, base64
import requests

API = "https://api.pcloud.com"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── BW 认证 ──
BW_ENV = {**os.environ, "BW_SKILL_CALL": "1"}

def _get_token():
    """通过 bw skill 读 pcloud token。也支持 PCLOUD_TOKEN env（兼容旧用法）。"""
    token = os.environ.get("PCLOUD_TOKEN", "") or os.environ.get("PCLOUD_AUTH", "")
    if token: return token
    r = subprocess.run(["bash", os.path.join(SCRIPT_DIR, "..", "bw", "bw.sh"),
                        "field", "ope.pcloud", "token"],
                      capture_output=True, text=True, timeout=15, env=BW_ENV)
    return r.stdout.strip() if r.returncode == 0 else None

def _api_get(path, params=None, token=None):
    if params is None: params = {}
    if token: params["auth"] = token
    r = requests.get(f"{API}{path}", params=params, timeout=15)
    if r.status_code != 200:
        print(f"❌ HTTP {r.status_code}")
        return None
    return r.json()

def _api_post(path, data=None, files=None, token=None):
    params = {}
    if token: params["auth"] = token
    if path.startswith("/"): path = path[1:]
    r = requests.post(f"{API}/{path}", params=params, data=data, files=files, timeout=30)
    if r.status_code != 200:
        print(f"❌ HTTP {r.status_code}")
        return None
    return r.json()

def _size_str(size):
    if not size: return "      -"
    s = int(size)
    if s > 1024*1024*1024: return f"{s/1024/1024/1024:.1f}GB"
    if s > 1024*1024: return f"{s/1024/1024:.1f}MB"
    if s > 1024: return f"{s/1024:.1f}KB"
    return f"{s:>5d}B"

def _folder_name(folderid, token):
    """获取文件夹名称（用于路径显示）"""
    j = _api_get("/listfolder", {"folderid": folderid}, token)
    if j and j.get("result") == 0:
        return j.get("metadata", {}).get("name", "?")
    return "?"

# ── 命令 ──

def cmd_ls(token, folderid="0"):
    j = _api_get("/listfolder", {"folderid": folderid, "showhidden": 1}, token)
    if not j or j.get("result") != 0:
        print(f"❌ 列出失败: {j}")
        return
    meta = j.get("metadata", {})
    contents = meta.get("contents", [])
    # 显示当前路径
    path = meta.get("name", "?")
    print(f"📂 {path}")
    for item in contents:
        name = item.get("name", "?")
        is_folder = item.get("isfolder", False)
        typ = "📁" if is_folder else "📄"
        sz = item.get("size", 0)
        modified = item.get("modified", "")[:10]
        fid_text = f"[{item.get('folderid','')}]" if is_folder else f"[{item.get('fileid','')}]"
        print(f"{typ} {fid_text:15s} {name:35s} {_size_str(sz):>10s}  {modified}")
    if not contents:
        print("(empty)")

def cmd_download(token, file_id, output=None):
    j = _api_get("/getfilelink", {"fileid": file_id}, token)
    if not j or j.get("result") != 0:
        # 可能传了文件名或路径
        j2 = _api_get("/getfilelink", {"path": file_id}, token)
        if not j2 or j2.get("result") != 0:
            print(f"❌ 获取下载链接失败")
            return
        j = j2
    host = j.get("hosts", [""])[0]
    path = j.get("path", "")
    if not host or not path:
        print("❌ 无下载链接"); return
    url = f"https://{host}{path}"
    name = output or path.rsplit("/", 1)[-1]
    r = requests.get(url, stream=True, timeout=30)
    if r.status_code != 200: print(f"❌ HTTP {r.status_code}"); return
    total = int(r.headers.get("content-length", 0)) or 0
    written = 0
    with open(name, "wb") as f:
        for chunk in r.iter_content(65536):
            if chunk: f.write(chunk); written += len(chunk)
            if total > 0:
                pct = int(written*100/total)
                sys.stdout.write(f"\r  {written/1024/1024:.1f}MB / {total/1024/1024:.1f}MB ({pct}%)")
                sys.stdout.flush()
    print(f"\n✅ {name}")

def cmd_mkdir(token, parent_id="0", name=None):
    if not name: print("Usage: mkdir <folder_name> [parent_id]"); return None
    j = _api_get("/createfolder", {"path": f"/{name}" if parent_id == "0" else name,
                                    "folderid": parent_id}, token)
    if j and j.get("result") == 0:
        fid = j.get("metadata", {}).get("folderid", "")
        print(f"✅ {fid}  {name}"); return fid
    print(f"❌ 创建失败: {j}"); return None

def cmd_rm(token, file_id):
    # 尝试文件夹删除
    j = _api_get("/deletefolder", {"folderid": file_id}, token)
    if j and j.get("result") == 0:
        print(f"✅ 已删除: {file_id}"); return True
    # 尝试文件删除
    j2 = _api_get("/deletefile", {"fileid": file_id}, token)
    if j2 and j2.get("result") == 0:
        print(f"✅ 已删除: {file_id}"); return True
    print(f"❌ 删除失败: {j}")
    return False

def cmd_upload(token, local_path, folder_id="0"):
    """上传文件。"""
    import os as _os
    if not _os.path.isfile(local_path):
        print(f"❌ 文件不存在: {local_path}"); return None
    name = _os.path.basename(local_path)
    with open(local_path, "rb") as f:
        files = {"file": (name, f, "application/octet-stream")}
        j = _api_post("uploadfile", data={"folderid": folder_id}, files=files, token=token)
    if j and j.get("result") == 0:
        meta = j.get("metadata", [{}])
        if isinstance(meta, list): meta = meta[0] if meta else {}
        fid = meta.get("fileid", "")
        h = meta.get("hash", "")
        sz = meta.get("size", 0)
        print(f"✅ {fid}  {name} ({sz}b)")
        return {"fileid": str(fid), "hash": h, "size": sz}
    print(f"❌ 上传失败: {j}"); return None

def cmd_check(token):
    print("=== pCloud 质检 ===")
    j = _api_get("/listfolder", {"folderid": 0}, token)
    if not j or j.get("result") != 0:
        print("❌ 读根目录失败"); return False
    print("✅ 读正常")
    ts = int(time.time())
    fname = f"ope-check-{ts}"
    j2 = _api_get("/createfolder", {"path": f"/{fname}"}, token)
    if not j2 or j2.get("result") != 0:
        print("❌ 创建文件夹失败"); return False
    fid = str(j2.get("metadata", {}).get("folderid", ""))
    print(f"✅ 创建 {fid}")
    j3 = _api_get("/listfolder", {"folderid": 0}, token)
    found = any(item.get("name") == fname
                for item in (j3.get("metadata", {}).get("contents", []) if j3 else []))
    if not found: cmd_rm(token, fid); print("❌ 创建后未找到"); return False
    print("✅ 写正常")
    if cmd_rm(token, fid): print("✅ 删正常")
    else: print("❌ 删失败"); return False
    print("=== pCloud 质检通过 ===")
    return True

# ── 主入口 ──

def main():
    args = list(sys.argv[1:])
    token = _get_token()
    if not token:
        print("❌ 需设置 PCLOUD_TOKEN 或 PCLOUD_AUTH 环境变量")
        sys.exit(1)
    cmd = args[0] if args else "ls"
    if cmd == "ls": cmd_ls(token, args[1] if len(args) > 1 else "0")
    elif cmd == "download":
        fid = args[1] if len(args) > 1 else ""
        if not fid: print("Usage: download <file_id|path> [output]"); sys.exit(1)
        cmd_download(token, fid, args[2] if len(args) > 2 else None)
    elif cmd == "mkdir": cmd_mkdir(token, args[2] if len(args) > 2 else "0", args[1] if len(args) > 1 else None)
    elif cmd == "rm":
        fid = args[1] if len(args) > 1 else None
        if not fid: print("Usage: rm <file_id|folder_id>"); sys.exit(1)
        cmd_rm(token, fid)
    elif cmd == "check": sys.exit(0 if cmd_check(token) else 1)
    else: print(f"Unknown: {cmd}"); print("Commands: ls, download, mkdir, rm, check"); sys.exit(1)

if __name__ == "__main__":
    main()
