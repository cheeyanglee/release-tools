'''
Created on Feb 22, 2018

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
import hashlib
import glob
import os.path
import shutil
from sh import git
from shutil import rmtree, copyfile
from subprocess import call, Popen

def split_thing(thing, marker):
    filebits = thing.split(marker)
    return filebits

def rejoin_thing(thing, marker):
    filebits = marker.join(thing)
    return filebits

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
    foo = chunks[-1].upper()            # If we have a milestone release, we want to fix
    chunks[-1] = foo
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
        print "We don't generate release notes for Milestone releases."
        sys.exit()

    if not (RELEASE and RC and YP_VER and REL_TYPE):
        print "Can't determine the release type. Check your args."
        print "You gave me: %s" %options.build
        sys.exit()

    YP_NAME = "-".join(["yocto", YP_VER])
    TAG = "-".join([META_VER, BRANCH, YP_VER])
    RC_SOURCE = os.path.join(AB_BASE, RC_DIR)
    RELEASE_DIR = os.path.join(AB_BASE, RELEASE)

    var_dict = {'RC': RC, 'YP_VER': YP_VER, 'BRANCH': BRANCH, 'META_VER': META_VER, 'RC_DIR': RC_DIR, 'RELEASE': RELEASE, 'REL_TYPE': REL_TYPE, 'YP_NAME': YP_NAME, 'TAG': TAG, 'RC_SOURCE': RC_SOURCE, 'RELEASE_DIR': RELEASE_DIR}
    return var_dict


if __name__ == '__main__':

    os.system("clear")
    print

    VHOSTS = "/srv/www/vhosts"
    AB_BASE = os.path.join(VHOSTS, "autobuilder.yoctoproject.org/pub/releases")
    DL_BASE = os.path.join(VHOSTS, "downloads.yoctoproject.org/releases/yocto")

    parser = optparse.OptionParser()
    parser.add_option("-i", "--build-id",
                      type="string", dest="build",
                      help="Required. Release candidate name including rc#. i.e. yocto-meta-intel-8.1-rocko-2.4.2.rc1, etc.")
    parser.add_option("-r", "--revisions",
                      type="string", dest="revs",
                      help="Required. Specify the revision range to use for the git log. i.e. meta-intel-8.1-rocko-2.4.2 would use 8.0-rocko-2.4..HEAD.")

    (options, args) = parser.parse_args()

    if not (options.build and options.revs):
        print "You must specify the RC and revision range."
        print "Please use -h or --help for options."
        sys.exit()
    
    print "Build ID: %s" %options.build
    print "Revisions: %s" %options.revs
    

    REVISIONS = options.revs
    VARS = release_type(options.build)
    RC = VARS['RC']
    YP_VER = VARS['YP_VER']
    BRANCH = VARS['BRANCH']
    META_VER = VARS['META_VER']
    RC_DIR = VARS['RC_DIR']
    RELEASE = VARS['RELEASE']
    REL_TYPE = VARS['REL_TYPE']
    YP_NAME = VARS['YP_NAME']
    TAG = VARS['TAG']
    RC_SOURCE = VARS['RC_SOURCE']
    RELEASE_DIR = VARS['RELEASE_DIR']
    RELEASE_NOTES = ".".join(["RELEASE_NOTES", RELEASE])
    META_TARBALL = RELEASE + ".tar.bz2"
    MD5FILE = META_TARBALL + ".md5sum"
    DL_BASE = "http://downloads.yoctoproject.org/releases/yocto"
    MIRROR_BASE = "http://mirrors.kernel.org/yocto/yocto"
    HOME = os.getcwd()
    META_REPO = os.path.join(HOME, "meta-intel")
    GIT_LOG = os.path.join(HOME, "git_log.txt")
    FIXES = os.path.join(HOME, "FIXES")
    CVE = os.path.join(HOME, "CVE")

    # Running through the dictionary to print var values results in random order, making it hard to read. So loop through values in desired order.
    for thing in ['RC_DIR', 'RELEASE', 'REL_TYPE', 'META_VER', 'YP_VER', 'YP_NAME', 'RC', 'BRANCH', 'TAG', 'RC_SOURCE', 'RELEASE_DIR']:
        print "%s: %s" %(thing, VARS[thing])
    print "RELEASENOTES file: %s" %RELEASE_NOTES
    print "META_TARBALL: %s" %META_TARBALL
    print "MD5FILE: %s" %MD5FILE

    # Set up the release notes file
    outpath = os.path.join(HOME, RELEASE_NOTES)
    outfile = open(outpath, 'w')
    outfile.write("\n----------------------\n%s Errata\n----------------------\n\n" %TAG)
    os.chdir(RELEASE_DIR)
    
    # Hash file is a symlink to the blob. So find the symlink
    for root, dirs, files in os.walk(RELEASE_DIR, topdown=True):
        for name in files:
           filename = (os.path.join(root, name))
           if os.path.islink(filename):
               hashfile = name
    chunks = split_thing(hashfile, ".")
    new_chunk = split_thing(chunks[0], '-')
    hash = new_chunk.pop()
    print "Hash: %s" %hash

    #Get the md5sum
    md5path = os.path.join(RELEASE_DIR, MD5FILE)
    f = open(md5path, 'r')
    rawline = f.readline()
    md5line = split_thing(rawline, " ")
    md5 = md5line[0]
    print "MD5: %s" %md5
    blob = md5line[1]
    print "blob: %s" %blob
    f.close()
    DL_URL = "/".join([DL_BASE, YP_NAME, blob]).strip()
    MIRROR_URL = "/".join([MIRROR_BASE, YP_NAME, blob]).strip()
    outfile.write("Release Name: %s\n" %RELEASE)
    outfile.write("Branch: %s\n" %BRANCH)
    outfile.write("Tag: %s\n" %TAG)
    outfile.write("Hash: %s\n" %hash)
    outfile.write("md5: %s\n" %md5)
    outfile.write("Download Locations:\n")
    outfile.write(DL_URL + "\n")
    outfile.write(MIRROR_URL + "\n\n")

    if REL_TYPE == "major":
        outfile.write("\n---------------------------\nNew Features / Enhancements\n---------------------------\n\n")
    outfile.write("\n--------------\n Known Issues\n--------------\n")
    outfile.write("N\A\n\n")  # If there are known issues to add, we do that manually later
    os.chdir(HOME)
    print "Cloning the meta-intel repo."
    if not os.path.exists(META_REPO):
        git.clone('ssh://git@git.yoctoproject.org/meta-intel')  
    os.chdir(META_REPO)
    git.fetch("origin")
    print "Checking out %s branch." %BRANCH
    git.checkout(BRANCH)
    format_string = '\"%s\"'
    os.system('git log --pretty=format:%s %s > %s' %(format_string, REVISIONS, GIT_LOG))
    os.chdir(HOME)
    print "Getting Security Fixes."
    outfile.write("\n---------------\nSecurity Fixes\n---------------\n")
    with open(GIT_LOG, 'r') as gitlog:
        lines = gitlog.readlines()
    for line in lines:
        if "CVE" in line:
            outfile.write(line)
    outfile.write("\n\n---------------\nFixes\n---------------\n")
    for line in lines:
        if not "CVE" in line:
            outfile.write(line)
    gitlog.close()
    outfile.close()
    print "DONE!"
