#!/usr/bin/env python3

import argparse
import os
import subprocess

import sys
import pyone
import config

base_path = os.path.abspath(os.path.dirname(sys.argv[0]))

# ----------------------------
# Define parser
# ----------------------------
parser = argparse.ArgumentParser(description='Move Image from one datastore to another only in OpenNebula database')
parser.add_argument('-i', '--image', help='Image ID', type=int, required=True)
parser.add_argument('-ds', '--datastore', help='Datastore ID', type=int, required=True)

# -------------------------------------
# Parse args and proceed with execution
# -------------------------------------
args = parser.parse_args()

# -----------------------
# Connect to OpenNebula
# -----------------------
one = pyone.OneServer(config.ONE['address'], session='%s:%s' % (config.ONE['username'], config.ONE['password']))

# get info about image
image = one.image.info(args.image)

# get info about datastore
datastore = one.datastore.info(args.datastore)

# change attrs on image object
subprocess.check_call('onedb change-body image --id %s /IMAGE/DATASTORE_ID %s' % (image.ID, datastore.ID), shell=True)
subprocess.check_call('onedb change-body image --id %s /IMAGE/DATASTORE %s' % (image.ID, datastore.NAME), shell=True)

# remove image from old DS list
subprocess.check_call('onedb change-body datastore --id %s /DATASTORE/IMAGES/ID[.=%s] --delete' % (image.DATASTORE_ID, image.ID), shell=True)

# add image to new DS list
subprocess.check_call('onedb change-body datastore --id %s /DATASTORE/IMAGES/ID %s --append' % (datastore.ID, image.ID), shell=True)