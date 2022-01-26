# SPDX-License-Identifier: GPL-2.0-only
'''
Created on Nov 7, 2018

__author__ = "Tracy Graydon"
__copyright__ = "Copyright 2018, Intel Corp."
__credits__ = ["Tracy Graydon"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Tracy Graydon"
__email__ = "tracy.graydon@intel.com"
'''

# This script takes two revisions on a branch and find the CVEs between them.
# It creates a fresh clone of the poky repo, and blindly nukes any pre-existing poky
# repo first, so watch out. It ensures that we have a fresh repo on the correct branch
# to avoid bogus git logs and subsequently erroneous output. 

import os
import optparse
import sys
import os.path
import git
from shutil import rmtree
from utils import split_thing

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

if __name__ == '__main__':

    os.system("clear")
    print

    parser = optparse.OptionParser()
    parser.add_option("-b", "--branch",
                      type="string", dest="branch",
                      help="Required. This is the poky branch to checkout.")
    parser.add_option("-r", "--revisions",
                      type="string", dest="revs",
                      help="Required. Specify the revision range to use for the git log. From <tag or revision> to <tag or revision> i.e. For yocto-2.0.1: yocto-2.0..HEAD. ")
    (options, args) = parser.parse_args()

    if not (options.branch and options.revs):
        print("You must specify branch and revision range.")
        print("Please use -h or --help for options.")
        sys.exit()

    BRANCH = options.branch
    REVISIONS = options.revs
    HOME = os.getcwd()

    CVE_REPORT = ".".join(["CVE_REPORT", BRANCH])
    print("BRANCH: %s" %BRANCH)
    print("REPORT file: %s" %CVE_REPORT)

    # Clone the repo
    repo = get_repo(BRANCH)

    outpath = os.path.join(HOME, CVE_REPORT)
    outfile = open(outpath, 'w')
    outfile.write("\n---------------\nSecurity Fixes\n---------------\n")
    for commit in repo.iter_commits(REVISIONS):
        if 'CVE' in commit.summary:
            commit_id = commit.hexsha
            print("%s: %s" %(commit_id[0:8], commit.summary))
            outfile.write("%s: %s\n" %(commit_id[0:8], commit.summary))
    outfile.close()
    print("DONE!")
