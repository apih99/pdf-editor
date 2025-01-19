# Deployment Guide for PDF Editor

This guide provides step-by-step instructions for deploying the PDF Editor application on an Ubuntu EC2 instance with Nginx, SSL, and automated Git updates.

## Prerequisites
- An AWS account with an EC2 instance running Ubuntu
- A domain or subdomain pointing to your EC2 instance
- Basic knowledge of Linux commands
- GitHub repository access

## 1. Initial Server Setup

### 1.1 Connect to EC2
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 1.2 Update System Packages
```bash
sudo apt update
sudo apt upgrade -y
```

### 1.3 Install Required Packages
```bash
sudo apt install python3-pip python3-venv nginx certbot python3-certbot-nginx -y
```

## 2. Application Setup

### 2.1 Set Up GitHub SSH Access
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your-email@example.com"

# Start SSH agent and add key
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Display public key (add this to GitHub)
cat ~/.ssh/id_ed25519.pub
```

Add the SSH key to GitHub:
1. Go to GitHub.com → Settings → SSH and GPG keys
2. Click "New SSH key"
3. Title: "EC2 PDF Editor Deploy Key"
4. Key: Paste the output from `cat ~/.ssh/id_ed25519.pub`
5. Click "Add SSH key"

Test the connection:
```bash
ssh -T git@github.com
```

### 2.2 Clone Repository
```bash
cd /home/ubuntu
git clone git@github.com:yourusername/pdf-editor.git
cd pdf-editor

# Set correct ownership
sudo chown -R ubuntu:ubuntu /home/ubuntu/pdf-editor
```

### 2.3 Set Up Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

## 3. Gunicorn Configuration

### 3.1 Create Systemd Service
```bash
sudo vim /etc/systemd/system/pdf-editor.service
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

### 3.2 Start and Enable Service
```bash
sudo systemctl start pdf-editor
sudo systemctl enable pdf-editor
```

## 4. Nginx Configuration

### 4.1 Create Nginx Configuration
```bash
sudo vim /etc/nginx/sites-available/pdf-editor
```

Add the following configuration:
```nginx
server {
    server_name your.domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 16M;
}
```

### 4.2 Enable Site Configuration
```bash
sudo ln -s /etc/nginx/sites-available/pdf-editor /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

## 5. SSL Configuration

### 5.1 Set Up SSL with Certbot
```bash
sudo certbot --nginx -d your.domain.com
```

### 5.2 Configure Firewall
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 6. Automated Git Updates

### 6.1 Simple Update Script
Create an update script:
```bash
sudo vim /home/ubuntu/update-pdf-editor.sh
```

Add the following content:
```bash
#!/bin/bash
cd /home/ubuntu/pdf-editor
git pull origin main
sudo systemctl restart pdf-editor
```

Make it executable:
```bash
chmod +x /home/ubuntu/update-pdf-editor.sh
```

### 6.2 Webhook Setup (Automated Updates)

Install webhook:
```bash
sudo apt-get install webhook
```

Create webhook script:
```bash
sudo vim /home/ubuntu/pdf-editor-webhook.sh
```

Add content:
```bash
#!/bin/bash
# Run as ubuntu user
if [ "$(id -u)" = "0" ]; then
    exec sudo -u ubuntu "$0" "$@"
    exit
fi

# Setup SSH agent
export HOME=/home/ubuntu
eval "$(ssh-agent -s)"
ssh-add /home/ubuntu/.ssh/id_ed25519

cd /home/ubuntu/pdf-editor
git pull origin main

# Restart service (this needs sudo)
sudo systemctl restart pdf-editor

# Kill SSH agent
kill $SSH_AGENT_PID
```

Set correct permissions:
```bash
sudo chown ubuntu:ubuntu /home/ubuntu/pdf-editor-webhook.sh
sudo chmod 755 /home/ubuntu/pdf-editor-webhook.sh
```

Test the webhook script:
```bash
# Test as ubuntu user
./pdf-editor-webhook.sh

# Test with sudo (should still work)
sudo ./pdf-editor-webhook.sh
```

Create webhook configuration:
```bash
sudo mkdir /etc/webhook
sudo vim /etc/webhook/hooks.json
```

Add configuration:
```json
[
  {
    "id": "pdf-editor-deploy",
    "execute-command": "/home/ubuntu/pdf-editor-webhook.sh",
    "command-working-directory": "/home/ubuntu/pdf-editor"
  }
]
```

Create webhook service:
```bash
sudo vim /etc/systemd/system/webhook.service
```

Add content:
```ini
[Unit]
Description=Webhook for PDF Editor
After=network.target

[Service]
ExecStart=/usr/bin/webhook -hooks /etc/webhook/hooks.json -verbose -ip "0.0.0.0" -port 9000
WorkingDirectory=/home/ubuntu

[Install]
WantedBy=multi-user.target
```

Start and enable webhook:
```bash
sudo systemctl start webhook
sudo systemctl enable webhook
```

## 7. GitHub Webhook Configuration

1. Go to your GitHub repository
2. Navigate to Settings > Webhooks
3. Click "Add webhook"
4. Configure webhook:
   - Payload URL: `http://your.domain.com:9000/hooks/pdf-editor-deploy`
   - Content type: `application/json`
   - Select "Just the push event"
   - Save webhook

## 8. Security Considerations

1. EC2 Security Group:
   - Allow HTTP (80)
   - Allow HTTPS (443)
   - Allow SSH (22)
   - Allow Webhook port (9000) if using webhooks

2. File Permissions:
```bash
sudo chown -R ubuntu:ubuntu /home/ubuntu/pdf-editor
chmod -R 755 /home/ubuntu/pdf-editor
```

## 9. Troubleshooting

### Check Application Status
```bash
sudo systemctl status pdf-editor
```

### View Application Logs
```bash
sudo journalctl -u pdf-editor -f
```

### Check Nginx Logs
```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Common Issues
1. **502 Bad Gateway**: Check if gunicorn is running
2. **Permission Issues**: Verify file permissions
3. **SSL Issues**: Check certbot configuration
4. **Git Pull Fails**: 
   - Check if SSH key is properly set up
   - Ensure git commands are run as ubuntu user, not root
   - Verify repository permissions: `sudo chown -R ubuntu:ubuntu /home/ubuntu/pdf-editor`
   - Test SSH connection: `ssh -T git@github.com`
5. **Webhook Connection Failed**: Follow these steps:
   ```bash
   # 1. Check webhook service status
   sudo systemctl status webhook
   
   # 2. Verify webhook is listening
   sudo netstat -tlpn | grep webhook
   
   # 3. Check webhook logs
   sudo journalctl -u webhook -f
   
   # 4. Ensure port 9000 is open
   sudo ufw status
   
   # 5. Test webhook locally
   curl -X POST http://localhost:9000/hooks/pdf-editor-deploy
   
   # 6. Check EC2 security group
   # Make sure inbound rule for port 9000 is added
   
   # 7. Check webhook script permissions
   ls -la /home/ubuntu/pdf-editor-webhook.sh
   
   # 8. Verify git repository permissions
   ls -la /home/ubuntu/pdf-editor
   ```

## 10. Maintenance

### Regular Updates
```bash
sudo apt update
sudo apt upgrade -y
```

### SSL Renewal
Certbot automatically renews certificates. To force renewal:
```bash
sudo certbot renew
```

### Backup Configuration
Regularly backup these files:
- `/etc/nginx/sites-available/pdf-editor`
- `/etc/systemd/system/pdf-editor.service`
- `/etc/webhook/hooks.json` (if using webhooks)

## Railway Deployment Guide

### Prerequisites
- A GitHub account
- A Railway account (sign up at railway.app)
- Your project pushed to GitHub

### 1. Project Setup

1. Create a new file named `Procfile` in your project root:
```bash
web: gunicorn app:app
```

2. Create a `runtime.txt` file to specify Python version:
```bash
python-3.9.18
```

3. Update your `requirements.txt` to ensure all dependencies are listed:
```txt
Flask==2.0.1
PyPDF2==3.0.1
Werkzeug==2.0.1
python-dotenv==0.19.0
PyMuPDF==1.23.8
Pillow==10.2.0
gunicorn==21.2.0
```

### 2. Railway Setup

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your PDF Editor repository
5. Railway will automatically detect your Python project

### 3. Environment Setup

1. In Railway dashboard, go to your project settings
2. Add the following environment variables:
   - `PYTHON_VERSION`: 3.9.18
   - `FLASK_APP`: app.py
   - `FLASK_ENV`: production

### 4. Deployment

Railway will automatically:
1. Detect your Python project
2. Install dependencies from requirements.txt
3. Run the Procfile command
4. Assign a domain to your project

### 5. Custom Domain (Optional)

1. In Railway dashboard, go to your project
2. Click on "Settings"
3. Navigate to "Domains"
4. Click "Generate Domain" or "Add Custom Domain"
5. Follow the DNS configuration instructions if using a custom domain

### 6. Monitoring

1. View logs in Railway dashboard:
   - Go to your project
   - Click "Deployments"
   - Select current deployment
   - View real-time logs

2. Monitor application metrics:
   - CPU usage
   - Memory usage
   - Request logs

### 7. Automatic Deployments

Railway automatically deploys when you:
1. Push to your GitHub repository
2. Merge pull requests
3. Make changes through the Railway CLI

### 8. Troubleshooting

1. **Build Failures**:
   - Check build logs in Railway dashboard
   - Verify requirements.txt is complete
   - Ensure Python version is correct

2. **Runtime Errors**:
   - Check application logs
   - Verify environment variables
   - Check resource limits

3. **Common Issues**:
   ```bash
   # If your app crashes, check logs:
   railway logs

   # If you need to restart:
   railway up

   # To check status:
   railway status
   ```

### 9. Best Practices

1. **Security**:
   - Never commit sensitive data
   - Use environment variables for secrets
   - Keep dependencies updated

2. **Performance**:
   - Set appropriate gunicorn workers
   - Configure proper timeouts
   - Monitor memory usage

3. **Maintenance**:
   - Regularly update dependencies
   - Monitor application logs
   - Set up alerts for errors

### 10. Railway CLI (Optional)

1. Install Railway CLI:
```bash
# macOS or Linux
brew install railway

# Windows
scoop install railway
```

2. Login to Railway:
```bash
railway login
```

3. Link your project:
```bash
railway link
```

4. Common commands:
```bash
# Deploy your project
railway up

# View logs
railway logs

# Open dashboard
railway open

# List environment variables
railway variables
```

### 11. Cost Management

1. Monitor usage in Railway dashboard
2. Set up usage alerts
3. Configure auto-scaling limits
4. Review pricing tiers regularly

Remember to:
- Keep your repository up to date
- Monitor application logs
- Set up proper error notifications
- Regularly update dependencies
- Back up your data if needed

For more information, visit [Railway Documentation](https://docs.railway.app/)