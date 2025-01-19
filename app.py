import os
from flask import Flask, render_template, request, send_file, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import io
from PIL import Image
import fitz  # PyMuPDF
import zipfile
import time

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_file_size_mb(file_obj):
    if isinstance(file_obj, io.BytesIO):
        return len(file_obj.getvalue()) / (1024 * 1024)
    else:
        return os.path.getsize(file_obj) / (1024 * 1024)

def compress_pdf_file(input_path, target_size_mb=2):
    # Get original file size
    original_size = get_file_size_mb(input_path)
    print(f"Original size: {original_size:.2f} MB")

    # Open the PDF
    pdf_document = fitz.open(input_path)
    output_pdf = io.BytesIO()

    # Compression settings
    image_compression_quality = 20  # Start with 20% quality
    max_image_size = 800  # Maximum dimension for images

    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        
        # Get all images on the page
        image_list = page.get_images()
        
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_data = base_image["image"]
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Resize if too large
            if max(image.size) > max_image_size:
                ratio = max_image_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Compress image
            output_buffer = io.BytesIO()
            if image.mode in ['RGBA', 'LA']:
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
            
            image.save(output_buffer, format="JPEG", quality=image_compression_quality, optimize=True)
            page.replace_image(xref, stream=output_buffer.getvalue())

    # Save the compressed PDF
    pdf_document.save(output_pdf, garbage=4, deflate=True, clean=True)
    compressed_size = get_file_size_mb(output_pdf)
    
    # Calculate compression ratio
    compression_ratio = ((original_size - compressed_size) / original_size) * 100
    print(f"Compressed size: {compressed_size:.2f} MB")
    print(f"Compression ratio: {compression_ratio:.1f}%")
    
    # If we haven't achieved desired compression, try again with more aggressive settings
    if compressed_size > target_size_mb and image_compression_quality > 5:
        print("Target size not achieved, trying with more aggressive compression...")
        image_compression_quality -= 5
        max_image_size = int(max_image_size * 0.8)
        return compress_pdf_file(input_path, target_size_mb)
    
    return output_pdf

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compress', methods=['POST'])
def compress_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'}), 400

    try:
        # Save uploaded file temporarily
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp.pdf')
        file.save(temp_path)
        
        # Compress the PDF
        output_pdf = compress_pdf_file(temp_path, target_size_mb=2)
        
        # Clean up
        os.remove(temp_path)
        
        # Prepare response
        output_pdf.seek(0)
        original_filename = secure_filename(file.filename)
        filename_without_ext = os.path.splitext(original_filename)[0]
        compressed_filename = f'compressed_{filename_without_ext}.pdf'

        return send_file(
            output_pdf,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=compressed_filename
        )

    except Exception as e:
        # Clean up on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({'error': str(e)}), 500

@app.route('/merge', methods=['POST'])
def merge_pdf():
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files[]')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400

    try:
        merger = PdfMerger()
        
        # Get the order of files
        order = request.form.getlist('order[]')
        if not order:
            order = range(len(files))
        
        # Create a list of (file, order) tuples and sort by order
        file_order = list(zip(files, map(int, order)))
        file_order.sort(key=lambda x: x[1])
        
        # Append files in the specified order
        for file, _ in file_order:
            if not file.filename.lower().endswith('.pdf'):
                return jsonify({'error': 'All files must be PDFs'}), 400
            merger.append(file)

        # Create output PDF in memory
        output_pdf = io.BytesIO()
        merger.write(output_pdf)
        merger.close()
        output_pdf.seek(0)

        return send_file(
            output_pdf,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='merged.pdf'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/convert-to-images', methods=['POST'])
def convert_to_images():
    pdf_document = None
    pdf_content = None
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        format = request.form.get('format', 'png').lower()
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'File must be a PDF'}), 400

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
            
        app.logger.error(f"PDF conversion error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 