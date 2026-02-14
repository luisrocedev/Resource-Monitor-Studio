from __future__ import annotations

import os
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil
from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "resource_metrics.sqlite3"
HTTP_PORT = int(os.getenv("MON_HTTP_PORT", "5070"))
SAMPLE_SECONDS = float(os.getenv("MON_SAMPLE_SECONDS", "2.0"))

app = Flask(__name__)

state_lock = threading.Lock()
runtime_state: dict[str, Any] = {
    "is_sampling": True,
    "sample_seconds": SAMPLE_SECONDS,
    "samples_collected": 0,
    "alerts_generated": 0,
}


def db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = db_conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            epoch INTEGER NOT NULL,
            cpu_percent REAL NOT NULL,
            ram_percent REAL NOT NULL,
            disk_percent REAL NOT NULL,
            disk_free_gb REAL NOT NULL,
            net_bytes_sent INTEGER NOT NULL,
            net_bytes_recv INTEGER NOT NULL,
            process_count INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            metric_id INTEGER NOT NULL,
            severity TEXT NOT NULL,
            reason TEXT NOT NULL,
            value REAL NOT NULL,
            threshold REAL NOT NULL,
            FOREIGN KEY(metric_id) REFERENCES metrics(id)
        );

        CREATE INDEX IF NOT EXISTS idx_metrics_epoch ON metrics(epoch);
        CREATE INDEX IF NOT EXISTS idx_alerts_metric ON alerts(metric_id);
        """
    )
    conn.commit()
    conn.close()


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def collect_sample() -> dict[str, Any]:
    cpu_percent = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    process_count = len(psutil.pids())

    sample = {
        "created_at": now_text(),
        "epoch": int(time.time()),
        "cpu_percent": round(float(cpu_percent), 2),
        "ram_percent": round(float(ram.percent), 2),
        "disk_percent": round(float(disk.percent), 2),
        "disk_free_gb": round(float(disk.free / (1024 ** 3)), 2),
        "net_bytes_sent": int(net.bytes_sent),
        "net_bytes_recv": int(net.bytes_recv),
        "process_count": int(process_count),
    }
    return sample


def insert_metric(sample: dict[str, Any]) -> int:
    conn = db_conn()
    cur = conn.execute(
        """
        INSERT INTO metrics (
            created_at, epoch, cpu_percent, ram_percent, disk_percent,
            disk_free_gb, net_bytes_sent, net_bytes_recv, process_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            sample["created_at"],
            sample["epoch"],
            sample["cpu_percent"],
            sample["ram_percent"],
            sample["disk_percent"],
            sample["disk_free_gb"],
            sample["net_bytes_sent"],
            sample["net_bytes_recv"],
            sample["process_count"],
        ),
    )
    conn.commit()
    metric_id = int(cur.lastrowid)
    conn.close()
    return metric_id


def evaluate_alerts(metric_id: int, sample: dict[str, Any]) -> int:
    rules = [
        ("critical", "cpu_percent", 92.0, "CPU crítica"),
        ("warning", "cpu_percent", 80.0, "CPU elevada"),
        ("critical", "ram_percent", 92.0, "RAM crítica"),
        ("warning", "ram_percent", 80.0, "RAM elevada"),
        ("warning", "disk_percent", 88.0, "Disco alto"),
    ]

    created = 0
    conn = db_conn()
    for severity, key, threshold, reason in rules:
        value = float(sample[key])
        if value >= threshold:
            conn.execute(
                """
                INSERT INTO alerts (created_at, metric_id, severity, reason, value, threshold)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (now_text(), metric_id, severity, reason, value, threshold),
            )
            created += 1
    conn.commit()
    conn.close()
    return created


def sampler_loop() -> None:
    while True:
        with state_lock:
            active = bool(runtime_state["is_sampling"])
            interval = float(runtime_state["sample_seconds"])

        if active:
            sample = collect_sample()
            metric_id = insert_metric(sample)
            alerts = evaluate_alerts(metric_id, sample)
            with state_lock:
                runtime_state["samples_collected"] += 1
                runtime_state["alerts_generated"] += alerts

        time.sleep(max(0.5, interval))


def start_sampler() -> None:
    thread = threading.Thread(target=sampler_loop, daemon=True)
    thread.start()


@app.get("/")
def index() -> str:
    return render_template("index.html", sample_seconds=SAMPLE_SECONDS)


@app.get("/api/stats")
def stats():
    conn = db_conn()
    total = conn.execute("SELECT COUNT(*) AS c FROM metrics").fetchone()["c"]
    latest = conn.execute(
        """
        SELECT id, created_at, cpu_percent, ram_percent, disk_percent, disk_free_gb,
               net_bytes_sent, net_bytes_recv, process_count
        FROM metrics
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    alerts_total = conn.execute("SELECT COUNT(*) AS c FROM alerts").fetchone()["c"]
    alerts_critical = conn.execute(
        "SELECT COUNT(*) AS c FROM alerts WHERE severity='critical'"
    ).fetchone()["c"]
    conn.close()

    with state_lock:
        state_snapshot = dict(runtime_state)

    return jsonify(
        {
            "ok": True,
            "total_samples": total,
            "alerts_total": alerts_total,
            "alerts_critical": alerts_critical,
            "latest": dict(latest) if latest else None,
            "runtime": state_snapshot,
        }
    )


@app.get("/api/series")
def series():
    limit = int(request.args.get("limit", 180))
    limit = max(20, min(limit, 2000))

    conn = db_conn()
    rows = conn.execute(
        """
        SELECT created_at, epoch, cpu_percent, ram_percent, disk_percent,
               disk_free_gb, process_count
        FROM metrics
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()

    items = [dict(r) for r in rows]
    items.reverse()
    return jsonify({"ok": True, "items": items})


@app.get("/api/rollup")
def rollup():
    mode = request.args.get("mode", "hour")
    if mode not in ("hour", "day"):
        mode = "hour"

    if mode == "hour":
        bucket_expr = "strftime('%Y-%m-%d %H:00:00', created_at)"
        max_rows = 48
    else:
        bucket_expr = "strftime('%Y-%m-%d 00:00:00', created_at)"
        max_rows = 60

    conn = db_conn()
    rows = conn.execute(
        f"""
        SELECT {bucket_expr} AS bucket,
               ROUND(AVG(cpu_percent), 2) AS cpu_avg,
               ROUND(AVG(ram_percent), 2) AS ram_avg,
               ROUND(AVG(disk_percent), 2) AS disk_avg,
               COUNT(*) AS samples
        FROM metrics
        GROUP BY bucket
        ORDER BY bucket DESC
        LIMIT ?
        """,
        (max_rows,),
    ).fetchall()
    conn.close()

    items = [dict(r) for r in rows]
    items.reverse()
    return jsonify({"ok": True, "mode": mode, "items": items})


@app.get("/api/alerts")
def alerts():
    limit = int(request.args.get("limit", 80))
    limit = max(10, min(limit, 400))

    conn = db_conn()
    rows = conn.execute(
        """
        SELECT id, created_at, metric_id, severity, reason, value, threshold
        FROM alerts
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()

    return jsonify({"ok": True, "items": [dict(r) for r in rows]})


@app.post("/api/control")
def control():
    payload = request.get_json(silent=True) or {}
    action = str(payload.get("action", "")).lower().strip()

    with state_lock:
        if action == "pause":
            runtime_state["is_sampling"] = False
        elif action == "resume":
            runtime_state["is_sampling"] = True
        elif action == "interval":
            try:
                value = float(payload.get("value", runtime_state["sample_seconds"]))
                runtime_state["sample_seconds"] = max(0.5, min(value, 60.0))
            except Exception:
                pass

        snapshot = dict(runtime_state)

    return jsonify({"ok": True, "runtime": snapshot})


if __name__ == "__main__":
    init_db()
    start_sampler()
    app.run(host="127.0.0.1", port=HTTP_PORT, debug=True)
