#!/usr/bin/env python

import autodnsfailover
import logging

fqdn = 'www.example.com'

ipaddr = autodnsfailover.WhatIsMyAddr()

dns = autodnsfailover.ZerigoDns('zerigo@example.com',
                                '1234567890',
                                'example.com')

check = autodnsfailover.HttpCheck()

timer = autodnsfailover.TickTimer(10, 2)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('autodnsfailover')

autodnsfailover.run(fqdn, ipaddr, dns, check, timer, logger)
