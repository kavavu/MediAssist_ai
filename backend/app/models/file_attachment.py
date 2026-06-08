"""FileAttachment model — stores metadata for files uploaded to consultations."""
from ..extensions import db


class FileAttachment(db.Model):
    __tablename__ = "file_attachments"

    id = db.Column(db.Integer, primary_key=True)
    consultation_id = db.Column(
        db.Integer, db.ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)          # stored filename (uuid)
    original_filename = db.Column(db.String(255), nullable=False) # original user filename
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)        # bytes
    mime_type = db.Column(db.String(128))
    file_category = db.Column(db.String(32)) # 'image', 'document'
    created_at = db.Column(db.DateTime, default=db.func.now())

    consultation = db.relationship("Consultation", back_populates="files")
    uploader = db.relationship("User", foreign_keys=[uploaded_by])

    def to_dict(self):
        return {
            "id": self.id,
            "consultation_id": self.consultation_id,
            "uploaded_by": self.uploaded_by,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "file_category": self.file_category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
