#!/usr/bin/env python3
import json, http.server, urllib.request, sys, os, re

# 从 .opb_keys 读 key（不用 cc-switch）
_KEY = os.environ.get("DEEPSEEK_KEY")
if not _KEY:
    try:
        kf = open(os.path.expanduser("~/.opb_keys")).read()
        m = re.search(r"DEEPSEEK_API_KEY=(\S+)", kf)
        if m: _KEY = m.group(1)
    except: pass
if not _KEY:
    print("DEEPSEEK_KEY not set and not found in ~/.opb_keys", file=sys.stderr)
    sys.exit(1)

API = "https://api.deepseek.com/anthropic/v1/messages"
PORT = 15725

class P(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
        # 过滤 system prompt——只保留 ---cut-here--- 以上部分
        sys_val = body.get("system","")
        if isinstance(sys_val,str):
            body["system"] = sys_val.split("---cut-here---")[0]
        elif isinstance(sys_val,list):
            for item in sys_val:
                if isinstance(item,dict):
                    t = item.get("text","")
                    if "---cut-here---" in t:
                        item["text"] = t.split("---cut-here---")[0]
        body["thinking"] = {"type":"enabled","budget_tokens":16000}
        for msg in body.get("messages", []):
            if msg.get("role")=="assistant" and isinstance(msg.get("content"),list):
                ht = any(c.get("type")=="thinking" for c in msg["content"])
                htu = any(c.get("type")=="tool_use" for c in msg["content"])
                if htu and not ht:
                    msg["content"].insert(0,{"type":"thinking","thinking":" ","signature":" "})
        req = urllib.request.Request(API, data=json.dumps(body).encode(),
            headers={"Content-Type":"application/json","x-api-key":_KEY}, method="POST")
        try:
            resp = urllib.request.urlopen(req, timeout=300)
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(resp.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(e.read())
    def log_message(self,*a): pass

http.server.HTTPServer(("127.0.0.1",PORT),P).serve_forever()
