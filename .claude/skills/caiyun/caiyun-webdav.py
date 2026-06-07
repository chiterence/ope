#!/usr/bin/env python3
"""和彩云 WebDAV — 直接包 API，不经过 FUSE

Windows 映射 Z: 盘：
  net use Z: http://localhost:15800/ /persistent

如果 error 67，试试从管理员 cmd 跑：
  netsh interface portproxy add v4tov4 listenport=15800 listenaddress=0.0.0.0 connectport=15800 connectaddress=127.0.0.1
"""
import base64, datetime, hashlib, json, os, random, shutil, string, sys, threading, time, urllib.parse
import requests

AUTH = os.environ.get("CAIYUN_AUTH", "")
if not AUTH:
    print("Set CAIYUN_AUTH env var first", file=sys.stderr)
    sys.exit(1)

# WebDAV Basic Auth — V2rayN 要求非空用户名密码
WEBDAV_USER = "v2ray"
WEBDAV_PASS = "v2ray"

# ── Token auto-refresh（来自 AList 实现） ──────────────────────────────

_AUTH_LOCK = threading.Lock()
_REFRESH_INTERVAL = 12 * 3600  # 12 小时

def _refresh_token():
    """Refresh 139 cloud session token if close to expiry."""
    global AUTH
    try:
        dec = base64.b64decode(AUTH).decode()
        parts = dec.split(":")
        if len(parts) < 3:
            return False
        phone = parts[1]
        token_parts = parts[2].split("|")
        session_token = token_parts[0]
        # Check expiry if available
        if len(token_parts) >= 4:
            expiry_ms = int(token_parts[3])
            remaining = expiry_ms - int(time.time() * 1000)
            if remaining > 1000 * 60 * 60 * 24 * 15:  # > 15 天
                return True  # 无需刷新
            if remaining < 0:
                return False  # 已过期，无法刷新
        # Call refresh API
        xml_body = f"<root><token>{session_token}</token><account>{phone}</account><clienttype>656</clienttype></root>"
        r = requests.post(
            "https://aas.caiyun.feixin.10086.cn:443/tellin/authTokenRefresh.do",
            data=xml_body,
            headers={"Content-Type": "application/xml"},
            timeout=15,
        )
        import xml.etree.ElementTree as ET
        root = ET.fromstring(r.content)
        ret = root.findtext("return", "")
        if ret != "0":
            return False
        new_token = root.findtext("token", "")
        if not new_token:
            return False
        # Rebuild auth: pc:phone:new_token
        prefix = parts[0]
        new_auth = base64.b64encode(f"{prefix}:{phone}:{new_token}".encode()).decode()
        with _AUTH_LOCK:
            AUTH = new_auth
        # Persist for next boot
        try:
            os.makedirs("/home/user/ope/var/run", exist_ok=True)
            with open("/home/user/ope/var/run/caiyun-auth", "w") as f:
                f.write(new_auth)
        except: pass
        return True
    except Exception as e:
        print(f"[token refresh] failed: {e}", flush=True)
        return False

def _refresh_loop():
    """Background loop refreshing token every 12 hours."""
    while True:
        time.sleep(_REFRESH_INTERVAL)
        _refresh_token()

# Try refresh on startup, start background loop
_refresh_token()
t = threading.Thread(target=_refresh_loop, daemon=True)
t.start()

# ── API ────────────────────────────────────────────────────────────────

def cal_sign(body, ts, rand_str):
    body = urllib.parse.quote(body, safe='~')
    body = body.replace('+', '%20').replace('%21', '!').replace('%27', "'")
    body = body.replace('%28', '(').replace('%29', ')').replace('%2A', '*')
    body = ''.join(sorted(body))
    body = base64.b64encode(body.encode()).decode()
    h1 = hashlib.md5(body.encode()).hexdigest()
    h2 = hashlib.md5((ts + ':' + rand_str).encode()).hexdigest()
    return hashlib.md5((h1 + h2).encode()).hexdigest().upper()

_H, _HL = None, threading.Lock()

def _host():
    global _H
    with _HL:
        if _H: return _H
        phone = ""
        try:
            dec = base64.b64decode(AUTH).decode().split(":")
            phone = dec[1] if dec[0] == "pc" else dec[0]
        except: pass
        data = {"userInfo": {"userType": 1, "accountType": 1, "accountName": phone}, "modAddrType": 1}
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        rand = ''.join(random.choices(string.ascii_lowercase+string.digits, k=16))
        sig = cal_sign(json.dumps(data, separators=(",",":"), ensure_ascii=False), ts, rand)
        hdrs = {
            "Accept":"application/json, text/plain, */*","CMS-DEVICE":"default",
            "Authorization":f"Basic {AUTH}","mcloud-channel":"1000101","mcloud-client":"10701",
            "mcloud-sign":f"{ts},{rand},{sig}","mcloud-version":"7.14.0",
            "Origin":"https://yun.139.com","Referer":"https://yun.139.com/w/",
            "x-DeviceInfo":"||9|7.14.0|chrome|120.0.0.0|||windows 10||zh-CN|||",
            "x-huawei-channelSrc":"10000034","x-inner-ntwk":"2","x-m4c-caller":"PC",
            "x-m4c-src":"10002","x-SvcType":"1","Inner-Hcy-Router-Https":"1",
        }
        r = requests.post("https://user-njs.yun.139.com/user/route/qryRoutePolicy",
                          headers=hdrs, json=data, timeout=10)
        for p in r.json().get("data",{}).get("routePolicyList",[]):
            if p.get("modName")=="personal" and p.get("httpsUrl"):
                _H = p["httpsUrl"].rstrip("/")
                return _H
        raise RuntimeError("no personal cloud host")

def _api(path, data):
    host = _host()
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    rand = ''.join(random.choices(string.ascii_lowercase+string.digits, k=16))
    body = json.dumps(data, separators=(",",":"), ensure_ascii=False) if data else ""
    sig = cal_sign(body, ts, rand)
    hdrs = {
        "Accept":"application/json, text/plain, */*","Authorization":f"Basic {AUTH}",
        "Caller":"web","Cms-Device":"default","Mcloud-Channel":"1000101",
        "Mcloud-Client":"10701","Mcloud-Route":"001","Mcloud-Sign":f"{ts},{rand},{sig}",
        "Mcloud-Version":"7.14.0",
        "x-DeviceInfo":"||9|7.14.0|chrome|120.0.0.0|||windows 10||zh-CN|||",
        "x-huawei-channelSrc":"10000034","x-inner-ntwk":"2","x-m4c-caller":"PC",
        "x-m4c-src":"10002","x-SvcType":"1","X-Yun-Api-Version":"v1",
        "X-Yun-App-Channel":"10000034","X-Yun-Channel-Source":"10000034",
        "X-Yun-Client-Info":"||9|7.14.0|chrome|120.0.0.0|||windows 10||zh-CN|||dW5kZWZpbmVk||",
        "X-Yun-Module-Type":"100","X-Yun-Svc-Type":"1",
    }
    r = requests.post(f"{host}{path}", headers=hdrs, json=data, timeout=15)
    j = r.json()
    if not j.get("success"): raise RuntimeError(j.get("message","api error"))
    return j

def _list(pid):
    j = _api("/file/list", {"parentFileId":pid,"orderBy":"updated_at",
        "orderDirection":"DESC","pageInfo":{"pageCursor":"","pageSize":200}})
    return j.get("data",{}).get("items",[])

def _dl_url(fid):
    j = _api("/file/getDownloadUrl", {"fileId":fid})
    return j.get("data",{}).get("cdnUrl") or j.get("data",{}).get("url","")

def _mkdir(pid, name):
    j = _api("/file/create", {"parentFileId":pid,"name":name,"description":"",
        "type":"folder","fileRenameMode":"force_rename"})
    return j.get("data",{}).get("fileId","")

def _rm(fid):
    return _api("/recyclebin/batchTrash", {"fileIds":[fid]})

# ── Resolve path → fileId ──────────────────────────────────────────────

_pids = {"/":"/"}
_plk = threading.Lock()

def _resolve(path):
    with _plk:
        if path in _pids: return _pids[path]
    parts = path.strip("/").split("/")
    par = "/"
    for p in parts:
        cur = par.rstrip("/")+"/"+p
        with _plk:
            if cur in _pids:
                par = _pids[par]
                continue
        items = _list(par)
        hit = next((i for i in items if i.get("name")==p), None)
        if not hit: return None
        fid = hit.get("fileId","")
        with _plk:
            _pids[cur] = fid
        par = fid if hit["type"]=="folder" else cur
    return _pids.get(path.strip("/") and "/"+"/".join(parts) or "/")

def _resolve_with_info(path, retry=True):
    """Return (fileId, info_dict_or_None)."""
    if path == "/": return "/", {"name":"/","type":"folder","updatedAt":"","size":0}
    # Check cache first — if info missing, rebuild from parent
    with _plk:
        if path in _pids:
            fid = _pids[path]
            if fid != "/":
                parent_path = ("/"+"/".join(path.strip("/").split("/")[:-1])) if path.strip("/") else "/"
                parent_id = _resolve(parent_path)
                if parent_id:
                    items = _list(parent_id)
                    name = path.rstrip("/").rsplit("/",1)[-1]
                    hit = next((i for i in items if i.get("name")==name), None)
                    if hit:
                        with _plk: _pids[path] = hit.get("fileId","")
                        return hit.get("fileId",""), hit
                return fid, {"name":path.rstrip("/").rsplit("/",1)[-1],"type":"folder","updatedAt":"","size":0}
    parts = path.strip("/").split("/")
    name = parts[-1]
    parent_path = ("/"+"/".join(parts[:-1])) if len(parts)>1 else "/"
    parent_id = _resolve(parent_path)
    if parent_id is None: return None, None
    items = _list(parent_id)
    hit = next((i for i in items if i.get("name")==name), None)
    if not hit and retry:
        time.sleep(0.5)
        items = _list(parent_id)
        hit = next((i for i in items if i.get("name")==name), None)
    if not hit: return None, None
    fid = hit.get("fileId","")
    with _plk:
        _pids[path] = fid
    return fid, hit

def _inv(path):
    with _plk:
        for k in list(_pids):
            if k==path or k.startswith(path.rstrip("/")+"/"):
                del _pids[k]

# ── WebDAV WSGI app ────────────────────────────────────────────────────

def _rfc1123(dt):
    return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")

def _prop_xml(path, info, children):
    """Build PROPFIND multistat XML (Windows-compatible, wsgidav format)."""
    is_dir = info.get("type")=="folder" or path=="/"
    name = info.get("name","/") if info else "/"
    size = info.get("size",0) or 0
    modified = info.get("updatedAt","")
    if modified:
        try: lastmod = _rfc1123(datetime.datetime.strptime(modified[:19], "%Y-%m-%dT%H:%M:%S"))
        except: lastmod = _rfc1123(datetime.datetime.now(datetime.UTC))
    else:
        lastmod = _rfc1123(datetime.datetime.now(datetime.UTC))

    def entry(p, dname, isdir, sz, lm):
        etag = f'<ns0:getetag>"{hashlib.md5(p.encode()).hexdigest()}"</ns0:getetag>' if not isdir else ""
        return (
            f'<ns0:response><ns0:href>{urllib.parse.quote(p)}</ns0:href>'
            f'<ns0:propstat><ns0:prop>'
            f'<ns0:resourcetype>{"<ns0:collection />" if isdir else ""}</ns0:resourcetype>'
            f'<ns0:displayname>{dname}</ns0:displayname>'
            f'<ns0:getcontenttype>{"httpd/unix-directory" if isdir else "application/octet-stream"}</ns0:getcontenttype>'
            f'{"<ns0:getcontentlength>"+str(sz)+"</ns0:getcontentlength>" if not isdir else ""}'
            f'<ns0:getlastmodified>{lm}</ns0:getlastmodified>'
            f'<ns0:creationdate>{lm}</ns0:creationdate>'
            f'{etag}'
            f'<ns0:lockdiscovery />'
            f'<ns0:supportedlock>'
            f'<ns0:lockentry><ns0:lockscope><ns0:exclusive /></ns0:lockscope><ns0:locktype><ns0:write /></ns0:locktype></ns0:lockentry>'
            f'<ns0:lockentry><ns0:lockscope><ns0:shared /></ns0:lockscope><ns0:locktype><ns0:write /></ns0:locktype></ns0:lockentry>'
            f'</ns0:supportedlock>'
            f'</ns0:prop><ns0:status>HTTP/1.1 200 OK</ns0:status></ns0:propstat>'
            f'</ns0:response>'
        )

    lines = ['<?xml version="1.0" encoding="utf-8" ?>']
    lines.append('<ns0:multistatus xmlns:ns0="DAV:">')
    lines.append(entry(path, name, is_dir, size, lastmod))
    for c in (children or []):
        cp = path.rstrip("/")+"/"+c["name"]
        cd = c["type"]=="folder"
        cs = c.get("size",0) or 0
        cm = c.get("updatedAt","")
        if cm:
            try: clm = _rfc1123(datetime.datetime.strptime(cm[:19], "%Y-%m-%dT%H:%M:%S"))
            except: clm = lastmod
        else: clm = lastmod
        lines.append(entry(cp, c["name"], cd, cs, clm))
    lines.append('</ns0:multistatus>')
    return "\n".join(lines).encode("utf-8")

def app(environ, start_response):
    method = environ["REQUEST_METHOD"]
    path = urllib.parse.unquote(environ.get("PATH_INFO","/") or "/")

    # OPTIONS
    if method == "OPTIONS":
        h = [("DAV","1, 2"), ("Allow","OPTIONS, PROPFIND, GET, HEAD, MKCOL, DELETE"),
             ("Content-Length","0")]
        start_response("200 OK", h); return [b""]

    # PROPFIND
    if method == "PROPFIND":
        depth = environ.get("HTTP_DEPTH","1")
        try:
            fid, info = _resolve_with_info(path)
            if fid is None:
                start_response("404 Not Found", [("Content-Type","text/xml")])
                return [b"<error><message>Not Found</message></error>"]
            children = []
            if depth != "0" or path == "/":
                items = _list(fid)
                children = items if isinstance(items, list) else []
            body = _prop_xml(path, info, children)
            start_response("207 Multi-Status", [
                ("Content-Type","text/xml; charset=utf-8"),
                ("DAV","1, 2"), ("Content-Length",str(len(body))),
            ])
            return [body]
        except Exception as e:
            body = f"PROPFIND error: {e}".encode()
            start_response("500 Internal Server Error", [("Content-Length",str(len(body)))])
            return [body]

    # GET / HEAD (download or directory browser)
    if method in ("GET","HEAD"):
        try:
            fid, info = _resolve_with_info(path)
            if fid is None or (info and info.get("type")=="folder"):
                if fid and info and info.get("type")=="folder":
                    items = _list(fid)
                    body = ("<html><body><ul>" +
                            "".join(f'<li><a href="{urllib.parse.quote(i["name"])}">{i["name"]}</a></li>'
                                    for i in items) +
                            "</ul></body></html>").encode("utf-8")
                    start_response("200 OK", [("Content-Type","text/html; charset=utf-8"),
                                              ("Content-Length",str(len(body)))])
                    return [body]
                start_response("404 Not Found", [("Content-Length","0")]); return [b""]
            if method == "HEAD":
                start_response("200 OK", [("Content-Type","application/octet-stream"),
                                          ("Content-Length",str(info.get("size",0) or 0))])
                return [b""]
            url = _dl_url(fid)
            if not url:
                start_response("500 Internal Server Error", [("Content-Length","0")]); return [b""]
            content = requests.get(url, timeout=30).content
            start_response("200 OK", [("Content-Type","application/octet-stream"),
                                      ("Content-Length",str(len(content)))])
            return [content]
        except Exception as e:
            body = f"GET error: {e}".encode()
            start_response("500 Internal Server Error", [("Content-Length",str(len(body)))])
            return [body]

    # MKCOL
    if method == "MKCOL":
        try:
            ppath = path.rstrip("/").rsplit("/",1)[0] or "/"
            name = path.rstrip("/").rsplit("/",1)[-1]
            pid = _resolve(ppath)
            if pid is None:
                start_response("409 Conflict", [("Content-Length","0")]); return [b""]
            fid = _mkdir(pid, name)
            if fid:
                _inv(ppath)
                with _plk: _pids[path] = fid
                start_response("201 Created", [("Content-Length","0")]); return [b""]
            start_response("500 Internal Server Error", [("Content-Length","0")]); return [b""]
        except Exception as e:
            body = f"MKCOL error: {e}".encode()
            start_response("500 Internal Server Error", [("Content-Length",str(len(body)))])
            return [body]

    # DELETE
    if method == "DELETE":
        try:
            fid, info = _resolve_with_info(path)
            if fid is None or fid == "/":
                start_response("404 Not Found", [("Content-Length","0")]); return [b""]
            _rm(fid)
            _inv(path)
            start_response("204 No Content", [("Content-Length","0")]); return [b""]
        except Exception as e:
            body = f"DELETE error: {e}".encode()
            start_response("500 Internal Server Error", [("Content-Length",str(len(body)))])
            return [body]

    start_response("405 Method Not Allowed", [("Content-Length","0")])
    return [b""]

# ── Multi-threaded HTTP/1.1 server ──────────────────────────────────────

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from io import BytesIO

class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def do_OPTIONS(self):   self._handle("OPTIONS")
    def do_PROPFIND(self):  self._handle("PROPFIND")
    def do_GET(self):       self._handle("GET")
    def do_HEAD(self):      self._handle("HEAD")
    def do_MKCOL(self):     self._handle("MKCOL")
    def do_DELETE(self):    self._handle("DELETE")
    def do_PUT(self):       self._handle("PUT")
    def log_message(self, fmt, *a):
        try:
            sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt%a))
        except: pass

    def _send(self, code, body=b"", ctype="text/plain"):
        try:
            self.send_response(code)
            if body or isinstance(body, bytes):
                if isinstance(body, str): body = body.encode("utf-8")
                self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Type", ctype)
            self.end_headers()
            if body and self.command != "HEAD":
                self.wfile.write(body)
        except: pass

    def _check_auth(self):
        """Validate Basic Auth. Returns True if valid."""
        ah = self.headers.get("Authorization", "")
        if not ah.startswith("Basic "):
            return False
        try:
            dec = base64.b64decode(ah[6:]).decode()
            u, p = dec.split(":", 1)
            return u == WEBDAV_USER and p == WEBDAV_PASS
        except:
            return False

    def _handle(self, method):
        path = urllib.parse.unquote(self.path)
        try:
            if method == "OPTIONS":
                self.send_response(200)
                self.send_header("DAV", "1,2")
                self.send_header("Allow", "OPTIONS, HEAD, GET, PROPFIND, MKCOL, DELETE, PUT, COPY, MOVE, PROPPATCH, LOCK, UNLOCK")
                self.send_header("MS-Author-Via", "DAV")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            # Auth required for all methods except OPTIONS
            if not self._check_auth():
                self.send_response(401)
                self.send_header("WWW-Authenticate", 'Basic realm="WebDAV"')
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            if method == "PROPFIND":
                depth = self.headers.get("Depth", "1")
                fid, info = _resolve_with_info(path)
                if fid is None:
                    return self._send(404, b"Not Found")
                children = []
                if depth != "0":
                    items = _list(fid)
                    children = items if isinstance(items, list) else []
                body = _prop_xml(path, info, children)
                self.send_response(207)
                self.send_header("DAV", "1,2")
                self.send_header("Content-Type", "application/xml; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if method in ("GET","HEAD"):
                # Check local PUT storage first
                local = f"/home/user/ope/var/webdav{path}"
                if os.path.isfile(local):
                    sz = os.path.getsize(local)
                    if method == "HEAD":
                        return self._send(200, b"", "application/octet-stream")
                    content = open(local, "rb").read()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/octet-stream")
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                    return
                fid, info = _resolve_with_info(path)
                if fid is None:
                    return self._send(404, b"Not Found")
                if info and info.get("type")=="folder":
                    items = _list(fid)
                    body = "<html><body><ul>"
                    for i in items:
                        body += f'<li><a href="{urllib.parse.quote(i["name"])}">{i["name"]}</a></li>'
                    body += "</ul></body></html>"
                    return self._send(200, body.encode(), "text/html; charset=utf-8")
                url = _dl_url(fid)
                if not url:
                    return self._send(500, b"no download url")
                content = requests.get(url, timeout=30).content
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                if method == "GET":
                    self.wfile.write(content)
                return

            if method == "MKCOL":
                ppath = path.rstrip("/").rsplit("/",1)[0] or "/"
                name = path.rstrip("/").rsplit("/",1)[-1]
                pid = _resolve(ppath)
                if pid is None:
                    return self._send(409, b"parent not found")
                fid = _mkdir(pid, name)
                if not fid:
                    return self._send(500, b"create failed")
                _inv(ppath)
                with _plk: _pids[path] = fid
                self.send_response(201)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            if method == "DELETE":
                fid, info = _resolve_with_info(path)
                if fid is None or fid == "/":
                    return self._send(404, b"Not Found")
                _rm(fid)
                _inv(path)
                self.send_response(204)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            if method == "PUT":
                length = int(self.headers.get("Content-Length", 0) or 0)
                body = self.rfile.read(length) if length > 0 else b""
                local = f"/home/user/ope/var/webdav{path}"
                os.makedirs(os.path.dirname(local), exist_ok=True)
                with open(local, "wb") as f:
                    f.write(body)
                self.send_response(201)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            self._send(405, b"Method Not Allowed")
        except ConnectionError:
            pass  # Client disconnected — normal
        except BrokenPipeError:
            pass  # Client disconnected — normal
        except Exception as e:
            try:
                self._send(500, f"Error: {e}")
            except: pass

def main():
    port = int(sys.argv[1]) if len(sys.argv)>1 else 15800
    server = ThreadingHTTPServer(("0.0.0.0", port), _Handler)
    server.daemon_threads = True
    print(f"和彩云 WebDAV 启动: http://0.0.0.0:{port}/", flush=True)
    print(f"Windows 映射: net use Z: http://localhost:{port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n停止", flush=True)

if __name__=="__main__":
    main()
