#!/usr/bin/env python

import boto

class Route53Dns(object):
    """
    Updates a DNS zone hosted by Amazon Route53
    """
    def __init__(self, access_key_id, secret_access_key, zone, notes=None, ttl=60):
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.zone = zone if zone.endswith('.') else zone + '.'
        self.notes = notes
        self.ttl = ttl
        self.zone_id = None
        self._zone  # hacky way of getting self.zone_id
        

    @property
    def _conn(self):
        return boto.connect_route53(self.access_key_id, self.secret_access_key)

    @property
    def _zone(self):
        if not self.zone_id:
            for zone in self._conn.get_all_hosted_zones() \
                .get('ListHostedZonesResponse').get('HostedZones'):

                if zone['Name'] == self.zone:
                    selected_zone_id = zone['Id'].replace('/hostedzone/','')
                    self.zone_id = selected_zone_id

        if self.zone_id:
            return self._conn.get_all_rrsets(self.zone_id)

        return None

    def _resources(self, fqdn):
        fqdn = fqdn if fqdn.endswith('.') else fqdn+'.'
        return [h
                for h in self._zone
                if h.name==fqdn]

    def getARecords(self, fqdn):
        fqdn = fqdn if fqdn.endswith('.') else fqdn+'.'
        records = [h.resource_records
                for h in self._resources(fqdn)
                if h.type == 'A']
        return records[0] if len(records) > 0 else []

    def addARecord(self, fqdn, a):
        fqdn = fqdn if fqdn.endswith('.') else fqdn+'.'
        resource = self._resources(fqdn)

        changes = boto.route53.record.ResourceRecordSets(self._conn,
            self.zone_id)

        records = []
        if resource:
            # update record
            records = self.getARecords(fqdn)
            ttl = [r.ttl for r in self._resources(fqdn) if r.type == 'A'][0]
            change = changes.add_change("DELETE", fqdn, "A", ttl)
            for record in records:
                change.add_value(record)

        # add ourselves to the list
        records.append(a)

        # make sure list is unique (ugly)
        records = list(set(records))

        # create new A record
        change = changes.add_change("CREATE", fqdn, "A", self.ttl)

        # re-apply A records
        for record in records:
            change.add_value(record)
        changes.commit()


    def delARecord(self, fqdn, a):
        fqdn = fqdn if fqdn.endswith('.') else fqdn+'.'
        resource = self._resources(fqdn)

        changes = boto.route53.record.ResourceRecordSets(self._conn,
            self.zone_id)

        records = []
        if resource:
            # update record
            records = self.getARecords(fqdn)
            ttl = [r.ttl for r in self._resources(fqdn) if r.type == 'A'][0]
            change = changes.add_change("DELETE", fqdn, "A", ttl)
            for record in records:
                change.add_value(record)

        # add ourselves to the list
        records.append(a)

        # make sure list is unique (ugly)
        records = list(set(records))

        # create new A record
        change = changes.add_change("CREATE", fqdn, "A")

        # re-apply A records
        for record in records:
            if record == a:
                continue    # Don't re-add what we are deleting
            change.add_value(record)
        changes.commit()


