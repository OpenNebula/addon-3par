#!/usr/bin/env bash

SCRIPT_PATH=$(dirname $0)

. ${SCRIPT_PATH}/scripts_3par.sh

# Log function that knows how to deal with severities and adds the
# script name
function log_function
{
    echo "$1: $SCRIPT_NAME: $2" 1>&2
}

# Logs an info message
function log_info
{
    log_function "INFO" "$1"
}

# Logs an error message
function log_error
{
    log_function "ERROR" "$1"
}

# Logs a debug message
function log_debug
{
    log_function "DEBUG" "$1"
}

# This function is used to pass error message to the mad
function error_message
{
    (
        echo "ERROR MESSAGE --8<------"
        echo "$1"
        echo "ERROR MESSAGE ------>8--"
    ) 1>&2
}

# Executes a command, if it fails returns error message and exits
# If a second parameter is present it is used as the error message when
# the command fails
function exec_and_log
{
    EXEC_LOG_ERR=`bash -s 2>&1 1>/dev/null <<EOF
export LANG=C
export LC_ALL=C
$1
EOF`
    EXEC_LOG_RC=$?

    if [ $EXEC_LOG_RC -ne 0 ]; then
        log_error "Command \"$1\" failed: $EXEC_LOG_ERR"

        if [ -n "$2" ]; then
            error_message "$2"
        else
            error_message "Error executing $1: $EXEC_LOG_ERR"
        fi
        exit $EXEC_LOG_RC
    fi
}


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
