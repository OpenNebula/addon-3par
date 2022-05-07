# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------- #
# Copyright 2019, FeldHost™ (feldhost.net)                                    #
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

from hpe3parclient import client, exceptions
import argparse
import time

# ----------------------------
# Define parser and subparsers
# ----------------------------
parser = argparse.ArgumentParser(description='3PAR WSAPI One Driver')
subparsers = parser.add_subparsers(title='List of available tasks', description='You can view help for each task by passing task name and -h option', dest='task')

# helper function
def boolarg(string):
    if string != True and string != '1' and string != 'YES':
        return False
    return True

# Common Parser
commonParser = argparse.ArgumentParser(add_help=False)
commonParser.add_argument('-a', '--api', help='WSAPI Endpoint', required=True)
commonParser.add_argument('-sapi', '--sapi', help='Secondary WSAPI Endpoint', required=False)
commonParser.add_argument('-s', '--secure',
                          help='WSAPI SSL certification verification is disabled. In order to override this, '
                               'set this to 1 or to /path/to/cert.crt',
                          type=boolarg,
                          default=False)
commonParser.add_argument('-i', '--ip', help='3PAR IP for SSH authentication options for the SSH based calls',
                          required=True)
commonParser.add_argument('-sip', '--sip', help='Secondary 3PAR IP for SSH authentication options for the SSH based calls',
                          required=False)
commonParser.add_argument('-u', '--username', help='3PAR username', required=True)
commonParser.add_argument('-p', '--password', help='3PAR password', required=True)
commonParser.add_argument('-sd', '--softDelete', help='Soft-delete volumes/snapshots', type=boolarg, default=True)

# MonitorCPG task parser
monitorCPGParser = subparsers.add_parser('monitorCPG', parents=[commonParser], help='Get CPG Available Space')
monitorCPGParser.add_argument('-c', '--cpg', help='CPG Name', required=True)
monitorCPGParser.add_argument('-d', '--disks', help='Return disks info', type=boolarg, default=False)
monitorCPGParser.add_argument('-di', '--datastoreId', help='DS ID', type=int)
monitorCPGParser.add_argument('-nt', '--namingType', help='Best practices Naming conventions <TYPE> part', default='dev')
monitorCPGParser.add_argument('-lf', '--legacyFormat', help='Legacy format to support OpenNebula <5.12', type=boolarg, default=False)

# CreateVV task parser
createVVParser = subparsers.add_parser('createVV', parents=[commonParser], help='Create new VV')
createVVParser.add_argument('-nt', '--namingType', help='Best practices Naming conventions <TYPE> part', default='dev')
createVVParser.add_argument('-id', '--id', help='ID of VV to use in VV name', required=True)
createVVParser.add_argument('-sz', '--size', help='Size of VV in MiB', type=int, required=True)
createVVParser.add_argument('-tpvv', '--tpvv', help='Thin provision', type=boolarg, default=True)
createVVParser.add_argument('-tdvv', '--tdvv', help='Thin provision with deduplication', type=boolarg, default=False)
createVVParser.add_argument('-compr', '--compression', help='Thin provision compressed volume', type=boolarg, default=False)
createVVParser.add_argument('-c', '--cpg', help='CPG Name', required=True)
createVVParser.add_argument('-co', '--comment', help='Comment')

# DeleteVV task parser
deleteVVParser = subparsers.add_parser('deleteVV', parents=[commonParser], help='Delete VV')
deleteVVParser.add_argument('-nt', '--namingType', help='Best practices Naming conventions <TYPE> part', default='dev')
deleteVVParser.add_argument('-id', '--id', help='ID of VV to use in VV name', required=True)
deleteVVParser.add_argument('-rc', '--remoteCopy', help='Enable Remote Copy', type=boolarg, default=False)

# CloneVV task parser
cloneVVParser = subparsers.add_parser('cloneVV', parents=[commonParser], help='Clone specific VV to new one')
cloneVVParser.add_argument('-snt', '--srcNamingType', help='Source: Best practices Naming conventions <TYPE> part',
                           default='dev')
cloneVVParser.add_argument('-sid', '--srcId', help='ID of source VV to use in VV name', required=True)
cloneVVParser.add_argument('-nt', '--namingType', help='Destination: Best practices Naming conventions <TYPE> part',
                           default='dev')
cloneVVParser.add_argument('-id', '--id', help='ID of destination VV to use in VV name', required=True)
cloneVVParser.add_argument('-sz', '--size', help='Size of destination VV in MiB', type=int, required=True)
cloneVVParser.add_argument('-c', '--cpg', help='Destination VV CPG Name', required=True)
cloneVVParser.add_argument('-tpvv', '--tpvv', help='Destination VV thin provision', type=boolarg, default=True)
cloneVVParser.add_argument('-tdvv', '--tdvv', help='Destination VV thin provision with deduplication', type=boolarg,
                           default=False)
cloneVVParser.add_argument('-compr', '--compression', help='Thin provision compressed volume', type=boolarg, default=False)
cloneVVParser.add_argument('-co', '--comment', help='Comment')

# CopyVV task parser
copyVVParser = subparsers.add_parser('copyVV', parents=[commonParser], help='Copy specific VV to another one')
copyVVParser.add_argument('-nt', '--namingType', help='Source: Best practices Naming conventions <TYPE> part',
                          default='dev')
copyVVParser.add_argument('-id', '--id', help='ID of source VV or VM disk', required=True)
copyVVParser.add_argument('-si', '--snapId', help='ID of snapshot', required=True)
copyVVParser.add_argument('-d', '--destName', help='Name of the destination VV', required=True)
copyVVParser.add_argument('-vi', '--vmId', help='Id of source VV VM')
copyVVParser.add_argument('-vc', '--vmClone', help='Is VM clone?', type=boolarg, default=False)
copyVVParser.add_argument('-c', '--cpg', help='Destination VV CPG Name', required=True)

# GrowVV task parser
growVVParser = subparsers.add_parser('growVV', parents=[commonParser], help='Grow VV by specific size')
growVVParser.add_argument('-n', '--name', help='Name of VV to grow', required=True)
growVVParser.add_argument('-gb', '--growBy', help='Grow by in MiB', type=int, required=True)
growVVParser.add_argument('-vi', '--vmId', help='Id of VM')
growVVParser.add_argument('-nt', '--namingType', help='Best practices Naming conventions <TYPE> part', default='dev')
growVVParser.add_argument('-rc', '--remoteCopy', help='Enable Remote Copy', type=boolarg, default=False)

# getVVSize task parser
getVVSizeParser = subparsers.add_parser('getVVSize', parents=[commonParser], help='Get size of VV')
getVVSizeParser.add_argument('-n', '--name', help='Name of VV', required=True)
getVVSizeParser.add_argument('-t', '--type', help='Type of size to get', choices=['USED', 'SNAP', 'VSIZE'],
                             required=True)

# ExportVV task parser
exportVVParser = subparsers.add_parser('exportVV', parents=[commonParser], help='Export VV to host')
exportVVParser.add_argument('-n', '--name', help='Name of VV to export', required=True)
exportVVParser.add_argument('-hs', '--host', help='Name of host to export to', required=True)
exportVVParser.add_argument('-rc', '--remoteCopy', help='Enable Remote Copy', type=boolarg, default=False)

# UnexportVV task parser
unexportVVParser = subparsers.add_parser('unexportVV', parents=[commonParser], help='Unexport VV from host')
unexportVVParser.add_argument('-n', '--name', help='Name of VV to unexport', required=True)
unexportVVParser.add_argument('-hs', '--host', help='Name of host to unexport from', required=True)
unexportVVParser.add_argument('-rc', '--remoteCopy', help='Enable Remote Copy', type=boolarg, default=False)

# CreateVmClone task parser
createVmCloneParser = subparsers.add_parser('createVmClone', parents=[commonParser],
                                            help='Create VM Clone VV based on source VV')
createVmCloneParser.add_argument('-sn', '--srcName', help='Name of source VV to copy to VM disk', required=True)
createVmCloneParser.add_argument('-nt', '--namingType', help='Best practices Naming conventions <TYPE> part',
                                 default='dev')
createVmCloneParser.add_argument('-id', '--id', help='ID of VM disk', required=True)
createVmCloneParser.add_argument('-vi', '--vmId', help='Id of VM', required=True)
createVmCloneParser.add_argument('-sz', '--size', help='Size of destination VV in MiB', type=int, required=True)
createVmCloneParser.add_argument('-c', '--cpg', help='Destination VV CPG Name', required=True)
createVmCloneParser.add_argument('-tpvv', '--tpvv', help='Thin provision', type=boolarg, default=True)
createVmCloneParser.add_argument('-tdvv', '--tdvv', help='Thin provision with deduplication', type=boolarg, default=False)
createVmCloneParser.add_argument('-compr', '--compression', help='Thin provision compressed volume', type=boolarg, default=False)
createVmCloneParser.add_argument('-co', '--comment', help='Comment')

# CreateVmVV task parser
createVmVVParser = subparsers.add_parser('createVmVV', parents=[commonParser], help='Create new VM VV')
createVmVVParser.add_argument('-nt', '--namingType', help='Best practices Naming conventions <TYPE> part', default='dev')
createVmVVParser.add_argument('-id', '--id', help='ID of VM disk', required=True)
createVmVVParser.add_argument('-vi', '--vmId', help='Id of VM', required=True)
createVmVVParser.add_argument('-sz', '--size', help='Size of destination VV in MiB', type=int, required=True)
createVmVVParser.add_argument('-c', '--cpg', help='Destination VV CPG Name', required=True)
createVmVVParser.add_argument('-tpvv', '--tpvv', help='Thin provision', type=boolarg, default=True)
createVmVVParser.add_argument('-tdvv', '--tdvv', help='Thin provision with deduplication', type=boolarg, default=False)
createVmVVParser.add_argument('-compr', '--compression', help='Thin provision compressed volume', type=boolarg, default=False)
createVmVVParser.add_argument('-co', '--comment', help='Comment')

# GetVmClone task parser
getVmCloneParser = subparsers.add_parser('getVmClone', parents=[commonParser], help='Get VM Clone VV name and wwn')
getVmCloneParser.add_argument('-nt', '--namingType', help='Best practices Naming conventions <TYPE> part',
                              default='dev')
getVmCloneParser.add_argument('-id', '--id', help='ID of VM disk', required=True)
getVmCloneParser.add_argument('-vi', '--vmId', help='Id of VM', required=True)

# DeleteVmClone task parser
deleteVmCloneParser = subparsers.add_parser('deleteVmClone', parents=[commonParser], help='Delete VM Clone VV')
deleteVmCloneParser.add_argument('-nt', '--namingType', help='Best practices Naming conventions <TYPE> part',
                                 default='dev')
deleteVmCloneParser.add_argument('-id', '--id', help='ID of VM disk', required=True)
deleteVmCloneParser.add_argument('-vi', '--vmId', help='Id of VM', required=True)

# CreateVVSetSnapshot task parser
createVVSetSnapshotParser = subparsers.add_parser('createVVSetSnapshot', parents=[commonParser], help='Create snapshot of volume set')
createVVSetSnapshotParser.add_argument('-nt', '--namingType', help='Source: Best practices Naming conventions <TYPE> part',
                                  default='dev')
createVVSetSnapshotParser.add_argument('-vi', '--vmId', help='Id of VM')
createVVSetSnapshotParser.add_argument('-si', '--snapId', help='ID of snapshot', required=True)
createVVSetSnapshotParser.add_argument('-rc', '--remoteCopy', help='Enable Remote Copy', type=boolarg, default=False)

# DeleteVVSetSnapshot task parser
deleteVVSetSnapshotParser = subparsers.add_parser('deleteVVSetSnapshot', parents=[commonParser], help='Delete volume set snapshot')
deleteVVSetSnapshotParser.add_argument('-nt', '--namingType', help='Source: Best practices Naming conventions <TYPE> part',
                                  default='dev')
deleteVVSetSnapshotParser.add_argument('-vi', '--vmId', help='Id of VM')
deleteVVSetSnapshotParser.add_argument('-si', '--snapId', help='ID of snapshot', required=True)
deleteVVSetSnapshotParser.add_argument('-rc', '--remoteCopy', help='Enable Remote Copy', type=boolarg, default=False)

# CreateSnapshot task parser
createSnapshotParser = subparsers.add_parser('createSnapshot', parents=[commonParser], help='Create snapshot of VV')
createSnapshotParser.add_argument('-nt', '--namingType', help='Source: Best practices Naming conventions <TYPE> part',
                                  default='dev')
createSnapshotParser.add_argument('-id', '--id', help='ID of source VV or VM disk', required=True)
createSnapshotParser.add_argument('-vi', '--vmId', help='Id of VM')
createSnapshotParser.add_argument('-vc', '--vmClone', help='Is VM clone VV?', type=boolarg, default=False)
createSnapshotParser.add_argument('-si', '--snapId', help='ID of snapshot', required=True)
createSnapshotParser.add_argument('-rc', '--remoteCopy', help='Enable Remote Copy', type=boolarg, default=False)

# RevertSnapshot task parser
revertSnapshotParser = subparsers.add_parser('revertSnapshot', parents=[commonParser],
                                             help='Revert snapshot to base VV')
revertSnapshotParser.add_argument('-nt', '--namingType', help='Source: Best practices Naming conventions <TYPE> part',
                                  default='dev')
revertSnapshotParser.add_argument('-id', '--id', help='ID of source VV or VM disk', required=True)
revertSnapshotParser.add_argument('-vi', '--vmId', help='Id of VM')
revertSnapshotParser.add_argument('-vc', '--vmClone', help='Is VM clone VV?', type=boolarg, default=False)
revertSnapshotParser.add_argument('-si', '--snapId', help='ID of snapshot', required=True)
revertSnapshotParser.add_argument('-o', '--online', help='Revert snapshot while VV is online (exported)', type=boolarg,
                                  default=False)
revertSnapshotParser.add_argument('-off', '--offline', help='Revert snapshot while VV is not attached to VM', type=boolarg,
                                  default=False)
revertSnapshotParser.add_argument('-rc', '--remoteCopy', help='Enable Remote Copy', type=boolarg, default=False)

# DeleteSnapshot task parser
deleteSnapshotParser = subparsers.add_parser('deleteSnapshot', parents=[commonParser], help='Delete snapshot of VV')
deleteSnapshotParser.add_argument('-nt', '--namingType', help='Source: Best practices Naming conventions <TYPE> part',
                                  default='dev')
deleteSnapshotParser.add_argument('-id', '--id', help='ID of source VV or VM disk', required=True)
deleteSnapshotParser.add_argument('-vi', '--vmId', help='Id of VM')
deleteSnapshotParser.add_argument('-vc', '--vmClone', help='Is VM clone VV?', type=boolarg, default=False)
deleteSnapshotParser.add_argument('-si', '--snapId', help='ID of snapshot', required=True)
deleteSnapshotParser.add_argument('-rc', '--remoteCopy', help='Enable Remote Copy', type=boolarg, default=False)

# FlattenSnapshot task parser
flattenSnapshotParser = subparsers.add_parser('flattenSnapshot', parents=[commonParser],
                                              help='Promote selected snapshot and delete all snapshots of source VV')
flattenSnapshotParser.add_argument('-sn', '--srcName', help='Name of source VV to which snapshot belongs', required=True)
flattenSnapshotParser.add_argument('-si', '--snapId', help='ID of snapshot', required=True)
flattenSnapshotParser.add_argument('-rc', '--remoteCopy', help='Enable Remote Copy', type=boolarg, default=False)

# HostExists task parser
hostExistsParser = subparsers.add_parser('hostExists', parents=[commonParser],
                                         help='Check if host with this name is registered')
hostExistsParser.add_argument('-hs', '--host', help='Name of host', required=True)

# AddVolumeToVVSet task parser
addVolumeToVVSetParser = subparsers.add_parser('addVolumeToVVSet', parents=[commonParser],
                                              help='Add volume to VM VV set. If VV set not exists, it creates new one')
addVolumeToVVSetParser.add_argument('-nt', '--namingType', help='Best practices Naming conventions <TYPE> part',
                                   default='dev')
addVolumeToVVSetParser.add_argument('-vi', '--vmId', help='Id of VM', required=True)
addVolumeToVVSetParser.add_argument('-n', '--name', help='Name of VV', required=True)
addVolumeToVVSetParser.add_argument('-co', '--comment', help='Comment')

# DeleteVolumeFromVVSet task parser
deleteVolumeFromVVSetParser = subparsers.add_parser('deleteVolumeFromVVSet', parents=[commonParser],
                                        help='Delete volume from VM VV set. If it is last member, it deletes VV set')
deleteVolumeFromVVSetParser.add_argument('-nt', '--namingType', help='Best practices Naming conventions <TYPE> part',
                                   default='dev')
deleteVolumeFromVVSetParser.add_argument('-vi', '--vmId', help='Id of VM', required=True)
deleteVolumeFromVVSetParser.add_argument('-n', '--name', help='Name of VV', required=True)

# CreateQosPolicy task parser
createQosPolicyParser = subparsers.add_parser('createQosPolicy', parents=[commonParser],
                                              help='Create QoS policy on VM VV set')
createQosPolicyParser.add_argument('-nt', '--namingType', help='Best practices Naming conventions <TYPE> part',
                                   default='dev')
createQosPolicyParser.add_argument('-vi', '--vmId', help='Id of VM', required=True)
createQosPolicyParser.add_argument('-qp', '--qosPriority', help='QoS Priority', choices=['LOW', 'NORMAL', 'HIGH'],
                                        required=True)
createQosPolicyParser.add_argument('-qxi', '--qosMaxIops', help='QoS Max IOPS', type=int, required=True)
createQosPolicyParser.add_argument('-qmi', '--qosMinIops', help='QoS Min IOPS', type=int, required=True)
createQosPolicyParser.add_argument('-qxb', '--qosMaxBw', help='QoS Max BW in kB/s', type=int, required=True)
createQosPolicyParser.add_argument('-qmb', '--qosMinBw', help='QoS Min BW in kB/s', type=int, required=True)
createQosPolicyParser.add_argument('-ql', '--qosLatency', help='QoS Latency in ms', type=int, required=True)
createQosPolicyParser.add_argument('-rc', '--remoteCopy', help='Enable Remote Copy', type=boolarg, default=False)


# addVolumeToRCGroup task parser
addVolumeToRCGroupParser = subparsers.add_parser('addVolumeToRCGroup', parents=[commonParser],
                                              help='Add volume to Remote Copy group. If RC group does not exists, it creates new one')
addVolumeToRCGroupParser.add_argument('-nt', '--namingType', help='Best practices Naming conventions <TYPE> part',
                                   default='dev')
addVolumeToRCGroupParser.add_argument('-vi', '--vmId', help='Id of VM', required=True)
addVolumeToRCGroupParser.add_argument('-n', '--name', help='Name of VV', required=True)
addVolumeToRCGroupParser.add_argument('-rcm', '--remoteCopyMode', help='Remote Copy mode', choices=['SYNC', 'PERIODIC', 'ASYNC'], required=True)
addVolumeToRCGroupParser.add_argument('-c', '--cpg', help='Local CPG Name', required=True)
addVolumeToRCGroupParser.add_argument('-sc', '--secCpg', help='Remote CPG Name', required=True)

# DeleteVolumeFromRCGroup task parser
deleteVolumeFromRCGroupParser = subparsers.add_parser('deleteVolumeFromRCGroup', parents=[commonParser],
                                        help='Delete volume from Remote Copy group. If it is last member, it stop RC group')
deleteVolumeFromRCGroupParser.add_argument('-nt', '--namingType', help='Best practices Naming conventions <TYPE> part',
                                   default='dev')
deleteVolumeFromRCGroupParser.add_argument('-vi', '--vmId', help='Id of VM', required=True)
deleteVolumeFromRCGroupParser.add_argument('-n', '--name', help='Name of VV', required=True)

# ------------
# Define tasks
# ------------
def monitorCPG(cl, args):
    cpgName = args.cpg
    cpgData = cl.getCPG(cpgName)
    cpgAvailableSpace = cl.getCPGAvailableSpace(cpgName)

    used = cpgData.get('UsrUsage').get('usedMiB')
    free = cpgAvailableSpace.get('usableFreeMiB')
    total = used + free

    print 'USED_MB={used}'.format(used=used)
    print 'TOTAL_MB={total}'.format(total=total)
    print 'FREE_MB={free}'.format(free=free)

    if args.disks == True:
      import subprocess
      import xmltodict
      from base64 import b64encode
      
      vvs = cl.getVolumes()
      diskSizes = {}

      for vv in vvs.get('members'):
        diskSizes[vv.get('name')] = vv.get('userSpace').get('usedMiB')
      
      vmsXml = subprocess.check_output('onevm list --extended -x', shell=True)
      vms = xmltodict.parse(vmsXml, force_list=('VM',))
      if vms['VM_POOL'] is None:
        return
      for vm in vms.get('VM_POOL')['VM']:
        if args.datastoreId != int(vm.get('HISTORY_RECORDS')['HISTORY'].get('DS_ID')):
          continue
        
        if args.legacyFormat:
          result = 'VM=[ID={vmId},POLL="'.format(vmId=vm.get('ID'))
        else:
          result = 'VM=[ID={vmId},MONITOR="'.format(vmId=vm.get('ID'))
        
        disks = vm.get('TEMPLATE').get('DISK')
        if isinstance(disks,dict):
          disks = [disks]

        diskResult = []
        for disk in disks:
          if disk.get('CLONE') == 'YES' or disk.get('SOURCE') is None or disk.get('SOURCE') == '':
            name = '{namingType}.one.vm.{vmId}.{diskId}.vv'.format(namingType=args.namingType, vmId=vm.get('ID'), diskId=disk.get('DISK_ID'))
          else:
            source = disk.get('SOURCE').split(':')
            name = source[0]

          if name in diskSizes:
            diskResult.append('DISK_SIZE=[ID={diskId},SIZE={diskSize}]'.format(diskId=disk.get('DISK_ID'), diskSize=diskSizes[name]))
       
        if args.legacyFormat:
            print result + ' '.join(diskResult) + '"]'
        else:
            print result + b64encode(' '.join(diskResult).encode('ascii')).decode('ascii') + '"]'

def createVV(cl, args):
    name = createVVName(args.namingType, args.id)

    vv = createVVWithName(cl, name, args)
    wwn = vv.get('wwn').lower()
    print '{name}:{wwn}'.format(name=name, wwn=wwn)

def deleteVV(cl, args):
    vvName = createVVName(args.namingType, args.id)
    deleteVVWithName(cl, vvName)

    if args.remoteCopy:
        vvName = '{name}.r'.format(name=vvName)
        cl = getRemoteSystemClient(args)
        deleteVVWithName(cl, vvName)

def cloneVV(cl, args):
    srcName = createVVName(args.srcNamingType, args.srcId)
    destName = createVVName(args.namingType, args.id)

    # first create volume
    vv = createVVWithName(cl, destName, args)

    optional = {'skipZero': True}

    cl.copyVolume(srcName, destName, args.cpg, optional)

    wwn = vv.get('wwn').lower()
    print '{name}:{wwn}'.format(name=destName, wwn=wwn)

def copyVV(cl, args):
  snapId = args.snapId

  if args.vmClone == True:
    srcName = createVmCloneName(args.namingType, args.id, args.vmId)
  else:
    srcName = createVVName(args.namingType, args.id)

  if snapId != "-1":
      srcName, metaKey = createSnapshotNameAndMetaKey(srcName, snapId)

  optional = {'skipZero': True}

  cl.copyVolume(srcName, args.destName, args.cpg, optional)

def growVV(cl, args):
    rcgName = '{namingType}.one.vm.{vmId}'.format(namingType=args.namingType, vmId=args.vmId)

    if args.remoteCopy:
        cl.stopRemoteCopy(rcgName)

    try:
        cl.growVolume(args.name, args.growBy)
    except exceptions.ClientException:
        if args.remoteCopy:
            cl.startRemoteCopy(rcgName)

    if args.remoteCopy:
        cl.startRemoteCopy(rcgName)

def getVVSize(cl, args):
    vv = cl.getVolume(args.name)

    if args.type == 'USED':
        print vv.get('userSpace').get('usedMiB')
    elif args.type == 'SNAP':
        print vv.get('snapshotSpace').get('usedMiB')
    elif args.type == 'VSIZE':
        print vv.get('sizeMiB')

def exportVV(cl, args):
    if args.remoteCopy:
        name = '{name}.r'.format(name=args.name)
        cl = getRemoteSystemClient(args)
    else:
        name = args.name

    host = args.host

    # check if VLUN already exists
    try:
        vluns = cl.getHostVLUNs(host)
        for vlun in vluns:
            if vlun.get('volumeName') == name:
                print vlun.get('lun')
                return
    except exceptions.HTTPNotFound:
        pass

    # create VLUN
    done = False
    while not done:
        try:
            location = cl.createVLUN(name, None, host, None, None, None, True)
            print location.split(',')[1]
            return
        except exceptions.HTTPConflict:
            time.sleep(5)

def unexportVV(cl, args):
    if args.remoteCopy:
        name = '{name}.r'.format(name=args.name)
        cl = getRemoteSystemClient(args)
    else:
        name = args.name

    host = args.host

    # check if VLUN exists
    found = False
    vluns = cl.getHostVLUNs(host)
    for vlun in vluns:
        if vlun.get('volumeName') == name:
            found = True
            break

    if found == False:
        return

    cl.deleteVLUN(name, vlun.get('lun'), host)

def createVmClone(cl, args):
    destName = createVmCloneName(args.namingType, args.id, args.vmId)

    # create new VV
    vv = createVVWithName(cl, destName, args)

    # define optional for speed up process
    optional = {'priority': 1, 'skipZero': True}

    # copy volume
    done = False
    i = 0
    while not done:
        try:
            cl.copyVolume(args.srcName, destName, args.cpg, optional)
            done = True
        except exceptions.HTTPConflict as ex:
            # failed after 5 tries, revert, exit
            if i > 5:
                cl.deleteVolume(destName)
                cl.logout()
                print ex
                exit(1)
            i += 1
            time.sleep(1)

    # print info
    wwn = vv.get('wwn').lower()
    print '{name}:{wwn}'.format(name=destName, wwn=wwn)

def createVmVV(cl, args):
    name = createVmCloneName(args.namingType, args.id, args.vmId)

    # create new VV
    vv = createVVWithName(cl, name, args)

    # print info
    wwn = vv.get('wwn').lower()
    print '{name}:{wwn}'.format(name=name, wwn=wwn)

def getVmClone(cl, args):
    name = createVmCloneName(args.namingType, args.id, args.vmId)
    vv = cl.getVolume(name)
    wwn = vv.get('wwn').lower()
    print '{name}:{wwn}'.format(name=name, wwn=wwn)

def deleteVmClone(cl, args):
    name = createVmCloneName(args.namingType, args.id, args.vmId)

    deleteVVWithName(cl, name)


def createVVSetSnapshot(cl, args):
    snapId = 's{snapId}'.format(snapId=args.snapId)

    if args.remoteCopy:
        vvsetName = 'RCP_{namingType}.one.vm.{vmId}'.format(namingType=args.namingType, vmId=args.vmId)
    else:
        vvsetName = '{namingType}.one.vm.{vmId}.vvset'.format(namingType=args.namingType, vmId=args.vmId)

    # get volume set info
    try:
        vvset = cl.getVolumeSet(vvsetName)
        members = vvset.get('setmembers')
    except exceptions.HTTPNotFound:
        print 'Volume set does not exits, exiting...'
        return

    # no members in volume set? unexpected
    if not members or not len(members) > 0:
        print 'Volume set has no members, exiting...'
        return

    # check for soft deleted snapshot
    if args.softDelete:
        for member in members:
            snapName, metaKey = createSnapshotNameAndMetaKey(member, snapId)
            try:
                cl.getVolume(snapName)
                # snap exists, so delete it
                cl.deleteVolume(snapName)
            except exceptions.HTTPNotFound:
                pass

            if args.remoteCopy:
                scl = getRemoteSystemClient(args)
                try:
                    scl.getVolume(snapName)
                    # snap exists, so delete it
                    scl.deleteVolume(snapName)
                except exceptions.HTTPNotFound:
                    pass

    # prepare snapshot vv name pattern
    name = '@vvname@.{snapId}'.format(snapId=snapId)

    # create snapshots
    if args.remoteCopy:
        rcgName = 'rcgroup:{namingType}.one.vm.{vmId}'.format(namingType=args.namingType, vmId=args.vmId)
        cmd = ['createsv', '-rcopy', '-ro', name, rcgName]
        cl._run(cmd)
    else:
        cl.createSnapshotOfVolumeSet(name, vvsetName, {'readOnly': True})

    # create and add snapshot metadata to all members
    for member in members:
        snapName, metaKey = createSnapshotNameAndMetaKey(member, snapId)
        cl.setVolumeMetaData(member, metaKey, snapName)

    print args.snapId


def deleteVVSetSnapshot(cl, args):
    snapId = 's{snapId}'.format(snapId=args.snapId)
    scl = None

    if args.remoteCopy:
        scl = getRemoteSystemClient(args)
        vvsetName = 'RCP_{namingType}.one.vm.{vmId}'.format(namingType=args.namingType, vmId=args.vmId)
    else:
        vvsetName = '{namingType}.one.vm.{vmId}.vvset'.format(namingType=args.namingType, vmId=args.vmId)

    # get volume set info
    try:
        vvset = cl.getVolumeSet(vvsetName)
        members = vvset.get('setmembers')
    except exceptions.HTTPNotFound:
        print 'Volume set does not exits, exiting...'
        return

    # no members in volume set? unexpected
    if not members or not len(members) > 0:
        print 'Volume set has no members, exiting...'
        return

    # iterate over volumes and find snapshots to delete
    for member in members:
        name, metaKey = createSnapshotNameAndMetaKey(member, snapId)

        if args.softDelete:
            cl.modifyVolume(name, {'expirationHours': 168})
            args.remoteCopy and scl.modifyVolume(name, {'expirationHours': 168})
        else:
            cl.deleteVolume(name)
            args.remoteCopy and scl.deleteVolume(name)

        try:
            cl.removeVolumeMetaData(member, metaKey)
        except exceptions.HTTPNotFound:
            pass



def createSnapshot(cl, args):
    snapId = args.snapId

    if args.vmClone == True:
        srcName = createVmCloneName(args.namingType, args.id, args.vmId)
    else:
        srcName = createVVName(args.namingType, args.id)

    name, metaKey = createSnapshotNameAndMetaKey(srcName, snapId)

    # check for soft deleted snapshot
    if args.softDelete:
        try:
            cl.getVolume(name)
            # snap exists, so delete it
            cl.deleteVolume(name)
        except exceptions.HTTPNotFound:
            pass

        if args.remoteCopy:
            scl = getRemoteSystemClient(args)
            try:
                scl.getVolume(name)
                # snap exists, so delete it
                scl.deleteVolume(name)
            except exceptions.HTTPNotFound:
                pass

    optional = {'readOnly': True}

    if args.remoteCopy:
        optional['syncSnapRcopy'] = True

    cl.createSnapshot(name, srcName, optional)
    cl.setVolumeMetaData(srcName, metaKey, name)


def revertSnapshot(cl, args):
    snapId = args.snapId
    rcgName = '{namingType}.one.vm.{vmId}'.format(namingType=args.namingType, vmId=args.vmId)

    if args.vmClone == True:
        srcName = createVmCloneName(args.namingType, args.id, args.vmId)
    else:
        srcName = createVVName(args.namingType, args.id)

    name, metaKey = createSnapshotNameAndMetaKey(srcName, snapId)

    optional = {'online': args.online}

    if not args.offline and args.remoteCopy:
        cl.stopRemoteCopy(rcgName)
        optional['allowRemoteCopyParent'] = True

    try:
        cl.promoteVirtualCopy(name, optional)
    except exceptions.ClientException as ex:
        if not args.offline and args.remoteCopy:
            cl.startRemoteCopy(rcgName)

        parser.error(ex)

    if not args.offline and args.remoteCopy:
        # need to wait for snapshot promoting
        done = False
        i = 0
        while not done:
            try:
                cl.startRemoteCopy(rcgName)
                done = True
            except exceptions.HTTPBadRequest as ex:
                # wait max 5min
                if i > 60:
                    # other issue, exiting
                    cl.logout()
                    print ex
                    exit(1)
                i += 1

                time.sleep(5)


def deleteSnapshot(cl, args):
    snapId = args.snapId
    scl = None

    if args.remoteCopy:
        scl = getRemoteSystemClient(args)

    if args.vmClone == True:
        srcName = createVmCloneName(args.namingType, args.id, args.vmId)
    else:
        srcName = createVVName(args.namingType, args.id)

    name, metaKey = createSnapshotNameAndMetaKey(srcName, snapId)

    if args.softDelete:
        cl.modifyVolume(name, {'expirationHours': 168})
        args.remoteCopy and scl.modifyVolume(name, {'expirationHours': 168})
    else:
        cl.deleteVolume(name)
        args.remoteCopy and scl.deleteVolume(name)

    try:
        cl.removeVolumeMetaData(srcName, metaKey)
    except exceptions.HTTPNotFound:
        pass


def flattenSnapshot(cl, args):
    srcName = args.srcName
    snapId = args.snapId
    scl = None

    if args.remoteCopy:
        scl = getRemoteSystemClient(args)

    name, metaKey = createSnapshotNameAndMetaKey(srcName, snapId)

    # promote selected snapshot
    cl.promoteVirtualCopy(name)

    # delete all snapshots
    meta = cl.getAllVolumeMetaData(srcName)
    for data in meta.get('members'):
        key = data.get('key')
        if key.startswith('snap'):
            snap = data.get('value')
            try:
                if args.softDelete:
                    cl.modifyVolume(snap, {'expirationHours': 168})
                    args.remoteCopy and scl.modifyVolume(name, {'expirationHours': 168})
                else:
                    # need to wait for snapshot promoting
                    done = False
                    while not done:
                        try:
                            cl.deleteVolume(snap)
                            done = True
                        except exceptions.HTTPConflict:
                            time.sleep(5)

                    args.remoteCopy and scl.deleteVolume(name)
                # snapshot deleted, remove metadata
                cl.removeVolumeMetaData(srcName, key)
            except exceptions.HTTPNotFound:
                # snapshot already not exists, remove metadata
                cl.removeVolumeMetaData(srcName, key)


def hostExists(cl, args):
    try:
        cl.getHost(args.host)
    except exceptions.HTTPNotFound:
        print 0
        return
    print 1

def addVolumeToVVSet(cl, args):
    vvsetName = '{namingType}.one.vm.{vmId}.vvset'.format(namingType=args.namingType, vmId=args.vmId)

    # get or create vvset
    try:
        cl.getVolumeSet(vvsetName)
    except exceptions.HTTPNotFound:
        print 'Volume Set does not exists, create new'
        cl.createVolumeSet(vvsetName, None, args.comment)

    # add volume to vvset
    try:
        cl.addVolumeToVolumeSet(vvsetName, args.name)
    except exceptions.HTTPConflict as ex:
        print 'VV already mapped to VV Set'


def deleteVolumeFromVVSet(cl, args):
    vvsetName = '{namingType}.one.vm.{vmId}.vvset'.format(namingType=args.namingType, vmId=args.vmId)

    # remove volume from volume set
    try:
        cl.removeVolumeFromVolumeSet(vvsetName, args.name)
    except exceptions.HTTPNotFound:
        print 'Volume is already removed from vv set'

    # get volume set info
    try:
        vvset = cl.getVolumeSet(vvsetName)
        members = vvset.get('setmembers')
    except exceptions.HTTPNotFound:
        print 'Volume set does not exits, exiting...'
        return

    # if there are other members them we do not remove VV Set
    if members and len(members) > 0:
        return

    # delete vv set
    try:
        cl.deleteVolumeSet(vvsetName)
    except exceptions.HTTPNotFound:
        print 'VV Set already does not exits'


def createQosPolicy(cl, args):
    if args.remoteCopy:
        vvsetName = 'RCP_{namingType}.one.vm.{vmId}'.format(namingType=args.namingType, vmId=args.vmId)
    else:
        vvsetName = '{namingType}.one.vm.{vmId}.vvset'.format(namingType=args.namingType, vmId=args.vmId)

    # create QoS policy if not exists
    qosRules = prepareQosRules(args)

    # primary system
    setQosRules(cl, vvsetName, qosRules)

    # remote system
    if args.remoteCopy:
        scl = getRemoteSystemClient(args)
        sysId = int(cl.getStorageSystemInfo().get('id'))
        secVvsetName = '{name}.r{sysId}'.format(name=vvsetName, sysId=sysId)
        # strip to 27 chars, like 3par
        setQosRules(scl, secVvsetName[0:27], qosRules)


def addVolumeToRCGroup(cl, args):
    shouldStartRcg = True
    rcgName = '{namingType}.one.vm.{vmId}'.format(namingType=args.namingType, vmId=args.vmId)

    scl, targetName = getRemoteCopyTargetName(args)

    # get or create rc group
    try:
        rcg = cl.getRemoteCopyGroup(rcgName)
        rcgState = rcg.get('targets')[0].get('state')
        # rc group already in starting/started state
        if rcgState == 2 or rcgState == 3:
            shouldStartRcg = False
    except exceptions.HTTPNotFound:
        print 'Remote Copy group does not exists, create new'
        targets, optional, policies = getRCGroupParams(targetName, args)
        cl.createRemoteCopyGroup(rcgName, targets, optional)
        # modify to add specific options
        cl.modifyRemoteCopyGroup(rcgName, {'targets': [{'policies': policies}]})

    # add volume to rc group
    try:
        secVVName = '{name}.r'.format(name=args.name)
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

        print 'Add volume to Remote Copy group'
        cl.addVolumeToRemoteCopyGroup(rcgName, args.name, [target], {
            'volumeAutoCreation': volumeAutoCreation,
            'skipInitialSync': skipInitialSync
        })

        # start rc group
        if shouldStartRcg:
            print 'Start Remote Copy group'
            cl.startRemoteCopy(rcgName)
    except exceptions.HTTPConflict as ex:
        print str(ex)

    scl.logout()


def deleteVolumeFromRCGroup(cl, args):
    rcgName = '{namingType}.one.vm.{vmId}'.format(namingType=args.namingType, vmId=args.vmId)

    # remove volume from rc group
    try:
        cl.stopRemoteCopy(rcgName)
        cl.removeVolumeFromRemoteCopyGroup(rcgName, args.name)
    except exceptions.HTTPNotFound:
        print 'Volume is already removed from rc group'

    # get rc group info
    try:
        rcg = cl.getRemoteCopyGroup(rcgName)
        volumes = rcg.get('volumes')
    except exceptions.HTTPNotFound:
        print 'Remote Copy group does not exits, exiting...'
        return

    # if there are other members them we do not remove VV Set
    if volumes and len(volumes) > 0:
        # start rc group back
        cl.startRemoteCopy(rcgName)
        return

    # delete rc group
    try:
        cl.removeRemoteCopyGroup(rcgName)
    except exceptions.HTTPNotFound:
        print 'Remote Copy group does not exits'

# ----------------
# Helper functions
# ----------------
def getRCGroupParams(targetName, args):
    target = {'targetName': targetName}
    policies = {'autoRecover': True}

    if args.remoteCopyMode == 'SYNC':
        target['mode'] = 1
        #policies['autoFailover'] = True
        policies['pathManagement'] = True
    elif args.remoteCopyMode == 'PERIODIC':
        target['mode'] = 3
    elif args.remoteCopyMode == 'ASYNC':
        target['mode'] = 4

    target['userCPG'] = args.secCpg
    target['snapCPG'] = args.secCpg

    optional = {
        'localSnapCPG': args.cpg,
        'localUserCPG': args.cpg
    }

    return [target], optional, policies

def getRemoteCopyTargetName(args):
    scl = getRemoteSystemClient(args)

    targetName = scl.getStorageSystemInfo().get('name').encode('ascii', 'ignore')

    return scl, targetName

def getRemoteSystemClient(args):
    # check for remoteCopy required args
    if args.sapi is None or args.sip is None:
        parser.error("--remoteCopy requires --sapi and --sip.")

    secure = False
    if args.secure == True:
        secure = True

    scl = client.HPE3ParClient(args.sapi, False, secure, None, True)
    scl.setSSHOptions(args.sip, args.username, args.password)

    try:
        scl.login(args.username, args.password)
    except exceptions.HTTPUnauthorized as ex:
        print "Remote system: Login failed."

    return scl


def createVVName(namingType, id):
    return '{namingType}.one.{id}.vv'.format(namingType=namingType, id=id)

def createVmCloneName(namingType, id, vmId):
    return '{namingType}.one.vm.{vmId}.{id}.vv'.format(namingType=namingType, id=id, vmId=vmId)

def createSnapshotNameAndMetaKey(srcName, snapId):
    name = '{srcName}.{snapId}'.format(srcName=srcName, snapId=snapId)
    metaKey = 'snap{snapId}'.format(snapId=snapId)

    return name, metaKey

def createVVWithName(cl, name, args):
    cpgName = args.cpg

    optional = {'snapCPG': cpgName}
    if args.tpvv == True and args.tdvv != True and args.compression != True:
        optional['tpvv'] = True

    if args.tdvv == True:
        optional['tdvv'] = True

    if args.compression == True and args.size >= 16384:
        optional['compression'] = True

    # minumum size for volume is 256MiB
    if args.size < 256:
        args.size = 256

    if args.comment:
        optional['comment'] = args.comment

    cl.createVolume(name, cpgName, args.size, optional)

    return cl.getVolume(name)

def deleteVVWithName(cl, name):
    if args.softDelete:
        cl.modifyVolume(name, {'expirationHours': 168})
        # find and delete snapshots
        meta = cl.getAllVolumeMetaData(name)
        for data in meta.get('members'):
            key = data.get('key')
            if key.startswith('snap'):
                snap = data.get('value')
                cl.modifyVolume(snap, {'expirationHours': 168})
    else:
        try:
            cl.deleteVolume(name)
        except exceptions.HTTPConflict:
            # try to find and delete snapshots
            meta = cl.getAllVolumeMetaData(name)
            for data in meta.get('members'):
                key = data.get('key')
                if key.startswith('snap'):
                    snap = data.get('value')
                    cl.deleteVolume(snap)

            # try delete again
            done = False
            i = 0
            while not done:
                try:
                    cl.deleteVolume(name)
                    done = True
                except exceptions.HTTPConflict as ex:
                    # this can happen, if vv has child - deleting after cloning disk, which is not finished yet
                    # wait max 15min
                    if i > 180:
                        # other issue, exiting
                        cl.logout()
                        print ex
                        exit(1)
                    i += 1
                    time.sleep(5)

def prepareQosRules(args):
    qosRules = {
        'enable': True,
        'ioMinGoal': args.qosMinIops,
        'ioMaxLimit': args.qosMaxIops,
        'bwMinGoalKB': args.qosMinBw,
        'bwMaxLimitKB': args.qosMaxBw,
        'latencyGoal': args.qosLatency
    }

    if args.qosMinIops == 0:
        qosRules['ioMinGoal'] = 1

    if args.qosMinBw == 0:
        qosRules['bwMinGoalKB'] = 1

    if args.qosLatency == 0:
        qosRules['latencyGoal'] = None
        qosRules['defaultLatency'] = True

    if args.qosPriority == 'LOW':
        qosRules['priority'] = 1
    elif args.qosPriority == 'NORMAL':
        qosRules['priority'] = 2
    elif args.qosPriority == 'HIGH':
        qosRules['priority'] = 3

    return qosRules

def setQosRules(cl, vvsetName, qosRules):
    try:
        qos = cl.queryQoSRule(vvsetName)
        # compare rules
        for k, v in qosRules.items():
            if k == 'enable':
                k = 'enabled'
            if k == 'defaultLatency' and v:
                v = None
            if qos.get(k) != v:
                # not match, update
                print 'QoS Policy Rules changed, need update'
                cl.modifyQoSRules(vvsetName, qosRules)
                break
    except exceptions.HTTPNotFound:
        print 'QoS Policy does not exists, create new'
        cl.createQoSRules(vvsetName, qosRules)

# -------------------------------------
# Parse args and proceed with execution
# -------------------------------------
args = parser.parse_args()

# ------------------
# Login and run task
# ------------------
secure = False
if args.secure == True:
    secure = True

cl = client.HPE3ParClient(args.api, False, secure, None, True)
cl.setSSHOptions(args.ip, args.username, args.password)

try:
    cl.login(args.username, args.password)
except exceptions.HTTPUnauthorized as ex:
    print "Login failed."

try:
    globals()[args.task](cl, args)
    cl.logout()
except Exception as ex:
    # something unexpected happened
    print ex
    cl.logout()
    exit(1)
