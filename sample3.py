#!/usr/bin/env python

import autodnsfailover
import os
import logging
import logging.handlers
import socket

hostname = socket.gethostname().split('.')[0]
basename = hostname.rsplit('-', 1)[0]
fqdn = basename + '.' + os.environ.get('ADF_ZONE')

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
    autodnsfailover.run(fqdn, ipaddr, dns, check, timer, logger)
