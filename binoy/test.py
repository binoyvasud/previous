#!/usr/bin/env python
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
import calendar
from cloudkitty import utils as ck_utils

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
print "hai1"
ta_begin_period = '2017-04-01 00:00:00'
ta_end_period = '2017-04-30 23:59:59'
ta_tenant_id = ' 5a4fb03113d44f7590789f9aa9ff3618'
rate = '1.8'
#begin= 2017-04-01 00:00:00 end= 2017-04-30 23:59:59 tenant_id= 5a4fb03113d44f7590789f9aa9ff3619
"""
list_rated_frames = ck.storage.dataframes.list(resource_type='tenant.addon',
                                                           begin=ta_begin_period,
                                                           end=ta_end_period,
                                                           tenant_id=ta_tenant_id)
"""
search_dict = {'resource_type':'tenant.addon','begin':ta_begin_period,'end':ta_end_period,'tenant_id':ta_tenant_id}
#list_rated_frames = ck.storage.dataframes.list(search_dict)
print "hai2"
#print list_rated_frames
dicts = {'name': 'ta_tenant.name', 'description': 'ta_tenant.description', 'tenant_id': ta_tenant_id}
create_dict = {'res_type':'tenant.addon',
                               'begin':ta_begin_period,
                               'end':ta_begin_period,
                               'tenant_id':ta_tenant_id,
                               'unit':'tenant',
                               'qty':'1',
                               'rate':rate}
#add_rated_frames = ck.storage.dataframes.create(create_dict)
add_rated_frames = ck.storage.dataframes.create(res_type='tenant.addon',
                                                                begin=ta_begin_period,
                                                                end=ta_begin_period,
                                                                tenant_id=ta_tenant_id,
                                                                unit='tenant', 
                                                                qty='1', 
                                                                rate=rate, 
                                                                desc=dicts)

