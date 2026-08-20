#!/usr/bin/env bash
# Linux/Strix side of the StrixLink Thunderbolt IP link (Ubuntu, netplan).
# Loads the thunderbolt network driver and pins a static address on the
# point-to-point interface. Run once with sudo; persists across reboots.
set -euo pipefail

STRIX_IP="${STRIX_IP:-10.55.0.2}"

sudo modprobe thunderbolt-net
printf 'thunderbolt-net\n' | sudo tee /etc/modules-load.d/thunderbolt-net.conf >/dev/null

printf 'network:\n  version: 2\n  ethernets:\n    thunderbolt0:\n      addresses: [%s/24]\n' "$STRIX_IP" \
    | sudo tee /etc/netplan/60-thunderbolt.yaml >/dev/null
sudo chmod 600 /etc/netplan/60-thunderbolt.yaml
sudo netplan apply

ip -br addr show thunderbolt0
echo "Test after the Mac side is up:  ping ${STRIX_IP%.*}.1"
