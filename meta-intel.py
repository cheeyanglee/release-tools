'''
Created on Aug 16, 2017

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
import sys
import hashlib
import os.path
import fnmatch
import shutil
from shutil import rmtree
from utils import where_am_i, sanity_check, split_thing, rejoin_thing, get_md5sum, gen_md5sum


def release_type(build_id):
    RC = split_thing(build_id, ".")[-1].lower()
    foo = RC.find("rc")
    if foo == -1:
        print "%s doesn't appear to be a valid RC candidate. Check your args." %build_id
        print "Please use -h or --help for options."
        sys.exit()
    chunks = split_thing(build_id, ".") # yocto-meta-intel-8, 0-rocko-2, 4, 1, rc1
    chunks.pop()                        # yocto-meta-intel-8, 0-rocko-2, 4, 1
    chunks = rejoin_thing(chunks, ".")  # yocto-meta-intel-8.0-rocko-2.4.1
    chunks = split_thing(chunks, "-")   # yocto, meta, intel, 8.0, rocko, 2.4.1
    foo = chunks[-1].upper()            # If we have a milestone release, we want to fix any lowercase letters in version
    chunks[-1] = foo                    # We want this for an RC_DIR check
    YP_VER = chunks[-1]                 # 2.4.1 or for milestone 2.5_M1
    BRANCH = chunks[-2]
    META_VER = chunks[-3]
    RC_DIR = rejoin_thing(chunks, "-")
    RC_DIR = ".".join([RC_DIR, RC])
    chunks.pop(0)
    RELEASE = rejoin_thing(chunks, "-")
    
    relstring = split_thing(YP_VER, "_")
    if len(relstring) == 1:
        thing = split_thing(relstring[0], ".")
        if len(thing) == 3:
            REL_TYPE = "point"
        elif len(thing) == 2:
            REL_TYPE = "major"
    else:
        MILESTONE = relstring.pop()
        REL_TYPE = "milestone"

    if not (RELEASE and RC and YP_VER and REL_TYPE):
        print "Can't determine the release type. Check your args."
        print "You gave me: %s" %options.build
        sys.exit()

    TAG = "-".join([META_VER, BRANCH, YP_VER])
    RC_SOURCE = os.path.join(AB_BASE, RC_DIR)
    RELEASE_DIR = os.path.join(AB_BASE, RELEASE)

    var_dict = {'RC': RC, 'YP_VER': YP_VER, 'BRANCH': BRANCH, 'META_VER': META_VER, 'RC_DIR': RC_DIR, 'RELEASE': RELEASE, 'REL_TYPE': REL_TYPE, 'TAG': TAG, 'RC_SOURCE': RC_SOURCE, 'RELEASE_DIR': RELEASE_DIR}
    return var_dict


if __name__ == '__main__':

    os.system("clear")
    print

    parser = optparse.OptionParser()
    parser.add_option("-i", "--build-id",
                      type="string", dest="build",
                      help="Required. Release candidate name including rc#. i.e. yocto-meta-intel-8.1-rocko-2.4.2.rc1, etc.")
    (options, args) = parser.parse_args()
    if not (options.build):
        print "You must specify the RC name. i.e. yocto-meta-intel-6.1-rocko-2.4.2.rc1"
        print "Please use -h or --help for options."
        sys.exit()
    
    PATH_VARS = where_am_i()
    VHOSTS = PATH_VARS['VHOSTS']
    AB_HOME = PATH_VARS['AB_HOME']
    AB_BASE = PATH_VARS['AB_BASE']
    DL_HOME = PATH_VARS['DL_HOME']
    DL_BASE = PATH_VARS['DL_BASE']
    print "VHOSTS: %s" %VHOSTS
    print "AB_HOME: %s" %AB_HOME
    print "AB_BASE: %s" %AB_BASE
    print "DL_HOME: %s" %DL_HOME
    print "DL_BASE: %s" %DL_BASE

    VARS = release_type(options.build)

    RC = VARS['RC']
    YP_VER = VARS['YP_VER']
    BRANCH = VARS['BRANCH']
    META_VER = VARS['META_VER']
    RC_DIR = VARS['RC_DIR']
    RELEASE = VARS['RELEASE']
    REL_TYPE = VARS['REL_TYPE']
    TAG = VARS['TAG']
    RC_SOURCE = VARS['RC_SOURCE']
    RELEASE_DIR = VARS['RELEASE_DIR']
  
    # Running through the dictionary to print var values results in random order, making it hard to read. So loop through values in desired order.
    for thing in ['RC_DIR', 'RELEASE', 'REL_TYPE', 'META_VER', 'YP_VER', 'RC', 'BRANCH', 'TAG', 'RC_SOURCE', 'RELEASE_DIR']:
        print "%s: %s" %(thing, VARS[thing])

    META_TARBALL = RELEASE + ".tar.bz2"
    print "META_TARBALL: %s\n" %META_TARBALL

    print "Creating the staging directory."
    if not os.path.exists(RELEASE_DIR):
        print "Creating the release dir."
        os.mkdir(RELEASE_DIR)
    else:
        print "Staging dir exists! Quitting."
        sys.exit()
        
    # Find and copy the meta-intel blob over to staging
    print "Finding the meta-intel blob."
    for file in os.listdir(RC_SOURCE):
        if fnmatch.fnmatch(file, 'meta-intel-*.tar.bz2'):
            blob = file
            blob_source = (os.path.join(RC_SOURCE, file))
    if not blob_source:
        print "I can't find the meta-intel blob. Quitting. Check your RC dir: %s" %RC_SOURCE
        sys.exit()
    blob_dir = split_thing(blob, ".")
    blob_dir = rejoin_thing(blob_dir[:-2], ".")
    print "Copying the meta-intel blob to the staging directory."
    os.system("cp -v %s %s" %(blob_source, RELEASE_DIR))
    os.chdir(RELEASE_DIR)
    print "Creating the new meta-intel blob."
    os.system("tar jxf %s" %blob)
    meta_dir = split_thing(META_TARBALL, ".")
    meta_dir = rejoin_thing(meta_dir[:-2], ".")
    shutil.move(blob_dir, meta_dir)
    os.remove(blob)
    os.system("tar jcf %s %s" %(META_TARBALL, meta_dir))
    rmtree(meta_dir)
    print "Creating new symlink."
    os.symlink(META_TARBALL, blob)
    print "Generating the md5sum."
    gen_md5sum(RELEASE_DIR)
    print "DONE!"

