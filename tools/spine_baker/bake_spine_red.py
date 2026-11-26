# -*- coding: utf-8 -*-
"""
bake_spine_red.py - 明日方舟红 Spine 骨骼动作自动化离线烘焙引擎 (v4.5 精细重塑版)
  - 画布规格：360x480，统一缩放 scale=0.85，统一接地底线 Bottom Y=425px
  - 导出格式：32位标准 RGBA 完全透明通道 PNG 序列帧，全边界零裁切
  - 动作时长契约：全套 17 项动作，每一项均严格 >= 1.0 秒
  - 包含真·双轨道骨骼+视口 Crossfade 过渡切片 (trans_sit, trans_sleep)
"""

import sys
import os
import json
import base64
import threading
import http.server
import socketserver
from typing import Dict, List, Any

from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings

FPS = 30
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../skins/spine_red"))
BAKER_DIR = os.path.dirname(os.path.abspath(__file__))

# 17 套全动作技术规格清单 (全部统一 scale=0.85，接地线齐平 B=425px)
ACTION_SPECS: List[Dict[str, Any]] = [
    {
        "id": "idle",
        "name": "待机长呼吸",
        "model": "build",
        "type": "loop",
        "source_anim": "Relax",
        "duration": 2.00,
        "offsetX": 0,
        "offsetY": 0,
        "scale": 0.85,
        "desc": "单周期 2.0s 超平滑起承转合深呼吸与尾巴波浪摇摆"
    },
    {
        "id": "walk",
        "name": "欢快漫步",
        "model": "build",
        "type": "loop",
        "source_anim": "Move",
        "duration": 1.8667,
        "offsetX": 0,
        "offsetY": 4,
        "scale": 0.85,
        "desc": "完整单步态周期欢快迈步，红风衣微扬"
    },
    {
        "id": "drag",
        "name": "提溜悬空扑腾",
        "model": "build",
        "type": "loop",
        "source_anim": "Relax",
        "custom_pose": "drag_neck",
        "duration": 1.00,
        "offsetX": 0,
        "offsetY": 60,
        "scale": 0.85,
        "desc": "后颈提起悬空，双耳与4节尾巴自然重垂，双手出兜垂放，小短腿半空轻蹬"
    },
    {
        "id": "sit",
        "name": "抱尾乖坐",
        "model": "build",
        "type": "loop",
        "source_anim": "Sit",
        "duration": 2.667,
        "offsetX": 0,
        "offsetY": 98,
        "scale": 0.85,
        "desc": "统一 0.85 全尺寸稳稳坐于桌面地面线，双手插兜微晃尾巴乖巧陪伴"
    },
    {
        "id": "sleep",
        "name": "蜷缩熟睡",
        "model": "build",
        "type": "loop",
        "source_anim": "Sleep",
        "custom_pose": "sleep_bubble",
        "duration": 2.00,
        "offsetX": 28,
        "offsetY": 18,
        "scale": 0.85,
        "desc": "统一 0.85 全尺寸贴地安睡，附带随呼吸缩放的高光睡眠小气泡"
    },
    {
        "id": "headpat",
        "name": "摸头反应",
        "model": "build",
        "type": "once",
        "source_anim": "Relax",
        "custom_pose": "headpat",
        "duration": 1.50,
        "offsetX": 0,
        "offsetY": 0,
        "scale": 0.85,
        "desc": "被温柔摸头时闭上幸福月牙笑眼、泛起双颊红晕、轻轻迎合摇尾"
    },
    {
        "id": "dizzy",
        "name": "戳晕防备",
        "model": "build",
        "type": "once",
        "source_anim": "Interact",
        "custom_pose": "dizzy",
        "duration": 1.00,
        "offsetX": 0,
        "offsetY": 0,
        "scale": 0.85,
        "desc": "短时间内被连续快速狂戳脑袋时，露出蚊香晕眩眼后退防备的傲娇彩蛋"
    },
    {
        "id": "trans_sit",
        "name": "站姿转坐过渡",
        "model": "build",
        "type": "transition",
        "from_anim": "Relax",
        "to_anim": "Sit",
        "custom_pose": "trans_sit",
        "mix_duration": 1.00,
        "duration": 1.00,
        "offsetX": 0,
        "offsetY": 0,
        "scale": 0.85,
        "desc": "站立姿态真·双轨道融合屈膝下坐至地面过渡切片"
    },
    {
        "id": "trans_sleep",
        "name": "坐姿转睡过渡",
        "model": "build",
        "type": "transition",
        "from_anim": "Sit",
        "to_anim": "Sleep",
        "custom_pose": "trans_sleep",
        "mix_duration": 1.00,
        "duration": 1.00,
        "offsetX": 0,
        "offsetY": 98,
        "scale": 0.85,
        "desc": "坐姿真·双轨道平滑蜷身俯卧入睡过渡切片"
    },
    {
        "id": "fall",
        "name": "半空飘落",
        "model": "build",
        "type": "loop",
        "source_anim": "Relax",
        "custom_pose": "pure_fall",
        "duration": 1.00,
        "offsetX": 0,
        "offsetY": 0,
        "scale": 0.85,
        "desc": "半空自由落体，双手出兜微张平衡，风衣飘带与尾巴受风上扬"
    },
    {
        "id": "land",
        "name": "触地缓冲",
        "model": "build",
        "type": "once",
        "source_anim": "Relax",
        "custom_pose": "pure_land",
        "duration": 1.00,
        "offsetX": 0,
        "offsetY": 0,
        "scale": 0.85,
        "desc": "完美承接飘落瞬间屈膝受力缓冲，双臂平顺收回口袋，零跳变站稳"
    },
    {
        "id": "cuddle_tail",
        "name": "抱尾蹭脸",
        "model": "build",
        "type": "loop",
        "source_anim": "Sit",
        "custom_pose": "cuddle_tail",
        "duration": 2.667,
        "offsetX": 0,
        "offsetY": 98,
        "scale": 0.85,
        "desc": "坐姿双手环抱前置蓬松大狼尾，双颊红晕闭眼轻蹭绒毛"
    },
    {
        "id": "sharpen_knife",
        "name": "磨刀拭刃",
        "model": "build",
        "type": "loop",
        "source_anim": "Relax",
        "custom_pose": "sharpen_knife",
        "duration": 2.00,
        "offsetX": 0,
        "offsetY": 0,
        "scale": 0.85,
        "desc": "左手胸前横持便携短匕首，右手持战术磨刀石贴刃往复打磨并绽放寒芒"
    },
    {
        "id": "alert_scout",
        "name": "警惕耸耳",
        "model": "build",
        "type": "once",
        "source_anim": "Relax",
        "custom_pose": "alert_scout",
        "duration": 1.80,
        "offsetX": 0,
        "offsetY": 0,
        "scale": 0.85,
        "desc": "屈膝下伏、左手轻护腰后刀柄，狼耳直竖平滑环顾侦察动静"
    },
    {
        "id": "yawn_stretch",
        "name": "伸懒腰打哈欠",
        "model": "build",
        "type": "once",
        "source_anim": "Relax",
        "custom_pose": "yawn_stretch",
        "duration": 2.00,
        "offsetX": 0,
        "offsetY": 0,
        "scale": 0.85,
        "desc": "右手出兜轻掩嘴边打哈欠，左臂斜伸舒展，闭眼含晶莹泪珠并翘尾抖耳"
    },
    {
        "id": "edge_peek",
        "name": "边缘探头张望",
        "model": "build",
        "type": "once",
        "source_anim": "Relax",
        "custom_pose": "edge_peek",
        "duration": 2.00,
        "offsetX": 0,
        "offsetY": 0,
        "scale": 0.85,
        "desc": "双手出兜并行扒住屏幕边界，脊柱自然前倾探头，瞪大黄瞳好奇张望"
    },
    {
        "id": "doze_off",
        "name": "深夜打瞌睡",
        "model": "build",
        "type": "once",
        "source_anim": "Sit",
        "custom_pose": "doze_off",
        "duration": 2.667,
        "offsetX": 0,
        "offsetY": 98,
        "scale": 0.85,
        "desc": "坐姿安详闭眼吹起睡眠泡，两次小鸡啄米打盹后猛地惊醒抖耳守候"
    }
]

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-background-timer-throttling --disable-renderer-backgrounding --no-sandbox"

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BAKER_DIR, **kwargs)
    def log_message(self, format, *args):
        pass

httpd = socketserver.TCPServer(("127.0.0.1", 0), QuietHandler)
PORT = httpd.server_address[1]
server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
server_thread.start()
print(f"HTTP Server started at http://127.0.0.1:{PORT}")

class SpineBakerApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.view = QWebEngineView()
        self.view.resize(520, 680)
        self.view.setWindowTitle("Spine Red Automated Baker Engine v4.5")
        self.view.show()

        settings = self.view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)

        self.current_action_idx = 0
        self.current_frame_idx = 0
        self.total_frames_for_action = 0
        self.dt = 1.0 / FPS

        target_action = None
        for i, arg in enumerate(sys.argv[1:]):
            if arg.startswith("--action="):
                target_action = arg.split("=")[1]
            elif arg == "--action" and i + 1 < len(sys.argv[1:]):
                target_action = sys.argv[1:][i + 1]
        if target_action:
            self.action_specs = [s for s in ACTION_SPECS if s["id"] == target_action]
            print(f"Target action specified: {target_action} ({len(self.action_specs)} found)")
        else:
            self.action_specs = ACTION_SPECS

        self.skin_manifest: Dict[str, Any] = {
            "name": "spine_red",
            "title": "明日方舟·红 (Spine 工业级骨骼版)",
            "author": "Antigravity Pipeline",
            "version": "4.5.0",
            "description": "明日方舟红 4.5 精修版：自制补全道具/表情/怀抱大尾部件，17 套自然流畅 Spine 动作与统一接地过渡。",
            "fps": FPS,
            "width": 360,
            "height": 480,
            "anchor_y": 466,
            "default_scale": 1.0,
            "actions": {},
            "transitions": {
                "idle->sit": "trans_sit",
                "sit->sleep": "trans_sleep",
                "Relax->Sit": "trans_sit",
                "Sit->Sleep": "trans_sleep",
                "fall->land": "land",
                "drag->fall": "fall"
            },
            "dialogues": [
                "红的尾巴……给博士摸摸。",
                "尾巴……毛茸茸的大尾巴，红也想摸……",
                "红会一直在这里，守着博士。",
                "狼的气味……红抓到你了。",
                "红很听话的，不会咬人。",
                "呼呼……大尾巴很暖和。",
                "红在看着你呢，博士。",
                "红的小刀很锋利，不会弄伤博士的。",
                "博士……累了吗？红给你捏捏肩？",
                "下雪了……红的围巾分你一半。",
                "耳朵抖了抖……博士刚才在叫红吗？",
                "博士还不睡吗……红在这里守着你。",
                "哈啊……红不困，红要保护博士。",
                "夜深了……给博士倒一杯温水。",
                "红的耳朵动了动……外面只有风声，很安全。"
            ]
        }

        self.view.loadFinished.connect(self.on_load_finished)
        self.view.load(QUrl(f"http://127.0.0.1:{PORT}/baker.html"))

    def run(self):
        return self.app.exec()

    def on_load_finished(self, ok):
        if not ok:
            print("Failed to load baker.html!")
            self.app.quit()
            return
        QTimer.singleShot(600, self.wait_for_ready)

    def wait_for_ready(self):
        def check_cb(is_ready):
            if is_ready:
                print("Baker Engine initialized successfully! Starting batch export...")
                self.start_next_action()
            else:
                QTimer.singleShot(300, self.wait_for_ready)
        self.view.page().runJavaScript("window.bakerApi && window.bakerApi.isReady();", check_cb)

    def start_next_action(self):
        if self.current_action_idx >= len(self.action_specs):
            self.finish_all()
            return

        spec = self.action_specs[self.current_action_idx]
        action_id = spec["id"]
        model = spec["model"]
        duration = spec["duration"]
        self.total_frames_for_action = int(round(duration * FPS))
        self.current_frame_idx = 0

        target_action_dir = os.path.join(OUTPUT_DIR, "frames", action_id)
        os.makedirs(target_action_dir, exist_ok=True)
        import glob
        for old_f in glob.glob(os.path.join(target_action_dir, "*.png")):
            try:
                os.remove(old_f)
            except Exception:
                pass

        print(f"\n=======================================================")
        print(f"[{self.current_action_idx + 1}/{len(self.action_specs)}] 烘焙动作: {action_id} ({spec['name']})")
        print(f"  时长: {duration:.3f}s | 总帧数: {self.total_frames_for_action} 帧 ({FPS} FPS) | 模式: {spec['type']}")
        print(f"=======================================================")

        def apply_params_and_bake():
            c_pose = spec.get('custom_pose', '')
            set_js = f"window.bakerApi.setRenderParams({spec['offsetX']}, {spec['offsetY']}, {spec['scale']}); window.bakerApi.setCustomPoseType('{c_pose}');"
            self.view.page().runJavaScript(set_js, lambda _: QTimer.singleShot(50, self.bake_next_frame))

        def check_model_cb(current_model):
            if current_model == model:
                apply_params_and_bake()
            else:
                print(f"  切换骨骼模型至: {model} ...")
                def init_cb(res):
                    apply_params_and_bake()
                self.view.page().runJavaScript(f"window.bakerApi.init('{model}', '{spec.get('source_anim', 'Relax')}');", init_cb)

        self.view.page().runJavaScript("window.bakerApi.getModelType();", check_model_cb)

    def bake_next_frame(self):
        spec = self.action_specs[self.current_action_idx]
        action_id = spec["id"]

        if self.current_frame_idx >= self.total_frames_for_action:
            self.skin_manifest["actions"][action_id] = {
                "name": spec["name"],
                "type": spec["type"],
                "duration": spec["duration"],
                "frames_count": self.total_frames_for_action,
                "fps": FPS,
                "loop": (spec["type"] == "loop"),
                "desc": spec["desc"]
            }
            if spec["type"] == "transition":
                trans_key = f"{spec['from_anim']}->{spec['to_anim']}"
                self.skin_manifest["transitions"][trans_key] = action_id

            self.current_action_idx += 1
            QTimer.singleShot(50, self.start_next_action)
            return

        # 对 transition 和带自定义包络的 once 动作采用闭区间 [0, dur] 采样，确保首尾帧 100% 精准闭合终点！
        if spec["type"] == "transition":
            time_sec = spec["mix_duration"] * self.current_frame_idx / max(1, self.total_frames_for_action - 1)
        elif spec["type"] == "once" and spec.get("custom_pose"):
            time_sec = spec["duration"] * self.current_frame_idx / max(1, self.total_frames_for_action - 1)
        else:
            time_sec = spec.get("start_time", 0.0) + self.current_frame_idx * self.dt

        frame_file = f"frame_{self.current_frame_idx:03d}.png"
        out_path = os.path.join(OUTPUT_DIR, "frames", action_id, frame_file)

        def on_seek_done(ok):
            def on_capture(data_url):
                if data_url and data_url.startswith("data:image/png;base64,"):
                    b64 = data_url.split(",", 1)[1]
                    raw_bytes = base64.b64decode(b64)
                    with open(out_path, "wb") as f:
                        f.write(raw_bytes)

                    from PIL import Image
                    import numpy as np
                    with Image.open(out_path) as im:
                        arr = np.array(im.convert("RGBA"))
                        arr[0, :, 3] = 0
                        arr[-1, :, 3] = 0
                        arr[:, 0, 3] = 0
                        arr[:, -1, 3] = 0
                        arr[1, :, 3] = (arr[1, :, 3].astype(float) * 0.5).astype(np.uint8)
                        arr[-2, :, 3] = (arr[-2, :, 3].astype(float) * 0.5).astype(np.uint8)
                        arr[:, 1, 3] = (arr[:, 1, 3].astype(float) * 0.5).astype(np.uint8)
                        arr[:, -2, 3] = (arr[:, -2, 3].astype(float) * 0.5).astype(np.uint8)
                        Image.fromarray(arr).save(out_path)

                    progress = (self.current_frame_idx + 1) / self.total_frames_for_action * 100
                    if (self.current_frame_idx + 1) % 15 == 0 or (self.current_frame_idx + 1) == self.total_frames_for_action:
                        print(f"  Frame {self.current_frame_idx + 1:03d}/{self.total_frames_for_action:03d} ({progress:.1f}%) -> {frame_file}")

                    self.current_frame_idx += 1
                    QTimer.singleShot(10, self.bake_next_frame)
                else:
                    print(f"Error capturing frame {self.current_frame_idx}!")
                    self.current_frame_idx += 1
                    QTimer.singleShot(10, self.bake_next_frame)

            self.view.page().runJavaScript("window.bakerApi.captureDataUrl();", on_capture)

        if spec["type"] == "transition":
            js_code = f"window.bakerApi.seekTransitionFrame('{spec['from_anim']}', '{spec['to_anim']}', {time_sec:.4f}, {spec['mix_duration']});"
        else:
            is_loop = 'true' if spec['type'] == 'loop' else 'false'
            js_code = f"window.bakerApi.seekFrame('{spec['source_anim']}', {time_sec:.4f}, {is_loop});"

        self.view.page().runJavaScript(js_code, on_seek_done)

    def finish_all(self):
        print(f"\n🎉 本次动作序列烘焙完成！正在输出皮肤元数据清单...")
        manifest_path = os.path.join(OUTPUT_DIR, "skin.json")
        # 仅当单动作 --action 烘焙时才读取合并，全量烘焙时以最新 ACTION_SPECS 为准彻底刷新
        if len(self.action_specs) < len(ACTION_SPECS) and os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                if "actions" in existing:
                    existing["actions"].update(self.skin_manifest.get("actions", {}))
                    self.skin_manifest = existing
            except Exception as e:
                print(f"Warning merging existing skin.json: {e}")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.skin_manifest, f, ensure_ascii=False, indent=2)
        print(f"已生成配置文件: {manifest_path}")

        matrix_path = os.path.join(OUTPUT_DIR, "transition_matrix.json")
        trans_matrix = {
            "default_mix_duration": 0.25,
            "transitions": {
                "idle->sit": "trans_sit",
                "sit->sleep": "trans_sleep",
                "fall->land": "land",
                "drag->fall": "fall"
            }
        }
        with open(matrix_path, "w", encoding="utf-8") as f:
            json.dump(trans_matrix, f, ensure_ascii=False, indent=2)
        print(f"已生成状态迁移表: {matrix_path}")

        print("\n✅ Spine 4.5 精修版骨骼平滑烘焙套件全部执行完毕！")
        self.app.quit()

if __name__ == "__main__":
    baker = SpineBakerApp()
    sys.exit(baker.run())
