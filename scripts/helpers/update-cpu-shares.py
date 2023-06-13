#!/usr/bin/env python3
from pprint import pprint
import subprocess

import pyone
import config

# -----------------------
# Connect to OpenNebula
# -----------------------
one = pyone.OneServer(config.ONE['address'], session='%s:%s' % (config.ONE['username'], config.ONE['password']))

# prepare hosts to ips mapping
hostToIp = {}
hosts = one.hostpool.info()
for host in hosts.HOST:
    if host.STATE != 2:
        continue

    host_name = host.TEMPLATE['HOSTNAME']
    hostToIp[host_name] = {}
    hostToIp[host_name]['ip'] = host.TEMPLATE['IP_ADDRESS']
    hostToIp[host_name]['cgroups'] = host.TEMPLATE['CGROUPS_VERSION']

print('{count} compute nodes found'.format(count=len(hostToIp)))

# get vms
vms = one.vmpool.infoextended(-2, -1, -1, -1)

for vm in vms.VM:
    host = vm.HISTORY_RECORDS.HISTORY[-1].HOSTNAME
    
    hostIp = hostToIp[host]['ip']
    hostCgroups = int(hostToIp[host]['cgroups'])
    
    if hostCgroups == 2:
        cpuCount = float(vm.TEMPLATE.get('CPU'))
        shares = int(100 * cpuCount)
    
        print('Updating VM %s: virsh -c qemu+tcp://%s/system schedinfo %s  --set cpu_shares=%s' % (vm.NAME, hostIp, vm.DEPLOY_ID, shares))
        subprocess.check_call('virsh -c qemu+tcp://%s/system schedinfo %s  --set cpu_shares=%s' % (hostIp, vm.DEPLOY_ID, shares),
                          shell=True)
