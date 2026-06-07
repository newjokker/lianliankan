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
    c.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT NOT NULL,
            level_id INTEGER NOT NULL,
            level_name TEXT NOT NULL,
            score INTEGER NOT NULL,
            stars INTEGER NOT NULL,
            time_left INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
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
    """提交分数"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()

    c.execute(
        "INSERT INTO scores (nickname, level_id, level_name, score, stars, time_left, created_at) VALUES (?,?,?,?,?,?,?)",
        (data.nickname, data.level_id, data.level_name, data.score, data.stars, data.time_left, now),
    )
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
def get_leaderboard(level_id: int = None, limit: int = 20):
    """获取排行榜"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if level_id:
        c.execute(
            "SELECT nickname, score, stars, time_left, created_at FROM scores WHERE level_id = ? ORDER BY score DESC, time_left DESC LIMIT ?",
            (level_id, limit),
        )
        rows = c.fetchall()
        result = [
            {"nickname": r[0], "score": r[1], "stars": r[2], "time_left": r[3], "created_at": r[4]}
            for r in rows
        ]
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
