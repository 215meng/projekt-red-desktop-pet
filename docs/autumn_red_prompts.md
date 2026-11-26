# 红崽（Projekt Red）第二版：秋雨小红帽动态桌宠【全套全动作逐帧生图手册】

本手册专为**红崽动态桌宠全面升级（v2.2）**量身定制。为了彻底解决上一版中“动作僵硬、眨眼歪斜、走路反向太空步、尾巴死板硬摆”的问题，本手册将所有动作拆解为符合经典 2D 动画标准的逐帧画面。

---

## 📌 一致性控制与生图核心铁律（必读）

1. **背景必须 100% 纯白**：
   - 提示词中已强制内置 `isolated on pure flat solid white background, no background, zero shadow`。
   - **绝对不要出现地面阴影、雨丝、水洼或背景杂物**，以确保本地程序能够 0 瑕疵自动抠图提取透明通道。
2. **构图必须全身留白（Full Body）**：
   - 画面四周必须留出至少 10% 的空白，确保**狼耳尖、伞尖、尾巴尖和鞋底**没有被图片画框切断。
3. **人物朝向统一规范**：
   - **所有走动动作统一设定为面朝左侧（Side view, facing left）**。向左走直接渲染，向右走由桌宠程序自动水平镜像，杜绝朝向错乱。
4. **垫图一致性（推荐）**：
   - **Midjourney**：以上一版生成的 `idle.png` 为垫图，末尾添加 `--cref [原图链接] --cw 100 --niji 6 --ar 1:1`。
   - **Stable Diffusion / WebUI**：
     - 对于眨眼（`idle_blink`），强烈推荐使用 **Inpaint（局部重绘）**，底图直接放 `idle.png`，仅涂抹眼部，Denoise=0.35~0.42，保证身体与雨伞 100% 像素级不动。

---

## 🎨 全套生图提示词清单（一次性全部包含，绝无遗漏）

### 【第一组：待机与自然律动序列（Idle & Breathing）】
> **动画逻辑**：3 帧闭环播放（`待机立正` $\rightarrow$ `尾巴微扬呼吸` $\rightarrow$ `自然眨眼微笑`），形成有生命体温的自然律动。

#### 1.1 `idle_stand.png`（基准待机正立站姿 - 琥珀金大眼睛平视）
- **姿态说明**：双脚并拢自然站立，面朝正前方，单手握黄色长柄小雨伞立于身侧，蓬松大狼尾巴自然垂在身后，琥珀金眼睛呆萌平视前方。
- **Prompt (直接复制)**：
```text
masterpiece, best quality, chibi 2-head-tall anime wolf girl, Projekt Red from Arknights, standing quietly facing forward, relaxed frontal idle pose, eyes wide open, amber golden eyes, innocent blank stare, holding a pale yellow umbrella with curved wooden handle on side, fluffy silver-gray pointed wolf ears with white inner fluff, huge bushy wolf tail resting behind, short messy silver-gray hair, wearing oversized brick-red duffle coat with white shearling fur collar, dark charcoal ribbed knitted turtleneck sweater, dark pleated skirt, black tights, glossy dark red ankle boots with buckles, small brown leather crossbody satchel, cute anime dorm chibi sticker, full body, isolated on pure flat solid white background, clean crisp lineart, no background, zero shadow --ar 1:1 --niji 6
```

#### 1.2 `idle_blink.png`（正立闭眼面容 - 彻底解决眨眼歪斜）
- **姿态说明**：【关键帧】与 1.1 完全相同的正立站姿，面部完全水平，双眼温柔地眯成闭眼月牙笑，神情恬静治愈。
- **Prompt (直接复制)**：
```text
masterpiece, best quality, chibi 2-head-tall anime wolf girl, Projekt Red from Arknights, standing quietly facing forward, relaxed frontal idle pose, eyes gently closed, sweet peaceful closed eyes smile, perfectly horizontal facial angle, holding a pale yellow umbrella with curved wooden handle, fluffy silver-gray wolf ears, huge bushy wolf tail resting behind, short messy silver-gray hair, wearing oversized brick-red duffle coat with white shearling fur collar, dark charcoal turtleneck sweater, dark pleated skirt, black tights, glossy red boots, small brown leather crossbody satchel, full body, isolated on pure flat solid white background, clean lineart, no background, zero shadow --ar 1:1 --niji 6
```
*(注：若使用 SD Inpaint，底图上传 `idle_stand.png`，仅涂抹眼眶，提示词输入：`closed eyes, sweet peaceful smile, gentle dark eyelashes, flat horizontal facial angle`)*

#### 1.3 `idle_sway.png`（待机呼吸与大尾巴轻扬帧）
- **姿态说明**：与 1.1 站姿一致，胸腔微挺（呼吸微起伏），蓬松的大狼尾巴向侧上方轻柔翘起微晃，狼耳尖轻微向外抖动。
- **Prompt (直接复制)**：
```text
masterpiece, best quality, chibi 2-head-tall anime wolf girl, Projekt Red from Arknights, standing facing forward, gentle breathing posture, chest slightly lifted, huge bushy fluffy wolf tail swaying gently upward to the side, wolf ear tips twitching slightly, amber golden eyes looking at viewer, holding pale yellow umbrella, wearing oversized brick-red duffle coat with white fur collar, dark turtleneck sweater, dark pleated skirt, red boots, lively cute anime sticker, full body, isolated on pure flat solid white background, clean crisp outlines, no background, zero shadow --ar 1:1 --niji 6
```

---

### 【第二组：漫步巡逻动作（Walk Cycle - 4 帧经典步态）】
> **动画逻辑**：经典 2D 行走循环标准（`左迈步` $\rightarrow$ `提腿通过` $\rightarrow$ `右迈步` $\rightarrow$ `提腿通过`），彻底消灭太空步、溜冰与两帧抽搐。
> **朝向统一**：全部面朝左侧。

#### 2.1 `walk_01_contact_L.png`（迈左脚着地 - 跨步接触位）
- **姿态说明**：侧面朝左，左腿向前迈出着地，右腿向后蹬出，黄色小伞握在手中微微前倾，砖红风衣衣摆与大狼尾巴随步伐后扬。
- **Prompt (直接复制)**：
```text
masterpiece, best quality, chibi 2-head-tall anime wolf girl, Projekt Red from Arknights, side view facing left, walking stride contact pose, left foot stepping forward touching ground, right leg extended backward, energetic cute walking pose, holding pale yellow umbrella tilted slightly forward, brick-red duffle coat hem and huge fluffy wolf tail fluttering backward from motion, amber golden eyes looking ahead, glossy red boots, brown crossbody satchel, clean anime walking sprite, full body, isolated on pure flat solid white background, clean lineart, no background, zero shadow --ar 1:1 --niji 6
```

#### 2.2 `walk_02_pass_R.png`（右脚屈膝向前通过 - 单腿支撑位）
- **姿态说明**：侧面朝左，左腿垂直支撑身体，右腿弯膝抬起准备向前跨出，双脚在中间靠拢，身体重心微升，尾巴微收。
- **Prompt (直接复制)**：
```text
masterpiece, best quality, chibi 2-head-tall anime wolf girl, Projekt Red from Arknights, side view facing left, walking passing pose, left leg supporting body straight, right knee bent lifting off ground stepping forward, feet passing close together, body slightly higher, holding pale yellow umbrella, brick-red coat, huge fluffy wolf tail swaying gently, focused cute walking expression, red boots, brown satchel, clean 2D animation keyframe, full body, isolated on pure flat solid white background, sharp crisp edges, no background, zero shadow --ar 1:1 --niji 6
```

#### 2.3 `walk_03_contact_R.png`（迈右脚着地 - 对侧跨步接触位）
- **姿态说明**：侧面朝左，右腿向前大步迈出着地，左腿向后蹬，身体前倾，黄色小伞稳定撑着，尾巴后扬。
- **Prompt (直接复制)**：
```text
masterpiece, best quality, chibi 2-head-tall anime wolf girl, Projekt Red from Arknights, side view facing left, walking stride contact pose, right foot stepping forward touching ground, left leg extended backward, confident cute steps, holding pale yellow umbrella, brick-red coat hem and huge fluffy wolf tail fluttering backward, amber eyes looking forward, red boots, brown satchel bag, clean walking animation sprite, full body, isolated on pure flat solid white background, clean outlines, no background, zero shadow --ar 1:1 --niji 6
```

#### 2.4 `walk_04_pass_L.png`（左脚屈膝向前通过 - 对侧单腿支撑位）
- **姿态说明**：侧面朝左，右腿垂直支撑地面，左腿弯膝抬起向前通过，双脚交错，重心过渡。
- **Prompt (直接复制)**：
```text
masterpiece, best quality, chibi 2-head-tall anime wolf girl, Projekt Red from Arknights, side view facing left, walking passing pose, right leg supporting body, left knee bent lifting foot forward, feet passing close in mid-stride, holding pale yellow umbrella, brick-red coat, bushy wolf tail swaying behind, red boots, brown satchel, full body, isolated on pure flat solid white background, clean outlines, no background, zero shadow --ar 1:1 --niji 6
```

---

### 【第三组：被提溜拖拽动作（Drag - 悬空乱蹬）】
#### 3.1 `drag_dangle.png`（被鼠标提溜后衣领 - 悬空无助蹬腿）
- **姿态说明**：整个人像小猫后颈皮一样被鼠标提在半空，两只穿红靴子的小短腿缩起乱蹬，双手紧抓黄色小伞和挎包，大圆眼睛呆滞懵圈，尾巴垂下。
- **Prompt (直接复制)**：
```text
masterpiece, best quality, chibi 2-head-tall anime wolf girl, Projekt Red from Arknights, dangling suspended in mid-air, picked up by back of hooded coat collar, dangling short legs curled up in air, clutching pale yellow umbrella tightly with both hands, surprised blank expression, wide amber golden eyes, innocent helpless expression, pointed wolf ears drooping slightly, huge fluffy wolf tail hanging straight down, wearing brick-red hooded duffle coat, glossy red boots, full body chibi character sprite, isolated on pure flat solid white background, sharp vector-like edges, no background, zero shadow --ar 1:1 --niji 6
```

---

### 【第四组：下落伞降动作（Fall - 撑伞滑翔垂直坠落）】
#### 4.1 `fall_glide.png`（小伞化作降落伞 - 迎风飘飞）
- **姿态说明**：半空中自然下落，黄色小雨伞在头顶化作降落伞，大风衣下摆和银灰长发迎风向上翻卷，两脚自然下垂，好奇又刺激地往下看。
- **Prompt (直接复制)**：
```text
masterpiece, best quality, chibi 2-head-tall anime wolf girl, Projekt Red from Arknights, falling from the sky, mid-air glide drop pose, pale yellow umbrella opened like a parachute overhead, upward air wind blowing brick-red coat hem and silver hair upward, cute curious expression looking downward, wolf ears flattened slightly, huge bushy wolf tail fluttering upward with the wind, red boots dangling, full body chibi sprite, isolated on pure flat solid white background, clean lineart, no background, zero shadow --ar 1:1 --niji 6
```

---

### 【第五组：摸头互动/欢呼动作（Click - 抓秋枫叶跳跃）】
#### 5.1 `click_happy.png`（开心小跳步 - 眯眼笑抓红叶）
- **姿态说明**：鼠标点击红崽触发。红崽开心地眯起月牙笑眼，两颊微红，小巧的双脚轻快跳起离地，一只小手高高伸出抓住一片飘落的橙红色秋枫叶，尾巴兴奋高翘。
- **Prompt (直接复制)**：
```text
masterpiece, best quality, chibi 2-head-tall anime wolf girl, Projekt Red from Arknights, happy joyful hopping pose, feet slightly off ground, closed crescent smiling eyes, soft rosy blush on cheeks, reaching one tiny hand upward catching a floating red autumn maple leaf, holding pale yellow umbrella in the other hand, pointed wolf ears twitching happily, huge fluffy wolf tail wagging high with joy, wearing brick-red duffle coat, adorable warm moment, chibi sticker, full body, isolated on pure flat solid white background, clean crisp lineart, no background, zero shadow --ar 1:1 --niji 6
```

---

### 【第六组：桌面陪伴拓展动作（Sit & Sleep - 治愈高频常驻动作）】
#### 6.1 `sit_idle.png`（乖巧坐在屏幕底部 - 静静陪伴）
- **姿态说明**：红崽乖巧地坐在任务栏或屏幕边缘，两只小红靴子并拢伸向前方，黄色小雨伞斜收在身旁，毛茸茸的大狼尾巴盘在身侧，静静看着屏幕前的你。
- **Prompt (直接复制)**：
```text
masterpiece, best quality, chibi 2-head-tall anime wolf girl, Projekt Red from Arknights, sitting quietly on the ground floor facing viewer, legs neatly tucked forward, closed yellow umbrella resting beside her on the ground, huge bushy fluffy wolf tail curled cozy around her side, amber golden eyes looking gently at viewer, wearing oversized brick-red coat, dark turtleneck sweater, cozy companion dorm chibi, full body, isolated on pure flat solid white background, clean outlines, no background, zero shadow --ar 1:1 --niji 6
```

#### 6.2 `sleep_curled.png`（玩累了抱尾巴沉睡 - 甜美打盹）
- **姿态说明**：长时间无操作时进入梦乡。红崽像小狼崽一样蜷缩成一小团，闭着眼睛安稳沉睡，把蓬松的大狼尾巴紧紧抱在怀里当被子，头枕着尾巴，神情甜美安详。
- **Prompt (直接复制)**：
```text
masterpiece, best quality, chibi 2-head-tall anime wolf girl, Projekt Red from Arknights, sleeping peacefully curled up into a soft ball on the ground, hugging her huge fluffy wolf tail like a plush blanket, sweet sleeping face, eyes peacefully closed, closed yellow umbrella lying next to her, wearing brick-red duffle coat, cozy wolf ears resting softly, warm tranquil atmosphere, chibi dorm sleeping sprite, full body, isolated on pure flat solid white background, clean lineart, no background, zero shadow --ar 1:1 --niji 6
```

---

## 📋 生图交付建议与文件命名对应表

您生成完毕后，请直接将高清图片重命名并保存至：`raw_assets/autumn_red/`

| 动作阶段 | 建议保存文件名 | 重要程度 |
| :--- | :--- | :---: |
| **待机基准** | `idle.png`（或使用您已有的那张） | ⭐⭐⭐⭐⭐ |
| **自然眨眼** | `idle_blink.png`（用 Inpaint 或提示词） | ⭐⭐⭐⭐⭐ |
| **待机晃尾** | `idle_sway.png` | ⭐⭐⭐⭐ |
| **走动步态 1** | `walk1.png`（迈左脚） | ⭐⭐⭐⭐⭐ |
| **走动步态 2** | `walk_pass1.png`（提右腿过渡） | ⭐⭐⭐⭐⭐ |
| **走动步态 3** | `walk2.png`（迈右脚） | ⭐⭐⭐⭐⭐ |
| **走动步态 4** | `walk_pass2.png`（提左腿过渡） | ⭐⭐⭐⭐⭐ |
| **被提溜** | `drag.png`（或使用您已有的那张） | ⭐⭐⭐⭐ |
| **下落** | `fall.png`（或使用您已有的那张） | ⭐⭐⭐⭐ |
| **摸头抓叶** | `click.png`（或使用您已有的那张） | ⭐⭐⭐⭐ |
| **坐下陪伴** | `sit.png`（拓展彩蛋） | ⭐⭐⭐ |
| **抱尾打盹** | `sleep.png`（拓展彩蛋） | ⭐⭐⭐ |

您准备好后直接放进文件夹并告诉我，我将为您一键启动全自动化透明抠图与图集构建流水线！
