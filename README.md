# HPE 3PAR Storage Driver

## Description

The 3PAR datastore driver enables OpenNebula to use a [HPE 3PAR](https://www.hpe.com/us/en/storage/3par.html) storage system for storing disk images.

## Development

To contribute bug patches or new features, you can use the GitLab Merge Request model. It is assumed that code and documentation are contributed under the Apache License 2.0.

More info:

* Issues Tracking: GitLab issues (https://gitlab.feldhost.cz/feldhost-public/one-addon-3par/issues)

## Authors

* Leader: Kristian Feldsam (feldsam@feldhost.net)

## Support

[FeldHost™](https://www.feldhost.net/products/opennebula) offers design, implementation, operation and management of a cloud solution based on OpenNebula.

## Compatibility

This add-on is developed and tested with:
- OpenNebula 5.6 and 3PAR OS 3.2.2.612 (MU4)+P51,P56,P59,P94,P98,P102,P106,P113,P118,P127  
- OpenNebula 5.8 and 3PAR OS 3.3.1.410 (MU2)+P32,P34,P36,P37,P39,P40,P41,P42,P45,P48
- OpenNebula 5.8 and 3PAR OS 3.3.1.460 (MU3)+P50,P58,P61,P77,P78,P81

## Requirements

### OpenNebula Front-end

* Working OpenNebula CLI interface with `oneadmin` account authorized to OpenNebula's core with UID=0
* Password-less SSH access from the front-end `oneadmin` user to the `node` instances.
* 3PAR python package `python-3parclient` installed, WSAPI username, password and access to the 3PAR API network
* libvirt-client package installed
* xmlstarlet package installed - used in TM monitor script instead of OpenNebula native ruby script because it is slow

```bash
yum install python-setuptools libvirt-client xmlstarlet
easy_install pip
pip install python-3parclient
```

### OpenNebula Node (or Bridge Node)

* There is only one task (`datastore/3par/cp`), which use `BRIDGE_LIST`, so there is no need to have separate Bridge Node
* Each OpenNebula Node (or Bridge Node) need to have relevant Host created on 3PAR
* Host name on 3PAR and OpenNebula Node name (or Bridge Node name) must be same. Name is used for (un)exporting volumes
* sg3_utils package installed
* `/etc/multipath.conf` need to have set `user_friendly_names no`, because we use WWNs instead of `mpathx` aliasses
* `/etc/sudoers.d/opennebula` - add `ONE_3PAR` cmd alias

```
nano /etc/sudoers.d/opennebula
...
Cmnd_Alias ONE_3PAR = /sbin/multipath, /usr/sbin/multipathd, /sbin/dmsetup, /usr/sbin/blockdev, /usr/bin/tee /sys/block/*/device/delete, /usr/bin/rescan-scsi-bus.sh
oneadmin ALL=(ALL) NOPASSWD: ONE_MISC, ..., ONE_3PAR, ...
...
```

```bash
yum install sg3_utils
```

## Features
Support standard OpenNebula datastore operations:

* datastore configuration via CLI
* all Datastore MAD(DATASTORE_MAD) and Transfer Manager MAD(TM_MAD) functionality
* SYSTEM datastore
* TRIM/discard in the VM when virtio-scsi driver is in use (require `DEV_PREFIX=sd` and `DISCARD=unmap`)
* disk images can be full provisioned, thin provisioned, thin deduplicated, thin compressed or thin deduplicated and compressed RAW block devices
* support different 3PAR CPGs as separate datastores
* support for 3PAR Priority Optimization Policy (QoS)
* live VM snapshots
* live VM migrations
* Volatile disks support (need patched KVM driver `attach_disk` script)
* Sunstone integration - available via our enterprise repository

## Limitations

1. Tested only with KVM hypervisor
1. When SYSTEM datastore is in use the reported free/used/total space is the space on 3PAR CPG. (On the host filesystem there are mostly symlinks and small files that do not require much disk space)
1. Tested/confirmed working on CentOS 7 (Frontend) and Oracle Linux 7, Oracle Linux 8, CentOS 7, CentOS 8, Fedora 29+ (Nodes).

## ToDo

1. QOS Priority per VM
1. Configuration of API endpoint and auth in datastore template

## Installation

The installation instructions are for OpenNebula 5.6+.

### Get the addon from github
```bash
cd ~
git clone https://github.com/OpenNebula/addon-3par.git
```

### Automated installation
The automated installation is best suitable for new deployments.

* Run the install script as 'root' user and check for any reported errors or warnings
```bash
bash ~/addon-3par/install.sh
```

### Manual installation

The following commands are related to latest OpenNebula version.

#### oned related pieces

* Copy 3PAR's DATASTORE_MAD driver files
```bash
cp -a ~/addon-3par/datastore/3par /var/lib/one/remotes/datastore/

# copy config
cp -a ~/addon-3par/etc/datastore/3par /var/lib/one/remotes/etc/datastore/

# fix ownership
chown -R oneadmin.oneadmin /var/lib/one/remotes/datastore/3par /var/lib/one/remotes/etc/datastore/3par

```

* Copy 3PAR's TM_MAD driver files
```bash
cp -a ~/addon-3par/tm/3par /var/lib/one/remotes/tm/

# fix ownership
chown -R oneadmin.oneadmin /var/lib/one/remotes/tm/3par
```

### Addon configuration
The global configuration of one-addon-3par is in `/var/lib/one/remotes/etc/datastore/3par/3par.conf` file.


* Edit `/etc/one/oned.conf` and add `3par` to the `TM_MAD` arguments
```
TM_MAD = [
    executable = "one_tm",
    arguments = "-t 15 -d dummy,lvm,shared,fs_lvm,qcow2,ssh,vmfs,ceph,dev,3par"
]
```

* Edit `/etc/one/oned.conf` and add `3par` to the `DATASTORE_MAD` arguments

```
DATASTORE_MAD = [
    executable = "one_datastore",
    arguments  = "-t 15 -d dummy,fs,vmfs,lvm,ceph,dev,3par  -s shared,ssh,ceph,fs_lvm,qcow2,3par"
]
```

* Edit `/etc/one/oned.conf` and append `TM_MAD_CONF` definition for 3par
```
TM_MAD_CONF = [
  NAME = "3par", LN_TARGET = "NONE", CLONE_TARGET = "SELF", SHARED = "yes", DRIVER = "raw", ALLOW_ORPHANS="yes"
]
```

* Edit `/etc/one/oned.conf` and append DS_MAD_CONF definition for 3par
```
DS_MAD_CONF = [
    NAME = "3par",
    REQUIRED_ATTRS = "CPG,BRIDGE_LIST",
    PERSISTENT_ONLY = "NO",
    MARKETPLACE_ACTIONS = ""
]
```

* Enable live disk snapshots support for 3PAR by adding `kvm-3par` to `LIVE_DISK_SNAPSHOTS` variable in `/etc/one/vmm_exec/vmm_execrc`
```
LIVE_DISK_SNAPSHOTS="kvm-qcow2 kvm-ceph kvm-3par"
```

### Post-install
* Restart `opennebula` service
```bash
systemtl restart opennebula
```
* As oneadmin user (re)sync the remote scripts
```bash
su - oneadmin -c 'onehost sync --force'
```

### Live snapshots info

* Live snapshots are tested only by using TCP communication with libvirtd on OpenNebula Nodes. Follow [this docs](https://docs.opennebula.org/5.8/deployment/open_cloud_host_setup/kvm_driver.html?highlight=qemu%20tcp#multiple-actions-per-host)
* In `/var/lib/one/remotes/etc/vmm/kvm/kvmrc` also set `export QEMU_PROTOCOL=qemu+tcp`
* Probably works out of the box, because by default `QEMU_PROTOCOL=qemu+ssh`, so it should tries to connect like this `virsh -c qemu+ssh://node/ ...`, but not tested

### Volatile disks support info

To make volatile disks working, we need to patch vmm driver action `attach_disk`. Patched file is available in `vmm/kvm`
directory and have to be installed to `/var/lib/one/remotes/vmm/kvm/`.

### Configuring the System Datastore

This addon enables full support of transfer manager (TM_MAD) backend of type 3par for the system datastore.  
The system datastore will hold only the symbolic links to the 3PAR block devices and context isos, so it will not take much space. See more details on the [Open Cloud Storage Setup](https://docs.opennebula.org/5.8/deployment/open_cloud_storage_setup/).

### Configuring the Datastore

Some configuration attributes must be set to enable a datastore as 3PAR enabled one:

* **DS_MAD**: [mandatory] The DS driver for the datastore. String, use value `3par`
* **TM_MAD**: [mandatory] Transfer driver for the datastore. String, use value `3par`
* **DISK_TYPE**: [mandatory for IMAGE datastores] Type for the VM disks using images from this datastore. String, use value `block`
* **CPG**: [mandatory] Name of Common Provisioning Group created on 3PAR. String
* **THIN**: Use thin volumes `tpvv` or no. By default enabled. `YES|NO`
* **DEDUP**: Use deduplicated thin volumes `tdvv` or no. By default disabled. `YES|NO`
* **COMPRESSION**: Use compressed thin volumes or no. By default disabled. `YES|NO`
* **NAMING_TYPE**: Part of volume name defining environment. By default `dev`. String (1)
* **BRIDGE_LIST**: Nodes to use for image datastore operations. String (2)
* **QOS_ENABLE**: Enable QoS. `YES|NO` (3)
* **QOS_PRIORITY**: QoS Priority. `HIGH|NORMAL|LOW` (4)
* **QOS_MAX\_IOPS**: QoS Max IOPS. Int (5)
* **QOS_MIN\_IOPS**: QoS Min IOPS. Int (6)
* **QOS_MAX\_BW**: QoS Man bandwidth in kB/s. Int (7)
* **QOS_MIN\_BW**: QoS Min bandwidth in kB/s. Int (8)
* **QOS_LATENCY**: QoS Latency goal in ms. Int (9)

1. Volume names are created according to best practices naming conventions.
   `<TYPE>` part - can be prd for production servers, dev for development servers, tst for test servers, etc.
   Volume name will be `<TYPE>.one.<IMAGE_ID>.vv` for ex. `dev.one.1.vv` or `tst.one.3.vv`
   
2. Quoted, space separated list of server hostnames which are Hosts on the 3PAR System.

3. QoS Rules - Applied per VM, so if VM have multiple disks, them QoS policy applies to all VM disks
   - minimum goals and maximum limits are shared.
   Persistent disks use `QOS_*` attributes from IMAGE datastore.
   Non-Persistent disks use `QOS_*` attributes from target SYSTEM datastore.

4. QoS Priority - Determines the sequence for throttling policies to meet latency goals.
   High priority should be used for critical applications, lower priority should be used for less critical applications.
   The priority will be ignored if the system does not have policies with a latency goal and minimum goal.

5. The maximum IOPS permitted for the virtual volumes associated with the policy.
   The IOPS maximum limit must be between 0 and 2 147 483 647 IO/s.

6. If IOPS fall below this minimum goal, then IOPS will not be throttled (reduced) for the virtual volumes
   associated with the policy. If a minimum goal is set for IOPS, then a maximum limit must also be set for IOPS.
   The minimum goal will be ignored if the system does not have policies with a latency goal set.
   The IOPS minimum goal must be between 0 and 2 147 483 647 IO/s.
   Zero means disabled.

7. The maximum bandwidth permitted for the virtual volumes associated with the policy. The maximum limit does not have
   dependencies on the other optimization settings.
   The bandwidth maximum limit must be between 0 and 9 007 199 254 740 991 KB/s.

8. If bandwidth falls below this minimum goal, then bandwidth will not be throttled (reduced) for the virtual volumes
   associated with the policy. If a minimum goal is set for bandwidth, then a maximum limit must also be set
   for bandwidth. The minimum goal will be ignored if the system does not have policies with a latency goal set.
   The bandwidth minimum goal must be between 0 and 9 007 199 254 740 991 KB/s.
   Zero means disabled.

9. Service time that the system will attempt to achieve for the virtual volumes associated with the policy.
   A latency goal requires the system to have other policies with a minimum goal specified so that the latency goal
   algorithm knows which policies to throttle. The sequence in which these will be throttled is set
   by priority (low priority is throttled first).
   The latency goal must be between 0,50 and 10 000,00 ms.
   Zero means disabled.

The following example illustrates the creation of a 3PAR datastore.
The datastore will use hosts `tst.lin.fedora1.host`, `tst.lin.fedora2.host` and `tst.lin.fedora3.host` for importing and creating images.

#### Image datastore through *onedatastore*

```bash
# create datastore configuration file
$ cat >/tmp/imageds.tmpl <<EOF
NAME = "3PAR IMAGE"
DS_MAD = "3par"
TM_MAD = "3par"
TYPE = "IMAGE_DS"
DISK_TYPE = "block"
CPG = "SSD_r6"
NAMING_TYPE = "tst"
BRIDGE_LIST = "tst.lin.fedora1.host tst.lin.fedora2.host tst.lin.fedora3.host"
QOS_ENABLE = "YES"
EOF

# Create datastore
$ onedatastore create /tmp/imageds.tmpl

# Verify datastore is created
$ onedatastore list

  ID NAME                SIZE AVAIL CLUSTER      IMAGES TYPE DS       TM
   0 system             98.3G 93%   -                 0 sys  -        ssh
   1 default            98.3G 93%   -                 0 img  fs       ssh
   2 files              98.3G 93%   -                 0 fil  fs       ssh
 100 3PAR IMAGE         4.5T  99%   -                 0 img  3par     3par
```

#### System datastore through *onedatastore*

```bash
# create datastore configuration file
$ cat >/tmp/ds.conf <<EOF
NAME = "3PAR SYSTEM"
TM_MAD = "3par"
TYPE = "SYSTEM_DS"
CPG = "SSD_r6"
NAMING_TYPE = "tst"
QOS_ENABLE = "YES"
EOF

# Create datastore
$ onedatastore create /tmp/ds.conf

# Verify datastore is created
$ onedatastore list

  ID NAME                SIZE AVAIL CLUSTER      IMAGES TYPE DS       TM
   0 system             98.3G 93%   -                 0 sys  -        shared
   1 default            98.3G 93%   -                 0 img  fs       shared
   2 files              98.3G 93%   -                 0 fil  fs       ssh
 100 3PAR IMAGE         4.5T  99%   -                 0 img  3par     3par
 101 3PAR SYSTEM        4.5T  99%   -                 0 sys  -        3par
 ```

## 3PAR best practices guide incl. naming conventions

Please follow the [best practices guide](https://h20195.www2.hpe.com/v2/GetPDF.aspx/4AA4-4524ENW.pdf).
