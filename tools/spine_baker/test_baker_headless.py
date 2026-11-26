import sys
import os
import base64
import threading
import http.server
import socketserver
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-background-timer-throttling --disable-renderer-backgrounding --no-sandbox"

PORT = 19877
BAKER_DIR = os.path.dirname(os.path.abspath(__file__))

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BAKER_DIR, **kwargs)
    def log_message(self, format, *args):
        pass

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), QuietHandler) as httpd:
        httpd.serve_forever()

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
print(f"HTTP Server started at http://127.0.0.1:{PORT}")

class CustomWebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        print(f"[JS {level.name}] line {lineNumber}: {message}")

app = QApplication(sys.argv)
view = QWebEngineView()
page = CustomWebEnginePage()
view.setPage(page)
view.resize(520, 680)
view.setWindowTitle("Spine Baker Test")
view.show()

settings = view.settings()
settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)

step_timer = QTimer()
wait_count = 0

def check_ready():
    global wait_count
    wait_count += 1
    if wait_count > 30:
        print("Timeout waiting for bakerApi.isReady()!")
        view.page().runJavaScript("window.bakerApi && window.bakerApi.getLogs();", lambda l: print("DOM Logs:\n", l))
        app.quit()
        return

    def on_ready_check(res):
        if res is True:
            step_timer.stop()
            print("Baker API is READY! Running frame seek and capture...")
            run_capture_test()

    view.page().runJavaScript("window.bakerApi && window.bakerApi.isReady();", on_ready_check)

def run_capture_test():
    def on_seek(ok):
        print("seekFrame Relax @ 0.5s ->", ok)
        def on_captured(data_url):
            if data_url and data_url.startswith("data:image/png;base64,"):
                b64 = data_url.split(",", 1)[1]
                raw_bytes = base64.b64decode(b64)
                out_path = os.path.join(BAKER_DIR, "preview_test.png")
                with open(out_path, "wb") as f:
                    f.write(raw_bytes)
                print(f"🎉 SUCCESS! Exported frame ({len(raw_bytes)} bytes) to {out_path}")
            else:
                print("FAILED: Invalid data url:", data_url[:100] if data_url else None)
            app.quit()

        view.page().runJavaScript("window.bakerApi.captureDataUrl();", on_captured)

    view.page().runJavaScript("window.bakerApi.seekFrame('Relax', 0.5);", on_seek)

def on_load_finished(ok):
    print("Page load finished:", ok)
    if not ok:
        print("Failed to load page!")
        app.quit()
        return
    step_timer.timeout.connect(check_ready)
    step_timer.start(250)

view.loadFinished.connect(on_load_finished)
view.load(QUrl(f"http://127.0.0.1:{PORT}/baker.html"))

sys.exit(app.exec())
