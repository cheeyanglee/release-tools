'''
Created on Feb 22, 2016

__author__ = "Tracy Graydon"
__copyright__ = "Copyright 2016-2018, Intel Corp."
__credits__ = ["Tracy Graydon"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Tracy Graydon"
__email__ = "tracy.graydon@intel.com"
'''

''' This script will generate the release notes draft for a given Yocto release. There 
are some things that still need to be added manually to the release notes, such as
Known Issues and New Features and Enchancements. For major releases, we only produce
the Errata info. The rest is compiled elsewhere. We do not do release notes for milestones.
For point releases, we produce the Errata info and the list of CVE and other Fixes.
This script uses the release directory, and not the RC directory, so you must run the release.py
script first.
'''

import os
import os.path
import optparse
import sys
import hashlib
import glob
import shutil
import pygit2
import datetime
import re
from shutil import rmtree, copyfile
from utils import where_am_i, split_thing, rejoin_thing
from rel_type import release_type
from pygit2 import Repository, clone_repository, RemoteCallbacks
from pygit2 import GIT_SORT_TIME, GIT_SORT_TOPOLOGICAL

def get_bitbake_info(path):
    # Get the bitbake version
    with open(path) as search:
        for line in search:
           line = line.rstrip()
           if "__version__ = " in line:
               BITBAKE_VER = split_thing(line, '"')[1]
    if BITBAKE_VER == "NONE":
       # Let's do something if we can't determine the BitBake version for some reason.
       print "Can't determine the bitbake version. You'll have to fix that manually."
       BITBAKE_VER = "FIX ME!"  # Later we write this out to the release notes as a reminder to manually fix it.
    return BITBAKE_VER

def get_repo(codename):
    repo_url = 'http://git.yoctoproject.org/git/poky'
    CWD = os.getcwd()
    repo_path = os.path.join(CWD,'poky')
    if os.path.exists(repo_path):
        print "\nFound an existing poky repo. Nuking it."
        rmtree(repo_path)
    print "Cloning the poky repo."
    try:
        poky_repo = clone_repository(repo_url, repo_path, checkout_branch=codename)
    except:
        print "Couldn't check out the poky repo with branch %s. Check the branch name you passed in." %codename
        sys.exit()
    # Are we where we think we are?
    poky_repo = Repository(repo_path)
    head = poky_repo.head
    branch_name = head.name
    print "We are now on branch: %s\n" %branch_name
    return poky_repo

def do_errata(outfile):
    print "Generating the Errata."
    outfile.write("\n------------------\n%s Errata\n--------------------\n\n" %RELEASE)
    os.chdir(RELEASE_DIR)
    files = glob.glob('*.bz2')
    allfiles = filter(lambda f: os.path.isfile(f), files)
    # Filter out the renamed blobs. We want the symlinks with the hashes.
    filelist = filter(lambda x: POKY_VER not in x, allfiles)
    filelist.sort()
    for item in filelist:
        chunks = split_thing(item, ".")
        new_chunk = split_thing(chunks[0], '-')
        hash = new_chunk.pop()
        # Get the release name
        base_name = rejoin_thing(new_chunk, "-")
        RELEASE_NAME = "-".join([base_name, DEFAULT_TAG])
        # Now let's get the md5sum        
        files = glob.glob('*.md5sum')
        md5file = filter(lambda y: RELEASE_NAME in y, files).pop()
        filepath = os.path.join(RELEASE_DIR, md5file)
        f = open(filepath, 'r')
        rawline = f.readline()
        md5line = split_thing(rawline, " ")
        md5 = md5line[0]
        blob = md5line[2]
        f.close()
        # Set up the download URLS
        DL_URL = "/".join([DL_BASE_URL, RELEASE, blob]).strip()
        MIRROR_URL = "/".join([MIRROR_BASE_URL, RELEASE, blob]).strip()
        # Now figure out tags and branches
        name_chunks = split_thing(RELEASE_NAME, "-")
        if name_chunks[0] == "bitbake":
            PROJECT_BRANCH = BITBAKE_VER
            PROJECT_TAG = BITBAKE_VER
        elif name_chunks[0] == "eclipse":
            PROJECT_BRANCH = "/".join([name_chunks[2], BRANCH])
            PROJECT_BRANCH = BRANCH
            # For the tag we want the month and year of the build, so this is a reasonable approximation.
            timestamp = os.path.getmtime(item)
            foo = datetime.date.fromtimestamp(timestamp)
            foo = str(foo)
            time_chunk = foo.split("-")
            time_chunk.pop()
            time_chunk = rejoin_thing(time_chunk, "-")
            PROJECT_TAG = time_chunk
        else:
            PROJECT_BRANCH = BRANCH
            PROJECT_TAG = DEFAULT_TAG
        outfile.write("Release Name: %s\n" %RELEASE_NAME)
        outfile.write("Branch: %s\n" %PROJECT_BRANCH)
        outfile.write("Tag: %s\n" %PROJECT_TAG)
        outfile.write("Hash: %s\n" %hash)
        outfile.write("md5: %s\n" %md5)
        outfile.write("Download Locations:\n")
        outfile.write(DL_URL + "\n")
        outfile.write(MIRROR_URL + "\n\n")
    return

if __name__ == '__main__':

    os.system("clear")
    print

    PATH_VARS = where_am_i()
    VHOSTS = PATH_VARS['VHOSTS']
    AB_HOME = PATH_VARS['AB_HOME']
    AB_BASE = PATH_VARS['AB_BASE']
    DL_HOME = PATH_VARS['DL_HOME']
    DL_BASE = PATH_VARS['DL_BASE']

    parser = optparse.OptionParser()
    parser.add_option("-i", "--build-id",
                      type="string", dest="build",
                      help="Required. Release candidate name including rc#. i.e. yocto-2.0.rc1, yocto-2.1_M1.rc3, etc.")
    parser.add_option("-b", "--branch",
                      type="string", dest="branch",
                      help="Required for Major and Point releases. i.e. daisy, fido, jethro, etc. We don't do relnotes for milestones.")
    parser.add_option("-p", "--poky-ver",
                      type="string", dest="poky",
                      help="Required for Major and Point releases. i.e. 14.0.0. We don't do relnotes for milestones.")
    parser.add_option("-r", "--revisions",
                      type="string", dest="revs",
                      help="Required. Specify the revision range to use for the git log. i.e. yocto-2.0.1 would use yocto-2.0..HEAD. ")
    (options, args) = parser.parse_args()

    if not (options.build and options.branch and options.poky and options.revs):
        print "You must specify the RC, branch, poky version, and revision range."
        print "Please use -h or --help for options."
        sys.exit()

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

    for thing in ['RC_DIR', 'RELEASE', 'RC', 'REL_ID', 'REL_TYPE', 'MILESTONE']:
        print "%s: %s" %(thing, VARS[thing])
    print "RC_SOURCE: %s" %RC_SOURCE
    print "RELEASE_DIR: %s" %RELEASE_DIR

    if REL_TYPE == "milestone":
        print "We don't do release notes or errata for milestones. Quitting."
        sys.exit()

    POKY_VER = options.poky
    CODENAME = options.branch
    BRANCH = CODENAME
    REVISIONS = options.revs
    DEFAULT_TAG = "-".join([BRANCH, POKY_VER])

    # Note that we append the RELEASENOTES filename with the release it is for. i.e. RELEASENOTES.yocto-2.6
    # This is to avoid clobbering release notes for other releases that may be happening in parallel.
    # Drop the appended release name from the respective file when the finalized version gets 
    # copied into the release directory. i.e. Just RELEASENOTES, not RELEASENOTES.<release>
    RELEASE_NOTES = ".".join(["RELEASENOTES", RELEASE])
    DL_BASE_URL = "http://downloads.yoctoproject.org/releases/yocto"
    MIRROR_BASE_URL = "http://mirrors.kernel.org/yocto/yocto"
    HOME = os.getcwd()
    POKY_REPO = os.path.join(HOME, "poky")
    BITBAKE_FILE = "bitbake/bin/bitbake"
    BITBAKE_PATH = os.path.join(POKY_REPO, BITBAKE_FILE)
    outpath = os.path.join(HOME, RELEASE_NOTES)

    ''' About tagging...
    The default tag is of format <branch>-<poky_ver>. i.e. sumo-19.0.0, thud-20.0.0
    However, there are some exceptions to that, such as bitbake, eclipse, and oe-core.
    Respective tag formats are:
    poky: default tag i.e. sumo-19.0.0
    meta-intel: default tag  This is the tarball associated with the external release and not official (Intel) BSP releases.
    meta-mingw: default tag
    meta-qt3: default tag
    meta-qt4: default tag
    meta-gplv2: default tag
    oe-core: <year>-<month> This is the year and month that the release was generated. NOT THE RELEASE DATE.
    bitbake: <version> This is the bitbake version taken from the /bin/bitbake file.
    eclipse: <plugin_ver>/<branch>-<poky_ver> i.e. neon/sumo-19.0.0 or oxygen/sumo-19.0.0
    '''
    
    outfile = open(outpath, 'w')

    # Get the poky repo now so we can do all the things.
    repo = get_repo(BRANCH)
   
    # Get the bitbake version
    BITBAKE_VER = "NONE"
    BITBAKE_VER = get_bitbake_info(BITBAKE_PATH)
 
    do_errata(outfile)

    if REL_TYPE == "point":
        outfile.write("\n---------------\n Known Issues\n---------------\n")
        outfile.write("N/A\n\n")
        # We add known issues manually to the release notes.
        print "Getting the Security Fixes for the release."
        outfile.write("\n---------------\nSecurity Fixes\n---------------\n")
    
        # Make sure the starting revision/tag exists.
        rev_chunks = split_thing(REVISIONS, "..")
        start_rev = rev_chunks[0]  # The tag of the previous release
        head_rev = rev_chunks[1] # This is usually going to be the HEAD of the release branch we are on
        regex = re.compile('^refs/tags')
        tag_list = filter(lambda r: regex.match(r), repo.listall_references())
        if not start_rev in str(tag_list):
            print "I can't find a ta:g matching %s. Check your revisions." %start_rev
            sys.exit()

        start = repo.revparse_single(head_rev)
        end = repo.revparse_single(start_rev)

        walker = repo.walk(start.id, GIT_SORT_TOPOLOGICAL)
        walker.hide(end.id)
        for commit in walker:
            raw_message = commit.message.encode('utf-8').rstrip()
            commit_title = raw_message.splitlines()[0]
            if 'CVE' in commit_title:
                commit_id = str(commit.id)
                # If you want to include the commit has, uncomment the lines with the commit_id.
                print "%s" %commit_title
                #print "%s: %s" %(commit_id[0:8], commit_title)
                outfile.write("%s\n" %commit_title) 
                #outfile.write("%s: %s\n" %(commit_id[0:8], commit_title))
        print "DONE!"

        print "Getting the Fixes for the release."
        outfile.write("\n\n---------------\nFixes\n---------------\n")
        walker.reset()
        walker = repo.walk(start.id, GIT_SORT_TOPOLOGICAL)
        walker.hide(end.id)
        for commit in walker:
            raw_message = commit.message.encode('utf-8').rstrip()
            commit_title = raw_message.splitlines()[0]
            if 'CVE' not in commit_title:
                commit_id = str(commit.id)
                # If you want to include the commit has, uncomment the lines with the commit_id.
                print "%s" %commit_title
                #print "%s: %s" %(commit_id[0:8], commit_title)
                outfile.write("%s\n" %commit_title)
                #outfile.write("%s: %s\n" %(commit_id[0:8], commit_title))
    print "Done"
    outfile.close()
