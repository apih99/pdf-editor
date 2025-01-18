# PDF Editor Web Application

A modern, sleek web application for PDF manipulation with a dark theme and red accents. Built with Flask and modern web technologies, this application provides a user-friendly interface for common PDF operations.

![PDF Editor Interface](docs/interface.png)

## 🚀 Features

### PDF Compression
- Drag & drop interface for file upload
- Visual feedback during file selection
- Automatic file naming (compressed_filename.pdf)
- In-memory compression without server storage
- Support for large PDF files (up to 16MB)

### PDF Merger
- Multiple file upload support
- Interactive drag & drop reordering
- Visual position indicators
- File name preview
- Maintains original PDF quality
- Delete individual files from merge list

## 💻 Tech Stack

### Frontend
- HTML5 with modern semantic elements
- Tailwind CSS for styling
- Bebas Neue font for typography
- Font Awesome icons
- Vanilla JavaScript with modern ES6+ features
- Drag & Drop API implementation

### Backend
- Python 3.x
- Flask web framework
- PyPDF2 for PDF manipulation
- Werkzeug for file handling
- In-memory file processing

## 🛠️ Local Installation

1. Clone the repository:
```bash
git clone https://github.com/apih99/pdf-editor.git
cd pdf-editor
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application locally:
```bash
python app.py
```

5. Open your browser and navigate to:
```
http://localhost:5000
```

## 🚀 AWS EC2 Deployment

### Prerequisites
- An AWS account
- EC2 instance running Ubuntu
- Basic knowledge of SSH and Linux commands

### Server Setup

1. Connect to your EC2 instance:
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

2. Update system packages:
```bash
sudo apt update
sudo apt upgrade -y
```

3. Install required system packages:
```bash
sudo apt install python3-pip python3-venv nginx -y
```

4. Clone the repository:
```bash
git clone https://github.com/apih99/pdf-editor.git
cd pdf-editor
```

5. Set up Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

6. Create a systemd service file:
```bash
sudo nano /etc/systemd/system/pdf-editor.service
```

Add the following content:
```ini
[Unit]
Description=PDF Editor Flask Application
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/pdf-editor
Environment="PATH=/home/ubuntu/pdf-editor/venv/bin"
ExecStart=/home/ubuntu/pdf-editor/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app

[Install]
WantedBy=multi-user.target
```

7. Configure Nginx:
```bash
sudo nano /etc/nginx/sites-available/pdf-editor
```

Add the following configuration:
```nginx
server {
    listen 80;
    server_name your_domain_or_ip;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

8. Enable the Nginx configuration:
```bash
sudo ln -s /etc/nginx/sites-available/pdf-editor /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

9. Start the application:
```bash
sudo systemctl start pdf-editor
sudo systemctl enable pdf-editor
```

### Directory Structure
Ensure your directory structure looks like this:
```
/home/ubuntu/pdf-editor/
├── app.py
├── requirements.txt
├── templates/
│   └── index.html
├── static/
│   └── [static files if any]
└── venv/
```

### Troubleshooting

1. Check application status:
```bash
sudo systemctl status pdf-editor
```

2. View application logs:
```bash
sudo journalctl -u pdf-editor -f
```

3. Check Nginx logs:
```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

4. Common issues and solutions:
- **Template not found**: Ensure the `templates` directory is in the correct location
- **Permission issues**: Check file permissions with `ls -la`
- **Port in use**: Check if port 8000 is free with `sudo lsof -i :8000`
- **Nginx 502 Bad Gateway**: Check if gunicorn is running properly

5. Security considerations:
```bash
# Set proper permissions
sudo chown -R ubuntu:ubuntu /home/ubuntu/pdf-editor
chmod -R 755 /home/ubuntu/pdf-editor

# Configure firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 📝 Usage

### Compressing PDFs
1. Navigate to the "COMPRESS PDF" section
2. Either drag & drop your PDF file or click "CHOOSE FILE"
3. Once a file is selected, it will be displayed with its name
4. Click "COMPRESS PDF" to process
5. The compressed file will automatically download with the prefix "compressed_"

### Merging PDFs
1. Go to the "MERGE PDFs" section
2. Upload multiple PDF files using drag & drop or file selector
3. Rearrange files by dragging them into the desired order
4. Remove unwanted files using the delete button (×)
5. Click "MERGE PDFs" to combine files
6. The merged file will automatically download as "merged.pdf"

## ⚙️ Configuration

The application has several configurable parameters in `app.py`:

```python
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'              # Temporary upload directory
```

## 🎨 Customization

The interface uses CSS variables for easy theme customization:

```css
:root {
    --primary-red: #FF1E1E;    /* Primary accent color */
    --dark-red: #CC0000;       /* Secondary accent color */
    --bg-dark: #0A0A0A;        /* Background color */
    --card-dark: #1A1A1A;      /* Card background color */
    --border-dark: #2A2A2A;    /* Border color */
}
```

## 🔒 Security Features

- File type validation
- Maximum file size limit
- Secure filename handling
- No server-side file storage
- Input sanitization
- Error handling for all operations

## 🤝 Contributing

1. Fork the repository
2. Create a new branch: `git checkout -b feature-name`
3. Make your changes and commit: `git commit -m 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Flask](https://flask.palletsprojects.com/) for the web framework
- [PyPDF2](https://pypdf2.readthedocs.io/) for PDF manipulation
- [Tailwind CSS](https://tailwindcss.com/) for styling
- [Font Awesome](https://fontawesome.com/) for icons
- [Bebas Neue](https://fonts.google.com/specimen/Bebas+Neue) for typography 