#!/usr/bin/env python3
import json, http.server, urllib.request, sys, os
KEY = os.environ.get("DEEPSEEK_KEY") or open("/root/.cc-switch/key.txt").read().strip()
API = "https://api.deepseek.com/anthropic/v1/messages"
PORT = 15725
class P(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
        body["thinking"] = {"type":"enabled","budget_tokens":16000}
        for msg in body.get("messages", []):
            if msg.get("role")=="assistant" and isinstance(msg.get("content"),list):
                ht = any(c.get("type")=="thinking" for c in msg["content"])
                htu = any(c.get("type")=="tool_use" for c in msg["content"])
                if htu and not ht:
                    msg["content"].insert(0,{"type":"thinking","thinking":" ","signature":" "})
        req = urllib.request.Request(API, data=json.dumps(body).encode(),
            headers={"Content-Type":"application/json","x-api-key":KEY}, method="POST")
        try:
            resp = urllib.request.urlopen(req, timeout=300)
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(resp.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(e.read())
    def log_message(self,*a): pass
http.server.HTTPServer(("127.0.0.1",PORT),P).serve_forever()
