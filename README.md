# HPE 3PAR Storage Driver

## Description

The 3PAR datastore driver enables OpenNebula to use a [HPE 3PAR](https://www.hpe.com/us/en/storage/3par.html) storage system for storing disk images.

## Development

To contribute bug patches or new features, you can use the github Pull Request model. It is assumed that code and documentation are contributed under the Apache License 2.0.

More info:

* [How to Contribute](http://opennebula.org/addons/contribute/)
* Support: [OpenNebula user forum](https://forum.opennebula.org/c/support)
* Development: [OpenNebula developers forum](https://forum.opennebula.org/c/development)
* Issues Tracking: GitHub issues (https://github.com/FELDSAM-INC/one-addon-3par/issues)

## Authors

* Leader: Kristian Feldsam (feldsam@feldhost.cz)

## Compatibility

This add-on is developed and tested with OpenNebula 5.6.1 and 3PAR OS 3.2.2.612 (MU4)+P51,P56,P59,P94,P98,P102,P106,P113,P118,P127

## Requirements

### OpenNebula Front-end

* Working OpenNebula CLI interface with `oneadmin` account authorized to OpenNebula's core with UID=0
* Password-less SSH access from the front-end `oneadmin` user to the `node` instances.
* 3PAR python package `python-3parclient` installed, WSAPI username, password and access to the 3PAR API network
* libvirt-client package installed

```bash
easy_install pip
pip install python-3parclient
yum install libvirt-client
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
Cmnd_Alias ONE_3PAR = /sbin/multipath, /usr/sbin/multipathd, /sbin/dmsetup, /usr/sbin/blockdev, /usr/bin/dd, /usr/bin/tee, /usr/bin/rescan-scsi-bus.sh, /usr/bin/cat /proc/scsi/scsi
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
* support migration from one to another SYSTEM datastore if both are with `3par` TM_MAD
* TRIM/discard in the VM when virtio-scsi driver is in use (require `DEVICE_PREFIX=sd` and `DISCARD=unmap`)
* disk images can be thin provisioned RAW block devices
* support different 3PAR CPGs as separate datastores
* live VM snapshots

## Limitations

1. Tested only with KVM hypervisor
1. When SYSTEM datastore is in use the reported free/used/total space is the space on 3PAR CPG. (On the host filesystem there are mostly symlinks and small files that do not require much disk space)
1. No support for volatile disks, because SYSTEM datastore must be FILE type by design, so it is impossible to use volatile disks as block devices.
1. Tested/confirmed working on CentOS 7 (Frontend) and Fedora 29 (Nodes).

## ToDo

1. QoS - Disk I/O Throttling
1. Pre/Post migrate scripts
1. Disk size monitoring
1. Configuration of API endpoint and auth in datastore template
1. Sunstone integration

## Installation

The installation instructions are for OpenNebula 5.6+.

### Get the addon from github
```bash
cd ~
git clone https://github.com/FELDSAM-INC/one-addon-3par
```

### Automated installation
The automated installation is best suitable for new deployments.

* Run the install script as 'root' user and check for any reported errors or warnings
```bash
bash ~/one-addon-3par/install.sh
```

### Manual installation

The following commands are related to latest OpenNebula version.

#### oned related pieces

* Copy 3PAR's DATASTORE_MAD driver files
```bash
cp -a ~/one-addon-3par/datastore/3par /var/lib/one/remotes/datastore/

# copy config
cp -a ~/one-addon-3par/etc/datastore/3par /var/lib/one/remotes/etc/datastore/

# fix ownership
chown -R oneadmin.oneadmin /var/lib/one/remotes/datastore/3par /var/lib/one/remotes/etc/datastore/3par

```

* Copy 3PAR's TM_MAD driver files
```bash
cp -a ~/one-addon-3par/tm/3par /var/lib/one/remotes/tm/

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

* Live snapshots are tested only by using TCP communication with libvirtd on OpenNebula Nodes. Follow [this docs](https://docs.opennebula.org/5.6/deployment/open_cloud_host_setup/kvm_driver.html?highlight=qemu%20tcp#multiple-actions-per-host)
* In `/var/lib/one/remotes/etc/vmm/kvm/kvmrc` also set `export QEMU_PROTOCOL=qemu+tcp`
* Probably works out of box, because by default `QEMU_PROTOCOL=qemu+ssh`, so it tries connect like this `virsh -c qemu+ssh://node/ ...`, but not tested

### Post-install
* Restart `opennebula` service
```bash
service opennebula restart
```
* As oneadmin user (re)sync the remote scripts
```bash
su - oneadmin -c 'onehost sync --force'
```

### Configuring the System Datastore

This addon enables full support of transfer manager (TM_MAD) backend of type 3par for the system datastore.  
The system datastore will hold only the symbolic links to the 3PAR block devices and context isos, so it will not take much space. See more details on the [Open Cloud Storage Setup](http://docs.opennebula.org/5.6/deployment/open_cloud_storage_setup/).

### Configuring the Datastore

Some configuration attributes must be set to enable a datastore as 3PAR enabled one:

* **DS_MAD**: [mandatory] The DS driver for the datastore. String, use value `3par`
* **TM_MAD**: [mandatory] Transfer driver for the datastore. String, use value `3par`
* **DISK_TYPE**: [mandatory for IMAGE datastores] Type for the VM disks using images from this datastore. String, use value `block`
* **CPG**: [mandatory] Name of Common Provisioning Group created on 3PAR. String
* **THIN**: Use thin volumes `tpvv` or no. By default enabled. Int 0|1
* **DEDUP**: Use deduplicated thin volumes `tdvv` or no. By default disabled. Int 0|1
* **NAMING_TYPE**: Part of volume name defining environment. By default `dev`. String (1)
* **BRIDGE_LIST**: Nodes to use for image datastore operations. String (2)

1. Volume names are created according to best practices naming conventions.
   `<TYPE>` part - can be prd for production servers, dev for development servers, tst for test servers, etc.
   Volume name will be `<TYPE>.one.<IMAGE_ID>.vv` for ex. `dev.one.1.vv` or `tst.one.3.vv`
2. Quoted, space separated list of server hostnames which are Hosts on the 3PAR System.

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
$ cat >/tmp/ds.conf <<_EOF_
NAME = "3PAR SYSTEM"
TM_MAD = "3par"
TYPE = "SYSTEM_DS"
CPG = "SSD_r6"
NAMING_TYPE = "tst"
_EOF_

# Create datastore
$ onedatastore create /tmp/ds.conf

# Verify datastore is created
$ onedatastore list

  ID NAME                SIZE AVAIL CLUSTER      IMAGES TYPE DS       TM
   0 system             98.3G 93%   -                 0 sys  -        shared
   1 default            98.3G 93%   -                 0 img  fs       shared
   2 files              98.3G 93%   -                 0 fil  fs       ssh
 100 3PAR IMAGE         4.5T  99%   -                 0 img  3par     3par
 101 3PAR SYSTEM        4.5T  -     -                 0 sys  -        3par
 ```

## 3PAR best practices guide incl. naming conventions

Please follow the [best practices guide](https://h20195.www2.hpe.com/v2/GetPDF.aspx/4AA4-4524ENW.pdf).