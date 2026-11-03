# Shared helpers. Requires config.sh to be sourced first.

log() { echo "$(date '+%F %T') $*" >> "$LOG"; }

wifi_on() {
    lipc-set-prop com.lab126.cmd wirelessEnable 1
    i=0
    while [ $i -lt 60 ]; do
        [ "$(lipc-get-prop com.lab126.wifid cmState 2>/dev/null)" = "CONNECTED" ] && return 0
        sleep 1; i=$((i + 1))
    done
    log "wifi: not connected after 60s ($(lipc-get-prop com.lab126.wifid cmState 2>/dev/null))"
    return 1
}

wifi_off() { lipc-set-prop com.lab126.cmd wirelessEnable 0; }

# Downloads the board to $IMG. Keeps the previous image on failure.
fetch_board() {
    if curl -fsSL --retry 3 --retry-delay 5 -m 60 -o "$IMG.tmp" "$BOARD_URL"; then
        mv "$IMG.tmp" "$IMG"
        return 0
    fi
    rm -f "$IMG.tmp"
    log "fetch failed"
    return 1
}

# Draws the board plus a small status line at the bottom (ASCII only: fbink's font has no Japanese).
show_board() {
    status="$1"
    batt=$(lipc-get-prop com.lab126.powerd battLevel 2>/dev/null)
    eips -c
    [ -f "$IMG" ] && eips -f -g "$IMG"
    line="batt ${batt}%  ${status}"
    [ -n "$batt" ] && [ "$batt" -lt 15 ] && line="$line  PLEASE CHARGE"
    if [ -x "$FBINK" ]; then
        "$FBINK" -q -y -1 -r "$line"
    else
        eips 1 1 "$line"
    fi
}

# Seconds until the next WAKE_HOUR_JST:WAKE_MIN_JST. The Kindle clock runs on UTC internally.
seconds_until_wake() {
    now=$(date +%s)
    jst=$(( (now + 9 * 3600) % 86400 ))
    target=$(( WAKE_HOUR_JST * 3600 + WAKE_MIN_JST * 60 ))
    s=$(( (target - jst + 86400) % 86400 ))
    [ $s -lt 300 ] && s=$((s + 86400))
    echo $s
}
