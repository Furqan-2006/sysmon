import os
import uuid
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from .extensions import db
from .models import UploadedConfig

upload_bp = Blueprint("upload", __name__, url_prefix="/api/upload")


def _allowed(filename: str) -> bool:
    ext = Path(filename).suffix.lstrip(".").lower()
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


@upload_bp.route("/config", methods=["POST"])
@jwt_required()
def upload_config():
    """
    POST /api/upload/config
    Form-data: file=<config file>
    Accepts: .json, .yaml, .yml, .ini, .toml
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in request."}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "No file selected."}), 400
    if not _allowed(f.filename):
        allowed = ", ".join(current_app.config["ALLOWED_EXTENSIONS"])
        return jsonify({"error": f"File type not allowed. Accepted: {allowed}"}), 415

    # Save with UUID prefix to avoid name collisions
    safe_name   = Path(f.filename).name
    stored_name = f"{uuid.uuid4().hex}_{safe_name}"
    dest_dir    = Path(current_app.config["UPLOAD_FOLDER"])
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path   = dest_dir / stored_name
    f.save(str(dest_path))

    size = dest_path.stat().st_size
    user_id = get_jwt_identity()

    record = UploadedConfig(
        filename    = safe_name,
        stored_name = stored_name,
        uploaded_by = user_id,
        size_bytes  = size,
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({
        "message": "Config uploaded successfully.",
        "config":  record.to_dict(),
    }), 201


@upload_bp.route("/configs", methods=["GET"])
@jwt_required()
def list_configs():
    """GET /api/upload/configs — List all uploaded configs for current user."""
    user_id = get_jwt_identity()
    configs = UploadedConfig.query.filter_by(uploaded_by=user_id)\
                                  .order_by(UploadedConfig.uploaded_at.desc())\
                                  .all()
    return jsonify({
        "count": len(configs),
        "data":  [c.to_dict() for c in configs],
    }), 200


@upload_bp.route("/configs/<int:config_id>", methods=["GET"])
@jwt_required()
def download_config(config_id):
    """GET /api/upload/configs/<id> — Download a config file."""
    record = UploadedConfig.query.get_or_404(config_id)
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        record.stored_name,
        download_name=record.filename,
        as_attachment=True,
    )


@upload_bp.route("/configs/<int:config_id>", methods=["DELETE"])
@jwt_required()
def delete_config(config_id):
    """DELETE /api/upload/configs/<id> — Delete a config file."""
    user_id = get_jwt_identity()
    record  = UploadedConfig.query.get_or_404(config_id)

    if record.uploaded_by != user_id:
        return jsonify({"error": "Not authorized to delete this file."}), 403

    file_path = Path(current_app.config["UPLOAD_FOLDER"]) / record.stored_name
    if file_path.exists():
        file_path.unlink()

    db.session.delete(record)
    db.session.commit()
    return jsonify({"message": f"Config '{record.filename}' deleted."}), 200
