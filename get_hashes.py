'''
Created on Oct 16, 2018

__author__ = "Tracy Graydon"
__copyright__ = "Copyright 2018, Intel Corp."
__credits__ = ["Tracy Graydon"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Tracy Graydon"
__email__ = "tracy.graydon@intel.com"

We use these hashes for tagging, release notes, etc. Handy to
dump to a file for ease of use.

'''

import os
import optparse
import glob
from utils import where_am_i, split_thing, rejoin_thing
from rel_type import release_type

if __name__ == '__main__':

    os.system("clear")
    print

    PATH_DICT = where_am_i()
    AB_BASE = PATH_DICT['AB_BASE']

    parser = optparse.OptionParser()
    parser.add_option("-i", "--build-id",
                      type="string", dest="build",
                      help="Required. Release candidate name including rc#. i.e. yocto-2.5.rc1, yocto-2.5_M1.rc3, etc.")

    (options, args) = parser.parse_args()

    if not options.build:
        print "You must specify the RC name. i.e. yocto-2.5.rc1, yocto-2.5.1.rc2, yocto-2.5_M3.rc1, etc."
        print "Please use -h or --help for options."
        sys.exit()

    VARS = release_type(options.build)
    RELEASE = VARS['RELEASE']
    RC_DIR = VARS['RC_DIR']
    RC_SOURCE = os.path.join(AB_BASE, RC_DIR)
    RELEASE_DIR = os.path.join(AB_BASE, RELEASE)

    for thing in ['RELEASE', 'RC_DIR']:
        print "%s: %s" %(thing, VARS[thing])
    print "RC_SOURCE: %s" %RC_SOURCE
    print "RELEASE_DIR: %s" %RELEASE_DIR

    HOME = os.getcwd()
    HASH_FILE = ".".join(["HASHES", RELEASE])
    outpath = os.path.join(HOME, HASH_FILE)

    os.chdir(RC_SOURCE)
    files = glob.glob('*.bz2')
    filelist = filter(lambda f: os.path.isfile(f), files)
    filelist.sort()
    outfile = open(outpath, 'w')
    for item in filelist:
        chunks = split_thing(item, ".")
        new_chunk = split_thing(chunks[0], '-')
        hash = new_chunk.pop()
        RELEASE_NAME = rejoin_thing(new_chunk, "-")
        print "%s: %s" %(RELEASE_NAME, hash)
        outfile.write("%s: %s\n" %(RELEASE_NAME, hash))
    outfile.close()
    print "\nHashes written to %s" %HASH_FILE
