#!/bin/sh
# KUAL "Show once now": update and draw once, leaving the normal Kindle UI running.
. /mnt/us/extensions/dailyboard/bin/config.sh
sleep 3   # let KUAL close first
sh $DIR/bin/update.sh
