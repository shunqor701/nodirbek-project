from datetime import datetime, timedelta
from pathlib import Path

from app import create_app
from app.extensions import db
from app.models import UploadedFile

app = create_app()
with app.app_context():
    cutoff = datetime.utcnow() - timedelta(days=30)
    files = UploadedFile.query.filter(UploadedFile.uploaded_at < cutoff, UploadedFile.file_deleted.is_(False)).all()
    for record in files:
        path = Path(app.config["UPLOAD_FOLDER"]) / record.stored_filename
        if path.exists():
            path.unlink()
        record.file_deleted = True
        record.deleted_at = datetime.utcnow()
    db.session.commit()
    print(f"{len(files)} ta eski fayl tozalandi.")
