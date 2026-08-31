#!/usr/bin/env bash

set -euo pipefail

echo "==> Installing Flatpak..."
sudo pacman -S --needed --noconfirm flatpak

echo "==> Adding Flathub repository..."
sudo flatpak remote-add --if-not-exists \
    flathub https://dl.flathub.org/repo/flathub.flatpakrepo

echo "==> Updating Flatpak repositories..."
sudo flatpak update --appstream -y

echo "==> Installing applications..."

sudo flatpak install -y system flathub app.shizumu.Shizumu
sudo flatpak install -y system flathub io.github.hakuneko.HakuNeko
sudo flatpak install -y system flathub org.upscayl.Upscayl

echo
echo "==> Flatpak installation completed."
echo
echo "Installed applications:"
flatpak list --system --app \
    --columns=name,application,version,branch

echo
echo "==> Flatpak remotes:"
flatpak remotes --system
