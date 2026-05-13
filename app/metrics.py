from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from .extensions import db
from .models import MetricSnapshot
from .sysmon_bridge import get_cpu, get_memory, get_disk, get_processes, get_uptime, get_all_metrics

metrics_bp = Blueprint("metrics", __name__, url_prefix="/api/metrics")


# ── Live Endpoints (calls C extension in real time) ───────────────────────────

@metrics_bp.route("/cpu", methods=["GET"])
@jwt_required()
def cpu():
    """GET /api/metrics/cpu — Live CPU usage (100ms sample via C)."""
    return jsonify({"source": "c_extension", "data": get_cpu()}), 200


@metrics_bp.route("/memory", methods=["GET"])
@jwt_required()
def memory():
    """GET /api/metrics/memory — Live memory stats."""
    return jsonify({"source": "c_extension", "data": get_memory()}), 200


@metrics_bp.route("/disk", methods=["GET"])
@jwt_required()
def disk():
    """GET /api/metrics/disk — Root filesystem disk usage."""
    return jsonify({"source": "c_extension", "data": get_disk()}), 200


@metrics_bp.route("/processes", methods=["GET"])
@jwt_required()
def processes():
    """GET /api/metrics/processes — Process count by state."""
    return jsonify({"source": "c_extension", "data": get_processes()}), 200


@metrics_bp.route("/uptime", methods=["GET"])
@jwt_required()
def uptime():
    """GET /api/metrics/uptime — System uptime."""
    return jsonify({"source": "c_extension", "data": get_uptime()}), 200


@metrics_bp.route("/snapshot", methods=["GET"])
@jwt_required()
def snapshot():
    """GET /api/metrics/snapshot — All metrics in one call + saves to DB."""
    data = get_all_metrics()
    _save_snapshot(data)
    return jsonify({
        "source":    "c_extension",
        "timestamp": datetime.utcnow().isoformat(),
        "data":      data,
    }), 200


# ── History Endpoints (reads SQLite) ─────────────────────────────────────────

@metrics_bp.route("/history", methods=["GET"])
@jwt_required()
def history():
    """
    GET /api/metrics/history
    Query params:
      limit  (int, max 100, default 20)
      since  (ISO datetime string)
    Returns stored snapshots from SQLite.
    """
    limit = min(int(request.args.get("limit", 20)), 100)
    since = request.args.get("since")

    query = MetricSnapshot.query.order_by(MetricSnapshot.timestamp.desc())

    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            query = query.filter(MetricSnapshot.timestamp >= since_dt)
        except ValueError:
            return jsonify({"error": "Invalid 'since' format. Use ISO 8601."}), 400

    snapshots = query.limit(limit).all()
    return jsonify({
        "count":  len(snapshots),
        "data":   [s.to_dict() for s in snapshots],
    }), 200


@metrics_bp.route("/history/<int:snapshot_id>", methods=["GET"])
@jwt_required()
def history_detail(snapshot_id):
    """GET /api/metrics/history/<id> — Single stored snapshot."""
    snap = MetricSnapshot.query.get_or_404(snapshot_id)
    return jsonify(snap.to_dict()), 200


@metrics_bp.route("/history", methods=["DELETE"])
@jwt_required()
def clear_history():
    """DELETE /api/metrics/history — Purge all stored snapshots."""
    count = MetricSnapshot.query.delete()
    db.session.commit()
    return jsonify({"message": f"Deleted {count} snapshots."}), 200


# ── Internal helper ───────────────────────────────────────────────────────────

def _save_snapshot(data: dict):
    """Persist a metrics dict to SQLite."""
    cpu  = data["cpu"]
    mem  = data["memory"]
    disk = data["disk"]
    proc = data["processes"]

    snap = MetricSnapshot(
        cpu_usage  = cpu["usage_percent"],
        cpu_user   = cpu["user"],
        cpu_system = cpu["system"],
        cpu_idle   = cpu["idle"],

        mem_total_mb  = mem["total_mb"],
        mem_used_mb   = mem["used_mb"],
        mem_free_mb   = mem["free_mb"],
        mem_usage_pct = mem["usage_percent"],

        disk_total_gb  = disk["total_gb"],
        disk_used_gb   = disk["used_gb"],
        disk_free_gb   = disk["free_gb"],
        disk_usage_pct = disk["usage_percent"],

        proc_total    = proc["total"],
        proc_running  = proc["running"],
        proc_sleeping = proc["sleeping"],

        uptime_seconds = data["uptime"]["seconds"],
    )
    db.session.add(snap)
    db.session.commit()
