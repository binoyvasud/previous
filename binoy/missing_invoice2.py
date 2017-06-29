#!/usr/bin/env python
#
# Billing script
# Automated billing script for all tenants
# Will Add the invoice details details for tenants
# During the run it will check for creation date of tenant
# If creation day and current day is same
# Invoice will be generated to tenant
# Author: Binoy M V

#Importing the required packages
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
from dateutil.relativedelta import relativedelta
import simplejson as json
import pytz
import time
from dateutil import tz
from dateutil.parser import parse
import argparse
import os


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

class EnvDefault(argparse.Action):
    def __init__(self, envvar, required=True, default=None, **kwargs):
        if not default and envvar:
            if envvar in os.environ:
                default = os.environ[envvar]
        if required and default:
            required = False
        super(EnvDefault, self).__init__(default=default, required=required,
                                         **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
  

# Billing engine class
# let us create bill for tenants
class BillingEngine():
    
    # Process and insert Dict to Table
    def dict_create_insert(self, big_dict, tenant_id, begin, end, local_begin, local_end, date):

        # total amount for adding in tables 
        total_amount = big_dict['dict_all_cost_total']

        # dict json dumped for inserting to DB
        final_dict = json.dumps(big_dict)

        # Fetch tenant details
        tenant_details = keystone.tenants.get(tenant_id)

        # get tenant_name
        tenant_name = tenant_details.name

        # begin month and year calculation
        begin_month = begin.month
        begin_year = begin.year
        begin_month = str(begin_month)
        begin_year = str(begin_year)

        # invoice id set
        invoice_id = tenant_name + '-' + begin_month + '-' + begin_year

        paid_cost = '0.0'
        balance_cost = total_amount
        payment_status = '0'

        # for invoice insert
        kwargs = {
            "invoice_id":invoice_id,
            "invoice_date":date,
            "invoice_period_from":local_begin,
            "invoice_period_to":local_end,
            "tenant_id":tenant_id,
            "invoice_data":final_dict,
            "tenant_name":tenant_name,
            "total_cost":total_amount,
            "paid_cost":paid_cost,
            "balance_cost":balance_cost,
            "payment_status":payment_status
        }

        print kwargs

        # final_dict exists
        if final_dict:
            
            print kwargs
            # add the invoice using cloudkitty CLI
            ck.reports.add_invoice(**kwargs)

    # Calculataion of Cost for tenant for the particular period
    # Create necessary dict
    # process and fetch necessary values
    # adding the entries to Dict
    def calc_and_create(self, tenant_id, begin, end, local_begin, local_end, date):

        # Mega Dict which holds all necessary cost details
        big_dict = {
                'dict_compute': {},
                'dict_inbound': {},
                'dict_outbound': {},
                'dict_volume': {},
                'dict_floating': {},
                'dict_cloud_storage': {},
                'dict_instance_addon': {},
                'dict_total_all': {},
                'dict_all_cost_total': {}
        }

        # instance dict
        instance_id_dict = {}
        instance_size_list = {}

        # Instance list fetch
        instances = nt.servers.list(search_opts={'all_tenants':1, 'tenant_id':tenant_id})

        # Instance Flavor list fetch
        instance_flavor_types = nt.flavors.list()
        logging.info('====================================')
        logging.info(instance_flavor_types)
        # Create a Dict of flavor with ID and Name
        # We can use ot for comparison to find flavor of instance
        for flavors in instance_flavor_types:
            logging.info('-------------------flavors--------------')
            logging.info(flavors) 
            
            instance_size_list[flavors.id] = flavors.name

        # Instance details as needed
        for instance in instances:
             
            instance_id = instance.id
            instance_name = instance.name
            logging.info("**********instance_id = %s and instance_name = %s" % (instance_id, instance_name))

            # Getting instance details
            instance_size = nt.servers.get(instance_id)
            print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
            print instance_size.__dict__
            print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
            logging.info(instance_size)
            instance_size = instance_size.flavor['id']
            logging.info("instance_size %s" % (instance_size))

            # Compating the values with list to get flavor
            logging.info("instance_size_list %s" % (instance_size_list))
            try:
                instance_size_name = instance_size_list[instance_size]
            except Exception, e:
                logging.error(e) 
            logging.info("instance_size_name %s" % (instance_size_name))

            logging.info("Getting the necessary instance details for tenant %s" % (tenant_id))
            # Dict with necessary details on instance
            instance_id_dict[instance_id] = instance_name, instance_size_name
            logging.info("instance_name = %s instance_size_name = %s" % (instance_name, instance_size_name))

        # compute charges based on instances
        for a, b in instance_id_dict.iteritems():

            compute_value_for_instance = ck.reports.get_total(tenant_id=tenant_id, begin=begin, end=end, service='compute', instance_id=a)
            logging.info("Calculating compute charges for the tenant %s" % (tenant_id))
            logging.info("compute charges = %s" % (compute_value_for_instance))
            big_dict['dict_compute'][a] = b[0], b[1], compute_value_for_instance

        # inbound charges based on instances
        for a, b in instance_id_dict.iteritems():

            inbound_value_for_instance = ck.reports.get_total(tenant_id=tenant_id, begin=begin, end=end, service='network.bw.in', instance_id=a)
            logging.info("Calculating Inbound charges for the tenant %s" % (tenant_id))
            logging.info("Inbound charges = %s" % (inbound_value_for_instance))
            big_dict['dict_inbound'][a] = b[0], b[1], inbound_value_for_instance

        # outbound charges based on instances
        for a, b in instance_id_dict.iteritems():

            outbound_value_for_instance = ck.reports.get_total(tenant_id=tenant_id, begin=begin, end=end, service='network.bw.out', instance_id=a)
            logging.info("Calculating outbound charges for the tenant %s" % (tenant_id))
            logging.info("Outbound charges = %s" % (outbound_value_for_instance))

            big_dict['dict_outbound'][a] = b[0], b[1], outbound_value_for_instance

        # instance add-on charges based on instances
        for a, b in instance_id_dict.iteritems():

            instance_addon_value_for_instance = ck.reports.get_total(tenant_id=tenant_id, begin=begin, end=end, service='instance.addon', instance_id=a)
            logging.info("Calculating instance addon charges for the tenant %s" % (tenant_id))
            logging.info("instance addon = %s" % (instance_addon_value_for_instance))
            big_dict['dict_instance_addon'][a] = b[0], b[1], instance_addon_value_for_instance

        # Volume calculation
        volume = ck.reports.get_total(tenant_id=tenant_id, begin=begin, end=end, service='volume')
        logging.info("Calculating volume charges for the tenant %s" % (tenant_id))
        logging.info("Volume charges = %s" % (volume))
        big_dict['dict_volume'] = volume

        # floating calculations
        floating = ck.reports.get_total(tenant_id=tenant_id, begin=begin, end=end, service='network.floating')
        logging.info("Calculating floating IP charges for the tenant %s" % (tenant_id))
        logging.info("floating IP charges = %s" % (floating))
        big_dict['dict_floating'] = floating

        # Total Charge based on instance
        for a, b in instance_id_dict.iteritems():

            total_value_for_instance = ck.reports.get_total(tenant_id=tenant_id, begin=begin, end=end, instance_id=a)
            logging.info("Calculating Overall charges(based on instances) for the tenant %s" % (tenant_id))
            logging.info("Overall charges(based on instances) = %s" % (total_value_for_instance))
            big_dict['dict_total_all'][a] = b[0], b[1], total_value_for_instance

        # Cloud storage calculation
        cloud_storage = ck.reports.get_total(tenant_id=tenant_id, begin=begin, end=end, service='cloudstorage')
        logging.info("Calculating cloud storages charges for the tenant %s" % (tenant_id))
        logging.info("cloud storages charges = %s" % (cloud_storage))
        big_dict['dict_cloud_storage'] = cloud_storage

        # Total Charge calculations (Overall including all costs all instances)
        total_all_cost = ck.reports.get_total(tenant_id=tenant_id, begin=begin, end=end)
        logging.info("Calculating Total charges(Overall including all costs all instances) for the tenant %s" % (tenant_id))
        logging.info("Total charges(Overall including all costs all instances) = %s" % (total_all_cost))
        big_dict['dict_all_cost_total'] = total_all_cost

        # Process the Dict and insert to Table
        self.dict_create_insert(big_dict, tenant_id, begin, end, local_begin, local_end, date)

    # Execution starts here
    # Getting the tenant list
    # Fetch the creation_date of tenant if exists
    def invoice_creation(self, args):
    
        # Fetch tenant list
        tenants_list = keystone.tenants.list()
    
        # for each tenants in list
        for tenant in tenants_list:
    
            #print(tenant.__dict__)
    
            # fetch tenant id
            tenant_id = tenant.id
    
            # creation date for tenant
            creation_date = tenant.__dict__.get("creation_date", None)
            logging.info("Creation date for tenant with id %s is %s" % (tenant_id, creation_date))
    
            # if creation_date exists 
            if creation_date is not None: 
    
                # Format creation date
                creation_date = parse(creation_date)
                monthfrom = parse(args.monthfrom)
                if creation_date <= monthfrom:
       		    
		    date_list = []
                    create_date = []
		    created_date = {}
                    invoice = ck.reports.get_invoice(tenant_id=tenant_id)
                    #print ' invoice =====', invoice
                    if invoice:
            
                        # for storing items in dict
                        for items in invoice: 
                            invoice_period_from_date = parse(items.invoice_period_from)
                            date_list.append(str(invoice_period_from_date.year) + '-' + str(invoice_period_from_date.month))
                	    invoice_date = invoice_period_from_date.day
			    create_date.append(items.invoice_date)
			    created_date[str(invoice_period_from_date.year) + '-' + str(invoice_period_from_date.month)] = invoice_period_from_date 
                        
			latest_invoice = max(create_date)
                        latest_invoice = parse(latest_invoice)
			latest_invoice_day = latest_invoice.day
  		    month_from_date = str(monthfrom.year) + '-' + str(monthfrom.month)
		    today_date = str(date.year) + '-' + str(date.month)
		    a = 0
		    	
		    while True:
			print month_from_date ,today_date, date_list, "firstttt"
			if month_from_date in date_list:
			    print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
			    print month_from_date
			    print(created_date)
			    ab = created_date[month_from_date]
			    print ab.day
                            print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
                            
			    month_from_date = parse(month_from_date) + relativedelta(months=+1)
                            month_from_date = str(month_from_date.year) + '-' + str(month_from_date.month)
			    monthfrom = monthfrom + relativedelta(months=+1)	
			    continue
			if month_from_date < today_date:
			    print "*********************************************************", a,"*********************************************************"
			    a+=1
			    month_from_date = parse(month_from_date) + relativedelta(months=+1)
			    month_from_date = str(month_from_date.year) + '-' + str(month_from_date.month)
			    begin = monthfrom
                            local_begin = monthfrom
                            create_invoice_from = monthfrom + relativedelta(months=+1)
                            end = create_invoice_from
			    local_end = create_invoice_from
			    print 'tenant_id=',tenant_id,'begin=', begin, 'end=',end,'local_begin=', local_begin, 'local_end=', local_end, 'date=',date
                            self.calc_and_create(tenant_id, begin, end, local_begin, local_end, date)
			    monthfrom = monthfrom + relativedelta(months=+1)

			else:
			    break
			print "end"
		
            # else section for no creation date exists
            else:
                logging.info("Creation date not exists for client")
                
if __name__ == "__main__":
    #Argument parse
    ap = argparse.ArgumentParser(description='Details ')
    subparsers = ap.add_subparsers(help='sub-command help', dest='subparser_name')
    sp = subparsers.add_parser('invoice-creation', help='List MaaS Nodes')
    sp.add_argument("--monthfrom",
              action=EnvDefault,
              default=None,
              help="Month in integer format",
              envvar="MONTH_INT")
    
    #Argument parser
    args = ap.parse_args()
    if args.subparser_name == 'invoice-creation':
        BillingEngine().invoice_creation(args)
