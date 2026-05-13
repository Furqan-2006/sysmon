from datetime import datetime
from .extensions import db


class User(db.Model):
    """Registered API users."""
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80),  unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)   # bcrypt hash
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":         self.id,
            "username":   self.username,
            "email":      self.email,
            "created_at": self.created_at.isoformat(),
        }


class MetricSnapshot(db.Model):
    """A point-in-time snapshot of all system metrics (stored by background task)."""
    __tablename__ = "metric_snapshots"

    id         = db.Column(db.Integer, primary_key=True)
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # CPU
    cpu_usage  = db.Column(db.Float)
    cpu_user   = db.Column(db.Float)
    cpu_system = db.Column(db.Float)
    cpu_idle   = db.Column(db.Float)

    # Memory
    mem_total_mb   = db.Column(db.Float)
    mem_used_mb    = db.Column(db.Float)
    mem_free_mb    = db.Column(db.Float)
    mem_usage_pct  = db.Column(db.Float)

    # Disk
    disk_total_gb  = db.Column(db.Float)
    disk_used_gb   = db.Column(db.Float)
    disk_free_gb   = db.Column(db.Float)
    disk_usage_pct = db.Column(db.Float)

    # Processes
    proc_total    = db.Column(db.Integer)
    proc_running  = db.Column(db.Integer)
    proc_sleeping = db.Column(db.Integer)

    # System
    uptime_seconds = db.Column(db.Float)

    def to_dict(self):
        return {
            "id":        self.id,
            "timestamp": self.timestamp.isoformat(),
            "cpu": {
                "usage_percent": round(self.cpu_usage or 0, 2),
                "user":          round(self.cpu_user or 0, 2),
                "system":        round(self.cpu_system or 0, 2),
                "idle":          round(self.cpu_idle or 0, 2),
            },
            "memory": {
                "total_mb":      round(self.mem_total_mb or 0, 1),
                "used_mb":       round(self.mem_used_mb or 0, 1),
                "free_mb":       round(self.mem_free_mb or 0, 1),
                "usage_percent": round(self.mem_usage_pct or 0, 2),
            },
            "disk": {
                "total_gb":      round(self.disk_total_gb or 0, 2),
                "used_gb":       round(self.disk_used_gb or 0, 2),
                "free_gb":       round(self.disk_free_gb or 0, 2),
                "usage_percent": round(self.disk_usage_pct or 0, 2),
            },
            "processes": {
                "total":    self.proc_total,
                "running":  self.proc_running,
                "sleeping": self.proc_sleeping,
            },
            "uptime_seconds": self.uptime_seconds,
        }


class UploadedConfig(db.Model):
    """Metadata for uploaded config files."""
    __tablename__ = "uploaded_configs"

    id          = db.Column(db.Integer, primary_key=True)
    filename    = db.Column(db.String(256), nullable=False)
    stored_name = db.Column(db.String(256), nullable=False)  # UUID-prefixed on disk
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    size_bytes  = db.Column(db.Integer)

    user = db.relationship("User", backref="configs")

    def to_dict(self):
        return {
            "id":          self.id,
            "filename":    self.filename,
            "uploaded_by": self.user.username if self.user else None,
            "uploaded_at": self.uploaded_at.isoformat(),
            "size_bytes":  self.size_bytes,
        }
