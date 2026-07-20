"""数据层：SQLite 持久化 + SM-2 间隔重复算法 + 词库加载"""
import json
import os
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from random import sample

DB_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = DB_DIR / "progress.db"
DATA_DIR = DB_DIR / "data"


# ═══════════════════════════════════════════════════════════════
# SM-2 算法（SuperMemo 2）
# ═══════════════════════════════════════════════════════════════

class SM2:
    """
    参数说明：
    - quality: 0-5，0=完全忘记，5=非常轻松
    - ease_factor: 舒适度，默认 2.5，最低 1.3
    - interval: 间隔天数
    - repetitions: 连续正确次数
    """

    @staticmethod
    def review(current_interval: int, current_ef: float, current_reps: int, quality: int):
        if quality < 0 or quality > 5:
            raise ValueError("quality 必须在 0-5 之间")

        if quality < 3:
            # 答错 → 重置
            new_interval = 1
            new_reps = 0
            new_ef = max(1.3, current_ef - 0.2)
        else:
            if current_reps == 0:
                new_interval = 1
            elif current_reps == 1:
                new_interval = 6
            else:
                new_interval = round(current_interval * current_ef)

            new_reps = current_reps + 1
            # 调整舒适度
            ef_delta = {3: -0.14, 4: 0.0, 5: 0.1}
            new_ef = max(1.3, current_ef + ef_delta.get(quality, 0))

        next_review = date.today() + timedelta(days=new_interval)
        return {
            "interval": new_interval,
            "ease_factor": round(new_ef, 2),
            "repetitions": new_reps,
            "next_review": next_review.isoformat(),
            "last_review": date.today().isoformat(),
        }


# ═══════════════════════════════════════════════════════════════
# 数据库操作
# ═══════════════════════════════════════════════════════════════

class ProgressDB:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH))
        self._init_tables()

    def _init_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS word_progress (
                word TEXT PRIMARY KEY,
                grade TEXT NOT NULL,
                interval_days INTEGER DEFAULT 0,
                ease_factor REAL DEFAULT 2.5,
                repetitions INTEGER DEFAULT 0,
                next_review TEXT NOT NULL DEFAULT '',
                last_review TEXT NOT NULL DEFAULT '',
                learned INTEGER DEFAULT 0,
                total_reviews INTEGER DEFAULT 0,
                total_correct INTEGER DEFAULT 0
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        # 默认设置
        self.conn.execute("""
            INSERT OR IGNORE INTO settings (key, value)
            VALUES ('daily_goal', '20'), ('selected_grades', '')
        """)
        self.conn.commit()

    def get_setting(self, key: str, default: str = "") -> str:
        row = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def set_setting(self, key: str, value: str):
        self.conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()

    def get_word_progress(self, word: str) -> dict | None:
        row = self.conn.execute(
            "SELECT word, grade, interval_days, ease_factor, repetitions, next_review, last_review, learned, total_reviews, total_correct FROM word_progress WHERE word=?",
            (word,),
        ).fetchone()
        if not row:
            return None
        return {
            "word": row[0], "grade": row[1], "interval_days": row[2],
            "ease_factor": row[3], "repetitions": row[4], "next_review": row[5],
            "last_review": row[6], "learned": row[7], "total_reviews": row[8],
            "total_correct": row[9],
        }

    def update_word_progress(self, word: str, grade: str, sm2_result: dict, quality: int):
        learned = 1 if sm2_result["repetitions"] >= 2 else 0
        correct = 1 if quality >= 3 else 0
        self.conn.execute("""
            INSERT INTO word_progress (word, grade, interval_days, ease_factor, repetitions, next_review, last_review, learned, total_reviews, total_correct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            ON CONFLICT(word) DO UPDATE SET
                interval_days=excluded.interval_days,
                ease_factor=excluded.ease_factor,
                repetitions=excluded.repetitions,
                next_review=excluded.next_review,
                last_review=excluded.last_review,
                learned=CASE WHEN excluded.repetitions >= 2 THEN 1 ELSE learned END,
                total_reviews=total_reviews + 1,
                total_correct=total_correct + ?
        """, (
            word, grade, sm2_result["interval"], sm2_result["ease_factor"],
            sm2_result["repetitions"], sm2_result["next_review"],
            sm2_result["last_review"], correct,
            correct, correct,
        ))
        self.conn.commit()

    def get_due_reviews(self, grades: list[str] | None = None) -> list[str]:
        """获取需要复习的单词列表"""
        today = date.today().isoformat()
        if grades:
            placeholders = ",".join("?" * len(grades))
            rows = self.conn.execute(
                f"SELECT word FROM word_progress WHERE next_review <= ? AND grade IN ({placeholders}) ORDER BY next_review ASC",
                [today] + grades,
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT word FROM word_progress WHERE next_review <= ? ORDER BY next_review ASC",
                (today,),
            ).fetchall()
        return [r[0] for r in rows]

    def get_due_count(self) -> int:
        today = date.today().isoformat()
        row = self.conn.execute(
            "SELECT COUNT(*) FROM word_progress WHERE next_review <= ?", (today,)
        ).fetchone()
        return row[0]

    def get_today_new_count(self) -> int:
        today = date.today().isoformat()
        row = self.conn.execute(
            "SELECT COUNT(*) FROM word_progress WHERE last_review = ?", (today,)
        ).fetchone()
        return row[0]

    def get_learned_count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) FROM word_progress WHERE learned = 1").fetchone()
        return row[0]

    def get_unseen_words(self, word_bank: "WordBank", count: int) -> list[dict]:
        """从未学过的词中取 N 个新词"""
        seen = set(
            r[0] for r in self.conn.execute("SELECT word FROM word_progress").fetchall()
        )
        candidates = [w for w in word_bank.words if w["word"] not in seen]
        return sample(candidates, min(count, len(candidates)))

    def close(self):
        self.conn.close()


# ═══════════════════════════════════════════════════════════════
# 词库加载
# ═══════════════════════════════════════════════════════════════

class WordBank:
    def __init__(self, grades: list[str] | None = None):
        self.words: list[dict] = []
        self.grades: set[str] = set()
        self._load_all(grades)

    def _load_all(self, grades: list[str] | None = None):
        word_dir = DATA_DIR / "word_banks"
        if not word_dir.exists():
            return
        for fname in sorted(os.listdir(str(word_dir))):
            if not fname.endswith(".json"):
                continue
            grade_name = fname.replace(".json", "")
            if grades and grade_name not in grades:
                continue
            with open(word_dir / fname, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.grades.add(grade_name)
                for w in data.get("words", []):
                    w["grade"] = grade_name
                    self.words.append(w)

    @staticmethod
    def available_grades() -> list[str]:
        word_dir = DATA_DIR / "word_banks"
        if not word_dir.exists():
            return []
        return sorted(
            f.replace(".json", "")
            for f in os.listdir(str(word_dir))
            if f.endswith(".json")
        )

    def get_by_word(self, word: str) -> dict | None:
        for w in self.words:
            if w["word"] == word:
                return w
        return None
