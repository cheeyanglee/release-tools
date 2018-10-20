'''
Created on Oct 16, 2018

__author__ = "Tracy Graydon"
__copyright__ = "Copyright 2018 Intel Corp."
__credits__ = ["Tracy Graydon"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Tracy Graydon"
__email__ = "tracy.graydon@intel.com"
'''

import os
import socket
import sys
import os.path

def where_am_i():
    abhost = socket.getfqdn()
    print "ABHOST: %s" %abhost
    if "yocto.io" in abhost:
        VHOSTS = "/srv/autobuilder"
    elif "autobuilder.yoctoproject.org" in abhost:
        VHOSTS = "/srv/www/vhosts"
    else:
        print "I don't know where we are, so I am going to guess..."
        # Uncomment this if you want to use /srv/www/vhosts as the VHOST dir. It's useful for testing.
        #VHOSTS = "/srv/www/vhosts"
        VHOSTS = "/srv/autobuilder"
        print "Setting VHOSTS to %s" %VHOSTS
    AB_HOME = os.path.join(VHOSTS, "autobuilder.yoctoproject.org/pub") # uninative release (uninative.py) uses this
    AB_BASE = os.path.join(AB_HOME, "releases") # all RC candidates live here
    DL_HOME = os.path.join(VHOSTS, "downloads.yoctoproject.org/releases") # uninative release (uninative.py) uses this
    DL_BASE = os.path.join(DL_HOME, "yocto") # all other releases use this
    path_dict = {'VHOSTS': VHOSTS, 'AB_HOME': AB_HOME, 'AB_BASE': AB_BASE, 'DL_HOME': DL_HOME, 'DL_BASE': DL_BASE}
    return path_dict

def get_list(dirname):
    dirlist = os.listdir(dirname)
    dirlist.sort()
    return dirlist

def split_thing(thing,st(dirname):
    dirlist = os.listdir(dirname)
    dirlist.sort()
    return dirlist

def rejoin_thing(thing, marker):
    filebits = marker.join(thing)
    return filebits

def sanity_check(source, target):
    if not os.path.exists(source):
       print
       print "SOURCE dir %s does NOT EXIST." %source
       print
       sys.exit()
    if not os.listdir(source):
       print
       print "SOURCE dir %s is EMPTY" %source
       print
    if os.path.exists(target):
       print
       print "The TARGET directory %s already exists! " %target
       print
       sys.exit()
    return

def sync_it(source, target, exclude_list):
    print "Syncing %s to %s" %(source, target)
    source = source + "/"
    if exclude_list:
        exclusions = ['--exclude=%s' % x.strip() for x in exclude_list]
        print "Exclusions: %s" %exclusions
        print
        exclude = "--exclude=" + exclude_list[0]
        length = len(exclude_list)
        for i in range(1, length):
            exclude = exclude + " " + "--exclude=" + exclude_list[i]
        command = 'rsync -avrl ' + str(exclude) + " " + str(source) + " " + str(target)
        os.system(command)
    else:
        os.system("rsync -avrl '%s' '%s'" %(source, target))
    print
    return

def check_rc(rc_source):
    if not os.path.isdir(rc_source):
        print "I cannot find %s. Please check your RC name." %rc_source
        print "Please use -h or --help for options."
        found = "False"
    else:
        print "Found RC dir %s." %rc_source
        found = "True"
    return found
