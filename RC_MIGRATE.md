# How to use Remote Copy to migrate between 3PARs

## Move VM with persistent disk from 3PAR A to B

We need two Image datastores, each pointing to different 3PAR:

- Image_DS_A - 3PAR A
- Image_DS_B - 3PAR B

For migration we need three System datastores:

- System_DS_A - 3PAR A
- System_DS_RC_AB - 3PAR A and SEC_config pointed to 3PAR B
- System_DS_B - 3PAR B

### Process of migration

In susntone select Migrate (without any label) and modal opens. In the modal select same host and in advanced select 
System_DS_RC_AB. VM will suspend for while, RC Group will be created and VM will be unsuspended. Now we have VM in HA
mode, because it is running with Peer Persistance and it has two groups of paths in multipath.

We can check RCG state in SSMC, and when volume(s) is fully synchronized we can proceed to next step.

**!!! IMPORTANT !!! Volume have to be fully synchronized.**

In sustone select again same dialog, select same host but for datastore select System_DS_B. VM goes to suspend state, 
RC Group will be removed and VM become unsuspended, but now running from 3PAR B.

### Post tasks

*TODO: This updates can be implemented into driver - tm/mv action.*

OpenNebula doesn't known about this migration, so we have to edit at lease three DB entities using onedb command:

Update body of image(s) and disk(s) in VM, change image datastore ID and Name to Image_DS_B

```
onedb change-body image --id IMAGE_ID /IMAGE/DATASTORE_ID DS_ID_B
onedb change-body image --id IMAGE_ID /IMAGE/DATASTORE DS_NAME_B
onedb change-body vm --id VM_ID /VM/TEMPLATE/DISK/DATASTORE_ID DS_ID_B
onedb change-body vm --id VM_ID /VM/TEMPLATE/DISK/DATASTORE DS_NAME_B
```

Update list of images in both image datastores, remove image ID from Image_DS_A and add it to Image_DS_B
```
onedb change-body datastore --id DS_ID_A /DATASTORE/IMAGES/ID[.=IMAGE_ID] --delete
onedb update-body datastore --id DS_ID_B
```

## Move VM with non-persistent disk from 3PAR A to B

This is pretty similar to persistent version, but we skip step with migration to System_DS_RC_AB. This driver doesn't
support RC for non-persistent images, at least for now. We migrate VM directly to System_DS_B. Downtime will be longer,
because disk is copied by using DD utility during VM suspension.

### Post tasks

Image_DS_A can have RC enabled, which on background synchronizes all non-persistent (base) images by using RCG. After
all VMs using same particular disk are migrated, them we can update-body of each to point it to Image_DS_B,
update-body of image itself and update-body for both image datastore's to finalize move. We have to remove the image
from RCG in SSMC manually.