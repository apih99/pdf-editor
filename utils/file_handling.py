import os
import io

def get_file_size_mb(file_obj):
    """Calculate file size in megabytes"""
    if isinstance(file_obj, io.BytesIO):
        return len(file_obj.getvalue()) / (1024 * 1024)
    else:
        return os.path.getsize(file_obj) / (1024 * 1024)

def validate_pdf_file(file):
    """Validate PDF file upload
    Returns:
        tuple: (is_valid, error_message)
    """
    if file.filename == '':
        return False, 'No file selected'

    if not file.filename.lower().endswith('.pdf'):
        return False, 'File must be a PDF'
        
    return True, None 