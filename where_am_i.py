'''
Created on Aug 21, 2018

__author__ = "Tracy Graydon"
__copyright__ = "Copyright 2018 Intel Corp."
__credits__ = ["Tracy Graydon"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Tracy Graydon"
__email__ = "tracy.graydon@intel.com"
'''

import sys
import socket

def where_am_i():
    abhost = socket.getfqdn()
    if "yocto.io" in abhost:
        VHOSTS = "/srv/autobuilder"
    if "autobuilder.yoctoproject.org" in abhost:
        VHOSTS = "/srv/www/vhosts"
    else:
        print "We're lost. Are you on an autobuilder host system? This is not intended to work elsewhere. You'll need to hack your path accordingly.\n"
        sys.exit()
    return VHOSTS

if __name__ == '__main__':

    # We use different paths on the different AB clusters. Figure out what cluster we are on and
    # set the paths accordingly. Root path on the yocto.io AB cluster is /srv/autobuilder. For
    # "old" cluster, it's /srv/www/vhosts. where_am_i figures it out for us.
    VHOSTS = where_am_i()
