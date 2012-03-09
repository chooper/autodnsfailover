# autodnsfailover

This is a little Python script to automatically update DNS records for a bunch of servers participating in a [Round-Robin DNS setup](http://en.wikipedia.org/wiki/Round-robin_DNS).

It tries to be very modular, so each basic feature is isolated in a separate class. This allows to replace e.g. the "are you alive" check with your own specific implementation, hopefully as cleanly as possible.

# How it works

Suppose you have a DNS round-robin setup involving three web servers, with the following DNS information:

    www.example.com A 1.1.1.1
    www.example.com A 1.1.1.2
    www.example.com A 1.1.1.3

You will run the autodnsfailover daemon on all three servers. When the daemon starts, it will make sure that the record for the server it's running on is present in the DNS. Then, it will check all the servers in the DNS (including itself). If one is found to be failing, it will be removed from the DNS.

With the configuration described above, if you add a 4th server (with IP address 1.1.1.4), you don't have anything special to do. The new server will also run the autodnsfailover daemon, so it will automatically add the relevant DNS record. If at some point you stop one of the servers, the other servers will detect that and remove its DNS record.

Of course, your DNS record TTL should be as low as possible, to make sure that failed servers removal is seen as soon as possible by the rest of the world.

# How to use it

You will need:

* a Zerigo account with your DNS zones (or to write an appropriate "DNS" class implementation to dynamically update your DNS records);
* to write a script (see the sample1.py script for an example), with your credentials, the name of the DNS entry to update, and a few other details;
* to arrange this script to be run automatically, and restarted automatically (it will exit when it fails to check itself correctly).

Since our servers all have a Supervisor infrastructure, we manage the autodnsfailover daemon with a small supervisord.conf snippet, but you could also use e.g. start-stop-daemon or whatever you like. The script stays in foreground by default.

# Safe guards

If for some reason, the check logic itself is broken, you could end up in a situation where each peer removes the others, leaving you with zero server in the round robin. Doing proper synchronization and locking over DNS records is probably risky business. So, to avoid problems, autodnsfailover implements the following policy:

* before checking other peers, it does a self-check, and if the self-check fails, it aborts;
* peers are sorted before being checked, to make sure that the checks will happen in the same order on all hosts;
* when a peer is found to be dead, it is removed, but the daemon will then start over the full loop: it will do a self-check before checking other hosts;
* if there is only one record, it won't be removed.

This is not 100% bullet-proof (there are scenarios where a bad timing could cause peers to remove each others) but it should at least prevent basic fsck-ups.

# Advanced example

Check sample2.py for examples of more advanced options:

* it sets the hostname of your server as a note attached to Zerigo record,
* assuming you run on EC2, it retrieves your IP address using EC2 internal API,
* the check is done on a specific virtualhost (assumed to be a very simple and stable static service),
* local logs have timestamps, and additionnally, messages of priority ERROR and CRITICAL are sent by e-mail.

This is almost exactly the setup used at dotCloud.

sample3.py is an extension of sample2.py. Instead of using Zerigo DNS, it uses Amazon's Route53 and supports the use of a YAML-based config file.

# Interfaces

The interfaces marked "TBD" are not implemented, but we acknowledge that they would probably be very useful to others, and that they should be pretty straightforward to implement.

## DNS

The DNS interface is responsible for updating the DNS records. A class implementing the DNS interface must provide the following methods:

* getARecords(fqdn): return a list of all IP addresses associated with the given FQDN.
* addARecord(fqdn,a): add a new A record for the given FQDN.
* delARecord(fqdn,a): delete the A record for the given FQDN.

The constructor will typically be implementation-dependent, and allow to set the credentials and/or the zone to act upon.

### Zerigo

ZerigoDns is the reference class for this interface. It is useful only if your zones are hosted by [Zerigo](http://www.zerigo.com/managed-dns). It will use the Zerigo API to list, add, and remove, DNS records.

### Boto

A boto implementation (allowing to update records located on AWS Route53) is now available! See sample3.py for an example of how to use it.

### DDNS

TBD.

Dynamic DNS (with DNSSEC or something like that) could also be interesting. Feel free to contribute an implementation if you need it :-)

## IP Address

The IP address class is just used to retrieve our own IP address. While this might sound obvious ("just parse the output of ifconfig!"), it is actually a little bit more complex. An increasing number of infrastructure providers don't allocate a public IP address to your server. On Amazon EC2, for instance, your instance has a private IP address. Retrieving the public IP address requires some extra work.

A class implementing the IP address discovery interface must just provide a getOwnAddr() method, returning the IP address of the current host.

### WhatIsMyAddr

The reference implementation makes a call to a remote URL to find out the public IP address of the current host.

This method relies on an external service (which is bad). However, it is probably the one that works on the greatest number of servers (except those who can't resolve DNS, or can't connect outside, or use a different path for outgoing and incoming traffic, e.g. a HTTP proxy).

By default, it will use http://myip.enix.org/REMOTE_ADDR. If you are on EC2, you can use http://169.254.169.254/latest/meta-data/public-ipv4 instead.

### ifconfig

TBD

Invoking ifconfig and parsing the output would probably work on some Linux/UNIX variants. Since this code was initially written to run on EC2, the plugin is not implemented yet, however!

## Check

The check class does a "are you alive?" verification. It must provide a single method, check(ipaddr). The method should check the server running at the given IP address, and return True (if it works) or False (if it doesn't).

If the check must call an external program, it can call a subprocess, but it's even better to directly exec() the external program: the main check will be executed in a forked process anyway, to make sure that any issue with the check function won't harm the main program. If you exec() in the check(), the exit status will be used to indicate success or failure, with a return code of zero and non-zero.

Since the main script runs the check in a subprocess, the check code does not have to bother about timeouts: it will be killed (and considered as failed) if it takes too long to complete.

### HTTP

The default implementation does a HTTP check. The constructor allows to specify optional method, url, body, headers, port, and a list of valid status codes. The defaults should be fine for most use cases.

### ICMP

TBD

It would be sensible to provide a simple ICMP check.

### TCP

TBD

There would be two use-cases where a TCP check would be better than a ICMP
check:

* ICMP is filtered, and you just want to make sure that this SSH or Apache process is still listening on port 22 or 80 to see if the machine is still up;
* the mission-critical process is prone to crashes, and it's not a web server (otherwise, the HTTP check would be probably better).

## Timer

The timer schedules the checks: how often they should be run, what should be the timeout, and how many times a check should be attempted before declaring it failed. It must expose those methods:

* getNextCheckTime(): returns the UNIX timestamp at which the next check should be executed;
* getCheckTimeout(): returns the time alloted to the check to execute (once this time is elapsed, the check is considered as failed).
* getRetry(): returns the number of times that a check should report an error before it is considered as really failing. 

### TickTimer

This implementation schedules a check at regular intervals with a fixed timeout and a constant number of tries.

## Logger

The code uses a logger compatible with the Python logging module. To get a full log of every event on stdout/stderr, you can use the following logger:

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('autodnsfailover')

We recommend checking the [Python Logging Tutorial](http://docs.python.org/howto/logging.html#logging-basic-tutorial); in our production setup, we use it to:

* add timestamps to the logs,
* mail to our ops team all messages with a priority equal or above WARNING.
