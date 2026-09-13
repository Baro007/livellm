"""
LiveLLM - Static Data Exporter for Netlify Jamstack Deployment
Exports database telemetry into static JSON files in livellm/frontend/data/
so the entire platform can be hosted 100% statically on Netlify at $0 cost,
automatically updated via GitHub Actions every 10 minutes.
"""

import os
import json
import time
from datetime import datetime, timezone

from livellm.storage.database import get_db_connection, DB_PATH
from livellm.benchmarks.datasets import SUPPORTED_MODELS

FRONTEND_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "data")


def export_static_data(db_path: str = DB_PATH, output_dir: str = FRONTEND_DATA_DIR):
    os.makedirs(output_dir, exist_ok=True)

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Models
        cursor.execute("SELECT * FROM models ORDER BY baseline_tps DESC")
        models = [dict(row) for row in cursor.fetchall()]

        for m in models:
            cursor.execute(
                "SELECT COUNT(*) as alert_count FROM nerf_alerts WHERE model_id = ?",
                (m["id"],)
            )
            m["active_alerts"] = cursor.fetchone()["alert_count"]

            cursor.execute(
                "SELECT * FROM probe_runs WHERE model_id = ? ORDER BY id DESC LIMIT 1",
                (m["id"],)
            )
            latest = cursor.fetchone()
            m["latest_run"] = dict(latest) if latest else None

        with open(os.path.join(output_dir, "models.json"), "w", encoding="utf-8") as f:
            json.dump({"models": models}, f, indent=2)

        # 2. Alerts
        cursor.execute("""
        SELECT a.*, m.name as model_name, m.provider
        FROM nerf_alerts a
        JOIN models m ON a.model_id = m.id
        ORDER BY a.id DESC
        """)
        alerts = [dict(r) for r in cursor.fetchall()]
        with open(os.path.join(output_dir, "alerts.json"), "w", encoding="utf-8") as f:
            json.dump({"alerts": alerts}, f, indent=2)

        # 3. Diurnal
        cursor.execute("SELECT * FROM diurnal_aggregates ORDER BY model_id, hour_utc ASC")
        diurnal = [dict(r) for r in cursor.fetchall()]
        with open(os.path.join(output_dir, "diurnal.json"), "w", encoding="utf-8") as f:
            json.dump({
                "peak_hours_utc": [14, 15, 16, 17, 18],
                "data": diurnal
            }, f, indent=2)

        # 4. Longitudinal Drift (all models)
        drift_data = {}
        for m in models:
            cursor.execute("""
            SELECT * FROM longitudinal_daily WHERE model_id = ? ORDER BY day_index ASC
            """, (m["id"],))
            points = [dict(r) for r in cursor.fetchall()]

            cursor.execute("""
            SELECT * FROM nerf_alerts WHERE model_id = ? ORDER BY id DESC
            """, (m["id"],))
            model_alerts = [dict(r) for r in cursor.fetchall()]

            drift_data[m["id"]] = {
                "model_id": m["id"],
                "series": points,
                "alerts": model_alerts
            }

        with open(os.path.join(output_dir, "drift.json"), "w", encoding="utf-8") as f:
            json.dump(drift_data, f, indent=2)

        # 5. Tail Latency (all models)
        latency_data = {}
        for m in models:
            cursor.execute("""
            SELECT hour_utc, avg_ttft_ms as p50, p95_ttft_ms as p95, p99_ttft_ms as p99
            FROM diurnal_aggregates WHERE model_id = ? ORDER BY hour_utc ASC
            """, (m["id"],))
            latency_data[m["id"]] = {
                "model_id": m["id"],
                "latency_data": [dict(r) for r in cursor.fetchall()]
            }

        with open(os.path.join(output_dir, "latency.json"), "w", encoding="utf-8") as f:
            json.dump(latency_data, f, indent=2)

        # 6. Meta / Platform Stats
        meta = {
            "platform": "LiveLLM",
            "version": "1.0.0",
            "cadence_minutes": 10,
            "last_updated_utc": datetime.now(timezone.utc).isoformat(),
            "last_updated_timestamp": time.time(),
            "models_count": len(models),
            "alerts_count": len(alerts),
            "peak_window_utc": "14:00 - 18:00 UTC",
            "deployment": "Netlify Jamstack Static CDN"
        }
        with open(os.path.join(output_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    print(f"[{datetime.now(timezone.utc).isoformat()}] Successfully exported static JSON files to {output_dir}")


if __name__ == "__main__":
    export_static_data()
