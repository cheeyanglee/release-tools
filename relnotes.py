# SPDX-License-Identifier: GPL-2.0-only
'''
Created on Feb 22, 2016

__author__ = "Tracy Graydon"
__copyright__ = "Copyright 2016-2019, Intel Corp."
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
import git
import datetime
import re
from shutil import rmtree, copyfile
from utils import where_am_i, split_thing, rejoin_thing
from rel_type import release_type

def get_repo(codename):
    repo_url = 'https://git.yoctoproject.org/git/poky'
    CWD = os.getcwd()
    repo_path = os.path.join(CWD,'poky')
    if os.path.exists(repo_path):
        print("\nFound an existing poky repo. Nuking it.")
        rmtree(repo_path)
    print("Cloning the poky repo.")
    try:
        poky_repo = git.Repo.clone_from(repo_url, repo_path)
        poky_repo.git.checkout(codename)
    except:
        print("Couldn't check out the poky repo with branch %s. Check the branch name you passed in." %codename)
        sys.exit()
    # Are we where we think we are?
    branch_name = poky_repo.head.ref
    print("We are now on branch: %s\n" %branch_name)
    return poky_repo

def do_errata(outfile, REL_TYPE):
    print("Generating the Repositories/Downloads.")
    outfile.write("\n--------------------------\n%s Release Notes\n--------------------------\n\n" %RELEASE)
    outfile.write("\n--------------------------\n Repositories/Downloads\n--------------------------\n\n")
    os.chdir(RC_SOURCE)
    files = glob.glob('*.bz2')
    allfiles = filter(lambda f: os.path.isfile(f), files)
    # For major release and point releases errata do not want to include meta-intel.
    blob_list = [y for y in allfiles if not y.startswith(('meta-intel', 'meta-aws', 'meta-openembedded', 'meta-arm', 'meta-agl', 'meta-virtualization'))]
    blob_list.sort(reverse = True)
    for item in blob_list:
        chunks = split_thing(item, ".")
        new_chunk = split_thing(chunks[0], '-')
        hash = new_chunk.pop()
        # Get the release name
        base_name = chunks[0]
        RELEASE_NAME = base_name
        # Now let's get the sha256sum        
        files = glob.glob('*.sha256sum')
        shafile = list(filter(lambda y: RELEASE_NAME in y, files)).pop()
        filepath = os.path.join(RC_SOURCE, shafile)
        f = open(filepath, 'r')
        rawline = f.readline()
        shaline = split_thing(rawline, " ")
        sha = shaline[0]
        blob = shaline[2]
        f.close()
        # Set up the download URLS
        DL_URL = "/".join([DL_BASE_URL, RELEASE, blob]).strip()
        MIRROR_URL = "/".join([MIRROR_BASE_URL, RELEASE, blob]).strip()
        # Now figure out tags and branches
        name_chunks = split_thing(RELEASE_NAME, "-")
        if name_chunks[0] == "eclipse":
            PROJECT_BRANCH = "/".join([name_chunks[2], BRANCH])
            PROJECT_TAG =  "/".join([name_chunks[2], DEFAULT_TAG])
        else:
            PROJECT_BRANCH = BRANCH
            PROJECT_TAG = RELEASE
            if name_chunks[0] == "poky" or name_chunks[0] == "bitbake":
                REPO_NAME = name_chunks[0]
                if REPO_NAME == "poky":
                    REPO_URL = "/".join(["https://git.yoctoproject.org/git",REPO_NAME])
                else:
                    REPO_URL = "/".join(["https://git.openembedded.org",REPO_NAME])
            elif name_chunks[0] == "oecore":
                REPO_NAME = "openembedded-core"
                REPO_URL = "/".join(["https://git.openembedded.org",REPO_NAME])
            else:
                REPO_NAME = "-".join([name_chunks[0], name_chunks[1]])
                REPO_URL = "/".join(["https://git.yoctoproject.org/git",REPO_NAME])
        outfile.write("Repository Name: %s\n" %REPO_NAME)
        outfile.write("Repository Location: %s\n" %REPO_URL)
        outfile.write("Branch: %s\n" %PROJECT_BRANCH)
        outfile.write("Tag: %s\n" %PROJECT_TAG)
        outfile.write("Git Revision: %s\n" %hash)
        outfile.write("Release Artefact: %s\n" %RELEASE_NAME)
        outfile.write("sha: %s\n" %sha)
        outfile.write("Download Locations:\n")
        outfile.write(DL_URL + "\n")
        outfile.write(MIRROR_URL + "\n\n")
    outfile.write("Repository Name: yocto-docs\n")
    outfile.write("Repository Location: https://git.yoctoproject.org/git/yocto-docs\n")
    outfile.write("Branch: %s\n" %PROJECT_BRANCH)
    outfile.write("Tag: %s\n" %PROJECT_TAG)
    outfile.write("Git Revision: <----------replace this with commit ID----------->\n\n")
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
    parser.add_option("-r", "--revisions",
                      type="string", dest="revs",
                      help="Required. Specify the revision range to use for the git log. i.e. yocto-2.0.1 would use yocto-2.0..HEAD. ")
    (options, args) = parser.parse_args()

    if not (options.build and options.branch and options.revs):
        print("You must specify the RC, branch, and revision range.")
        print("Please use -h or --help for options.")
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
    else:
       print("Build ID is a required argument.")
       print("Please use -h or --help for options.")
       sys.exit()

    for thing in ['RC_DIR', 'RELEASE', 'RC', 'REL_ID', 'REL_TYPE', 'MILESTONE']:
        print("%s: %s" %(thing, VARS[thing]))
    print("RC_SOURCE: %s" %RC_SOURCE)

    if REL_TYPE == "milestone":
        print("We don't do release notes or errata for milestones. Quitting.")
        sys.exit()

    CODENAME = options.branch
    BRANCH = CODENAME
    REVISIONS = options.revs
    DEFAULT_TAG = BRANCH

    # Note that we append the RELEASENOTES filename with the release it is for. i.e. RELEASENOTES.yocto-2.6
    # This is to avoid clobbering release notes for other releases that may be happening in parallel.
    # Drop the appended release name from the respective file when the finalized version gets 
    # copied into the release directory. i.e. Just RELEASENOTES, not RELEASENOTES.<release>
    RELEASE_NOTES = ".".join(["RELEASENOTES", RELEASE])
    DL_BASE_URL = "http://downloads.yoctoproject.org/releases/yocto"
    MIRROR_BASE_URL = "http://mirrors.kernel.org/yocto/yocto"
    HOME = os.getcwd()
    POKY_REPO = os.path.join(HOME, "poky")
    outpath = os.path.join(HOME, RELEASE_NOTES)

    ''' About tagging...
    The default tag is of format <branch>-<poky_ver>. i.e. sumo-19.0.0, thud-20.0.0
    However, there are some exceptions to that, such as bitbake, eclipse, and oe-core.
    Respective tag formats are:
    poky: default tag i.e. sumo-19.0.0 and tag with yocto-<yocto Project release number> (i.e., yocto-2.6.4)
    meta-intel: default tag  This is the tarball associated with the external release and not official (Intel) BSP releases.
    meta-mingw: default tag and tag with yocto-<yocto Project release number> (i.e., yocto-2.6.4)
    meta-qt3: default tag
    meta-qt4: default tag
    meta-gplv2: default tag and tag with yocto-<yocto Project release number> (i.e., yocto-2.6.4)
    eclipse: <plugin_ver>/<branch>-<poky_ver> i.e. neon/sumo-19.0.0 or oxygen/sumo-19.0.0
    NOTE: oecore and bitbake are NOT tagged for point and milestone releases, so they are not handled here. But this tag format info is included here in case 
          something changes, and for general reference. From 2.7.2, 2.6.4 and 3.0 point releases onwards oecore is tagged for point releases as well.
    oecore: yocto-<release number> (eg: yocto-2.6.4), <year>-<month> This is the year and month that the release was generated. NOT THE RELEASE DATE..
    bitbake: <version> This is the bitbake version taken from the /bin/bitbake file. 
    '''
    
    outfile = open(outpath, 'w')

    # Get the poky repo now so we can do all the things.
    repo = get_repo(BRANCH)
   
    do_errata(outfile, REL_TYPE)

    if REL_TYPE == "point":
        outfile.write("\n---------------\n Contributors\n---------------\n")
        contributors = []
        for commit in repo.iter_commits(REVISIONS):
            if commit.author.name not in contributors:
                contributors.append(commit.author.name)
        for contributor in sorted(contributors):
            outfile.write("%s\n" % contributor)
            print(contributor)

        outfile.write("\n---------------\n Known Issues\n---------------\n")
        outfile.write("N/A\n\n")
        # We add known issues manually to the release notes.
        print("Getting the Security Fixes for the release.")
        outfile.write("\n---------------\nSecurity Fixes\n---------------\n")
    
        for commit in repo.iter_commits(REVISIONS):
            if 'CVE' in commit.summary:
                # add commit.hexsha to print if commit id required
                print("%s" % commit.summary)
                outfile.write("%s\n" % commit.summary)
        print("DONE!")

        print("Getting the Fixes for the release.")
        outfile.write("\n\n---------------\nFixes\n---------------\n")
        for commit in repo.iter_commits(REVISIONS):
            if 'CVE' not in commit.summary:
                # add commit.hexsha to print if commit id required
                print("%s" % commit.summary)
                outfile.write("%s\n" % commit.summary)
    print("Done")
    outfile.close()
