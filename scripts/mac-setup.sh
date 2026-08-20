#!/usr/bin/env bash
# Mac side of the StrixLink Thunderbolt IP link.
# macOS auto-creates the "Thunderbolt Bridge" network service; this just gives
# it a static point-to-point address. Run once; survives reboots.
set -euo pipefail

MAC_IP="${MAC_IP:-10.55.0.1}"

networksetup -setmanual "Thunderbolt Bridge" "$MAC_IP" 255.255.255.0
echo "Thunderbolt Bridge -> $MAC_IP/24"
echo "Test after the Linux side is up:  ping ${MAC_IP%.*}.2"
