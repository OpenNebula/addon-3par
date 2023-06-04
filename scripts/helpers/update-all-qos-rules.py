#!/usr/bin/env python3
from pprint import pprint

from hpe3parclient import client, exceptions
import config

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

# login to 3par
login_3par()

rules = cl.queryQoSRules()

for rule in rules.get('members'):
    pprint(rule)

    qosRules = {
        'ioMinGoal': 100,
        'ioMaxLimit': rule['ioMaxLimit'],
        'bwMinGoalKB': 51200,
        'bwMaxLimitKB': rule['bwMaxLimitKB'],
        'latencyGoal': None,
        'defaultLatency': True
    }
    
    pprint(qosRules)
    
    cl.modifyQoSRules(rule['name'], qosRules)
