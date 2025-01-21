import os
import io
from flask import send_file, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import fitz
from utils.file_handling import get_file_size_mb, validate_pdf_file

def compress_pdf_file(input_path, target_size_mb=2):
    """Compress PDF file to target size"""
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

def handle_compression(request, upload_folder):
    """Handle PDF compression request"""
    try:
        # Validate request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Validate file
        is_valid, error_message = validate_pdf_file(file)
        if not is_valid:
            return jsonify({'error': error_message}), 400

        # Save uploaded file temporarily
        temp_path = os.path.join(upload_folder, 'temp.pdf')
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