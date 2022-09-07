#!/usr/bin/env bash

SCRIPT_PATH=$(dirname $0)

. /var/lib/one/remotes/tm/tm_common.sh
. ${SCRIPT_PATH}/scripts_3par.sh

LUN=$1
WWN=$2

DISCOVER_CMD=$(cat <<EOF
    set -e
    $(discover_lun "$LUN" "$WWN")
EOF
)

exec_and_log "$DISCOVER_CMD" \
    "Error discovering LUN $LUN:$WWN"

exit 0
