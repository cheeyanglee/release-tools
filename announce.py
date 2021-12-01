# SPDX-License-Identifier: GPL-2.0-only
'''
Created on June 19, 2019

__author__ = "Tracy Graydon"
__copyright__ = "Copyright 2019, Intel Corp."
__credits__ = ["Tracy Graydon"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Tracy Graydon"
__email__ = "tracy.graydon@intel.com"
'''

''' This script will generate the guts of the release announcement that gets sent
to the yocto@yoctoproject.org and yocto-announce@yoctoproject.org mailing lists.

It DOES NOT append release notes for point and major releases. Those must currently be
added by hand. It would be nice to have an option to do that.
'''

import os
import os.path
import optparse
import sys
from utils import where_am_i, split_thing, rejoin_thing, get_hashes, who_am_i, signature
from rel_type import release_type

def what_milestone(milestone):
    case = {
        "M1": "first",
        "M2": "second",
        "M3": "third"
    }
    return case.get(milestone, "Invalid milestone")

if __name__ == '__main__':

    os.system("clear")
    print

    PATH_VARS = where_am_i()
    VHOSTS = PATH_VARS['VHOSTS']
    AB_HOME = PATH_VARS['AB_HOME']
    AB_BASE = PATH_VARS['AB_BASE']
    DL_HOME = PATH_VARS['DL_HOME']
    DL_BASE = PATH_VARS['DL_BASE']
    DL_BASE_URL = "http://downloads.yoctoproject.org/releases/yocto"
    MIRROR_BASE_URL = "http://mirrors.kernel.org/yocto/yocto"
    TEST_REPORT = "testreport.txt"
    HOME = os.getcwd()

    parser = optparse.OptionParser()
    parser.add_option("-i", "--build-id",
                      type="string", dest="build",
                      help="Required. Release candidate name including rc#. i.e. yocto-2.0.rc1, yocto-2.1_M1.rc3, etc.")
    parser.add_option("-b", "--branch",
                      type="string", dest="branch",
                      help="Required for Major and Point releases. Not used for milestones. i.e. thud, warrior, zeus, etc.")
    (options, args) = parser.parse_args()

    # Get the release type and stuff
    if options.build:
       VARS = release_type(options.build)
       RC = VARS['RC']
       RELEASE = VARS['RELEASE']
       REL_ID = VARS['REL_ID']
       RC_DIR = VARS['RC_DIR']
       REL_TYPE = VARS['REL_TYPE']
       MILESTONE = VARS['MILESTONE']
       RC_SOURCE = os.path.join(AB_BASE, RC_DIR)
       RELEASE_DIR = os.path.join(AB_BASE, RELEASE)
    else:
       print "Build ID is a required argument."
       print "Please use -h or --help for options."
       sys.exit()

    CODENAME = options.branch
    BRANCH = CODENAME
    TEMPLATE = ".".join(["Announce", RELEASE])
    outpath = os.path.join(HOME, TEMPLATE)


    if ((REL_TYPE == "point") or (REL_TYPE == "major")) and not (options.branch):
        print "You need to specify the branch name for point or major releases."
        print "Please use -h or --help for options."

    # Find the release engineer name and email for email signature
    SIG = signature()
    FULL_NAME = SIG[0]
    EMAIL = SIG[1]
    TITLE = "Yocto Project Build and Release"
            
    if REL_TYPE == "milestone":
        print "\nGenerating announcement for %s release %s." %(REL_TYPE, REL_ID)
        TYPE_STR = "milestones"
        DL_URL = "/".join([DL_BASE_URL, TYPE_STR, RELEASE]).strip()
        REPORT_URL = "/".join([DL_URL, TEST_REPORT]).strip()
        chunks = split_thing(REL_ID, "_")
        ID = chunks[0]
        milestone = what_milestone(chunks[1])
    
        RELEASE_STR = milestone + " milestone release for Yocto Project " + ID +  " (" + RELEASE + ")"
        CLOSING = "\nThank you.\n"
        hash_file = get_hashes(options.build)
        hash_path = os.path.join(HOME, hash_file)
        SUBJECT = milestone + " for Yocto Project " + ID +  " (" + RELEASE + ")  Now Available"

    if REL_TYPE == "major" or REL_TYPE == "point":
        print "\nGenerating announcement for %s release %s." %(REL_TYPE, REL_ID)
        hash_file = get_hashes(options.build)
        hash_path = os.path.join(HOME, hash_file)
        f = open(hash_path, 'r')
        release_hashes = f.read()
        f.close()
        word = "poky"
        sentences = release_hashes.split('\n')
        for sentence in sentences :
            if word in sentence:
                poky_sentence = sentence
                x = poky_sentence.split(":")
                poky_hash = x[1].lstrip()
        BLOB = "poky" + "-" + poky_hash + ".tar.bz2"
        DL_URL = "/".join([DL_BASE_URL, RELEASE, BLOB]).strip()
        MIRROR_URL = "/".join([MIRROR_BASE_URL, RELEASE, BLOB]).strip()
        REPORT_URL = "/".join([DL_BASE_URL, RELEASE, TEST_REPORT]).strip()
        RELNOTES_URL = "/".join([DL_BASE_URL, RELEASE, "RELEASENOTES"]).strip()
        RELEASE_STR = "Yocto Project " + REL_ID +  " Release"
        RELNOTES = "\nA gpg signed version of these release notes is available at:\n"
        CLOSING = "\nThank you for everyone's contributions to this release.\n"
        SUBJECT = "Yocto Project " + REL_ID +  " is Released"
        print
    
    outfile = open(outpath, 'w')

    print "\nSubject : %s\n\n" %SUBJECT
    outfile.write("Subject : %s\n\n" %SUBJECT)

    GREETINGS = "We are pleased to announce the " + RELEASE_STR + " is now available for download."
    print GREETINGS
    outfile.write("%s\n" %GREETINGS)

    if REL_TYPE == "milestone":
        print "\nDownload:\n"
        outfile.write("\nDownload:\n\n")
        print "%s\n" %DL_URL
        outfile.write("%s\n\n" %DL_URL)
        if os.path.isfile(hash_path):
            f = open(hash_path, 'r')
            milestone_hashes = f.read()
            f.close()
            print milestone_hashes
            outfile.writelines("%s" %milestone_hashes)
        else:
            print "Can't find the hashes for the milestone. Quitting."
            sys.exit()
        print "Full Test Report:\n"
        outfile.write("\nFull Test Report:\n\n")
        print "%s" %REPORT_URL
        outfile.write("%s\n" %REPORT_URL)
    if REL_TYPE == "point" or REL_TYPE == "major":
        print
        print DL_URL
        outfile.write("\n%s\n" %DL_URL)
        print MIRROR_URL
        outfile.write("%s\n" %MIRROR_URL)
        print RELNOTES
        outfile.write("%s\n" %RELNOTES)
        print "%s\n" %RELNOTES_URL
        outfile.write("%s\n" %RELNOTES_URL)
        print "Full Test Report:\n"
        outfile.write("\nFull Test Report:\n\n")
        print REPORT_URL
        outfile.write("%s\n" %REPORT_URL)

    print CLOSING
    outfile.write("%s\n" %CLOSING)
    print FULL_NAME
    outfile.write("%s\n" %FULL_NAME)
    print EMAIL
    outfile.write("%s\n" %EMAIL)
    print TITLE
    outfile.write("%s\n" %TITLE)
    outfile.close()


