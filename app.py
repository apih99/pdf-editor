import os
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import io

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
        # Read the PDF
        pdf_reader = PdfReader(file)
        pdf_writer = PdfWriter()

        # Copy pages with reduced quality
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)

        # Create output PDF in memory
        output_pdf = io.BytesIO()
        pdf_writer.write(output_pdf)
        output_pdf.seek(0)

        # Create compressed filename
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

if __name__ == '__main__':
    app.run(debug=True) 