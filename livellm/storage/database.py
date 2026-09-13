"""
LiveLLM - Database Storage Layer
SQLite analytical schema storing probe runs, diurnal stats, and Nerf drift alerts.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "livellm.db")


def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_PATH):
    """Initializes the database schema."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # Models table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS models (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            provider TEXT NOT NULL,
            tier TEXT NOT NULL,
            baseline_tps REAL NOT NULL,
            baseline_ttft_ms REAL NOT NULL,
            base_accuracy REAL NOT NULL,
            current_status TEXT DEFAULT 'Healthy',
            last_checked_at TEXT
        )
        """)

        # Probe Runs table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS probe_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id TEXT NOT NULL,
            timestamp_utc TEXT NOT NULL,
            hour_utc INTEGER NOT NULL,
            tier INTEGER NOT NULL,
            task_id TEXT NOT NULL,
            ttft_ms REAL NOT NULL,
            tpot_ms REAL NOT NULL,
            tps REAL NOT NULL,
            universal_tokens INTEGER NOT NULL,
            is_correct INTEGER,
            score REAL,
            output_snippet TEXT,
            error TEXT,
            FOREIGN KEY(model_id) REFERENCES models(id)
        )
        """)

        # Diurnal Aggregates (24-hour UTC matrix)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS diurnal_aggregates (
            model_id TEXT NOT NULL,
            hour_utc INTEGER NOT NULL,
            avg_tps REAL NOT NULL,
            avg_ttft_ms REAL NOT NULL,
            p95_ttft_ms REAL NOT NULL,
            p99_ttft_ms REAL NOT NULL,
            accuracy_rate REAL NOT NULL,
            sample_count INTEGER NOT NULL,
            PRIMARY KEY(model_id, hour_utc),
            FOREIGN KEY(model_id) REFERENCES models(id)
        )
        """)

        # Longitudinal Time Series (Daily points)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS longitudinal_daily (
            model_id TEXT NOT NULL,
            date_str TEXT NOT NULL,
            day_index INTEGER NOT NULL,
            avg_tps REAL NOT NULL,
            avg_ttft_ms REAL NOT NULL,
            accuracy REAL NOT NULL,
            ph_score REAL NOT NULL,
            is_nerf_alert INTEGER DEFAULT 0,
            PRIMARY KEY(model_id, date_str),
            FOREIGN KEY(model_id) REFERENCES models(id)
        )
        """)

        # Nerf & Degradation Alerts
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS nerf_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id TEXT NOT NULL,
            detected_at TEXT NOT NULL,
            alert_type TEXT NOT NULL,  -- 'Page-Hinkley Capability Nerf' or 'CUSUM Latency Spike'
            metric_affected TEXT NOT NULL,
            ph_score REAL NOT NULL,
            threshold REAL NOT NULL,
            drop_percentage REAL NOT NULL,
            details TEXT,
            FOREIGN KEY(model_id) REFERENCES models(id)
        )
        """)

        conn.commit()


def save_probe_run(
    model_id: str,
    tier: int,
    task_id: str,
    ttft_ms: float,
    tpot_ms: float,
    tps: float,
    universal_tokens: int,
    is_correct: Optional[bool],
    score: Optional[float],
    output_snippet: str,
    error: Optional[str] = None,
    db_path: str = DB_PATH
) -> int:
    """Inserts a new telemetry probe run."""
    now_utc = datetime.now(timezone.utc)
    timestamp_utc = now_utc.isoformat()
    hour_utc = now_utc.hour

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO probe_runs (
            model_id, timestamp_utc, hour_utc, tier, task_id,
            ttft_ms, tpot_ms, tps, universal_tokens, is_correct,
            score, output_snippet, error
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            model_id, timestamp_utc, hour_utc, tier, task_id,
            ttft_ms, tpot_ms, tps, universal_tokens,
            1 if is_correct else (0 if is_correct is not None else None),
            score, output_snippet, error
        ))
        run_id = cursor.lastrowid

        # Update last_checked_at on model
        cursor.execute("""
        UPDATE models SET last_checked_at = ? WHERE id = ?
        """, (timestamp_utc, model_id))

        conn.commit()
        return run_id
