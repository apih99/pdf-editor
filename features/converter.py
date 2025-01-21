import io
from flask import send_file, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import fitz
import zipfile
from utils.file_handling import validate_pdf_file
import os

def handle_conversion(request):
    """Handle PDF to Image conversion request"""
    pdf_document = None
    pdf_content = None
    
    try:
        # Validate request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        format = request.form.get('format', 'png').lower()
        
        # Validate file
        is_valid, error_message = validate_pdf_file(file)
        if not is_valid:
            return jsonify({'error': error_message}), 400

        if format not in ['png', 'jpeg', 'jpg']:
            return jsonify({'error': 'Invalid format specified'}), 400

        # Save PDF content to memory
        pdf_content = io.BytesIO(file.read())
        
        # Open PDF from memory
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                
                # Convert to PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Save image to memory
                img_buffer = io.BytesIO()
                img.save(img_buffer, format=format.upper())
                img_buffer.seek(0)
                
                # Add to ZIP
                zip_file.writestr(f'page_{page_num + 1}.{format}', img_buffer.getvalue())
                
                # Clean up page resources
                img_buffer.close()
                pix = None
                img = None

        # Close PDF resources
        if pdf_document:
            pdf_document.close()
        if pdf_content:
            pdf_content.close()
        
        # Prepare ZIP file for download
        zip_buffer.seek(0)
        filename_without_ext = os.path.splitext(secure_filename(file.filename))[0]
        
        # Send file and let Flask handle the buffer closure
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'{filename_without_ext}_images.zip'
        )

    except Exception as e:
        # Clean up resources on error
        if pdf_document:
            try:
                pdf_document.close()
            except:
                pass
        if pdf_content:
            try:
                pdf_content.close()
            except:
                pass
            
        return jsonify({'error': str(e)}), 500 