#!/bin/bash
#
# VNC Monitor Installation Script
# This script installs the VNC monitoring service on the system
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Installation paths
INSTALL_DIR="/opt/vnc-monitoring"
SERVICE_FILE="/etc/systemd/system/vnc-monitor.service"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

install_dependencies() {
    log_info "Installing dependencies..."
    
    # Check if we're on Ubuntu/Debian or CentOS/RHEL
    if command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y python3 python3-pip tigervnc-standalone-server
    elif command -v yum &> /dev/null; then
        yum update -y
        yum install -y python3 python3-pip tigervnc-server
    elif command -v dnf &> /dev/null; then
        dnf update -y
        dnf install -y python3 python3-pip tigervnc-server
    else
        log_warn "Package manager not detected. Please install python3 and tigervnc-server manually"
    fi
}

create_directories() {
    log_info "Creating installation directories..."
    mkdir -p "$INSTALL_DIR"
    mkdir -p "/var/log"
}

copy_files() {
    log_info "Copying files to installation directory..."
    cp "$SCRIPT_DIR/vnc_monitor.py" "$INSTALL_DIR/"
    cp "$SCRIPT_DIR/vnc_monitor.conf" "$INSTALL_DIR/"
    
    # Make script executable
    chmod +x "$INSTALL_DIR/vnc_monitor.py"
    
    # Copy service file
    cp "$SCRIPT_DIR/vnc-monitor.service" "$SERVICE_FILE"
}

setup_service() {
    log_info "Setting up systemd service..."
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable service
    systemctl enable vnc-monitor.service
    
    log_info "VNC Monitor service has been enabled"
}

show_usage() {
    echo "VNC Monitor Installation Complete!"
    echo ""
    echo "Usage:"
    echo "  Start service:    sudo systemctl start vnc-monitor"
    echo "  Stop service:     sudo systemctl stop vnc-monitor"
    echo "  Restart service:  sudo systemctl restart vnc-monitor"
    echo "  Check status:     sudo systemctl status vnc-monitor"
    echo "  View logs:        sudo journalctl -u vnc-monitor -f"
    echo ""
    echo "Configuration file: $INSTALL_DIR/vnc_monitor.conf"
    echo "Log file: /var/log/vnc_monitor.log"
    echo ""
    echo "To start the service now, run:"
    echo "  sudo systemctl start vnc-monitor"
}

main() {
    log_info "Starting VNC Monitor installation..."
    
    check_root
    install_dependencies
    create_directories
    copy_files
    setup_service
    
    log_info "Installation completed successfully!"
    echo ""
    show_usage
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "VNC Monitor Installation Script"
        echo ""
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --uninstall    Uninstall VNC Monitor"
        echo ""
        exit 0
        ;;
    --uninstall)
        log_info "Uninstalling VNC Monitor..."
        systemctl stop vnc-monitor.service || true
        systemctl disable vnc-monitor.service || true
        rm -f "$SERVICE_FILE"
        rm -rf "$INSTALL_DIR"
        systemctl daemon-reload
        log_info "VNC Monitor uninstalled successfully"
        exit 0
        ;;
    "")
        main
        ;;
    *)
        log_error "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac