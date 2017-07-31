'''
Created on July 31, 2017

__author__ = "Tracy Graydon"
__copyright__ = "Copyright 2017 Intel Corp."
__credits__ = ["Tracy Graydon"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Tracy Graydon"
__email__ = "tracy.graydon@intel.com"
'''

import os
import optparse
import sys
import glob
import os.path
import shutil
from shutil import rmtree, copyfile
from subprocess import call

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
       print "I can't let you do it, Jim. The TARGET directory %s exists." %target
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

def get_list(dirname):
    dirlist = os.listdir(dirname)
    dirlist.sort()
    return dirlist


if __name__ == '__main__':

    os.system("clear")
    print

    # Root path on the new AB cluster is /srv/autobuilder. Old cluster still uses /srv/www/vhosts.
    # Will keep this commented out, but handy, until I get around to adding a swtich to pass in a
    # path override or a dynamic check for where things live.
    #VHOSTS = "/srv/www/vhosts"
    VHOSTS = "/srv/autobuilder"
    AB_BASE = os.path.join(VHOSTS, "autobuilder.yoctoproject.org/pub/")

    DL_DIR = os.path.join(VHOSTS, "downloads.yoctoproject.org/releases")
    DL_BASE = os.path.join(DL_DIR, "uninative")
    TOOLS_BASE = os.path.join(AB_BASE, "buildtools")  
     
    CRUFT_LIST = ['*.md5sum', '*.json']

    parser = optparse.OptionParser()
    parser.add_option("-i", "--build-id",
                      type="string", dest="build",
                      help="Required. The buildtools build ID. i.e. 20170731-1")
    parser.add_option("-n", "--release-is",
                      type="string", dest="version",
                      help="Required. This is the uninative release version. i.e. 1.7, etc.")

    (options, args) = parser.parse_args()


    if options.build and options.version:
        BUILD_ID = options.build
        print "BUILD_ID: %s" %BUILD_ID
        REL_ID = options.version
        print "REL_ID: %s" %REL_ID
        print
        
        SOURCE = os.path.join(TOOLS_BASE, BUILD_ID)
        if not os.path.exists(SOURCE):
            print "%s does not appear to be a valid source dir. Check your args." %SOURCE
            sys.exit()
        RELEASE_DIR = os.path.join(DL_BASE, REL_ID)
        TOOLS_DIR = os.path.join(SOURCE, "toolchain")
       
    else:
        print "Build ID and Release version are required arguments. Please check your args."
        print "Please use -h or --help for options."
        sys.exit()

    tools_list = get_list(TOOLS_DIR)
    for dirname in tools_list:
	sub_dir = os.path.join(TOOLS_DIR, dirname)
        sync_it(sub_dir, RELEASE_DIR, CRUFT_LIST)
