# SPDX-License-Identifier: GPL-2.0-only
'''
Created on Aug 21, 2018

__author__ = "Tracy Graydon"
__copyright__ = "Copyright 2018 Intel Corp."
__credits__ = ["Tracy Graydon"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Tracy Graydon"
__email__ = "tracy.graydon@intel.com"


We use different paths on the different AB clusters. Figure out what cluster we are on and
set some paths accordingly. Root path on the yocto.io AB cluster is /srv/autobuilder. For
"old" cluster, it's /srv/www/vhosts. where_am_i figures it out for us.

'''

import os
import sys
import socket

def where_am_i():
    hosts = ["ubuntu2004-ty-1", "ubuntu2004-ty-2", "ubuntu1804-ty-1", "ubuntu1804-ty-2", "ubuntu1804-ty-3", "ubuntu1604-ty-1",
                "centos7-ty-1", "centos7-ty-2", "centos7-ty-3", "centos7-ty-4", "centos8-ty-1", "centos8-ty-2",
                "fedora29-ty-1", "fedora30-ty-1", "fedora30-ty-2",
                "debian8-ty-1", "debian9-ty-2", "debian10-ty-1", "debian10-ty-2", "debian10-ty-3",
                "tumbleweed-ty-1", "tumbleweed-ty-2", "tumbleweed-ty-3", "opensuse151-ty-1", "opensuse150-ty-1",
                "ubuntu1804-ty-1", "ubuntu1804-ty-2", "ubuntu1804-ty-3",
                "perf-ubuntu1604", "perf-centos7",
                "ubuntu1804-arm-1"]
    abhost = socket.getfqdn()
    print "ABHOST: %s" %abhost
    if "yocto.io" in abhost or abhost in hosts:
        VHOSTS = "/srv/autobuilder"
    elif "autobuilder.yoctoproject.org" in abhost:
        VHOSTS = "/srv/www/vhosts"
    else:
        print("I don't recognize this host, so defaulting to /srv/www/vhosts")
        # Uncomment this if you want to use /srv/autobuilder as the VHOSTS dir. It's useful for testing.
        #VHOSTS = "/srv/autobuilder"
        VHOSTS = "/srv/www/vhosts"
        print("Setting VHOSTS to %s" %VHOSTS)
    AB_HOME = os.path.join(VHOSTS, "autobuilder.yoctoproject.org/pub") # uninative release (uninative.py) uses this
    AB_BASE = os.path.join(AB_HOME, "releases") # all RC candidates live here
    DL_HOME = os.path.join(VHOSTS, "downloads.yoctoproject.org/releases") # uninative release (uninative.py) uses this
    DL_BASE = os.path.join(DL_HOME, "yocto") # all other releases use this
    path_dict = {'VHOSTS': VHOSTS, 'AB_HOME': AB_HOME, 'AB_BASE': AB_BASE, 'DL_HOME': DL_HOME, 'DL_BASE': DL_BASE}
    return path_dict

if __name__ == '__main__':

    PATH_VARS = where_am_i()
    VHOSTS = PATH_VARS['VHOSTS']
    AB_HOME = PATH_VARS['AB_HOME']
    AB_BASE = PATH_VARS['AB_BASE']
    DL_HOME = PATH_VARS['DL_HOME']
    DL_BASE = PATH_VARS['DL_BASE']
    print("VHOSTS: %s" %VHOSTS)
    print("AB_HOME: %s" %AB_HOME)
    print("AB_BASE: %s" %AB_BASE)
    print("DL_HOME: %s" %DL_HOME)
    print("DL_BASE: %s" %DL_BASE)
