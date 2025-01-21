import io
from flask import send_file, jsonify
from PyPDF2 import PdfMerger
from utils.file_handling import validate_pdf_file

def handle_merger(request):
    """Handle PDF merger request"""
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
        
        # Validate and append files in the specified order
        for file, _ in file_order:
            # Validate each file
            is_valid, error_message = validate_pdf_file(file)
            if not is_valid:
                return jsonify({'error': f'Invalid file {file.filename}: {error_message}'}), 400
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