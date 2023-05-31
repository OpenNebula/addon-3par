#!/usr/bin/env python3

import argparse
import os
import subprocess

import sys
import time
from pprint import pprint

from hpe3parclient import client, exceptions
import pyone
import config

base_path = os.path.abspath(os.path.dirname(sys.argv[0]))

# ----------------------------
# Define parser
# ----------------------------
parser = argparse.ArgumentParser(description='Create and start RCG for VM persistent disks, so VM can be migrated '
                                             'directly to remote storage system')
parser.add_argument('-vm', '--vm', help='VM ID', type=int, required=True)
parser.add_argument('-ds', '--datastore', help='Target Datastore ID', type=int, required=True)

# -------------------------------------
# Parse args and proceed with execution
# -------------------------------------
args = parser.parse_args()

# -----------------------
# Connect to OpenNebula
# -----------------------
one = pyone.OneServer(config.ONE['address'], session='%s:%s' % (config.ONE['username'], config.ONE['password']))

cl = None


def login_3par(api=None, ip=None):
    global cl

    if api is None or ip is None:
        cl = client.HPE3ParClient(config._3PAR['api'], False, config._3PAR['secure'], None, True)
        cl.setSSHOptions(config._3PAR['ip'], config._3PAR['username'], config._3PAR['password'])
    else:
        cl = client.HPE3ParClient(api, False, config._3PAR['secure'], None, True)
        cl.setSSHOptions(ip, config._3PAR['username'], config._3PAR['password'])

    cl.login(config._3PAR['username'], config._3PAR['password'])


def logout_3par():
    global cl

    cl.logout()
    cl = None


def addVolumeToRCGroup(vvName, namingType, vmId, sapi, sip, cpg, secCpg):
    global cl

    shouldStartRcg = True

    rcgName = '{namingType}.one.vm.{vmId}'.format(namingType=namingType, vmId=vmId)

    scl, targetName = getRemoteCopyTargetName(sapi, sip)

    # get or create rc group
    try:
        rcg = cl.getRemoteCopyGroup(rcgName)
        rcgState = rcg.get('targets')[0].get('state')
        # rc group already in starting/started state
        if rcgState == 2 or rcgState == 3:
            shouldStartRcg = False
            # check for peer persistence enabled
            if rcg.get("targets")[0].get("policies").get("pathManagement"):
                cl.stopRemoteCopy(rcgName)
                shouldStartRcg = True
    except exceptions.HTTPNotFound:
        print('Remote Copy group does not exists, create new')
        targets, optional, policies = getRCGroupParams(targetName, cpg, secCpg)
        cl.createRemoteCopyGroup(rcgName, targets, optional)
        # modify to add specific options
        cl.modifyRemoteCopyGroup(rcgName, {'targets': [{'policies': policies}]})
        # modify to add autoSync policy, not exposed via API
        cl._run(['setrcopygroup', 'pol', 'auto_synchronize', rcgName])

    # add volume to rc group
    # we need to have same VV name on second system too
    secVVName = '{name}'.format(name=vvName)
    volumeAutoCreation = True
    skipInitialSync = False

    # check if remote VV exist
    try:
        secVV = scl.getVolume(secVVName)
        if 'expirationTimeSec' in secVV:
            scl.modifyVolume(secVVName, {'rmExpTime': True})
        volumeAutoCreation = False
        skipInitialSync = True
    except exceptions.HTTPNotFound:
        pass

    target = {
        'targetName': targetName,
        'secVolumeName': secVVName
    }

    done = False
    i = 0
    while not done:
        try:
            print('Add volume to Remote Copy group')
            cl.addVolumeToRemoteCopyGroup(rcgName, vvName, [target], {
                'volumeAutoCreation': volumeAutoCreation,
                'skipInitialSync': skipInitialSync
            })

            done = True

            # start rc group
            if shouldStartRcg:
                print('Start Remote Copy group')
                cl.startRemoteCopy(rcgName)
        except exceptions.HTTPForbidden as ex:
            # there can be physical copy in progress, so we need wait and retry
            # wait max 15min
            if i > 180:
                # other issue, exiting
                cl.logout()
                scl.logout()
                print(ex)
                exit(1)
            i += 1
            time.sleep(5)
        except exceptions.HTTPConflict as ex:
            # volume is already in RC Group
            print(ex)
            done = True

    scl.logout()


def areAllVolumesSynced(namingType, vmId):
    global cl
    rcgName = '{namingType}.one.vm.{vmId}'.format(namingType=namingType, vmId=vmId)

    rcg = cl.getRemoteCopyGroup(rcgName)
    rcgState = rcg.get('targets')[0].get('state')

    if rcgState != 3:
        return False

    synced = True
    volumes = []
    for volume in rcg.get('volumes'):
        remoteVolumeName = volume.get('remoteVolumes')[0].get('remoteVolumeName')
        volumeState = volume.get('remoteVolumes')[0].get('syncStatus')
        volumeData = {'name': remoteVolumeName, 'state': volumeState}

        if volumeState != 3:
            synced = False
            volumeSyncLength = volume.get('remoteVolumes')[0].get('volumeSyncLength')
            volumeSyncOffset = volume.get('remoteVolumes')[0].get('volumeSyncOffset')
            volumeData['syncPercent'] = volumeSyncOffset / volumeSyncLength * 100

        volumes.append(volumeData)

    if not synced:
        return volumes

    return True

def getRCGroupParams(targetName, cpg, secCpg):
    target = {'targetName': targetName}
    policies = {'autoRecover': True}

    target['mode'] = 1
    target['userCPG'] = secCpg
    target['snapCPG'] = secCpg

    optional = {
        'localSnapCPG': cpg,
        'localUserCPG': cpg
    }

    return [target], optional, policies


def getRemoteCopyTargetName(sapi, sip):
    scl = getRemoteSystemClient(sapi, sip)

    targetName = scl.getStorageSystemInfo().get('name').encode('ascii', 'ignore')

    return scl, targetName


def getRemoteSystemClient(sapi, sip):
    scl = client.HPE3ParClient(sapi, False, config._3PAR['secure'], None, True)
    scl.setSSHOptions(sip, config._3PAR['username'], config._3PAR['password'])

    try:
        scl.login(config._3PAR['username'], config._3PAR['password'])
    except exceptions.HTTPUnauthorized as ex:
        print("Remote system: Login failed.")

    return scl



# get vm info
vm = one.vm.info(args.vm)
vmLastHistory = vm.HISTORY_RECORDS.HISTORY[-1]

vmHostId = int(vmLastHistory.HID)

# get source disk datastore id
if type(vm.TEMPLATE['DISK']) is list:
    disks = vm.TEMPLATE['DISK']
    dsId = int(vm.TEMPLATE['DISK'][0]['DATASTORE_ID'])
else:
    disks = [vm.TEMPLATE['DISK']]
    dsId = int(vm.TEMPLATE['DISK']['DATASTORE_ID'])

if args.datastore == dsId:
    print('Target datastore is same as actual VM datastore!')
    exit(1)

# get info about source datastore
sourceDatastore = one.datastore.info(dsId)

# get info about target datastore
targetDatastore = one.datastore.info(args.datastore)
sysDsId = int(targetDatastore.TEMPLATE['COMPATIBLE_SYS_DS'])

if not sysDsId:
    print('Unable to determine system datastore ID, COMPATIBLE_SYS_DS on image datastore is missing')
    exit(1)

# login to 3par
login_3par(sourceDatastore.TEMPLATE.get('API_ENDPOINT'), sourceDatastore.TEMPLATE.get('IP'))

namingType = sourceDatastore.TEMPLATE['NAMING_TYPE']
sapi = targetDatastore.TEMPLATE['API_ENDPOINT']
sip = targetDatastore.TEMPLATE['IP']
cpg = sourceDatastore.TEMPLATE['CPG']
secCpg = targetDatastore.TEMPLATE['CPG']

for disk in disks:
    if disk.get('PERSISTENT') != 'YES':
        continue

    vvName = disk.get('SOURCE').split(':')[0]
    addVolumeToRCGroup(vvName, namingType, vm.ID, sapi, sip, cpg, secCpg)

done = False
while not done:
    volumes = areAllVolumesSynced(namingType, vm.ID)

    if volumes == True:
        print('All volumes synced.')
        done = True
    else:
        for volume in volumes:
            if volume['state'] != 3:
                print('Syncing volume {name}: {percent}%'.format(name=volume['name'], percent=round(volume['syncPercent'])))
            else:
                print('Syncing volume {name}: {percent}%'.format(name=volume['name'], percent=100))
        time.sleep(10)

print('Migrate VM')
one.vm.migrate(vm.ID, vmHostId, False, False, sysDsId, 0)

done = False
while not done:
    time.sleep(5)
    vm = one.vm.info(args.vm)

    if vm.LCM_STATE != 3 or vm.STATE != 3:
        continue

    print('VM Migrated')
    done = True


print('Update datastore on VM disk(s)')
# change attrs on vm disk(s)
subprocess.check_call('onedb change-body vm --id %s /VM/TEMPLATE/DISK/DATASTORE_ID %s' % (vm.ID, targetDatastore.ID),
                      shell=True)
subprocess.check_call('onedb change-body vm --id %s /VM/TEMPLATE/DISK/DATASTORE %s' % (vm.ID, targetDatastore.NAME),
                      shell=True)

print('Update datastores and image(s)')
for disk in disks:
    if disk.get('PERSISTENT') != 'YES':
        continue

    # change attrs on image object
    subprocess.check_call('onedb change-body image --id %s /IMAGE/DATASTORE_ID %s' % (disk.get('IMAGE_ID'), targetDatastore.ID),
                          shell=True)
    subprocess.check_call('onedb change-body image --id %s /IMAGE/DATASTORE %s' % (disk.get('IMAGE_ID'), targetDatastore.NAME),
                          shell=True)

    # remove image from old DS list
    subprocess.check_call(
        'onedb change-body datastore --id %s /DATASTORE/IMAGES/ID[.=%s] --delete' % (disk.get('DATASTORE_ID'), disk.get('IMAGE_ID')),
        shell=True)

    # add image to new DS list
    subprocess.check_call(
        'onedb change-body datastore --id %s /DATASTORE/IMAGES/ID %s --append' % (targetDatastore.ID, disk.get('IMAGE_ID')),
        shell=True)

logout_3par()
