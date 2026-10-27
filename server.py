import http.server
import socketserver
import urllib.request
import urllib.parse
import urllib.error
import json
import webbrowser
import os
import sys
import threading
import time
import subprocess
import re

PORT = 5050
DEFAULT_JETSON_HOST = "192.168.151.108:11434"
DEFAULT_DESKTOP_DIR = os.path.join(os.path.expanduser('~'), 'Desktop')
PILOT_REPO = r"C:\Users\topseven\.codex\worktrees\299f\Pilot-Futures"
STUDIO_REPO = r"C:\Users\topseven\Desktop\JetsonWebChat"
PILOT_GRAPH_PATH = r"C:\Users\topseven\Desktop\Pilot_Graft_Graph\index.html"

class GeneralPurposeAgentHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Jetson-Host')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == '/graph' or self.path == '/graph/':
            viz_path = os.path.join(STUDIO_REPO, 'viz_export', 'index.html')
            if os.path.exists(viz_path):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                with open(viz_path, 'rb') as f:
                    self.wfile.write(f.read())
                return

        if self.path == '/pilot-graph' or self.path == '/pilot-graph/':
            if os.path.exists(PILOT_GRAPH_PATH):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                with open(PILOT_GRAPH_PATH, 'rb') as f:
                    self.wfile.write(f.read())
                return

        if self.path.startswith('/api/repos'):
            repos = [
                {
                    "id": "desktop",
                    "name": "Windows Desktop (General Purpose)",
                    "path": DEFAULT_DESKTOP_DIR,
                    "type": "workspace"
                },
                {
                    "id": "pilot",
                    "name": "Pilot-Futures (WTG Inspection)",
                    "path": PILOT_REPO,
                    "nodes": 11346,
                    "edges": 33287,
                    "graph_url": "/pilot-graph",
                    "type": "graft_repo"
                },
                {
                    "id": "studio",
                    "name": "Jetson AI Studio",
                    "path": STUDIO_REPO,
                    "nodes": 4,
                    "edges": 4,
                    "graph_url": "/graph",
                    "type": "graft_repo"
                }
            ]
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"repos": repos, "active": "desktop"}).encode('utf-8'))
            return

        if self.path.startswith('/api/check_status'):
            host = self.headers.get('X-Jetson-Host', DEFAULT_JETSON_HOST)
            status_data = {"online": False, "models": [], "host": host}
            try:
                url = f"http://{host}/api/tags"
                req = urllib.request.Request(url, headers={'User-Agent': 'JetsonWebChat'})
                with urllib.request.urlopen(req, timeout=2.0) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode('utf-8'))
                        status_data["online"] = True
                        status_data["models"] = data.get("models", [])
            except Exception as e:
                status_data["error"] = str(e)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status_data).encode('utf-8'))
            return
        
        return super().do_GET()

    def do_POST(self):
        # 1. TOOL: Execute Shell/PowerShell/CMD Command
        if self.path.startswith('/api/tools/execute'):
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length).decode('utf-8'))
            cmd = body.get('command', '')
            timeout = float(body.get('timeout', 35.0))
            cwd = body.get('cwd', None)
            
            if not cwd:
                if any(k in cmd for k in ['Pilot', 'app/', 'UploadTask', 'graft', 'gradle', 'Wtg2']):
                    cwd = PILOT_REPO
                else:
                    cwd = DEFAULT_DESKTOP_DIR
            
            try:
                proc = subprocess.Popen(
                    cmd,
                    shell=True,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                try:
                    stdout, stderr = proc.communicate(timeout=timeout)
                    out = (stdout or '') + (stderr or '')
                    if not out.strip():
                        out = f"(Process finished successfully with exit code {proc.returncode})"
                    status = 200
                except subprocess.TimeoutExpired:
                    out = f"✓ Process running in background / GUI active on desktop (PID: {proc.pid})."
                    status = 200
            except Exception as e:
                out = f"Execution error: {e}"
                status = 500
            
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"output": out, "cwd": cwd}).encode('utf-8'))
            return

        # 2. TOOL: Write File
        if self.path.startswith('/api/tools/write_file'):
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length).decode('utf-8'))
            file_path = body.get('path', '')
            content = body.get('content', '')
            try:
                if not os.path.isabs(file_path):
                    file_path = os.path.join(DEFAULT_DESKTOP_DIR, file_path)
                os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                res = {"output": f"✓ Successfully wrote {len(content)} characters to {file_path}", "path": file_path, "bytes": len(content)}
                status = 200
            except Exception as e:
                res = {"error": str(e), "output": f"Failed to write file: {e}"}
                status = 500
            
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
            return

        # 3. TOOL: Read File
        if self.path.startswith('/api/tools/read_file'):
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length).decode('utf-8'))
            file_path = body.get('path', '')
            try:
                if not os.path.isabs(file_path):
                    file_path = os.path.join(DEFAULT_DESKTOP_DIR, file_path)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    data = f.read(50000)
                res = {"output": data, "path": file_path, "bytes": len(data)}
                status = 200
            except Exception as e:
                res = {"error": str(e), "output": f"Failed to read file: {e}"}
                status = 500
            
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
            return

        # 4. TOOL: Launch Desktop App
        if self.path.startswith('/api/tools/launch_app'):
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length).decode('utf-8'))
            app = body.get('app', '').strip()
            args = body.get('args', '').strip()
            
            cmd = f'start "" "{app}" {args}'.strip()
            try:
                proc = subprocess.Popen(cmd, shell=True)
                out = f"✓ Launched desktop application '{app}' (PID: {proc.pid})."
                res = {"output": out, "app": app, "status": "ok"}
                status = 200
            except Exception as e:
                res = {"error": str(e), "output": f"Failed to launch {app}: {e}"}
                status = 500

            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
            return

        # 5. TOOL: Open Browser / Web Search
        if self.path.startswith('/api/tools/open_browser'):
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length).decode('utf-8'))
            url = body.get('url', '').strip()
            query = body.get('query', '').strip()

            if not url and query:
                url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
            elif url and not (url.startswith('http://') or url.startswith('https://')):
                if '.' in url and ' ' not in url:
                    url = f"https://{url}"
                else:
                    url = f"https://www.google.com/search?q={urllib.parse.quote_plus(url)}"

            try:
                webbrowser.open(url)
                out = f"✓ Opened URL in default web browser: {url}"
                res = {"output": out, "url": url}
                status = 200
            except Exception as e:
                res = {"error": str(e), "output": f"Failed to open browser: {e}"}
                status = 500

            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
            return

        # 6. TOOL: Fetch URL Content
        if self.path.startswith('/api/tools/fetch_url'):
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length).decode('utf-8'))
            url = body.get('url', '').strip()
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'https://' + url
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                with urllib.request.urlopen(req, timeout=10.0) as resp:
                    raw_data = resp.read().decode('utf-8', errors='ignore')
                    cleaned = re.sub(r'<(script|style)[^>]*>[\s\S]*?</\1>', '', raw_data)
                    text = re.sub(r'<[^>]+>', ' ', cleaned)
                    text = re.sub(r'\s+', ' ', text).strip()
                    preview = text[:4000] if len(text) > 4000 else text
                    out = f"Content from {url}:\n\n{preview}"
                res = {"output": out, "url": url}
                status = 200
            except Exception as e:
                res = {"error": str(e), "output": f"Failed to fetch {url}: {e}"}
                status = 500

            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
            return

        # 7. GRAFT Specialized Endpoints
        if self.path.startswith('/api/graft/ask'):
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length).decode('utf-8'))
            query = body.get('query', '')
            in_path = body.get('in_path', 'app/')
            repo_path = body.get('repo', PILOT_REPO)
            
            cmd = f'graft ask "{query}" --source'
            if in_path:
                cmd += f' --in {in_path}'
            
            try:
                proc = subprocess.run(
                    cmd, shell=True,
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=45.0
                )
                output = proc.stdout if proc.stdout else proc.stderr
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"output": output, "exit_code": proc.returncode}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return

        if self.path.startswith('/api/graft/blast'):
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length).decode('utf-8'))
            base = body.get('base', 'mr-935~2')
            repo_path = body.get('repo', PILOT_REPO)
            
            cmd = f'graft blast --base {base}'
            try:
                proc = subprocess.run(
                    cmd, shell=True,
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=30.0
                )
                output = proc.stdout if proc.stdout else proc.stderr
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"output": output, "exit_code": proc.returncode}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return

        # Proxy to Ollama on Jetson
        if self.path.startswith('/api/chat') or self.path.startswith('/api/generate'):
            host = self.headers.get('X-Jetson-Host', DEFAULT_JETSON_HOST)
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            target_url = f"http://{host}{self.path}"
            try:
                req = urllib.request.Request(
                    target_url,
                    data=body,
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=300.0) as resp:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/x-ndjson')
                    self.end_headers()
                    while True:
                        chunk = resp.read(1024)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        self.wfile.flush()
            except Exception as e:
                self.send_response(502)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Failed to connect to Jetson at {host}: {e}"}).encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()

def open_browser():
    time.sleep(1.0)
    webbrowser.open(f"http://localhost:{PORT}")

if __name__ == '__main__':
    os.chdir(STUDIO_REPO)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("", PORT), GeneralPurposeAgentHandler) as httpd:
        print(f"[*] Jetson Autonomous General Purpose AI Studio running on http://localhost:{PORT}")
        threading.Thread(target=open_browser, daemon=True).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
