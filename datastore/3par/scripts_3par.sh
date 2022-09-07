#@IgnoreInspection BashAddShebang
# -------------------------------------------------------------------------- #
# Copyright 2022, FeldHost™ (feldhost.net)                                   #
#                                                                            #
# Portions copyright 2014-2016, Laurent Grawet <dev@grawet.be>               #
#                                                                            #
# Licensed under the Apache License, Version 2.0 (the "License"); you may    #
# not use this file except in compliance with the License. You may obtain    #
# a copy of the License at                                                   #
#                                                                            #
# http://www.apache.org/licenses/LICENSE-2.0                                 #
#                                                                            #
# Unless required by applicable law or agreed to in writing, software        #
# distributed under the License is distributed on an "AS IS" BASIS,          #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.   #
# See the License for the specific language governing permissions and        #
# limitations under the License.                                             #
# -------------------------------------------------------------------------- #

BLOCKDEV=blockdev
DMSETUP=dmsetup
MULTIPATH=multipath
MULTIPATHD=multipathd
TEE=tee
BASENAME=basename

if [ -z "${ONE_LOCATION}" ]; then
    PY3PAR="python /var/lib/one/remotes/datastore/3par/3par.py"
    XPATH="/var/lib/one/remotes/datastore/xpath.rb --stdin"
else
    PY3PAR="python $ONE_LOCATION/var/remotes/datastore/3par/3par.py"
    XPATH="$ONE_LOCATION/var/remotes/datastore/xpath.rb --stdin"
fi

function multipath_flush {
    local MAP_NAME="$1"

    echo "$SUDO $MULTIPATH -f $MAP_NAME"
}

function multipath_rescan {
    echo "$SUDO $MULTIPATH"
    echo "sleep 4"
}

function multipath_resize {
    local MAP_NAME="$1"

    echo "$SUDO $MULTIPATHD -k\"resize map $MAP_NAME\""
}

function rescan_scsi_bus {
  local LUN="$1"
  local FORCE

  # important to ignore rev, otherwise rescan failed when 3PAR OS get major update and device is online resized
  # https://gitlab.feldhost.cz/feldhost-public/one-addon-3par/-/issues/1
  [ "$2" == "force" ] && FORCE=" --forcerescan  --ignore-rev"
  echo "HOSTS=\$(cat /proc/scsi/scsi | awk -v RS=\"Type:\" '\$0 ~ \"Vendor: 3PARdata\" {print \$0}' |grep -Po \"scsi[0-9]+\"|grep -Eo \"[0-9]+\" |sort|uniq|paste -sd \",\" -)"
  echo "$SUDO /usr/bin/rescan-scsi-bus.sh --hosts=\$HOSTS --luns=$LUN --nooptscan$FORCE"
}

function get_vv_name {
  local NAME_WWN="$1"

  echo "$NAME_WWN" | $AWK -F: '{print $1}'
}

function get_vv_wwn {
  local NAME_WWN="$1"

  echo "$NAME_WWN" | $AWK -F: '{print $2}'
}

function image_update {
  local ID="$1"
  local DATA="$2"

  _TEMPLATE=$(mktemp -t oneimageUpdate-XXXXXXXXXX)
  trap "rm -f \"$_TEMPLATE\"" TERM INT QUIT HUP EXIT
  echo $DATA > $_TEMPLATE

  oneimage update $ID -a $_TEMPLATE
}

function get_image_running_vms_count {
    local IMAGE_ID="$1"
    local i XPATH_ELEMENTS

    while IFS= read -r -d '' element; do
        XPATH_ELEMENTS[i++]="$element"
    done < <(oneimage show -x "$IMAGE_ID" | $XPATH /IMAGE/RUNNING_VMS)

    echo "${XPATH_ELEMENTS[0]}"
}

function discover_lun {
    local LUN="$1"
    local WWN="$2"

    cat <<EOF
        $(rescan_scsi_bus "$LUN")
        $(multipath_rescan)

        DEV="/dev/mapper/3$WWN"

        # Wait a bit for new mapping
        COUNTER=1
        while [ ! -e \$DEV ] && [ \$COUNTER -le 10 ]; do
            sleep 1
            COUNTER=\$((\$COUNTER + 1))
        done
        if [ ! -e \$DEV ]; then
            # Last chance to get our mapping
            $(multipath_rescan)
            COUNTER=1
            while [ ! -e "\$DEV" ] && [ \$COUNTER -le 10 ]; do
                sleep 1
                COUNTER=\$((\$COUNTER + 1))
            done
        fi
        # Exit with error if mapping does not exist
        if [ ! -e \$DEV ]; then
            exit 1
        fi

        DM_HOLDER=\$($SUDO $DMSETUP ls -o blkdevname | grep -Po "(?<=3$WWN\s\()[^)]+")
        DM_SLAVE=\$(ls /sys/block/\${DM_HOLDER}/slaves)
        # Wait a bit for mapping's paths
        COUNTER=1
        while [ ! "\${DM_SLAVE}" ] && [ \$COUNTER -le 10 ]; do
            sleep 1
            COUNTER=\$((\$COUNTER + 1))
        done
        # Exit with error if mapping has no path
        if [ ! "\${DM_SLAVE}" ]; then
            exit 1
        fi
EOF
}

function remove_lun {
    local WWN="$1"

    cat <<EOF
      DEV="/dev/mapper/3$WWN"

      if [ -a \$DEV ]; then
        DM_HOLDER=\$($SUDO $DMSETUP ls -o blkdevname | grep -Po "(?<=3$WWN\s\()[^)]+")
        DM_SLAVE=\$(ls /sys/block/\${DM_HOLDER}/slaves)

        $(multipath_flush "\$DEV")

        unset device
        for device in \${DM_SLAVE}
        do
            if [ -e /dev/\${device} ]; then
                $SUDO $BLOCKDEV --flushbufs /dev/\${device}
                echo 1 | $SUDO $TEE /sys/block/\${device}/device/delete
            fi
        done
      fi
EOF
}

function unmap_lun {
  local HOST="$1"
  local WWN="$2"
  local PATH="$3"
  local CMD

  log "Unmapping $WWN from $HOST"

  CMD=$(cat <<EOF
          set -e
          $(remove_lun "$WWN")
          rm -f "$PATH"
EOF
)

  ssh_exec_and_log "$HOST" "$CMD" \
    "Error flushing out mapping"
}

function rescan_lun {
    local HOST="$1"
    local LUN="$2"
    local CMD

    CMD=$(cat <<EOF
                set -e
                $(rescan_scsi_bus "$LUN")
EOF
)

    ssh_exec_and_log "$HOST" "$CMD" \
      "Error registering remote $LUN to $HOST"
}

function map_lun {
    local HOST="$1"
    local LUN="$2"
    local WWN="$3"
    local DST_DIR="$4"
    local DST_PATH="$5"
    local CMD

    CMD=$(cat <<EOF
        set -e
        mkdir -p "$DST_DIR"
        $(discover_lun "$LUN" "$WWN")
        ln -sf "\$DEV" "$DST_PATH"
EOF
)

    ssh_exec_and_log "$HOST" "$CMD" \
        "Error registering $WWN to $HOST"
}

function map_and_copy_to_lun {
    local HOST="$1"
    local SRC_WWN="$2"
    local LUN="$3"
    local WWN="$4"
    local SRC_PATH="$5"
    local DEV SRC_DEV CMD

    SRC_DEV="/dev/mapper/3$SRC_WWN"
    DEV="/dev/mapper/3$WWN"

    CMD=$(cat <<EOF
        set -e
        $(discover_lun "$LUN" "$WWN")
        ln -sf "$DEV" "$SRC_PATH"
EOF
)

    ssh_exec_and_log "$HOST" "$CMD" \
        "Error mapping $WWN to $HOST"


    CMD=$(cat <<EOF
        set -e -o pipefail
        dd \if=$SRC_DEV of=$DEV bs=${DD_BLOCK_SIZE:-64k} oflag=direct
EOF
)

    ssh_exec_and_log "$HOST" "$CMD" \
         "Error copy from $SRC_WWN to $WWN"
}

function unexport_vv {
    local NAME="$1"
    local HOST="$2"
    local RC="${3:-NO}"
    local RESULT

    if [[ "$RC" == "YES" ]]; then
        log "Unexporting remote $NAME from $HOST"
        RESULT=$($PY3PAR unexportVV -a "$API_ENDPOINT" -i "$IP" -s "$SECURE" -u "$USERNAME" -p "$PASSWORD" -n "$NAME" \
                                    -hs "$HOST" -sapi "$SEC_API_ENDPOINT" -sip "$SEC_IP" -rc "$RC")
    else
        log "Unexporting $NAME from $HOST"
        RESULT=$($PY3PAR unexportVV -a "$API_ENDPOINT" -i "$IP" -s "$SECURE" -u "$USERNAME" -p "$PASSWORD" -n "$NAME" \
                                    -hs "$HOST")
    fi

    if [ $? -ne 0 ]; then
      error_message "Error unexporting VV: $RESULT"
      kill -s TERM $TOP_PID
    fi
}

function export_vv {
    local NAME="$1"
    local HOST="$2"
    local RC="${3:-NO}"
    local LUN

    if [[ "$RC" == "YES" ]]; then
        log "Mapping remote $NAME to $HOST"
        LUN=$($PY3PAR exportVV -a "$API_ENDPOINT" -i "$IP" -sapi "$SEC_API_ENDPOINT" -sip "$SEC_IP" -s "$SECURE" \
                               -u "$USERNAME" -p "$PASSWORD" -n "$NAME" -hs "$HOST" -rc "YES")
    else
        log "Mapping $NAME to $HOST"
        LUN=$($PY3PAR exportVV -a "$API_ENDPOINT" -i "$IP" -s "$SECURE" -u "$USERNAME" -p "$PASSWORD" -n "$NAME" \
                               -hs "$HOST")
    fi

    if [ $? -ne 0 ]; then
      error_message "$LUN"
      kill -s TERM $TOP_PID
    fi

    echo "$LUN"
}

function delete_vm_clone_vv {
  local API_ENDPOINT="$1"
  local IP="$2"
  local VMID="$3"
  local DISK_ID="$4"
  local DEL

  DEL=$($PY3PAR deleteVmClone -a "$API_ENDPOINT" -i "$IP" -s "$SECURE" -u "$USERNAME" -p "$PASSWORD" \
                              -nt "$NAMING_TYPE" -vi "$VMID" -id "$DISK_ID")

  if [ $? -ne 0 ]; then
      error_message "$DEL"
      kill -s TERM $TOP_PID
    fi
}

function host_exists {
    local HOST="$1"
    local HOST_3PAR

    HOST_3PAR=$($PY3PAR hostExists -a "$API_ENDPOINT" -i "$IP" -s "$SECURE" -u "$USERNAME" -p "$PASSWORD" -hs "$HOST")

    if [ $? -ne 0 ]; then
      error_message "$HOST_3PAR"
      kill -s TERM $TOP_PID
    fi

    echo "$HOST_3PAR"
}

function remove_vv_from_rcg {
    local NAME="$1"
    local VMID="$2"
    local RCG

    log "Remove disk from Remote Copy group"

    RCG=$($PY3PAR deleteVolumeFromRCGroup -a "$API_ENDPOINT" -i "$IP" -sapi "$SEC_API_ENDPOINT" -sip "$SEC_IP" \
                                -s "$SECURE" -u "$USERNAME" -p "$PASSWORD" -nt "$NAMING_TYPE" -n "$NAME" -vi "$VMID")

    if [ $? -ne 0 ]; then
      error_message "$RCG"
      kill -s TERM $TOP_PID
    fi
}

function add_vv_to_rcg {
    local NAME="$1"
    local VMID="$2"
    local RCG

    log "Create remote copy group"

    RCG=$($PY3PAR addVolumeToRCGroup -a "$API_ENDPOINT" -i "$IP" -sapi "$SEC_API_ENDPOINT" -sip "$SEC_IP" -s "$SECURE" \
                -u "$USERNAME" -p "$PASSWORD" -nt "$NAMING_TYPE" -c "$CPG" -sc "$SEC_CPG" -rcm "$REMOTE_COPY_MODE" \
                -n "$NAME" -vi "$VMID")

    if [ $? -ne 0 ]; then
      error_message "$RCG"
      kill -s TERM $TOP_PID
    fi

    log "$RCG"
}

function remove_vv_from_vvset {
    local NAME="$1"
    local VMID="$2"
    local VVSET

    log "Remove disk from VM VV Set"
    VVSET=$($PY3PAR deleteVolumeFromVVSet -a "$API_ENDPOINT" -i "$IP" -s "$SECURE" -u "$USERNAME" -p "$PASSWORD" \
                                          -nt "$NAMING_TYPE" -n "$NAME" -vi "$VMID")

    if [ $? -ne 0 ]; then
      error_message "$VVSET"
      kill -s TERM $TOP_PID
    fi
}

function add_vv_to_vvset {
    local NAME="$1"
    local VMID="$2"
    local VVSET

    log "Add disk to VM VV Set"
    VVSET=$($PY3PAR addVolumeToVVSet -a "$API_ENDPOINT" -i "$IP" -s "$SECURE" -u "$USERNAME" -p "$PASSWORD" \
                                     -nt "$NAMING_TYPE" -n "$NAME" -vi "$VMID")

    if [ $? -ne 0 ]; then
      error_message "$VVSET"
      kill -s TERM $TOP_PID
    fi
}

function get_vm_clone_vv_source {
    local API_ENDPOINT="$1"
    local IP="$2"
    local VMID="$3"
    local DISK_ID="$4"
    local NAME_WWN

    NAME_WWN=$($PY3PAR getVmClone -a "$API_ENDPOINT" -i "$IP" -s "$SECURE" -u "$USERNAME" -p "$PASSWORD" \
                                  -nt "$NAMING_TYPE" -vi "$VMID" -id "$DISK_ID")

    if [ $? -ne 0 ]; then
      error_message "$NAME_WWN"
      kill -s TERM $TOP_PID
    fi

    echo "$NAME_WWN"
}

function create_qos_policy {
    local VMID="$1"
    local QOS

    log "Create QoS Policy"
    QOS=$($PY3PAR createQosPolicy -a "$API_ENDPOINT" -i "$IP" -sapi "$SEC_API_ENDPOINT" -sip "$SEC_IP" -s "$SECURE" \
        -u "$USERNAME" -p "$PASSWORD" -nt "$NAMING_TYPE" -qp "$QOS_PRIORITY" -qxi "$QOS_MAX_IOPS" -qmi "$QOS_MIN_IOPS" \
        -qxb "$QOS_MAX_BW" -qmb "$QOS_MIN_BW" -ql "$QOS_LATENCY" -rc "$REMOTE_COPY" -vi "$VMID")

    if [ $? -ne 0 ]; then
      error_message "$QOS"
      kill -s TERM $TOP_PID
    fi
}

function create_vm_clone_vv {
    local SRC_NAME="$1"
    local VMID="$2"
    local DISK_ID="$3"
    local SIZE="$4"
    local COMMENT="$5"
    local NAME_WWN

    NAME_WWN=$($PY3PAR createVmClone -a "$API_ENDPOINT" -i "$IP" -s "$SECURE" -u "$USERNAME" -p "$PASSWORD" \
                        -nt "$NAMING_TYPE" -tpvv "$THIN" -tdvv "$DEDUP" -compr "$COMPRESSION" -sn "$SRC_NAME" -vi "$VMID" \
                        -id "$DISK_ID" -c "$CPG" -sz "$SIZE" -co "$COMMENT")

    if [ $? -ne 0 ]; then
      error_message "$NAME_WWN"
      kill -s TERM $TOP_PID
    fi

    echo "$NAME_WWN"
}