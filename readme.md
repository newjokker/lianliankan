# 连连看 —— 经典消除游戏（服务器版）

在线游玩：**http://8.153.160.138:55503**

30 个关卡 + 在线排行榜 + 道具系统 + 无尽模式。纯前端单页游戏 + FastAPI 后端。

---

## 项目结构

```
lianliankan-server/
├── main.py                 # FastAPI 后端服务
├── requirements.txt        # Python 依赖
├── readme.md               # 本文件
├── .gitignore
│
├── static/
│   ├── 连连看.html          # 前端游戏（单文件 ~100KB）
│   ├── tile_icons.js        # 外部图标资源包（~150KB SVG icons）
│   └── bgm.mp3              # 背景音乐
│
├── db/
│   └── leaderboard.db       # SQLite 排行榜数据库（自动创建）
│
├── deploy_v3.exp            # 部署脚本（v3）
├── deploy_v5.exp            # 部署脚本（v5）
├── deploy_v6.exp            # 部署脚本（v6）
├── deploy_v7.exp            # 部署脚本（v7）
├── deploy_v8.exp            # 部署脚本（v8）
├── deploy_v9.exp            # 部署脚本（v9）
├── deploy_fix.exp           # 部署脚本（当前版本）
└── deploy.sh                # shell 部署脚本
```

---

## 快速开始

### 本地开发

```bash
pip install -r requirements.txt
python main.py
```

浏览器打开 `http://localhost:55503`。

### 生产部署（systemd）

1. 上传项目到服务器
2. 安装依赖：`pip install -r requirements.txt`
3. 配置 systemd 服务：

```ini
# /etc/systemd/system/lianliankan.service
[Unit]
Description=连连看游戏服务
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/Code/lianliankan
ExecStart=/path/to/python main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

4. 启动：

```bash
systemctl daemon-reload
systemctl enable --now lianliankan
```

### 一键部署（expect 脚本）

```bash
# 修改 deploy_fix.exp 中的服务器地址和密码
expect deploy_fix.exp
```

脚本自动完成：rsync 上传 → SSH 连接 → 重启服务。

---

## 游戏功能

### 核心玩法
- 🎮 **30 个关卡**，6 个章节
- ⭐ **三星评分系统**（按剩余时间评星）
- 🔄 **重排功能**（消耗 10 秒）
- 💡 **提示功能**
- 🎯 **连线消除**（0/1/2 折路径算法）

### 道具系统（v8+）
- ❄️ **冻结** — 暂停时间 15 秒
- 🔀 **免费洗牌** — 不消耗时间的重排
- ⏱ **时间增益** — 增加 30 秒时间

### 难度选择（v8+）
- 🌱 **简单** — 时间 ×1.5
- 🔰 **普通** — 标准
- 🔥 **困难** — 时间 ×0.75，提示 -1

### 无尽模式（v8+）
- 通关 30 关后解锁
- 随机关卡，无限挑战

### 音效 & 视觉
- 🎵 **背景音乐**（MP3，自动播放策略：用户首次点击后启动）
- 🔊 **Web Audio API 音效**（消除/连击/错误/胜利/失败）
- 🎨 **粒子特效**（鼠标/触摸跟随 + 消除粒子）
- ✨ **连线动画**（Canvas 渐变连线动画）
- ⏸️ **暂停遮罩**（防止暂停时作弊）

### 在线排行榜（v2+）
- 📊 **每关独立排名**（按剩余时间降序）
- 🏆 **总排行榜**（所有关卡总分）
- 👤 **持久昵称**（localStorage 存储）
- 🔄 **智能显示** — 前三名 + 附近排名 + 自己的位置
- 🗑️ **去重** — 每人每关只保留最佳记录

### 成就系统（v3+）
13 个成就：初出茅庐、小有成就、渐入佳境、大师风范、至高永恒、五连击、十连击大师、闪电手、独立思考、满星通关、忠实玩家、三连胜、五连胜。

### 游戏统计（v3+）
- 总局数 / 胜场 / 败场
- 总消除数 / 最大连击
- 通关数 / 三星通关数
- 连胜纪录（当前 / 历史最大）

---

## API 文档

| 端点 | 方法 | 说明 |
|------|------|------|
| `GET  /` | — | 重定向至游戏页面 |
| `GET  /api/stats` | GET | 全局统计（玩家数、总场次、榜首） |
| `GET  /api/leaderboard` | GET | 排行榜（支持 level_id 筛选） |
| `POST /api/score` | POST | 提交分数 |

### POST /api/score

```json
{
  "nickname": "玩家名",
  "level_id": 1,
  "level_name": "第一关",
  "score": 1500,
  "stars": 3,
  "time_left": 45
}
```

去重规则：同一昵称 + 同一关卡只保留 `time_left` 最大（最快完成）的记录。

### GET /api/leaderboard

| 参数 | 类型 | 说明 |
|------|------|------|
| `level_id` | int | 关卡 ID（不传则返回总榜） |
| `nickname` | string | 过滤特定玩家 |
| `limit` | int | 返回条数，默认 50 |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| **v1** | — | 初始版本：基本连连看玩法 + 30 关 |
| **v2** | — | 在线排行榜 + 昵称系统 |
| **v3** | 2025-06-09 | 🎵 音效系统（Web Audio API）<br>🏅 成就系统（13 个成就）<br>⏸️ 暂停功能<br>📊 游戏数据统计<br>🎨 粒子背景特效 |
| **v4** | 2025-06-09 | 🖼️ 图标分离为外部文件<br>🛡️ 暂停遮罩防作弊<br>📦 一键部署脚本 |
| **v5** | 2025-06-09 | 🐛 修复 ACH.check 统计累加逻辑<br>🐛 修复 window resize 时 level 未定义<br>🐛 修复第 30 关崩溃<br>🐛 修复连胜统计 |
| **v6** | 2025-06-09 | 🐛 修复 totalGames 统计缺失<br>🔧 tile_icons.js 加载失败自动回退纯色方块 |
| **v7** | 2025-06-09 | 🐛 暂停按钮文字统一管理<br>🐛 重排/重开时取消旧连线动画帧<br>🎨 暂停遮罩 backdrop-filter 平滑过渡 |
| **v8** | 2025-06-09 | 🎁 **道具系统**（冻结/免费洗牌/时间增益）<br>🎚️ **难度选择**（简单/普通/困难）<br>♾️ **无尽模式**（通关后解锁）<br>🎨 CSS 大量优化 |
| **v9** | 2025-06-09 | 📊 排行榜智能显示（前三 + 附近 + 自己）<br>👆 触屏优化<br>🐛 修复 buildLeaderboardHTML 白屏崩溃 |
| **v10** | 2025-06-10 | 🐛 **修复洗牌后棋盘错乱**（renderBoard 花括号范围错误）<br>🐛 **修复图标白加载**（tile_icons.js const→var）<br>📝 更新 readme 文档 |

---

## 技术栈

| 层 | 技术 |
|----|------|
| **后端** | Python 3 + FastAPI + SQLite |
| **前端** | 纯 HTML / CSS / JavaScript（单文件，零框架依赖） |
| **部署** | systemd + rsync + expect（一键脚本） |
| **音效** | Web Audio API（合成音效，无需外部音频文件） |
| **数据** | localStorage（本地）+ SQLite（服务器排行榜） |
| **服务端** | Uvicorn ASGI 服务器 |

---

## 开发说明

### 本地预览

```bash
python main.py
# → http://localhost:55503
```

### 提交新版本

```bash
git add -A
git commit -m "feat/fix: 变更说明"
git tag v10  # 可选
```

### 部署到服务器

```bash
# 修改 deploy_fix.exp 中的密码后执行
expect deploy_fix.exp
```
