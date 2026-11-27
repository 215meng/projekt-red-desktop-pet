# 桌宠皮肤开发与扩展契约规范（Skin Spec v4.6）

面向 **4.6+ / 5.X 自制与 AI 生图主题皮肤** 的标准目录结构、分级动作契约、元数据扩展字段及自动化质检门禁说明。

---

## 1. 标准目录结构

每个皮肤包独立存放在 `skins/<skin_id>/` 下：

```text
skins/
└── <skin_id>/
    ├── skin.json             # 皮肤元数据配置文件（必须）
    ├── transition_matrix.json# 跨姿态过渡表（可选，也可写在 skin.json 的 transitions 中）
    ├── icon.png              # 自定义系统托盘图标（可选，缺省时回退 idle 首帧）
    └── frames/               # 动作序列帧目录（必须，兼容 actions/）
        ├── idle/
        │   ├── frame_000.png
        │   └── ...
        ├── walk/
        ├── drag/
        ├── fall/
        ├── land/
        └── headpat/
```

---

## 2. 分级动作契约（支持渐进式开发）

运行时 `_decide_behavior()` 会自动探测 `current_skin.has_action(...)` 并优雅降级，因此在 5.X 开发自制 / AI 生图主题皮肤时，可按以下三级逐步完善动作，无需一次性制作全套 17 项即可流畅运行：

| 等级 | 包含动作 Key | 适用阶段 |
| :--- | :--- | :--- |
| **Tier-1（最小可运行，6 项）** | `idle`（强制必选）、`walk`、`drag`、`fall`、`land`、`headpat` | 新主题皮肤快速验证与基础桌面互动 |
| **Tier-2（标准陪伴，4 项）** | `sit`、`sleep`、`trans_sit`、`trans_sleep` | 完整静坐陪伴、深夜小憩与丝滑姿态切换 |
| **Tier-3（进阶特质，7 项）** | `cuddle_tail`、`sharpen_knife`、`alert_scout`、`yawn_stretch`、`edge_peek`、`doze_off`、`dizzy` | 高丰富度招牌动作、边缘彩蛋与狂戳防备彩蛋 |

---

## 3. `skin.json` 元数据契约（v4.6 完整字段）

```json
{
  "name": "ai_winter_red",
  "title": "红 · 冬日咖啡馆（自制主题）",
  "author": "215meng",
  "version": "1.0.0",
  "description": "面向 5.X 的 AI 生图主题皮肤示例",
  "source_type": "ai_sprites",
  "theme": "winter_coffee",
  "native_facing": "right",
  "fps": 12,
  "width": 360,
  "height": 480,
  "anchor_y": 466,
  "ground_line_y": 426,
  "default_scale": 1.0,
  "actions": {
    "idle": {
      "name": "待机呼吸",
      "type": "loop",
      "duration": 2.0,
      "frames_count": 24,
      "fps": 12,
      "loop": true
    }
  },
  "transitions": {
    "idle->sit": "trans_sit",
    "sit->sleep": "trans_sleep",
    "fall->land": "land",
    "drag->fall": "fall"
  },
  "context_dialogues": {
    "headpat": ["手心有点凉……用热可可暖暖？"],
    "dizzy": ["呜，不要一直戳红的头啦。"],
    "drag": ["围巾要被拎散了……"],
    "land": ["稳稳落在桌面上了。"]
  },
  "dialogues": [
    "咖啡的香气……很让人安心。"
  ],
  "generation_meta": {
    "pipeline": "ai_image_to_sprites",
    "notes": "可选：记录生图模型、垫图或后处理备注（请勿写入个人路径或密钥）"
  }
}
```

### AI 生图皮肤专用扩展字段说明

1. **`native_facing`（`"right"` | `"left"`，默认 `"right"`）**：
   - 运行时规定 `facing_left=False` 表示朝右移动。若 AI 生成的序列帧原生人物**朝左**，只需填写 `"native_facing": "left"`，渲染器会自动翻转镜像，彻底避免“倒退太空步”。
2. **`fps`（`6 ~ 60`，默认 `30`）**：
   - AI 序列帧常用 `8 / 12 / 16 / 24 FPS`；可直接在皮肤级或单个 `actions.<key>.fps` 中指定真实帧率。
3. **`ground_line_y`（整数，可选）**：
   - 显式指定脚底接触地面线的参考 Y 像素（不填时质检工具默认读取 `idle[0]` 的底边 Y 像素）。
4. **`context_dialogues`（字典，可选）**：
   - 按 `headpat`、`dizzy`、`drag`、`land` 等语境覆盖默认台词，未配置时自动回退默认台词池。
5. **`source_type` / `theme` / `generation_meta`（可选）**：
   - 便于后续 5.X 皮肤生成工作流与皮肤管理器分类展示。

---

## 4. 画面规范与通用质检门禁

1. **统一尺度与零裁切**：所有动作在同一皮肤内必须保持等大身高比例，且角色像素不可接触画布四边缘 1px 边界。
2. **统一接地线**：除悬空 `drag` 与 `fall` 外，地面动作底边应与基准地面线对齐。
3. **运行自动化质检**：

```bash
# 校验指定皮肤包
python tools/validate_skin.py spine_red

# 批量校验 skins/ 下全部皮肤
python tools/validate_skin.py --all
```
