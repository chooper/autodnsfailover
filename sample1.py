#!/usr/bin/env python

import autodnsfailover
import logging

# DNS name used by the round-robin setup
fqdn = 'www.example.com'

# Implementation to be used to find our local IP address
ipaddr = autodnsfailover.WhatIsMyAddr()

# Implementation to be used to update the DNS records
dns = autodnsfailover.ZerigoDns('zerigo@example.com',
                                '1234567890',
                                'example.com')

# Implementation to be used to check if a server is alive
check = autodnsfailover.HttpCheck()

# Implementation to be used for timing parameters (how often to run the checks)
timer = autodnsfailover.TickTimer(10, 2, 3)

# Logger to use (this one will be pretty verbose and log to stdout/stderr)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('autodnsfailover')

# Run the DNS updater with all the previously set parameters!
autodnsfailover.run(fqdn, ipaddr, dns, check, timer, logger)
