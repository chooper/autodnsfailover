# DNS

## Interface

A class implementing the DNS interface must provide the following methods:

* getARecords(fqdn): return a list of all IP addresses associated with
  the given FQDN.
* addARecord(fqdn,a): add a new A record for the given FQDN.
* delARecord(fqdn,a): delete the A record for the given FQDN.

The constructor will typically be implementation-dependent, and allow
to set the credentials and/or the zone to act upon.

## Zerigo

ZerigoDns is the reference class for this interface.

## Boto

A boto implementation (allowing to update records located on AWS Route53)
could be useful, but the current interface is still a bit rough (it involves
generating queries directly in XML).

# IP Address

## Interface

A class implementing the IP address discovery interface must provide a
getOwnAddr() method, returning the IP address of the current host.

## myip.enix.org

The reference implementation makes a call to http://myip.enix.org/REMOTE_ADDR
to find out the public IP address of the currnet host.

This method relies on an external service (which is bad). However, it is
probably the one that works on the greatest number of servers (except those
who can't resolve DNS, or can't connect outside, or use a different path
for outgoing and incoming traffic, e.g. a HTTP proxy).

## EC2

When running on EC2, it would be reasonable to directly check EC2 meta-data,
e.g. on http://169.254.169.254/latest/meta-data/public-ipv4.

## ifconfig

Invoking ifconfig and parsing the output would probably work on some
Linux/UNIX variants.

# Check

A class implementing the check interface must provide a single check(ipaddr)
method. The method should check the server running at the given IP address,
and return True (if it works) or False (if it doesn't).

The check does not have to bother about timeouts: the main script
will run the check in a subprocess and kill it if it takes too long
to complete.

## HTTP

The default implementation does a HTTP check. The constructor allows
to specify optional method, url, body, headers, port, and a list
of valid status codes. The defaults should be fine for most use cases.

## ICMP

It would be sensible to provide a simple ICMP check.

## TCP

There would be two use-cases where a TCP check would be better than a ICMP
check:

* ICMP is filtered, and you just want to make sure that this SSH or Apache
  process is still listening on port 22 or 80 to see if the machine is still
  up;
* the mission-critical process is prone to crashes, and it's not a web
  server (otherwise, the HTTP check would be probably better).

# Timer

The timer schedules the checks. It must expose two methods:

* getNextCheckTime(): returns the UNIX timestamp at which the next check
  should be executed;
* getCheckTimeout(): returns the time alloted to the check to execute
  (once this time is elapsed, the check is considered as failed).

## TickTimer

This implementation schedules a check at regular intervals with a fixed
timeout.