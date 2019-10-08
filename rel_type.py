# SPDX-License-Identifier: GPL-2.0-only
'''
Created on Oct 16, 2018

__author__ = "Tracy Graydon"
__copyright__ = "Copyright 2018, Intel Corp."
__credits__ = ["Tracy Graydon"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Tracy Graydon"
__email__ = "tracy.graydon@intel.com"
'''

import os
import optparse
import sys
import os.path
from utils import where_am_i, check_rc, split_thing, rejoin_thing

def release_type(build_id):
    MILESTONE = "NONE"
    build_id = build_id.lower()
    RC = split_thing(build_id, ".")[-1]
    foo = RC.find("rc")
    if foo == -1:
        print "%s doesn't appear to be a valid RC candidate. Check your args." %build_id
        print "Please use -h or --help for options."
        sys.exit()
    chunks = split_thing(build_id, ".") # i.e. split yocto-2.1_m1.rc1
    chunks.pop()
    chunks[1] = chunks[1].upper()
    RELEASE = rejoin_thing(chunks, ".")  # i.e. yocto-2.1_m1
    REL_ID = split_thing(RELEASE, "-")[-1].upper()
    RC_DIR = rejoin_thing([RELEASE, RC], ".")
    relstring = split_thing(REL_ID, "_")
    if len(relstring) == 1:
        thing = split_thing(relstring[0], ".")
        if len(thing) == 3:
            REL_TYPE = "point"
        elif len(thing) == 2:
            REL_TYPE = "major"
    else:
        REL_TYPE = "milestone"
        MILESTONE = relstring.pop()
        
    # This is here to catch anything that slips by or is a result of something unexpected
    # in all the splitting that happens above.
    if not (RELEASE and RC and REL_ID and REL_TYPE):
        print "Can't determine the release type. Check your args."
        print "You gave me: %s" %options.build
        sys.exit()

    # We obviously generate these values above as part of determining the release type, so we we just return them since we almost always need these anyway.
    var_dict = {'RC': RC, 'RELEASE': RELEASE, 'REL_ID': REL_ID, 'RC_DIR': RC_DIR, 'REL_TYPE': REL_TYPE, 'MILESTONE': MILESTONE};
    return var_dict

if __name__ == '__main__':

    os.system("clear")
    print
   
    parser = optparse.OptionParser()
    parser.add_option("-i", "--build-id",
                      type="string", dest="build",
                      help="Required. Release candidate name including rc#. i.e. yocto-2.5.rc1, yocto-2.5.1.rc2, yocto-2.5_M1.rc3, etc.")
    (options, args) = parser.parse_args()

    if not options.build:
        print "You must provide the RC name. i.e. yocto-2.5.r1, yocto-2.5.1.rc2, yocto-2.6_M3.rc1, etc."
        print "Please use -h or --help for options."
        sys.exit()

    VARS = release_type(options.build)
    RC = VARS['RC']
    RELEASE = VARS['RELEASE']
    REL_ID = VARS['REL_ID']
    RC_DIR = VARS['RC_DIR']
    REL_TYPE = VARS['REL_TYPE']
    MILESTONE = VARS['MILESTONE']

    for thing in ['RC_DIR', 'RELEASE', 'REL_TYPE', 'RC', 'RELEASE', 'MILESTONE']:
        print "%s: %s" %(thing, VARS[thing])
