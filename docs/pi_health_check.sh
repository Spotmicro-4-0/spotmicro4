#!/bin/bash
# ============================================
# Raspberry Pi Zero 2 W Health Check Script
# ============================================
# Checks for undervoltage, throttling, temperature,
# CPU load, memory, and SD card issues.
# Run with:  sudo bash pi_health_check.sh
# ============================================

echo "============================================"
echo "Raspberry Pi Health Diagnostic"
echo "============================================"
echo ""

# ---- Power & Throttling ----
echo "Power & Throttling:"
if command -v vcgencmd &> /dev/null; then
    STATUS=$(vcgencmd get_throttled)
    echo "  Raw status: $STATUS"
    case $STATUS in
        *0x0*) echo "  No throttling or undervoltage detected." ;;
        *0x1*) echo "  Undervoltage has occurred." ;;
        *0x2*) echo "  ARM frequency capped due to temperature." ;;
        *0x4*) echo "  Throttled due to temperature." ;;
        *0x8*) echo "  Soft temperature limit active." ;;
        *) echo "  Power/thermal issues detected." ;;
    esac
else
    echo "  vcgencmd not found — skipping power check."
fi
echo ""

# ---- Temperature ----
echo "Temperature:"
if command -v vcgencmd &> /dev/null; then
    vcgencmd measure_temp
else
    echo "  vcgencmd not available."
fi
echo ""

# ---- CPU Load ----
echo "CPU Load:"
uptime
echo ""

# ---- Memory Usage ----
echo "Memory Usage:"
free -h
echo ""

# ---- Disk and SD Card ----
echo "Disk Usage:"
df -h | grep '/dev/root'
echo ""
echo "Checking SD card for I/O errors:"
dmesg | grep -i mmc | tail -n 5
echo ""

# ---- Network ----
echo "Network Interfaces:"
ip -brief address show
echo ""

# ---- Recent Kernel Warnings ----
echo "Last 20 kernel messages:"
dmesg | tail -n 20
echo ""

echo "============================================"
echo "Diagnostic complete."
echo "Check for any warnings or errors above."
echo "If 'undervoltage' or 'throttled' appear, power is unstable."
echo "============================================"
