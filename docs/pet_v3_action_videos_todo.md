# 桌宠 3.0 动作流体化升级：视频素材生成与过渡补完代办清单 (Action Videos Backlog)

> **目标与使命**：为彻底消灭桌面宠物在状态切换时的“动作阻塞感”（如从站立到坐下的瞬间突变、触地时的硬切），借助当下先进的 **AI 图生视频（Image-to-Video，如 Kling 可灵、Runway Gen-3、CogVideoX、海螺 MiniMax 等）**，为关键过渡姿态生成 1~2 秒、30~60 FPS 的无缝流体动作视频片段，后续可一键解构为透明微动帧序列载入桌宠系统。

---

## 📋 待生成动作视频清单 (Missing Action Videos Backlog)

### 1. 【高优先级】站立待机 $\to$ 就地坐下平滑过渡视频 (`trans_idle_to_sit.mp4`)
- **当前痛点**：红崽从漫步巡逻结束站立转为坐下陪伴时，直接硬切成坐姿，存在视线瞬移跳跃感。
- **视频期望效果**：
  - 时长：`1.2 ~ 1.5 秒`（建议 30 FPS）。
  - 起始帧：`body_idle` + `legs_stand`（站立立正持伞）。
  - 结束帧：`legs_sit_floor` + `tail_curl_cushion`（小靴子并拢平坐、大尾巴环抱身前）。
  - 动作描述：红崽单手收拢小伞，膝盖微微弯曲下蹲，身体重心下移平稳坐在地上，身后的大尾巴如流水般缓缓绕到身前抱住，面部保持呆萌温和。
- **图生视频 Prompt (可直接用于可灵/Runway)**：
  ```text
  chibi anime wolf girl wearing brick-red duffle coat gently bending knees and smoothly sitting down on the ground, wrapping her huge fluffy wolf tail around her front like a cozy cushion, resting folded umbrella on side, peaceful smooth transition, cute 2D animation, white background
  ```

---

### 2. 【高优先级】坐姿陪伴 $\to$ 抱尾入睡过渡视频 (`trans_sit_to_sleep.mp4`)
- **当前痛点**：静坐进入睡眠时眼睛和头部的瞬间切换缺乏困意渐浓的安睡过程。
- **视频期望效果**：
  - 时长：`1.0 ~ 1.2 秒`（建议 30 FPS）。
  - 起始帧：坐姿平视。
  - 结束帧：`head_sleeping` + `tail_curl_cushion`。
  - 动作描述：红崽打了个微小的哈欠，小脑袋轻轻向下一点，顺势埋进身前松软温暖的大狼尾巴中，双眼缓缓闭合变成甜美的熟睡月牙笑，耳朵轻轻耷拉放松，呼吸转为深沉。
- **图生视频 Prompt**：
  ```text
  chibi anime wolf girl sitting peacefully, head slowly nodding down into her huge fluffy wolf tail cushion, amber eyes gently closing into a sweet sleeping smile, ears relaxing, peaceful transition into deep cozy sleep, 2D anime animation, white background
  ```

---

### 3. 【中优先级】伞降下落 $\to$ 触地收伞站立缓冲视频 (`trans_fall_to_land.mp4`)
- **当前痛点**：半空下落触达任务栏时，伞面瞬间消失变回站姿。
- **视频期望效果**：
  - 时长：`1.0 ~ 1.3 秒`（建议 30 FPS）。
  - 起始帧：`umbrella_parachute` + `coat_updraft`（头顶降落伞张开，衣摆迎风翻卷）。
  - 结束帧：`body_idle`（稳稳站立持伞）。
  - 动作描述：红色小靴子触地瞬间身体微微受力下蹲（Q 弹缓冲），头顶充当降落伞的黄色小伞优雅收拢并垂直落在身侧，风衣下摆随重力自然垂落摆平，红崽眨了眨眼站稳。
- **图生视频 Prompt**：
  ```text
  chibi anime wolf girl floating down with an open yellow umbrella parachute, boots softly touching the ground with a gentle bounce squash cushion, smoothly closing the umbrella and standing upright, coat settling down, fluid 2D animation, white background
  ```

---

### 4. 【中优先级】提溜悬空扑腾乱蹬流体循环视频 (`action_drag_flail_loop.mp4`)
- **当前痛点**：目前提溜采用程序化悬垂摆动，若有真实手绘级物理扑腾循环将达到顶尖二次元水准。
- **视频期望效果**：
  - 时长：`1.5 ~ 2.0 秒`（无缝首尾循环 Seamless Loop）。
  - 起始/结束：被抓起后颈皮悬在半空。
  - 动作描述：像被拎住后颈皮的小奶狼，两只穿红靴子的小短腿在半空中无助慌乱地连续交替乱蹬、蜷缩挣扎，两只狼耳可怜巴巴地下垂微晃，大眼睛无辜震惊。
- **图生视频 Prompt**：
  ```text
  chibi anime wolf girl picked up in mid-air by the back of her coat collar, dangling helplessly with cute short legs flailing and kicking in continuous seamless loop, drooping wolf ears wobbling, wide shocked innocent eyes, smooth 2D anime animation, white background
  ```

---

### 5. 【低优先级·趣味互动】摸头欢呼跳跃抓落叶视频 (`action_click_hop_leaf.mp4`)
- **当前痛点**：点击互动摸头时，若能有一段连贯的眯眼跳起抓秋枫叶微电影动作，陪伴感将拉满。
- **视频期望效果**：
  - 时长：`1.5 秒`。
  - 动作描述：被鼠标摸头后头顶冒出两颊红晕，红崽开心地眯眼笑，两脚轻快跃起，一只小手向前伸出抓取一片旋转飘落的红枫叶捧在胸前，尾巴兴奋高高摇动，随后轻盈落回地面。
- **图生视频 Prompt**：
  ```text
  chibi anime wolf girl receiving headpat, blushing with joy, happy hop into the air catching a floating red autumn maple leaf with tiny hand, wagging bushy wolf tail excitedly, landing with a joyful smile, clean 2D anime animation, white background
  ```

---

## 🛠️ 视频素材接入桌宠的技术流水线 (Pipeline)

未来当你生成了上述 `.mp4` 或 `.mov` 视频素材后：
1. **自动提取透明通道帧**：
   通过 `ffmpeg -i input.mp4 -vf "colorkey=0xFFFFFF:0.1:0.1" frame_%03d.png` 或本地 Alpha 去背脚本，一键提取为 30 FPS 透明 PNG 序列。
2. **零代码挂载状态机**：
   在 `skin.json` 中声明过渡动作（例如 `"trans_idle_to_sit": {"fps": 30, "loop": false, "next": "sit"}`），主程序即可在状态切换时自动无缝插播过渡，彻底终结一切动作阻塞感！
