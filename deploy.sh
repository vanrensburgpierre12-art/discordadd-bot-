#!/bin/bash

# Discord Rewards Platform Deployment Script
# This script automates the deployment process on a VPS or server

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="rewards-platform"
APP_DIR="/opt/$APP_NAME"
SERVICE_USER="www-data"
PYTHON_VERSION="3.9"

# Logging
LOG_FILE="/var/log/$APP_NAME-deploy.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo -e "${BLUE}🚀 Starting Discord Rewards Platform Deployment${NC}"
echo "Timestamp: $(date)"
echo "Log file: $LOG_FILE"

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_error "This script should not be run as root. Please run as a regular user with sudo privileges."
    exit 1
fi

# Check if sudo is available
if ! command -v sudo &> /dev/null; then
    print_error "sudo is not available. Please install it first."
    exit 1
fi

print_info "Checking system requirements..."

# Update system packages
print_info "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
print_info "Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential

# Install additional system dependencies
sudo apt install -y nginx sqlite3 curl wget git

print_status "System packages installed successfully"

# Create application directory
print_info "Setting up application directory..."
sudo mkdir -p "$APP_DIR"
sudo chown "$USER:$USER" "$APP_DIR"

# Copy application files
print_info "Copying application files..."
cp -r . "$APP_DIR/"
cd "$APP_DIR"

# Set up Python virtual environment
print_info "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
print_info "Installing Python dependencies..."
pip install -r requirements.txt

print_status "Python environment setup complete"

# Set up environment file
print_info "Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    print_warning "Please edit .env file with your configuration before starting the service"
    print_info "Required variables: DISCORD_TOKEN, WEBHOOK_SECRET, WEBHOOK_URL"
else
    print_status "Environment file already exists"
fi

# Set proper permissions
print_info "Setting file permissions..."
sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"
sudo chmod -R 755 "$APP_DIR"
sudo chmod 600 "$APP_DIR/.env"

# Create systemd service
print_info "Creating systemd service..."
sudo tee /etc/systemd/system/$APP_NAME.service > /dev/null <<EOF
[Unit]
Description=Discord Rewards Platform
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
Environment=PYTHONPATH=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_DIR

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
print_info "Enabling systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable $APP_NAME

# Create nginx configuration (optional)
print_info "Setting up nginx configuration..."
sudo tee /etc/nginx/sites-available/$APP_NAME > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable nginx site
sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
if sudo nginx -t; then
    sudo systemctl restart nginx
    print_status "Nginx configuration applied successfully"
else
    print_warning "Nginx configuration test failed. Please check the configuration manually."
fi

# Create log directory
sudo mkdir -p /var/log/$APP_NAME
sudo chown $SERVICE_USER:$SERVICE_USER /var/log/$APP_NAME

# Create database directory
sudo mkdir -p /var/lib/$APP_NAME
sudo chown $SERVICE_USER:$SERVICE_USER /var/lib/$APP_NAME

# Set up firewall (if ufw is available)
if command -v ufw &> /dev/null; then
    print_info "Configuring firewall..."
    sudo ufw allow 22/tcp  # SSH
    sudo ufw allow 80/tcp  # HTTP
    sudo ufw allow 443/tcp # HTTPS
    sudo ufw --force enable
    print_status "Firewall configured"
fi

# Create backup script
print_info "Creating backup script..."
sudo tee /usr/local/bin/backup-$APP_NAME > /dev/null <<EOF
#!/bin/bash
BACKUP_DIR="/var/backups/$APP_NAME"
DATE=\$(date +%Y%m%d_%H%M%S)
mkdir -p \$BACKUP_DIR

# Backup database
if [ -f $APP_DIR/rewards.db ]; then
    cp $APP_DIR/rewards.db \$BACKUP_DIR/rewards_\$DATE.db
fi

# Backup configuration
cp $APP_DIR/.env \$BACKUP_DIR/env_\$DATE.backup

# Cleanup old backups (keep last 7 days)
find \$BACKUP_DIR -name "*.db" -mtime +7 -delete
find \$BACKUP_DIR -name "*.backup" -mtime +7 -delete

echo "Backup completed: \$BACKUP_DIR"
EOF

sudo chmod +x /usr/local/bin/backup-$APP_NAME

# Create log rotation
print_info "Setting up log rotation..."
sudo tee /etc/logrotate.d/$APP_NAME > /dev/null <<EOF
/var/log/$APP_NAME/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_USER $SERVICE_USER
    postrotate
        systemctl reload $APP_NAME > /dev/null 2>&1 || true
    endscript
}
EOF

# Create monitoring script
print_info "Creating monitoring script..."
sudo tee /usr/local/bin/monitor-$APP_NAME > /dev/null <<EOF
#!/bin/bash
# Simple monitoring script for the rewards platform

echo "=== Discord Rewards Platform Status ==="
echo "Timestamp: \$(date)"

# Check service status
echo -n "Service Status: "
if systemctl is-active --quiet $APP_NAME; then
    echo "✅ Running"
else
    echo "❌ Stopped"
fi

# Check database
if [ -f $APP_DIR/rewards.db ]; then
    echo "Database: ✅ Exists"
    DB_SIZE=\$(du -h $APP_DIR/rewards.db | cut -f1)
    echo "Database Size: \$DB_SIZE"
else
    echo "Database: ❌ Missing"
fi

# Check logs
echo -n "Recent Errors: "
ERROR_COUNT=\$(journalctl -u $APP_NAME --since "1 hour ago" | grep -i error | wc -l)
echo "\$ERROR_COUNT in last hour"

# Check disk space
echo -n "Disk Space: "
df -h $APP_DIR | tail -1 | awk '{print \$5}'

echo "================================"
EOF

sudo chmod +x /usr/local/bin/monitor-$APP_NAME

# Final setup
print_info "Finalizing setup..."

# Start the service
print_info "Starting the service..."
sudo systemctl start $APP_NAME

# Wait a moment for the service to start
sleep 5

# Check service status
if systemctl is-active --quiet $APP_NAME; then
    print_status "Service started successfully!"
else
    print_error "Service failed to start. Check logs with: sudo journalctl -u $APP_NAME -f"
    exit 1
fi

# Display final information
echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo "Service Information:"
echo "  - Service Name: $APP_NAME"
echo "  - Status: $(systemctl is-active $APP_NAME)"
echo "  - Logs: sudo journalctl -u $APP_NAME -f"
echo "  - Configuration: $APP_DIR/.env"
echo ""
echo "Useful Commands:"
echo "  - Start/Stop: sudo systemctl start/stop $APP_NAME"
echo "  - Restart: sudo systemctl restart $APP_NAME"
echo "  - Status: sudo systemctl status $APP_NAME"
echo "  - Monitor: /usr/local/bin/monitor-$APP_NAME"
echo "  - Backup: /usr/local/bin/backup-$APP_NAME"
echo ""
echo "Next Steps:"
echo "  1. Edit $APP_DIR/.env with your configuration"
echo "  2. Restart the service: sudo systemctl restart $APP_NAME"
echo "  3. Test the webhook endpoint: curl http://your-server-ip/"
echo "  4. Check service logs for any errors"
echo ""
echo "Log file: $LOG_FILE"
echo "Deployment completed at: $(date)"