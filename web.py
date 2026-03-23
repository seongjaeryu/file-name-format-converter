"""
파일명 포맷 컨버터 - 웹 버전
로컬 Flask 서버로 브라우저에서 파일을 선택하고 로컬 파일명을 직접 변환합니다.
"""

import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote
import webbrowser
import threading

from converter import convert_file, convert_filename

PORT = 8765
HTML_PAGE = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>파일명 포맷 컨버터 (Mac → Windows)</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: #f5f5f7;
            color: #1d1d1f;
            min-height: 100vh;
            padding: 40px 20px;
        }
        .container { max-width: 800px; margin: 0 auto; }
        h1 {
            font-size: 28px;
            text-align: center;
            margin-bottom: 8px;
        }
        .subtitle {
            text-align: center;
            color: #86868b;
            margin-bottom: 32px;
            font-size: 15px;
        }
        .drop-zone {
            background: white;
            border: 2px dashed #d2d2d7;
            border-radius: 16px;
            padding: 48px 24px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
            margin-bottom: 24px;
        }
        .drop-zone:hover, .drop-zone.drag-over {
            border-color: #0071e3;
            background: #f0f7ff;
        }
        .drop-zone p { color: #86868b; font-size: 16px; line-height: 1.6; }
        .drop-zone .icon { font-size: 48px; margin-bottom: 12px; }
        .path-input {
            display: flex;
            gap: 8px;
            margin-bottom: 24px;
        }
        .path-input input {
            flex: 1;
            padding: 12px 16px;
            border: 1px solid #d2d2d7;
            border-radius: 10px;
            font-size: 14px;
            outline: none;
        }
        .path-input input:focus { border-color: #0071e3; }
        button {
            padding: 12px 24px;
            border: none;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary {
            background: #0071e3;
            color: white;
        }
        .btn-primary:hover { background: #0077ed; }
        .btn-primary:disabled {
            background: #d2d2d7;
            cursor: not-allowed;
        }
        .btn-secondary {
            background: #e8e8ed;
            color: #1d1d1f;
        }
        .btn-secondary:hover { background: #d2d2d7; }
        .btn-add { white-space: nowrap; }
        .file-list {
            background: white;
            border-radius: 16px;
            overflow: hidden;
            margin-bottom: 24px;
        }
        .file-list-header {
            display: grid;
            grid-template-columns: 1fr 1fr 120px;
            padding: 12px 20px;
            background: #f5f5f7;
            font-weight: 600;
            font-size: 13px;
            color: #86868b;
        }
        .file-item {
            display: grid;
            grid-template-columns: 1fr 1fr 120px;
            padding: 14px 20px;
            border-top: 1px solid #f0f0f0;
            font-size: 14px;
            align-items: center;
        }
        .file-item .name {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .file-item .converted { color: #0071e3; }
        .file-item .no-change { color: #86868b; }
        .status-done { color: #34c759; font-weight: 500; }
        .status-needed { color: #ff9500; font-weight: 500; }
        .status-error { color: #ff3b30; font-weight: 500; }
        .status-same { color: #86868b; }
        .actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .file-count { color: #86868b; font-size: 14px; }
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #86868b;
        }
        .info-box {
            background: #fff3cd;
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 24px;
            font-size: 13px;
            color: #856404;
            line-height: 1.5;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>파일명 포맷 컨버터</h1>
        <p class="subtitle">macOS 파일명(NFD)을 Windows 호환 포맷(NFC)으로 변환합니다</p>

        <div class="info-box">
            이 앱은 로컬 서버로 동작하며, 파일을 직접 변환합니다 (재다운로드 아님).
            파일 경로를 입력하거나 폴더 경로를 입력해주세요.
        </div>

        <div class="path-input">
            <input type="text" id="pathInput"
                   placeholder="파일 또는 폴더 경로를 입력하세요 (예: /Users/me/Documents/파일.pdf)">
            <button class="btn-secondary btn-add" onclick="addPath()">추가</button>
            <button class="btn-secondary btn-add" onclick="addFolder()">폴더 스캔</button>
        </div>

        <div class="file-list" id="fileList">
            <div class="file-list-header">
                <div>원래 파일명</div>
                <div>변환 후 파일명</div>
                <div>상태</div>
            </div>
            <div id="fileItems">
                <div class="empty-state">파일 경로를 입력하고 추가 버튼을 눌러주세요</div>
            </div>
        </div>

        <div class="actions">
            <span class="file-count" id="fileCount"></span>
            <div style="display: flex; gap: 8px;">
                <button class="btn-secondary" onclick="clearAll()">목록 초기화</button>
                <button class="btn-primary" id="convertBtn" onclick="convertAll()" disabled>
                    변환 실행
                </button>
            </div>
        </div>
    </div>

    <script>
        let files = [];

        const pathInput = document.getElementById('pathInput');
        pathInput.addEventListener('keydown', e => {
            if (e.key === 'Enter') addPath();
        });

        async function addPath() {
            const path = pathInput.value.trim();
            if (!path) return;

            const res = await fetch('/api/preview', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({paths: [path]})
            });
            const data = await res.json();

            if (data.error) {
                alert(data.error);
                return;
            }

            data.files.forEach(f => {
                if (!files.some(existing => existing.path === f.path)) {
                    files.push(f);
                }
            });

            pathInput.value = '';
            renderFiles();
        }

        async function addFolder() {
            const path = pathInput.value.trim();
            if (!path) return;

            const res = await fetch('/api/scan-folder', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({folder: path})
            });
            const data = await res.json();

            if (data.error) {
                alert(data.error);
                return;
            }

            data.files.forEach(f => {
                if (!files.some(existing => existing.path === f.path)) {
                    files.push(f);
                }
            });

            pathInput.value = '';
            renderFiles();
        }

        function renderFiles() {
            const container = document.getElementById('fileItems');
            const countEl = document.getElementById('fileCount');
            const convertBtn = document.getElementById('convertBtn');

            if (files.length === 0) {
                container.innerHTML = '<div class="empty-state">파일 경로를 입력하고 추가 버튼을 눌러주세요</div>';
                countEl.textContent = '';
                convertBtn.disabled = true;
                return;
            }

            container.innerHTML = files.map((f, i) => {
                const changed = f.original !== f.converted;
                const statusClass = f.status === 'done' ? 'status-done'
                    : f.status === 'error' ? 'status-error'
                    : changed ? 'status-needed' : 'status-same';
                const statusText = f.status === 'done' ? '변환 완료 ✓'
                    : f.status === 'error' ? '오류'
                    : changed ? '변환 필요' : '변환 불필요';

                return '<div class="file-item">' +
                    '<div class="name" title="' + escapeHtml(f.original) + '">' + escapeHtml(f.original) + '</div>' +
                    '<div class="name ' + (changed ? 'converted' : 'no-change') + '" title="' + escapeHtml(f.converted) + '">' + escapeHtml(f.converted) + '</div>' +
                    '<div class="' + statusClass + '">' + statusText + '</div>' +
                    '</div>';
            }).join('');

            countEl.textContent = '총 ' + files.length + '개 파일';
            convertBtn.disabled = false;
        }

        async function convertAll() {
            const paths = files.filter(f => f.original !== f.converted && f.status !== 'done')
                               .map(f => f.path);

            if (paths.length === 0) {
                alert('변환이 필요한 파일이 없습니다.');
                return;
            }

            const res = await fetch('/api/convert', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({paths: paths})
            });
            const data = await res.json();

            data.results.forEach(r => {
                const idx = files.findIndex(f => f.path === r.path);
                if (idx !== -1) {
                    files[idx].status = r.success ? 'done' : 'error';
                    if (r.success) {
                        files[idx].converted = r.new_name;
                        files[idx].path = r.new_path;
                    }
                }
            });

            renderFiles();

            const ok = data.results.filter(r => r.success).length;
            const fail = data.results.filter(r => !r.success).length;
            let msg = ok + '개 파일 변환 완료';
            if (fail > 0) msg += ', ' + fail + '개 오류';
            alert(msg);
        }

        function clearAll() {
            files = [];
            renderFiles();
        }

        function escapeHtml(str) {
            const div = document.createElement('div');
            div.textContent = str;
            return div.innerHTML;
        }
    </script>
</body>
</html>"""


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        data = json.loads(body)

        if self.path == "/api/preview":
            result = self.handle_preview(data)
        elif self.path == "/api/scan-folder":
            result = self.handle_scan_folder(data)
        elif self.path == "/api/convert":
            result = self.handle_convert(data)
        else:
            result = {"error": "Unknown endpoint"}

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))

    def handle_preview(self, data):
        paths = data.get("paths", [])
        files = []
        for path in paths:
            path = os.path.expanduser(path)
            if not os.path.isfile(path):
                return {"error": f"파일을 찾을 수 없습니다: {path}"}
            name = os.path.basename(path)
            converted = convert_filename(name)
            files.append({
                "path": path,
                "original": name,
                "converted": converted,
                "status": "pending",
            })
        return {"files": files}

    def handle_scan_folder(self, data):
        folder = os.path.expanduser(data.get("folder", ""))
        if not os.path.isdir(folder):
            return {"error": f"폴더를 찾을 수 없습니다: {folder}"}

        files = []
        for entry in sorted(os.listdir(folder)):
            full = os.path.join(folder, entry)
            if os.path.isfile(full):
                converted = convert_filename(entry)
                files.append({
                    "path": full,
                    "original": entry,
                    "converted": converted,
                    "status": "pending",
                })
        return {"files": files}

    def handle_convert(self, data):
        paths = data.get("paths", [])
        results = []
        for path in paths:
            try:
                old_name, new_name, changed = convert_file(path)
                new_path = os.path.join(os.path.dirname(path), new_name)
                results.append({
                    "path": path,
                    "new_name": new_name,
                    "new_path": new_path,
                    "success": True,
                    "changed": changed,
                })
            except Exception as e:
                results.append({
                    "path": path,
                    "success": False,
                    "error": str(e),
                })
        return {"results": results}

    def log_message(self, format, *args):
        pass  # 로그 출력 억제


def main():
    server = HTTPServer(("127.0.0.1", PORT), RequestHandler)
    print(f"파일명 포맷 컨버터 웹 서버 시작: http://127.0.0.1:{PORT}")
    print("종료하려면 Ctrl+C를 누르세요")

    # 브라우저 자동 열기
    threading.Timer(0.5, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}")).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n서버 종료")
        server.server_close()


if __name__ == "__main__":
    main()
