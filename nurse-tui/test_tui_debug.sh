#!/bin/bash
# Test TUI with debug output captured to file

rm -rf /tmp/chromiumoxide-runner 2>/dev/null
pkill -f chromium 2>/dev/null
sleep 1

echo "Starting TUI with debug logging..."
echo "Debug output will be saved to: /tmp/nurse-tui-debug.log"
echo ""
echo "Steps:"
echo "  1. Press L to open nurse selector"
echo "  2. Press 1 (or number for your nurse)"
echo "  3. Wait for 'Logged in' toast"
echo "  4. Press R to load patients"
echo "  5. Press Q to quit"
echo ""
echo "Then check: cat /tmp/nurse-tui-debug.log"
echo ""
echo "Starting in 3 seconds..."
sleep 3

cd /var/home/htsapenko/Projects/Zav/nurse-tui
./target/release/nurse-tui 2>/tmp/nurse-tui-debug.log

echo ""
echo "=== DEBUG OUTPUT ==="
cat /tmp/nurse-tui-debug.log
