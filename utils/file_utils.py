import os
import uuid
from config import ALLOWED_EXTENSIONS, logger

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(original_filename):
    """Generate a unique filename for the uploaded file."""
    extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    unique_id = str(uuid.uuid4())
    
    if extension:
        return f"{unique_id}.{extension}"
    return unique_id