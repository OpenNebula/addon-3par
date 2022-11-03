#!/bin/bash

# -------------------------------------------------------------------------- #
# Copyright 2022, FeldHost™ (feldhost.net)                                   #
#                                                                            #
# Portions copyright OpenNebula Project (OpenNebula.org), CG12 Labs          #
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

###############################################################################
# This script should be called using hook when image persistent state is changed
###############################################################################

# Hook template
# NAME      = 3par-image-persistent
# TYPE      = api
# COMMAND   = "3par/image_persistent.sh"
# ARGUMENTS = $API
# CALL      = "one.image.persistent"


# ------------ Set up the environment to source common tools ------------

if [ -z "${ONE_LOCATION}" ]; then
    TMCOMMON=/var/lib/one/remotes/tm/tm_common.sh
else
    TMCOMMON=$ONE_LOCATION/var/remotes/tm/tm_common.sh
fi

. $TMCOMMON

DRIVER_PATH=$(dirname $0)

source ${DRIVER_PATH}/../../etc/datastore/3par/3par.conf
. ${DRIVER_PATH}/../../datastore/3par/scripts_3par.sh

# -------- Get template argument from OpenNebula core ------------

API=$1

#-------------------------------------------------------------------------------
# Get dest ds information
#-------------------------------------------------------------------------------

XPATH="${DRIVER_PATH}/../../datastore/xpath.rb -b $API"

unset i j XPATH_ELEMENTS

while IFS= read -r -d '' element; do
    XPATH_ELEMENTS[i++]="$element"
done < <($XPATH  /CALL_INFO/PARAMETERS/PARAMETER[2]/VALUE \
                 /CALL_INFO/PARAMETERS/PARAMETER[3]/VALUE \
                 /CALL_INFO/PARAMETERS/PARAMETER[4]/VALUE)

IMAGE_ID="${XPATH_ELEMENTS[j++]}"
PERSISTENT="${XPATH_ELEMENTS[j++]}"
SUCCESS="${XPATH_ELEMENTS[j++]}"

# api call for changing image persistant state was successfull
if [ "$SUCCESS" == "true" ]; then
    XPATH="${DRIVER_PATH}/../../datastore/xpath.rb --stdin"

    #-------------------------------------------------------------------------------
    # Get image datastore id and source
    #-------------------------------------------------------------------------------
    unset i j XPATH_ELEMENTS

    while IFS= read -r -d '' element; do
        XPATH_ELEMENTS[i++]="$element"
    done < <(oneimage show -x $IMAGE_ID| $XPATH /IMAGE/DATASTORE_ID)

    DSID="${XPATH_ELEMENTS[j++]}"

    #-------------------------------------------------------------------------------
    # Get image ds information
    #-------------------------------------------------------------------------------
    unset i j XPATH_ELEMENTS

    while IFS= read -r -d '' element; do
        XPATH_ELEMENTS[i++]="$element"
    done < <(onedatastore show -x $DSID | $XPATH \
                                /DATASTORE/TEMPLATE/API_ENDPOINT \
                                /DATASTORE/TEMPLATE/IP \
                                /DATASTORE/TEMPLATE/SEC_API_ENDPOINT \
                                /DATASTORE/TEMPLATE/SEC_IP \
                                /DATASTORE/TEMPLATE/REMOTE_COPY \
                                /DATASTORE/TEMPLATE/NAMING_TYPE \
                                /DATASTORE/TEMPLATE/CPG \
                                /DATASTORE/TEMPLATE/SEC_CPG)

    API_ENDPOINT="${XPATH_ELEMENTS[j++]:-$API_ENDPOINT}"
    IP="${XPATH_ELEMENTS[j++]:-$IP}"
    SEC_API_ENDPOINT="${XPATH_ELEMENTS[j++]:-$SEC_API_ENDPOINT}"
    SEC_IP="${XPATH_ELEMENTS[j++]:-$SEC_IP}"
    REMOTE_COPY="${XPATH_ELEMENTS[j++]:-$REMOTE_COPY}"
    NAMING_TYPE="${XPATH_ELEMENTS[j++]:-$NAMING_TYPE}"
    CPG="${XPATH_ELEMENTS[j++]:-$CPG}"
    SEC_CPG="${XPATH_ELEMENTS[j++]:-$SEC_CPG}"

    if [ "$REMOTE_COPY" == "YES" ]; then
        NAME="$NAMING_TYPE.one.$IMAGE_ID.vv"

        if [ "$PERSISTENT" == "0" ]; then
            log "Add image to remote copy group"
            RCG=$(python ${DRIVER_PATH}/../../datastore/3par/3par.py addVolumeToRCGroup -a $API_ENDPOINT -i $IP \
              -sapi $SEC_API_ENDPOINT -sip $SEC_IP -s $SECURE -u $USERNAME -p $PASSWORD -n $NAME \
              -c $CPG -sc $SEC_CPG -rcm $REMOTE_COPY_MODE -rcgn "$NAMING_TYPE.one.ds.$DSID" -rcha "NO")

            if [ $? -ne 0 ]; then
              error_message "$RCG"
              exit 1
            fi
        else
            log "Remove disk from Remote Copy group"
            RCG=$(python ${DRIVER_PATH}/../../datastore/3par/3par.py deleteVolumeFromRCGroup -a $API_ENDPOINT -i $IP \
                -sapi $SEC_API_ENDPOINT -sip $SEC_IP -s $SECURE -u $USERNAME -p $PASSWORD -n $NAME \
                -rcgn "$NAMING_TYPE.one.ds.$DSID")

            if [ $? -ne 0 ]; then
              error_message "$RCG"
              exit 1
            fi

            log "Remove disk from remote system"
            DEL=$(python ${DRIVER_PATH}/../../datastore/3par/3par.py deleteVV -a $SEC_API_ENDPOINT -i $SEC_IP \
                    -s $SECURE -u $USERNAME -p $PASSWORD -nt $NAMING_TYPE -id $IMAGE_ID)

            if [ $? -ne 0 ]; then
              error_message "$DEL"
              exit 1
            fi
        fi
    fi
fi
