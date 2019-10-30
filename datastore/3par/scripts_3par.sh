#@IgnoreInspection BashAddShebang
# -------------------------------------------------------------------------- #
# Copyright 2019, FeldHost™ (feldhost.net)                                   #
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

function multipath_flush {
    local MAP_NAME
    MAP_NAME="$1"
    echo "$SUDO $MULTIPATH -f $MAP_NAME"
}

function multipath_rescan {
    echo "$SUDO $MULTIPATH"
    echo "sleep 4"
}

function multipath_resize {
    local MAP_NAME
    MAP_NAME="$1"
    echo "$SUDO $MULTIPATHD -k\"resize map $MAP_NAME\""
}

function rescan_scsi_bus {
  local LUN
  local FORCE
  LUN="$1"
  [ "$2" == "force" ] && FORCE=" --forcerescan"
  echo "HOSTS=\$(cat /proc/scsi/scsi | awk -v RS=\"Type:\" '\$0 ~ \"Vendor: 3PARdata\" {print \$0}' |grep -Po \"scsi[0-9]+\"|grep -Eo \"[0-9]+\" |sort|uniq|paste -sd \",\" -)"
  echo "$SUDO /usr/bin/rescan-scsi-bus.sh --hosts=\$HOSTS --luns=$LUN --nooptscan$FORCE"
}

function get_vv_name {
  local NAME_WWN
  NAME_WWN="$1"
  echo "$NAME_WWN" | $AWK -F: '{print $1}'
}

function get_vv_wwn {
  local NAME_WWN
  NAME_WWN="$1"
  echo "$NAME_WWN" | $AWK -F: '{print $2}'
}

function discover_lun {
    local LUN
    local WWN
    LUN="$1"
    WWN="$2"
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
    local WWN
    WWN="$1"
    cat <<EOF
      DEV="/dev/mapper/3$WWN"
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
EOF
}