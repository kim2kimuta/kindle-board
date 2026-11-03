#!/bin/sh
# One update cycle: Wi-Fi on, sync clock, download, draw, Wi-Fi off.
. /mnt/us/extensions/dailyboard/bin/config.sh
. $DIR/bin/lib.sh

result="FAILED"
if wifi_on; then
    ntpdate -s pool.ntp.org 2>/dev/null || sntp -s pool.ntp.org 2>/dev/null
    fetch_board && result="updated"
fi
wifi_off
# The Kindle's local time zone is already JST
status="$result $(date '+%m/%d %H:%M')"
show_board "$status"
log "$status"
