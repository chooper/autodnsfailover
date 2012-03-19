#!/usr/bin/env python

import autodnsfailover
import autodnsfailover.route53
import os
import logging
import logging.handlers
import socket
import re
import yaml


hostname = socket.gethostname().split('.')[0]

def load_config(hostname, cfg_file = 'adf.yml'):
    """Loads a list of FQDNs from a yaml file.

    Format is like:

    zone: example.com
    provider:
        type: route53
        access_key: aws_access_key
        secret_key: aws_secret_key
    fqdn:
        - /-[0-9]+//


    Note that in the last case of fqdns, we are doing a sed-like string replacement.
    Also note that the "replacement" half of the regex is not escaped.
    """

    if not os.path.exists(cfg_file):
        print 'Config file {0} does not exist!'.format(cfg_file)
        return []

    managed_fqdns = []

    with open(cfg_file,'r') as cfg_fd:
        config = yaml.load(cfg_fd.read())

    fqdns = config.get('fqdn', [])
    for fqdn in fqdns:
        # start sed-ish substitution
        if fqdn.startswith('/') and fqdn.endswith('/'):
            partitions = fqdn.split('/')
            start, pattern, replace, end = partitions[:4]
            fqdn = re.sub(pattern, replace, hostname)+'.'+config['zone']

        managed_fqdns.append(fqdn)

    # overwrite config with resolved RRs
    config['fqdn'] = managed_fqdns

    return config


config = load_config(hostname)
managed_fqdns = config['fqdn']

if not managed_fqdns:
    basename = hostname.rsplit('-', 1)[0]
    fqdn = basename + config['zone']
    managed_fqdns = [fqdn]

ipaddr = autodnsfailover.WhatIsMyAddr(
    'http://169.254.169.254/latest/meta-data/public-ipv4')

if config['provider']['type'] == 'route53':
    dns = autodnsfailover.route53.Route53Dns(config['provider']['access_key'],
                                    config['provider']['secret_key'],
                                    config['zone'],
                                    notes='',
                                    ttl=60)
elif config['provider']['type'] == 'zerigodns':
    dns = autodnsfailover.ZerigoDns(config['provider']['username'],
                                    config['provider']['password'],
                                    config['zone'],
                                    hostname,
                                    60)
else:
    raise ValueError("Unknown provider from config file")

check = autodnsfailover.HttpCheck(headers={'Host':'ping.example.com'})

timer = autodnsfailover.TickTimer(30,1,10)

logger = logging.getLogger('autodnsfailover')
logger.setLevel(logging.DEBUG)
consoleLogger = logging.StreamHandler()
consoleLogger.setLevel(logging.WARNING)
consoleLogger.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(consoleLogger)
emailLogger = logging.handlers.SMTPHandler(
    'smtp.example.com',
    'sysadmin+autodnsfailover@example.com',
    ['sysadmin+autodnsfailover@example.com'],
    'autodnsfailover@{0} - notification about {1}'.format(hostname, fqdn)
    )
emailLogger.setLevel(logging.ERROR)
logger.addHandler(emailLogger)

if __name__=='__main__':
    autodnsfailover.run(managed_fqdns, ipaddr, dns, check, timer, logger)
