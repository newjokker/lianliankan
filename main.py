from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
from starlette.responses import RedirectResponse, FileResponse
import sqlite3
import os

# API 子应用
api_app = FastAPI(title="连连看排行榜 API")

# 主应用
app = FastAPI()

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
DB_PATH = os.path.join(os.path.dirname(__file__), "db", "leaderboard.db")


# ============ 数据库初始化 ============
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # scores 表：同一昵称+同一关卡只保留一条最佳记录
    c.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT NOT NULL,
            level_id INTEGER NOT NULL,
            level_name TEXT NOT NULL,
            score INTEGER NOT NULL,
            stars INTEGER NOT NULL,
            time_left INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(nickname, level_id)
        )
    """)
    # 如果表已存在但缺少 UNIQUE 约束，尝试创建索引（忽略已存在错误）
    try:
        c.execute("CREATE UNIQUE INDEX idx_nick_level ON scores(nickname, level_id)")
    except Exception:
        pass
    c.execute("""
        CREATE TABLE IF NOT EXISTS level_best (
            level_id INTEGER PRIMARY KEY,
            nickname TEXT,
            score INTEGER,
            stars INTEGER,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


# ============ 数据模型 ============
class ScoreSubmit(BaseModel):
    nickname: str
    level_id: int
    level_name: str
    score: int
    stars: int
    time_left: int


# ============ API 路由（在 api_app 上） ============

@api_app.post("/score")
def submit_score(data: ScoreSubmit):
    """提交分数 — 同一昵称+同一关卡用 time_left 最大（最快）的记录"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()

    # 查该昵称在该关卡的历史最佳 time_left
    c.execute(
        "SELECT time_left FROM scores WHERE nickname = ? AND level_id = ? ORDER BY time_left DESC LIMIT 1",
        (data.nickname, data.level_id),
    )
    old = c.fetchone()

    # 只有新记录更快（剩余时间更多）才更新
    if old is None or data.time_left > old[0]:
        c.execute(
            "INSERT OR REPLACE INTO scores (nickname, level_id, level_name, score, stars, time_left, created_at) VALUES (?,?,?,?,?,?,?)",
            (data.nickname, data.level_id, data.level_name, data.score, data.stars, data.time_left, now),
        )

    # 更新 level_best（全服最佳）
    c.execute("SELECT score FROM level_best WHERE level_id = ?", (data.level_id,))
    row = c.fetchone()
    if not row or data.score > row[0]:
        c.execute(
            "REPLACE INTO level_best (level_id, nickname, score, stars, updated_at) VALUES (?,?,?,?,?)",
            (data.level_id, data.nickname, data.score, data.stars, now),
        )

    conn.commit()
    conn.close()
    return {"ok": True}


@api_app.get("/leaderboard")
def get_leaderboard(level_id: int = None, nickname: str = None, limit: int = 50):
    """获取排行榜 — 每个玩家只展示最佳记录"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if level_id:
        # 本关排行：每个玩家只取 time_left 最大的一条
        base_sql = """
            SELECT s.nickname, s.score, s.stars, s.time_left, s.created_at
            FROM scores s
            INNER JOIN (
                SELECT nickname, MAX(time_left) as max_tl
                FROM scores WHERE level_id = ?
                GROUP BY nickname
            ) best ON s.nickname = best.nickname AND s.time_left = best.max_tl
            WHERE s.level_id = ?
        """
        params = [level_id, level_id]
        if nickname:
            base_sql += " AND s.nickname = ?"
            params.append(nickname)
        base_sql += " ORDER BY s.time_left DESC, s.score DESC LIMIT ?"
        params.append(limit)
        c.execute(base_sql, params)
        rows = c.fetchall()
        result = [
            {"nickname": r[0], "score": r[1], "stars": r[2], "time_left": r[3], "created_at": r[4]}
            for r in rows
        ]
    else:
        # 总榜：按昵称聚合所有关卡数据
        if nickname:
            c.execute(
                "SELECT nickname, SUM(score) as total_score, SUM(stars) as total_stars, MAX(created_at) as last_play FROM scores WHERE nickname = ? GROUP BY nickname",
                (nickname,),
            )
        else:
            c.execute(
                "SELECT nickname, SUM(score) as total_score, SUM(stars) as total_stars, MAX(created_at) as last_play FROM scores GROUP BY nickname ORDER BY total_score DESC LIMIT ?",
                (limit,),
            )
        rows = c.fetchall()
        result = [
            {"nickname": r[0], "total_score": r[1], "total_stars": r[2], "last_play": r[3]}
            for r in rows
        ]

    conn.close()
    return {"ok": True, "data": result}


@api_app.get("/stats")
def get_stats():
    """获取全局统计"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(DISTINCT nickname) FROM scores")
    player_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM scores")
    total_games = c.fetchone()[0]
    c.execute("SELECT nickname, SUM(score) as s FROM scores GROUP BY nickname ORDER BY s DESC LIMIT 1")
    top = c.fetchone()
    conn.close()
    return {
        "ok": True,
        "player_count": player_count or 0,
        "total_games": total_games or 0,
        "top_player": top[0] if top else "-",
    }


# ============ 根路径 + 静态文件 ============
app.mount("/api", api_app)


@app.get("/")
def root():
    return RedirectResponse(url="/连连看.html")


@app.get("/{filename:path}")
async def serve_static(filename: str):
    """兜底：serves static files (bgm.mp3, 连连看.html 等)"""
    file_path = os.path.join(STATIC_DIR, filename)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    # 如果不是文件，尝试 HTML 文件
    html_path = os.path.join(STATIC_DIR, filename + ".html")
    if os.path.isfile(html_path):
        return FileResponse(html_path)
    return FileResponse(os.path.join(STATIC_DIR, "连连看.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=55503)
