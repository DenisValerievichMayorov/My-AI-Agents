#!/bin/bash
mkdir -p ~/.ssh
cat ~/Sync/chromebook_ssh_key.pub >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
pkg install openssh -y
sshd
echo "SSH Setup complete!"
