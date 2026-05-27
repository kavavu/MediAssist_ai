"""File upload routes — handles image/document uploads for consultations."""
import os
import uuid
from pathlib import Path

from flask import Blueprint, request, send_file, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from werkzeug.utils import secure_filename

from backend.app.extensions import db
from backend.app.models.file_attachment import FileAttachment
from backend.app.models.consultation import Consultation

upload_bp = Blueprint("upload", __name__)

# 5 MB max
MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "pdf"}
ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/gif", "application/pdf"
}


def _get_upload_dir(consultation_id: int) -> Path:
    """Return the upload directory for a given consultation."""
    base = Path(__file__).resolve().parent.parent.parent / "uploads"
    folder = base / f"consultation_{consultation_id}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _allowed_file(filename: str, mimetype: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_EXTENSIONS and mimetype in ALLOWED_MIME_TYPES


def _category_from_mime(mime: str) -> str:
    if mime.startswith("image/"):
        return "image"
    return "document"


@upload_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_file():
    """POST /api/upload — Upload a file for a consultation.

    Form fields:
        - consultation_id (required)
        - file (required)
    """
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    consultation_id = request.form.get("consultation_id", type=int)
    if not consultation_id:
        return jsonify({"error": "consultation_id is required"}), 400

    consultation = Consultation.query.get(consultation_id)
    if not consultation:
        return jsonify({"error": "Consultation not found"}), 404

    # Auth check: patient must own it, doctor must be assigned
    if user.role == "patient" and consultation.patient_id != user.id:
        return jsonify({"error": "Not authorized for this consultation"}), 403
    if user.role == "doctor" and consultation.doctor_id != user.id:
        return jsonify({"error": "Not authorized for this consultation"}), 403

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Validate
    if not _allowed_file(file.filename, file.mimetype):
        return jsonify({"error": "File type not allowed. Use: jpg, png, gif, pdf"}), 400

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        return jsonify({"error": f"File too large. Max {MAX_FILE_SIZE // (1024*1024)}MB"}), 400

    # Save
    ext = secure_filename(file.filename).rsplit(".", 1)[-1].lower()
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = _get_upload_dir(consultation_id)
    file_path = upload_dir / stored_name
    file.save(str(file_path))

    # Record in DB
    attachment = FileAttachment(
        consultation_id=consultation_id,
        uploaded_by=user.id,
        filename=stored_name,
        original_filename=secure_filename(file.filename),
        file_path=str(file_path),
        file_size=size,
        mime_type=file.mimetype,
        file_category=_category_from_mime(file.mimetype),
    )
    db.session.add(attachment)
    db.session.commit()

    return jsonify({
        "message": "File uploaded",
        "file": attachment.to_dict(),
    }), 201


@upload_bp.route("/upload/consultation/<int:consultation_id>", methods=["GET"])
@jwt_required()
def list_files(consultation_id):
    """GET /api/upload/consultation/<id> — List files for a consultation."""
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    consultation = Consultation.query.get(consultation_id)
    if not consultation:
        return jsonify({"error": "Consultation not found"}), 404

    if user.role == "patient" and consultation.patient_id != user.id:
        return jsonify({"error": "Not authorized"}), 403
    if user.role == "doctor" and consultation.doctor_id != user.id:
        return jsonify({"error": "Not authorized"}), 403

    files = FileAttachment.query.filter_by(consultation_id=consultation_id).order_by(
        FileAttachment.created_at.desc()
    ).all()
    return jsonify({"files": [f.to_dict() for f in files]}), 200


@upload_bp.route("/upload/file/<int:file_id>", methods=["GET"])
@jwt_required()
def serve_file(file_id):
    """GET /api/upload/file/<id> — Download/serve a file."""
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    attachment = FileAttachment.query.get(file_id)
    if not attachment:
        return jsonify({"error": "File not found"}), 404

    consultation = Consultation.query.get(attachment.consultation_id)
    if user.role == "patient" and consultation.patient_id != user.id:
        return jsonify({"error": "Not authorized"}), 403
    if user.role == "doctor" and consultation.doctor_id != user.id:
        return jsonify({"error": "Not authorized"}), 403

    path = Path(attachment.file_path)
    if not path.exists():
        return jsonify({"error": "File not found on disk"}), 404

    return send_file(
        str(path),
        mimetype=attachment.mime_type,
        as_attachment=False,
        download_name=attachment.original_filename,
    )


@upload_bp.route("/upload/file/<int:file_id>", methods=["DELETE"])
@jwt_required()
def delete_file(file_id):
    """DELETE /api/upload/file/<id> — Delete a file (uploader or doctor only)."""
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    attachment = FileAttachment.query.get(file_id)
    if not attachment:
        return jsonify({"error": "File not found"}), 404

    # Only uploader or assigned doctor can delete
    consultation = Consultation.query.get(attachment.consultation_id)
    can_delete = (
        attachment.uploaded_by == user.id
        or (user.role == "doctor" and consultation.doctor_id == user.id)
    )
    if not can_delete:
        return jsonify({"error": "Not authorized to delete this file"}), 403

    # Remove from disk
    path = Path(attachment.file_path)
    if path.exists():
        path.unlink()

    db.session.delete(attachment)
    db.session.commit()

    return jsonify({"message": "File deleted"}), 200
