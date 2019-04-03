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
  echo "HOSTS=\$($SUDO cat /proc/scsi/scsi | awk -v RS=\"Type:\" '\$0 ~ \"Vendor: 3PARdata\" {print \$0}' |grep -Po \"scsi[0-9]+\"|grep -Eo \"[0-9]+\" |sort|uniq|paste -sd \",\" -)"
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