#!/usr/bin/env python
#
# Billing script
# Automated billing script for all tenants
# Will Add the invoice details details for tenants
# During the run it will check for creation date of tenant
# If creation day and current day is same
# Invoice will be generated to tenant
#
# Author: Muralidharan.S
#

from cloudkittyclient import client
from cloudkittyclient.common import utils
from novaclient import client as nova_client
from keystoneclient.v2_0 import client as kclient
from keystoneclient.auth.identity import v3
from keystoneclient import session
from collections import defaultdict
import ConfigParser
import datetime
import logging
import json
import dateutil.relativedelta
import simplejson as json
import pytz
import time
from dateutil import tz

# For importing details from config file
config = ConfigParser.RawConfigParser()
config.read('/etc/cloudkitty/cloudkitty.conf')

# Fetch details from config file
# For connection part
connection = dict(config.items("keystone_fetcher"))
extra_config = dict(config.items("extra_conf"))

# kwargs for connection
kwargs_conn = {
    "tenant_name":connection['username'],
    "auth_url":connection['auth_url'],
    "username":connection['username'],
    "password":connection['password'],
    "nova_version": extra_config['nova_version'],
    "cloudkitty_version": extra_config['cloudkitty_version'],
    "log_file": extra_config['log_file'],
    "region_name": connection['region']
}

# keystone client establish connection
keystone = kclient.Client(**kwargs_conn)

# Establish the connection Cloudkitty
ck = client.get_client(kwargs_conn.get('cloudkitty_version'), **kwargs_conn)

# Establish the connection NOVA
nt = nova_client.Client(kwargs_conn.get('nova_version'), kwargs_conn.get('username'), kwargs_conn.get('password'), kwargs_conn.get('tenant_name'), kwargs_conn.get('auth_url'))

# Logging the items
# Log Definition
logging.basicConfig(filename=kwargs_conn.get('log_file'), level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%m-%d %H:%M:%S')

# current date operations
mylist = []
today = datetime.datetime.today()
mylist.append(today)
date = mylist[0]

# for debugging you can assume date here
#date = date.replace(day=22, month=04, year=2016, hour=22, minute=47, second=59, microsecond=0)
# print date

# Billing engine class
# let us create bill for tenants
class BillingEngine():

    # Execution starts here
    # Getting the tenant list
    # Fetch the creation_date of tenant if exists
    def run(self):

        # Fetch tenant list
        tenants_list = keystone.tenants.list()

        # for each tenants in list
        for tenant in tenants_list:

            print(tenant)
            print(tenant)
            print (tenant.__dict__)


            # fetch tenant id
            tenant_id = tenant.id

            # creation date for tenant
            creation_date = tenant.__dict__.get("creation_date", None)
        
# Execute billing engine
if __name__ == "__main__":
        BillingEngine().run()

