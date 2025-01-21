import io
import os
import logging
from flask import send_file, jsonify
from werkzeug.utils import secure_filename
import markdown
import pdfkit
from utils.file_handling import get_file_size_mb

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def check_wkhtmltopdf():
    """Check if wkhtmltopdf is installed and accessible"""
    try:
        path = pdfkit.configuration()
        if not path:
            return False, "wkhtmltopdf not found in system PATH"
        return True, None
    except Exception as e:
        return False, f"Error checking wkhtmltopdf: {str(e)}"

def validate_md_file(file):
    """Validate Markdown file upload
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        if not file:
            return False, 'No file provided'

        if file.filename == '':
            return False, 'No file selected'

        if not file.filename.lower().endswith(('.md', '.markdown')):
            return False, 'File must be a Markdown document'
            
        # Try to read the file content to verify it's valid
        try:
            content = file.read().decode('utf-8')
            file.seek(0)  # Reset file pointer after reading
            return True, None
        except UnicodeDecodeError:
            return False, 'File is not a valid text document'
            
    except Exception as e:
        logger.error(f"Error validating markdown file: {str(e)}")
        return False, f'Error validating file: {str(e)}'

def handle_md_to_pdf(request):
    """Handle Markdown to PDF conversion request"""
    try:
        logger.info("Starting Markdown to PDF conversion")
        
        # Check wkhtmltopdf installation
        wkhtmltopdf_ok, error_msg = check_wkhtmltopdf()
        if not wkhtmltopdf_ok:
            logger.error(f"wkhtmltopdf check failed: {error_msg}")
            return jsonify({'error': f'PDF conversion tool not available: {error_msg}'}), 500

        # Validate request
        if 'file' not in request.files:
            logger.error("No file in request")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        logger.info(f"Processing file: {file.filename}")
        
        # Validate file
        is_valid, error_message = validate_md_file(file)
        if not is_valid:
            logger.error(f"File validation failed: {error_message}")
            return jsonify({'error': error_message}), 400

        # Read markdown content
        try:
            md_content = file.read().decode('utf-8')
            logger.debug(f"Successfully read markdown content, length: {len(md_content)}")
        except Exception as e:
            logger.error(f"Error reading markdown content: {str(e)}")
            return jsonify({'error': f'Error reading markdown content: {str(e)}'}), 400
        
        # Convert markdown to HTML
        try:
            html_content = markdown.markdown(
                md_content,
                extensions=['extra', 'codehilite', 'tables', 'toc']
            )
            logger.debug(f"Successfully converted to HTML, length: {len(html_content)}")
        except Exception as e:
            logger.error(f"Error converting markdown to HTML: {str(e)}")
            return jsonify({'error': f'Error converting markdown to HTML: {str(e)}'}), 500
        
        # Add CSS for better styling
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                code {{
                    background-color: #f4f4f4;
                    padding: 2px 4px;
                    border-radius: 4px;
                    font-family: monospace;
                }}
                pre {{
                    background-color: #f4f4f4;
                    padding: 10px;
                    border-radius: 4px;
                    overflow-x: auto;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 15px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f4f4f4;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    color: #333;
                    margin-top: 24px;
                    margin-bottom: 16px;
                }}
                blockquote {{
                    border-left: 4px solid #ddd;
                    margin: 0;
                    padding-left: 16px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        logger.info("Converting HTML to PDF")
        # Convert HTML to PDF with detailed error handling
        try:
            pdf_content = pdfkit.from_string(
                styled_html,
                False,
                options={
                    'encoding': 'UTF-8',
                    'page-size': 'A4',
                    'margin-top': '20mm',
                    'margin-right': '20mm',
                    'margin-bottom': '20mm',
                    'margin-left': '20mm',
                    'enable-local-file-access': None,
                    'quiet': '',
                    'no-outline': None,
                    'disable-smart-shrinking': None
                }
            )
            logger.debug(f"Successfully generated PDF, size: {len(pdf_content)} bytes")
        except Exception as e:
            logger.error(f"Error converting HTML to PDF: {str(e)}")
            return jsonify({'error': f'Error converting to PDF: {str(e)}'}), 500
        
        # Create PDF buffer
        try:
            pdf_buffer = io.BytesIO(pdf_content)
            pdf_buffer.seek(0)
            logger.info("Successfully created PDF buffer")
        except Exception as e:
            logger.error(f"Error creating PDF buffer: {str(e)}")
            return jsonify({'error': f'Error preparing PDF: {str(e)}'}), 500
        
        # Prepare filename
        original_filename = secure_filename(file.filename)
        filename_without_ext = os.path.splitext(original_filename)[0]
        pdf_filename = f'{filename_without_ext}.pdf'
        
        logger.info(f"Sending PDF file: {pdf_filename}")
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=pdf_filename
        )

    except Exception as e:
        logger.error(f"Unexpected error in handle_md_to_pdf: {str(e)}", exc_info=True)
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500 