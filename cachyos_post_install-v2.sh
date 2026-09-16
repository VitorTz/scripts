#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting CachyOS post-installation setup..."

# 0. Optimize pacman configurations
echo "Optimizing pacman configurations (enabling parallel downloads)..."
sudo sed -i 's/^#ParallelDownloads/ParallelDownloads/' /etc/pacman.conf

# 1. Create /mnt/HD, give permissions to create/execute files
echo "Configuring /mnt/HD..."
sudo mkdir -p /mnt/HD
# Change ownership to the current user
sudo chown -R $USER:$USER /mnt/HD
# Set permissions (rwxr-xr-x) so user has full access and execution rights
sudo chmod -R 755 /mnt/HD

# 2. Install Git, Python (FastAPI), C, C++ development packages
echo "Installing development packages..."
sudo pacman -Syu --noconfirm
sudo pacman -S --needed --noconfirm     git     python     python-pip     python-virtualenv     python-fastapi     python-uvicorn     base-devel     cmake     gcc     clang     gdb

# 3. Create repos directory
echo "Creating repos directory..."
mkdir -p ~/repos

# 4. Set bash as default shell
echo "Setting bash as default shell..."
if [ "$SHELL" != "/bin/bash" ]; then
    chsh -s /bin/bash $USER
fi

# 5. Add custom aliases and pfetch to .bashrc
echo "Configuring .bashrc..."
BASHRC="$HOME/.bashrc"
if ! grep -q 'alias hd="cd /mnt/HD"' "$BASHRC"; then
    echo -e '
# Custom Aliases' >> "$BASHRC"
    echo 'alias hd="cd /mnt/HD"' >> "$BASHRC"
    echo 'alias repo="cd ~/repos"' >> "$BASHRC"
fi

# 6. Enable fstrim.timer
echo "Enabling fstrim timer..."
sudo systemctl enable fstrim.timer

# 7. Install paru (AUR helper) if not present
echo "Installing paru..."
if ! command -v paru &> /dev/null; then
    sudo pacman -S --needed --noconfirm base-devel
    git clone https://aur.archlinux.org/paru.git /tmp/paru
    cd /tmp/paru
    makepkg -si --noconfirm
    cd -
    rm -rf /tmp/paru
fi

# Install pfetch via paru
echo "Installing pfetch..."
paru -S --needed --noconfirm pfetch

# Add pfetch to end of .bashrc if not present
if ! grep -q 'pfetch' "$BASHRC"; then
    echo -e '
# Run pfetch on startup' >> "$BASHRC"
    echo 'pfetch' >> "$BASHRC"
fi

# 8. Install JetBrains Mono font
echo "Installing JetBrains Mono fonts..."
sudo pacman -S --needed --noconfirm ttf-jetbrains-mono ttf-jetbrains-mono-nerd

# 9 & 10. Install Alacritty, set dark theme, JetBrains font, and AMD optimizations
echo "Installing and configuring Alacritty..."
sudo pacman -S --needed --noconfirm alacritty

# Create Alacritty config directory
mkdir -p ~/.config/alacritty

# Write Alacritty TOML configuration
cat << 'EOF' > ~/.config/alacritty/alacritty.toml
[env]
TERM = "xterm-256color"
WINIT_X11_SCALE_FACTOR = "1.0"
# Force Wayland/X11 compatibility for modern AMD cards when needed
# WINIT_UNIX_BACKEND = "wayland" 

[window]
# Dimensions optimized for a 24-inch monitor (assuming 1080p or 1440p resolution)
dimensions = { columns = 130, lines = 30 }
dynamic_padding = true
decorations = "Full"
# Slightly increased opacity to keep the dark theme highly readable
opacity = 1.0
title = "Alacritty@CachyOS"
class = { instance = "Alacritty", general = "Alacritty" }
decorations_theme_variant = "Dark"

[scrolling]
# Increased scrollback history from 10k to 100k lines for better log inspection
history = 100000
multiplier = 3

[font]
normal = { family = "JetBrainsMono Nerd Font", style = "Regular" }
bold = { family = "JetBrainsMono Nerd Font", style = "Bold" }
italic = { family = "JetBrainsMono Nerd Font", style = "Italic" }
bold_italic = { family = "JetBrainsMono Nerd Font", style = "Bold Italic" }
# Slightly larger font for 24-inch monitor
size = 11.5

# Tokyo Night Dark Theme
[colors.primary]
background = "#1a1b26"
foreground = "#c0caf5"

[colors.cursor]
text = "#1a1b26"
cursor = "#c0caf5"

[colors.normal]
black   = "#15161e"
red     = "#f7768e"
green   = "#9ece6a"
yellow  = "#e0af68"
blue    = "#7aa2f7"
magenta = "#bb9af7"
cyan    = "#7dcfff"
white   = "#a9b1d6"

[colors.bright]
black   = "#414868"
red     = "#f7768e"
green   = "#9ece6a"
yellow  = "#e0af68"
blue    = "#7aa2f7"
magenta = "#bb9af7"
cyan    = "#7dcfff"
white   = "#c0caf5"
EOF

# 11. Install performance and hardware monitoring packages (optimized for AMD)
echo "Installing hardware monitoring tools..."
sudo pacman -S --needed --noconfirm cpu-x amdgputop btop nvtop

# 12. Install Docker, Docker Compose, and PostgreSQL
echo "Installing Docker and PostgreSQL..."
sudo pacman -S --needed --noconfirm docker docker-compose postgresql
sudo systemctl enable docker.service
# Add current user to docker group to run containers without sudo
sudo usermod -aG docker $USER

# 13. Install modern CLI productivity tools
echo "Installing CLI utilities..."
sudo pacman -S --needed --noconfirm fzf ripgrep eza bat fd

# Add modern aliases to .bashrc if not present
if ! grep -q 'alias ls="eza' "$BASHRC"; then
    echo -e '
# CLI Tools Aliases' >> "$BASHRC"
    echo 'alias ls="eza --icons=always"' >> "$BASHRC"
    echo 'alias ll="eza -la --icons=always"' >> "$BASHRC"
    echo 'alias cat="bat"' >> "$BASHRC"
fi

# 14. Setting up basic firewall (UFW)
echo "Setting up basic firewall..."
sudo pacman -S --needed --noconfirm ufw
sudo systemctl enable ufw.service
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw --force enable

# 15. Git configuration
echo "Configuring Git..."
git config --global user.name "VitorTz"
git config --global user.email "vitor.fsz@proton.me"

echo "Setup complete! Please restart your terminal or log out and log back in for shell changes to take effect."
