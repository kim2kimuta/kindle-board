#!/bin/sh
# Board loop: update, then suspend until the next wake time. $1 = fixed interval in seconds (test mode).
. /mnt/us/extensions/dailyboard/bin/config.sh
. $DIR/bin/lib.sh
INTERVAL="$1"

log "loop start (interval=${INTERVAL:-daily})"
lipc-set-prop com.lab126.powerd preventScreenSaver 1
stop lab126_gui 2>/dev/null   # stop the reader UI so it does not redraw over the board
sleep 5

while true; do
    sh $DIR/bin/update.sh
    if [ -n "$INTERVAL" ]; then s=$INTERVAL; else s=$(seconds_until_wake); fi
    log "sleep ${s}s"
    sleep 3   # let the e-ink refresh finish before suspending
    rtcwake -d /dev/rtc1 -m no -s "$s" >/dev/null 2>&1
    echo mem > /sys/power/state
    # resumed (by the RTC alarm or the power button)
    sleep 2
done
