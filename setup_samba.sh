#!/bin/bash

# Samba setup script for script_creator3 folder
# Run this script with sudo: sudo bash setup_samba.sh

echo "Setting up Samba share for script_creator3..."

# Install Samba if not present
echo "Checking/Installing Samba packages..."
if ! rpm -qa | grep -q "^samba-[0-9]"; then
    dnf install -y samba samba-common samba-client
else
    echo "Samba is already installed"
fi

# Create system user 'd' if it doesn't exist
if ! id "d" &>/dev/null; then
    echo "Creating system user 'd'..."
    useradd -M -s /sbin/nologin d
fi

# Set Samba password for user 'd'
echo "Setting Samba password for user 'd'..."
echo -e "d\nd" | smbpasswd -a -s d

# Backup original smb.conf
cp /etc/samba/smb.conf /etc/samba/smb.conf.backup

# Add share configuration to smb.conf
echo "Configuring Samba share..."
cat >> /etc/samba/smb.conf << 'EOF'

[script_creator3]
    comment = Script Creator 3 Django Project
    path = /home/dani/laika/script_creator3
    browseable = yes
    writable = yes
    valid users = d
    create mask = 0777
    directory mask = 0777
    force create mode = 0777
    force directory mode = 0777
    force user = dani
    force group = dani
EOF

# Set full permissions on the folder
echo "Setting permissions on folder..."
chmod -R 777 /home/dani/laika/script_creator3
chown -R dani:dani /home/dani/laika/script_creator3

# Set SELinux context if SELinux is enabled
if command -v getenforce &> /dev/null && [ "$(getenforce)" != "Disabled" ]; then
    echo "Configuring SELinux..."
    setsebool -P samba_enable_home_dirs on
    chcon -t samba_share_t /home/dani/laika/script_creator3
fi

# Configure firewall
echo "Configuring firewall..."
firewall-cmd --permanent --add-service=samba
firewall-cmd --reload

# Enable and start Samba service
echo "Starting Samba service..."
systemctl enable smb nmb
systemctl restart smb nmb

# Test configuration
echo "Testing configuration..."
testparm -s

echo ""
echo "Samba setup complete!"
echo "Share details:"
echo "  Share name: script_creator3"
echo "  Path: /home/dani/laika/script_creator3"
echo "  Username: d"
echo "  Password: d"
echo ""
echo "Access the share from:"
echo "  Windows: \\\\$(hostname -I | awk '{print $1}')\\script_creator3"
echo "  Linux: smb://$(hostname -I | awk '{print $1}')/script_creator3"