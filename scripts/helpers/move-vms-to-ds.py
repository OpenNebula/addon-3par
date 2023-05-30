#!/usr/bin/env python3

import argparse
import os
import subprocess

import sys
import pyone
import config

base_path = os.path.abspath(os.path.dirname(sys.argv[0]))


def list_of_int_arg(string):
    return list(map(int, string.split(',')))


# ----------------------------
# Define parser
# ----------------------------
parser = argparse.ArgumentParser(
    description='Move VM disk(s) from one datastore to another only in OpenNebula database')
parser.add_argument('-vi', '--vmId',
                    help='VM id or comma separated list of VM ids',
                    type=list_of_int_arg, required=True)
parser.add_argument('-ds', '--datastore', help='Datastore ID', type=int, required=True)

# -------------------------------------
# Parse args and proceed with execution
# -------------------------------------
args = parser.parse_args()

# -----------------------
# Connect to OpenNebula
# -----------------------
one = pyone.OneServer(config.ONE['address'], session='%s:%s' % (config.ONE['username'], config.ONE['password']))

# get info about datastore
datastore = one.datastore.info(args.datastore)

for vm in args.vmId:
    # change attrs on image object
    subprocess.check_call('onedb change-body vm --id %s /VM/TEMPLATE/DISK/DATASTORE_ID %s' % (vm, datastore.ID),
                          shell=True)
    subprocess.check_call('onedb change-body vm --id %s /VM/TEMPLATE/DISK/DATASTORE %s' % (vm, datastore.NAME),
                          shell=True)
