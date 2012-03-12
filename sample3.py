#!/usr/bin/env python

import autodnsfailover
import os
import logging
import logging.handlers
import socket
import re
import yaml


def load_config(cfg_file = 'adf.yml'):
    """Loads a list of FQDNs from a yaml file.

    Format is like:

    fqdn:
        - bar.example.com.
        - /-[0-9]+\././


    Note that in the last case, we are doing a sed-like string replacement.
    Also note that the "replacement" half of the regex is not escaped.
    """

    managed_fqdns = []

    if os.path.exists(cfg_file):
        hostname = socket.gethostname()

        with open(cfg_file,'r') as cfg_fd:
            config = yaml.load(cfg_fd.read())

        fqdns = config.get('fqdn', [])

        for fqdn in fqdns:
            if fqdn.startswith('/') and fqdn.endswith('/'):  # sed-like substitution
                partitions = fqdn.split('/')
                start, pattern, replace, end = partitions[:4]  # there shouldn't be any more than 3, anyway
                fqdn = re.sub(pattern, replace, hostname)

            fqdn = fqdn if fqdn.endswith('.') else '{0}.'.format(fqdn)
            managed_fqdns.append(fqdn)
    else:
        hostname = socket.gethostname().split('.')[0]
        basename = hostname.rsplit('-', 1)[0]
        fqdn = basename + '.' + os.environ.get('ADF_ZONE')
        managed_fqdns.append(fqdn)


managed_fqdns = load_config()

ipaddr = autodnsfailover.WhatIsMyAddr(
    'http://169.254.169.254/latest/meta-data/public-ipv4')

dns = autodnsfailover.route53.Route53Dns(os.environ.get('ADF_ACCESS_KEY_ID',''),
                                os.environ.get('ADF_SECRET_ACCESS_KEY',''),
                                os.environ.get('ADF_ZONE',''),
                                hostname,
                                60)

check = autodnsfailover.HttpCheck(headers={'Host':'ping.example.com'})

timer = autodnsfailover.TickTimer(30,1,10)

logger = logging.getLogger('autodnsfailover')
logger.setLevel(logging.DEBUG)
consoleLogger = logging.StreamHandler()
consoleLogger.setLevel(logging.WARNING)
consoleLogger.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(consoleLogger)
#emailLogger = logging.handlers.SMTPHandler(
#    'smtp.example.com',
#    'sysadmin+autodnsfailover@example.com',
#    ['sysadmin+autodnsfailover@example.com'],
#    'autodnsfailover@{0} - notification about {1}'.format(hostname, fqdn)
#    )
#emailLogger.setLevel(logging.ERROR)
#logger.addHandler(emailLogger)

if __name__=='__main__':
    autodnsfailover.run(managed_fqdns, ipaddr, dns, check, timer, logger)
