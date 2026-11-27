# 红（Projekt Red）桌面宠物 v4.6.0

基于 **Python + PySide6 (Qt6)** 构建的轻量级、低内存占用 Windows 桌面宠物（《明日方舟》角色 **红 / Projekt Red**）。采用离线高精 Spine 序列帧预烘焙 + 硬件矩阵零内存分配渲染管线，常驻物理内存约 77 MB，支持原生 32 位 RGBA 抗锯齿透明通道、全套 17 项无缝过渡动作、多显示器独立跨屏支持、极简纯文字菜单及面向 5.X 的可扩展多皮肤 / AI 生图主题皮肤基座。

---

## 核心特性

- **17 套精修 Spine 动作（共 875 帧，30 FPS）**：
  - **基础陪伴**：`idle`（待机呼吸）、`walk`（漫步巡逻，屏幕边缘自动转向）、`sit`（抱尾乖坐）、`sleep`（蜷缩熟睡带呼吸泡）。
  - **真·双轨道骨骼过渡**：`trans_sit`（站姿转坐）、`trans_sleep`（坐姿转睡）、`fall`（半空飘落）、`land`（触地立定屈膝缓冲）。
  - **招牌特质动作**：`cuddle_tail`（抱尾蹭脸）、`sharpen_knife`（磨刀拭刃配刀锋寒芒）、`alert_scout`（警惕耸耳环顾）、`yawn_stretch`（掩嘴伸懒腰含泪珠）、`edge_peek`（屏幕边缘探头张望）、`doze_off`（深夜小鸡啄米打瞌睡后平滑回归坐姿）。
  - **互动反馈与彩蛋**：`drag`（后颈提溜悬空扑腾）、常规点击播放温柔 `headpat`（月牙笑眼 + 双颊红晕）、**2 秒内连续快速点击 >= 5 次**触发 `dizzy`（蚊香眼傲娇防备彩蛋 + 专属气泡）。
- **面向 5.X 的可扩展皮肤架构（Skin Spec v4.6）**：
  - **分级契约与优雅降级**：皮肤仅需提供 Tier-1 最小动作集即可运行，缺失的进阶动作会自动回退，方便自制或 AI 生图皮肤渐进式开发；
  - **AI 皮肤原生态支持**：支持 `source_type`、`theme`、`native_facing`（原生朝左自动镜像）、`6 ~ 60 FPS`、皮肤专属 `context_dialogues`、自定义 `icon.png` 及切肤自动释放纹理缓存；
  - **通用质量门禁**：内置 `tools/validate_skin.py` 一键检查帧尺寸、零裁切、接地线及零头身分离。
- **无缝动作衔接与单实例防双开**：结合 Spine 双轨道混合采样与 120ms 余弦 Crossfade 淡入淡出，并内置 `QSharedMemory` 单实例保护。
- **多显示器独立自适应**：自动感知主/副显示器可用工作区与各自任务栏地平线，支持跨屏拖拽投放与菜单一键切屏。
- **极简深色面板**：右键上下文菜单与系统托盘菜单统一采用纯文字 Fluent Dark 风格（支持鼠标穿透防误触与 0.35x ~ 2.00x 全比例缩放）。

---

## 项目目录结构

```text
projekt-red-desktop-pet/
├── run.py                          # 主启动入口
├── config.json                     # 用户运行时配置（自动持久化）
├── pyproject.toml                  # 项目元数据与依赖定义
├── LICENSE                         # MIT 开源许可证
├── CHANGELOG.md                    # 版本演进记录
├── README.md                       # 项目说明文档
├── 运行.bat                        # Windows 静默启动脚本
├── 运行(调试控制台).bat             # Windows 调试控制台启动脚本
├── src/pet/                        # 核心源码包
│   ├── app.py                      # 应用主控与单实例托盘管理
│   ├── window.py                   # 透明悬浮窗、行为状态机与交互驱动
│   ├── config/                     # 配置读写管理
│   ├── core/                       # 零分配渲染器、物理动力学、状态迁移调度
│   ├── dialogue/                   # 角色台词与半透明气泡组件
│   ├── skin/                       # 皮肤图集加载与帧序列惰性缓存
│   └── ui/                         # 极简纯文字右键/托盘菜单与托盘管理器
├── skins/                          # 生产皮肤资源包
│   ├── README.md                   # Skin Spec v4.6 皮肤开发契约
│   └── spine_red/                  # 默认旗舰皮肤（17 套动作 / 875 帧）
├── tools/                          # 资产加工与质检流水线
│   ├── validate_skin.py            # 通用皮肤包质量门禁命令行工具
│   └── spine_baker/                # WebGL 无头烘焙器与自制扩展部件流水线
├── docs/                           # 规划与设计说明文档
└── tests/                          # 自动化单元测试与解剖学/连续性审计套件
```

---

## 快速开始

### 1. 环境准备

需要 **Python 3.9+**（推荐 3.10+）：

```bash
pip install PySide6 Pillow numpy scipy
```

（可选）如需重新运行 `tools/spine_baker/` 离线烘焙流水线，请额外安装 `PySide6-Addons`（QtWebEngine）。

### 2. 启动桌宠

- **命令行启动**：
  ```bash
  python run.py
  ```
- **Windows 一键启动**：双击根目录下的 `运行.bat`（后台无黑框运行）或 `运行(调试控制台).bat`（查看运行日志）。脚本会自动探测当前激活的 Conda 环境、`./.venv` 虚拟环境或系统 PATH 中的 Python。

---

## 交互指引

| 操作 | 响应效果 |
| :--- | :--- |
| **左键单击** | 温柔摸头反应，触发闭眼笑脸与角色台词 |
| **2 秒内连续快速左键点击 >= 5 次** | 触发「戳晕防备」彩蛋动作与吐槽气泡 |
| **左键按住拖拽** | 后颈提溜悬空，小短腿轻蹬并带钟摆惯性倾角 |
| **半空松开左键** | 物理重力自由落体，触及任务栏顶端时屈膝缓冲站稳 |
| **鼠标右键点击** | 唤出极简菜单（动作点播、皮肤切换、缩放、节律、切屏、鼠标穿透等） |

> 开启「鼠标穿透」后鼠标事件将直达下层窗口，可通过桌面右下角**系统托盘图标右键菜单**随时关闭穿透或退出程序。

---

## 自动化测试

运行仓库内全部单元测试、性能基准与解剖学连续性审计套件，以及皮肤包质量门禁校验：

```bash
python tools/validate_skin.py --all
python tests/test_v4_6_skin_readiness.py
python tests/test_anatomical_and_transition_quality.py
python tests/test_fall_land_continuity.py
python tests/test_phase4_skin_menu.py
```

测试覆盖全量 875 帧零边界裁切、零头身分离像素连通性、`fall -> land -> idle` 连续性、多显示器适配及 1000 帧渲染耗时基准。

---

## 版权与免责声明

- 本项目程序代码以 **MIT License** 开源。
- 角色原型 **红（Projekt Red）** 及相关原始美术/Spine 骨骼素材版权均归属 **鹰角网络（Hypergryph）** 所有。本项目为纯粹的个人技术学习与非商业同人开源作品，禁止将任何角色素材用于商业用途。
