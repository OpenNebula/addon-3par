#!/bin/bash

# -------------------------------------------------------------------------- #
# Copyright 2019, FeldHost™ (feldhost.net)                                    #
#                                                                            #
# Portions copyright 2015-2018, Storpool (storpool.com)                      #
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
#--------------------------------------------------------------------------- #

end_msg=

# install datastore and tm MAD
for MAD in datastore tm; do
    M_DIR="${ONE_VAR}/remotes/${MAD}"
    echo "*** Installing ${M_DIR}/3par ..."
    mkdir -pv "${M_DIR}/3par"
    cp $CP_ARG ${MAD}/3par/* "${M_DIR}/3par/"
    chown -R "$ONE_USER" "${M_DIR}/3par"
    chmod u+x -R "${M_DIR}/3par"
done

echo "*** Copy VM snapshot scripts to ${ONE_VAR}/remotes/vmm/kvm/ ..."
cp $CP_ARG "$CWD/vmm/kvm/"snapshot_*-3par "${ONE_VAR}/remotes/vmm/kvm/"
chmod a+x "${ONE_VAR}/remotes/vmm/kvm/"snapshot_*-3par
chown oneadmin: "${ONE_VAR}/remotes/vmm/kvm/"snapshot_*-3par

# Enable 3PAR in oned.conf
if grep -q -i 3par /etc/one/oned.conf >/dev/null 2>&1; then
    echo "*** 3PAR is already enabled in /etc/one/oned.conf"
else
    echo "*** enabling 3PAR plugin in /etc/one/oned.conf"
    cp $CP_ARG /etc/one/oned.conf /etc/one/oned.conf.bak;

    sed -i -e 's|ceph,dev|ceph,dev,3par|g' /etc/one/oned.conf

    sed -i -e 's|shared,ssh,ceph,|shared,ssh,ceph,3par,|g' /etc/one/oned.conf

    cat <<_EOF_ >>/etc/one/oned.conf
# 3PAR related config
TM_MAD_CONF = [
  NAME = "3par", LN_TARGET = "NONE", CLONE_TARGET = "SELF", SHARED = "yes", DRIVER = "raw", ALLOW_ORPHANS="yes"
]
DS_MAD_CONF = [
    NAME = "3par",
    REQUIRED_ATTRS = "CPG,BRIDGE_LIST",
    PERSISTENT_ONLY = "NO",
    MARKETPLACE_ACTIONS = ""
]
_EOF_
fi

# Enable snap_create_live in vmm_exec/vmm_execrc
LIVE_DISK_SNAPSHOTS_LINE=$(grep -e '^LIVE_DISK_SNAPSHOTS' /etc/one/vmm_exec/vmm_execrc | tail -n 1)
if [ "x${LIVE_DISK_SNAPSHOTS_LINE/kvm-3par/}" = "x$LIVE_DISK_SNAPSHOTS_LINE" ]; then
    if [ -n "$LIVE_DISK_SNAPSHOTS_LINE" ]; then
        echo "*** adding 3PAR to LIVE_DISK_SNAPSHOTS in /etc/one/vmm_exec/vmm_execrc"
        sed -i -e 's|kvm-qcow2|kvm-qcow2 kvm-3par|g' /etc/one/vmm_exec/vmm_execrc
    else
        echo "*** LIVE_DISK_SNAPSHOTS not defined in /etc/one/vmm_exec/vmm_execrc"
        echo "*** to enable 3PAR add the following line to /etc/one/vmm_exec/vmm_execrc"
        echo "LIVE_DISK_SNAPSHOTS=\"kvm-3par\""
    fi
else
    echo "*** 3PAR is already enabled for LIVE_DISK_SNAPSHOTS in /etc/one/vmm_exec/vmm_execrc"
fi

echo -n "*** 3par.conf "
if [ -f "${ONE_VAR}/remotes/etc/datastore/3par/3par.conf" ]; then
    echo "(found)"
else
    mkdir "${ONE_VAR}/remotes/etc/datastore/3par"
    cp $CP_ARG etc/datastore/3par/3par.conf "${ONE_VAR}/remotes/etc/datastore/3par/3par.conf"
fi

echo "*** Please sync hosts (onehost sync --force)"

echo "*** Please restart opennebula${end_msg:+ and $end_msg} service${end_msg:+s}"