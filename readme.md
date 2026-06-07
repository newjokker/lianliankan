# 连连看 - 服务器版

经典连连看消除游戏，支持在线排行榜。

## 项目结构

```
lianliankan-server/
├── main.py             # FastAPI 后端服务
├── requirements.txt    # Python 依赖
├── readme.md           # 本文件
├── .gitignore
├── static/
│   ├── 连连看.html     # 前端游戏（单文件）
│   └── bgm.mp3         # 背景音乐
└── db/
    └── leaderboard.db  # SQLite 数据库（自动创建）
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python main.py
```

服务默认监听 `0.0.0.0:55503`，浏览器访问 `http://localhost:55503` 即可。

### 3. 后台运行（生产环境）

```bash
nohup python main.py > server.log 2>&1 &
```

## 部署到服务器

### 方式一：手动部署

1. 将整个 `lianliankan-server` 目录上传到服务器
2. 在服务器上安装依赖：`pip install -r requirements.txt`
3. 启动服务：`python main.py`
4. 确保防火墙开放 55503 端口

### 方式二：使用 systemd 管理（推荐）

创建 `/etc/systemd/system/lianliankan.service`：

```ini
[Unit]
Description=连连看游戏服务
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/lianliankan-server
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

然后执行：

```bash
systemctl daemon-reload
systemctl enable lianliankan
systemctl start lianliankan
systemctl status lianliankan  # 查看状态
```

## API 文档

### POST /api/score - 提交分数

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

**去重规则**：同一昵称 + 同一关卡只保留 `time_left` 最大（最快完成）的记录。

### GET /api/leaderboard - 获取排行榜

| 参数 | 类型 | 说明 |
|------|------|------|
| `level_id` | int | 关卡 ID，不传则返回总榜 |
| `nickname` | string | 过滤特定玩家 |
| `limit` | int | 返回条数，默认 50 |

### GET /api/stats - 全局统计

返回玩家总数、游戏场次、最高分玩家。

## 游戏功能

- 🎮 30 个关卡，6 个章节
- ⭐ 三星评分系统
- 🔄 重排功能（消耗 10 秒）
- 💡 提示功能
- 🎵 背景音乐
- 🏆 在线排行榜（去重，每关独立排名）
- 👤 持久昵称设置
- 🔒 只有通关的关卡才能查看排行榜
- 🎨 粒子特效 + 连线动画

## 技术栈

- **后端**: Python + FastAPI + SQLite
- **前端**: 纯 HTML/CSS/JS（单文件，无框架依赖）
- **部署**: 单进程，适合中小规模使用
