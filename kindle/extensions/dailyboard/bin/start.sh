#!/bin/sh
# KUAL entry: start the board loop in the background. $1 = optional test interval (seconds).
. /mnt/us/extensions/dailyboard/bin/config.sh
pkill -f "$DIR/bin/loop.sh" 2>/dev/null
nohup sh $DIR/bin/loop.sh "$1" >/dev/null 2>&1 &
