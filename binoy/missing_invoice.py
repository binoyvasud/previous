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
        
# Execution starts here
# Getting the tenant list
# Fetch the creation_date of tenant if exists
def invoice_creation(args):

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
		print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
		print creation_date
		print "_+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++_"
		if creation_date <= parse(args.monthfrom):
		    #print "data is less"

		    invoice = ck.reports.get_invoice(tenant_id=tenant_id)
		    #print ' invoice =====', invoice
		    if invoice:
	
			date_list = []
 			# for storing items in dict
                    	for items in invoice: 
			    invoice_period_from_date = parse(items.invoice_period_from)
			    #print invoice_period_from_date
			    #print invoice_period_from_date.day
			    #print invoice_period_from_date.month
			    #print invoice_period_from_date.year
			    date_list.append(invoice_period_from_date)
	
		    print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
		    #print date_list
		    first_invoice = min(date_list)
	
		    first_invoices = str(first_invoice.year) + '-'+ str(first_invoice.month)+ '-'+ str(first_invoice.day)+ ' 00:00:00' 
		    #print 'args.monthfrom', parse(args.monthfrom), args.monthfrom 
		    #print 'first_invoice==,', first_invoice, type(first_invoice)
		    first_invoice =  datetime.datetime.strptime(first_invoices, '%Y-%m-%d %H:%M:%S')
		    #print first_invoice #, parse(first_invoice, '%Y-%m-%dT%H:%M:%S')
		    #print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
                    create_invoice_from = parse(args.monthfrom)
		   
		    
 		    while True:
			print create_invoice_from, first_invoice			
			if create_invoice_from <= first_invoice:
			    print 'create_invoice_from', create_invoice_from
			    create_invoice_from = create_invoice_from + relativedelta(months=+1)	   
			self.calc_and_create(tenant_id, begin, end, local_begin, local_end, date)
     
			    continue
			else:
			    break
		    

		    #parse(args.monthfrom)  

		    """
	            # replacing the creation_date of tenant 
                    # which have unclear creation date      
                    if creation_date.day in (29, 30, 31):

                        logging.info("Assuming creation date for tenant %s having unclear creation date" % (creation_date))
                        creation_date = creation_date.replace(day=28)

                        # start with date check operations
                        #self.date_check(creation_date, tenant_id, date)
		        print "----------------------------------------------------"
		        print "hai1"
     	                print "----------------------------------------------------"
                        # tenant have clear creation date
                    else:

                        # start with date check operations
   		        print "----------------------------------------------------"
		        print "hai2"
		        invoice = ck.reports.get_invoice(tenant_id=tenant_id)
		        print ' invoice =====', invoice	
	 	        print "----------------------------------------------------"
                        #self.date_check(creation_date, tenant_id, date)
		    """

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
        invoice_creation(args)
