import sqlite3
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from core.models.log_model import LogModel

class DatabaseManager:
    """Manages SQLite database connections and operations."""
    
    def __init__(self, db_path: str = "logs.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._initialize_db()
    
    def _initialize_db(self):
        """Create logs table if it doesn't exist."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                status TEXT NOT NULL,
                reasons TEXT,
                timestamp TEXT NOT NULL,
                redacted_prompt TEXT,
                gemini_response TEXT,
                risk_score REAL DEFAULT 0,
                intent TEXT,
                integrity_hash TEXT,
                prev_hash TEXT
            )
        ''')
        # Ensure new columns exist for upgrades
        for column_def in [
            ("risk_score", "REAL", "0"),
            ("intent", "TEXT", "'general'"),
            ("integrity_hash", "TEXT", "NULL"),
            ("prev_hash", "TEXT", "NULL")
        ]:
            name, col_type, default = column_def
            try:
                self.cursor.execute(f"ALTER TABLE logs ADD COLUMN {name} {col_type} DEFAULT {default}")
            except sqlite3.OperationalError:
                pass

        # Audit trail table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                action TEXT NOT NULL,
                detail TEXT,
                timestamp TEXT NOT NULL,
                integrity_hash TEXT,
                prev_hash TEXT
            )
        ''')
        self.conn.commit()
        print("🗄️ SQLite database initialized")
    
    def insert_log(self, log: LogModel) -> bool:
        """Insert a log entry into the database."""
        try:
            prev_hash = self._get_last_log_hash()
            integrity_hash = self._compute_log_hash(log, prev_hash)
            log.prev_hash = prev_hash
            log.integrity_hash = integrity_hash

            self.cursor.execute(
                """
                INSERT INTO logs (prompt, status, reasons, timestamp, redacted_prompt, gemini_response, risk_score, intent, integrity_hash, prev_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log.prompt,
                    log.status,
                    json.dumps(log.reasons),
                    log.timestamp,
                    log.redacted_prompt,
                    log.gemini_response,
                    log.risk_score,
                    log.intent,
                    log.integrity_hash,
                    log.prev_hash
                )
            )
            self.conn.commit()
            print(f"📝 Log inserted successfully. Status: {log.status}")
            return True
        except Exception as e:
            print(f"❌ Failed to insert log: {e}")
            return False
    
    def get_all_logs(self) -> List[Dict[str, Any]]:
        """Retrieve all logs from the database."""
        try:
            self.cursor.execute("SELECT id, prompt, status, reasons, timestamp, redacted_prompt, gemini_response, risk_score, intent, integrity_hash, prev_hash FROM logs ORDER BY id DESC")
            logs_list = [
                {
                    "id": row[0],
                    "prompt": row[1],
                    "status": row[2],
                    "reasons": json.loads(row[3]),
                    "timestamp": row[4],
                    "redacted_prompt": row[5],
                    "gemini_response": row[6],
                    "risk_score": row[7],
                    "intent": row[8],
                    "integrity_hash": row[9],
                    "prev_hash": row[10],
                } for row in self.cursor.fetchall()
            ]
            print(f"✅ {len(logs_list)} logs retrieved")
            return logs_list
        except Exception as e:
            print(f"❌ Failed to retrieve logs: {e}")
            return []
    
    def clear_logs(self) -> bool:
        """Clear all logs from the database."""
        try:
            self.cursor.execute("DELETE FROM logs")
            self.conn.commit()
            print("🧹 All logs cleared from database")
            return True
        except Exception as e:
            print(f"❌ Failed to clear logs: {e}")
            return False
    
    def close(self):
        """Close database connection."""
        try:
            self.conn.close()
            print("✅ Database connection closed")
        except Exception as e:
            print(f"⚠️ Error closing database: {e}")

    # ---- Integrity helpers ----
    def _get_last_log_hash(self) -> Optional[str]:
        self.cursor.execute("SELECT integrity_hash FROM logs ORDER BY id DESC LIMIT 1")
        row = self.cursor.fetchone()
        return row[0] if row and row[0] else None

    def _compute_log_hash(self, log: LogModel, prev_hash: Optional[str]) -> str:
        payload = json.dumps({
            "prompt": log.prompt,
            "status": log.status,
            "reasons": log.reasons,
            "timestamp": log.timestamp,
            "redacted_prompt": log.redacted_prompt,
            "gemini_response": log.gemini_response,
            "risk_score": log.risk_score,
            "intent": log.intent,
            "prev_hash": prev_hash,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def _get_last_audit_hash(self) -> Optional[str]:
        self.cursor.execute("SELECT integrity_hash FROM audit_events ORDER BY id DESC LIMIT 1")
        row = self.cursor.fetchone()
        return row[0] if row and row[0] else None

    def _compute_audit_hash(self, username: str, action: str, detail: str, timestamp: str, prev_hash: Optional[str]) -> str:
        payload = json.dumps({
            "username": username,
            "action": action,
            "detail": detail,
            "timestamp": timestamp,
            "prev_hash": prev_hash
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    # ---- Audit trail ----
    def log_audit(self, username: str, action: str, detail: str = "") -> None:
        ts = datetime.now().isoformat()
        prev_hash = self._get_last_audit_hash()
        integrity_hash = self._compute_audit_hash(username, action, detail, ts, prev_hash)
        self.cursor.execute(
            """
            INSERT INTO audit_events (username, action, detail, timestamp, integrity_hash, prev_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (username, action, detail, ts, integrity_hash, prev_hash)
        )
        self.conn.commit()

    def get_audit_events(self, limit: int = 200) -> List[Dict[str, Any]]:
        self.cursor.execute("SELECT id, username, action, detail, timestamp, integrity_hash, prev_hash FROM audit_events ORDER BY id DESC LIMIT ?", (limit,))
        return [
            {
                "id": row[0],
                "username": row[1],
                "action": row[2],
                "detail": row[3],
                "timestamp": row[4],
                "integrity_hash": row[5],
                "prev_hash": row[6],
            }
            for row in self.cursor.fetchall()
        ]

    # ---- Analytics ----
    def get_status_counts(self) -> Dict[str, int]:
        self.cursor.execute("SELECT status, COUNT(*) FROM logs GROUP BY status")
        return {row[0]: row[1] for row in self.cursor.fetchall()}

    def get_recent_timeseries(self, days: int = 7) -> List[Dict[str, Any]]:
        self.cursor.execute("""
            SELECT date(timestamp) as day, status, COUNT(*) as count
            FROM logs
            WHERE date(timestamp) >= date('now', ? || ' days')
            GROUP BY day, status
            ORDER BY day ASC
        """, (-days,))
        rows = self.cursor.fetchall()
        series = {}
        for day, status, count in rows:
            series.setdefault(day, {})[status] = count
        return [{"day": day, **series.get(day, {})} for day in sorted(series.keys())]

    def get_reason_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        self.cursor.execute("SELECT reasons FROM logs")
        for (reasons_json,) in self.cursor.fetchall():
            try:
                reasons = json.loads(reasons_json)
                for r in reasons:
                    r_type = r.get("type", "unknown")
                    counts[r_type] = counts.get(r_type, 0) + 1
            except Exception:
                continue
        return counts

