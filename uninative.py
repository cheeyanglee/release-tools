# SPDX-License-Identifier: GPL-2.0-only
'''
Created on July 31, 2017

__author__ = "Tracy Graydon"
__copyright__ = "Copyright 2017-2018 Intel Corp."
__credits__ = ["Tracy Graydon"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Tracy Graydon"
__email__ = "tracy.graydon@intel.com"
'''

import os
import optparse
import socket
import sys
import glob
import os.path
import shutil
from shutil import rmtree, copyfile
from unihash import main
from where_am_i import where_am_i
from utils import split_thing, get_list, sanity_check, sync_it

def get_build_hash(source_dir):
    # This looks in the build directory and gets the hash from the poky tarball.
    os.chdir(source_dir)
    files = glob.glob('*.bz2')
    poky_blob = filter(lambda x: 'poky' in x, files).pop()
    chunks = split_thing(poky_blob, ".")
    hash = split_thing(chunks[0], '-').pop()
    os.chdir(WORK_DIR)
    return hash

if __name__ == '__main__':

    os.system("clear")
    print

    WORK_DIR = os.getcwd() 
    PATH_DICT = where_am_i()
    VHOSTS = PATH_DICT['VHOSTS']
    AB_HOME = PATH_DICT['AB_HOME']
    DL_HOME = PATH_DICT['DL_HOME']
    DL_DIR = os.path.join(DL_HOME, "uninative")
    TOOLS_BASE = os.path.join(AB_HOME, "buildtools")
    LINK_DIR = os.path.join(AB_HOME, "uninative")

    CRUFT_LIST = ['*.md5sum', '*.json'] # We don't want to copy this stuff for a release.

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
        print("BUILD_ID: %s" %BUILD_ID)
        REL_ID = options.version
        print("REL_ID: %s\n" %REL_ID)
        
        SOURCE = os.path.join(TOOLS_BASE, BUILD_ID)
        RELEASE_DIR = os.path.join(DL_DIR, REL_ID)
        sanity_check(SOURCE, RELEASE_DIR)
        TOOLS_DIR = os.path.join(SOURCE, "toolchain")
    else:
        print("Build ID and Release version are required arguments. Please check your args.")
        print("Please use -h or --help for options.")
        sys.exit()

    # Go find the poky commit that we built for the uninative release.
    POKY_HASH = get_build_hash(SOURCE)
    print("POKY_HASH: %s" %POKY_HASH)
    
    # Make the dowloads directory and copy the stuff over from build dir
    tools_list = get_list(TOOLS_DIR)
    for dirname in tools_list:
        SUB_DIR = os.path.join(TOOLS_DIR, dirname)
        sync_it(SUB_DIR, RELEASE_DIR, CRUFT_LIST)

    # Create a symlink to VHOSTS/autobuilder.yoctoproject.org/pub/uninative from downloads
    # This is a convenience thing. Can get to this via public URL for ease of review.
    if not os.path.exists(LINK_DIR):
        os.mkdir(LINK_DIR)
    TARGET = os.path.join(LINK_DIR, REL_ID)
    if not os.path.islink(TARGET):
       print("Creating symlink from %s to %s\n" %(RELEASE_DIR, TARGET))
       os.symlink(RELEASE_DIR, TARGET)
    else:
       print("Link to %s already exists. Might want to check on that." %TARGET)

    # Take the poky commit and find the corresponding OE-Core revision.
    # We need this for tagging purposes for poky and openembedded-core.
    main(POKY_HASH)
