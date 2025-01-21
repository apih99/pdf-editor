import os
from flask import Flask, render_template, request
from features.compression import handle_compression
from features.merger import handle_merger
from features.converter import handle_conversion
from features.md_converter import handle_md_to_pdf

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compress', methods=['POST'])
def compress_pdf():
    return handle_compression(request=request, upload_folder=app.config['UPLOAD_FOLDER'])

@app.route('/merge', methods=['POST'])
def merge_pdf():
    return handle_merger(request=request)

@app.route('/convert-to-images', methods=['POST'])
def convert_to_images():
    return handle_conversion(request=request)

@app.route('/md-to-pdf', methods=['POST'])
def md_to_pdf():
    return handle_md_to_pdf(request=request)

if __name__ == '__main__':
    app.run(debug=True) 