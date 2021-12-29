# SPDX-License-Identifier: GPL-2.0-only
'''
Created on June 20, 2019

__author__ = "Tracy Graydon"
__copyright__ = "Copyright 2019, Intel Corp."
__credits__ = ["Tracy Graydon"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Tracy Graydon"
__email__ = "tracy.graydon@intel.com"
'''

''' This script is run as part of the release staging process. QA testresults are published
along with the respective release, as part of the release artefacts. This takes the build testresults,
merges them with any QA team testresults (currently just Intel/WindRiver QA) and generates a
master testreport with the combined results.
'''

import os
import os.path
import optparse
import sys
import subprocess
import glob
import shutil
import pygit2
import json
import collections
from pprint import pprint
from shutil import rmtree, copytree, copyfile
from utils import where_am_i, split_thing
from rel_type import release_type
from pygit2 import Repository, clone_repository, RemoteCallbacks

def get_repo(repo_url, repo_branch):
    CWD = os.getcwd()
    repo_name = split_thing(repo_url, "/")[-1]
    repo_path = os.path.join(CWD, repo_name)
    if os.path.exists(repo_path):
        print("\nFound an existing %s repo. Nuking it." %repo_name)
        rmtree(repo_path)
    print("Cloning the %s repo." %repo_name)
    try:
        the_repo = clone_repository(repo_url, repo_path, checkout_branch=repo_branch)
    except:
        print("Couldn't check out the %s repo with branch %s. Check the branch name you passed in." %(repo_name, repo_branch))
        sys.exit()
    # Are we where we think we are?
    the_repo = Repository(repo_path)
    head = the_repo.head
    branch_name = head.name
    print("We are now on branch: %s\n" %branch_name)
    return the_repo

def get_poky_hash(rel_dir,rel_type, branch):
    os.chdir(RELEASE_DIR)
    files = glob.glob('*.bz2')
    allfiles = filter(lambda f: os.path.isfile(f), files)
    dirlist = filter(lambda x: "poky" in x, allfiles)
    if rel_type == "milestone":
        thing = dirlist[0]
    else:
        filelist = filter(lambda x: branch not in x, dirlist)
        thing = filelist[0]
    chunks = split_thing(thing, ".")
    new_chunk = split_thing(chunks[0], '-')
    hash = new_chunk.pop()
    return hash

def get_revisions(logfile):
    with open(logfile) as search:
        for line in search:
            line = line.rstrip()  # remove '\n' at end of line
            if "revisions" in line:
                rev_chunks = split_thing(line, " ")
                revs = rev_chunks[2]
    search.close()
    return revs

def find_bogus(results_dir, branch, commit):
   status = "GOOD"
   print("\nChecking the testresults for bogus branches and commits.\n")
   for dirname, subdir_list, file_list in os.walk(results_dir):
       for fname in file_list:
           bogus = []
           if TEST_FILE in fname:
               filename = os.path.join(dirname, fname)
               with open(filename) as f:
                   report = json.loads(f.read())
               key = list(report.keys())[0]

               meta_branch = report[key]['configuration']['LAYERS']['meta']['branch']
               meta_commit = report[key]['configuration']['LAYERS']['meta']['commit']
               meta_poky_branch = report[key]['configuration']['LAYERS']['meta-poky']['branch']
               meta_poky_commit = report[key]['configuration']['LAYERS']['meta-poky']['commit']
               meta_yocto_bsp_branch = report[key]['configuration']['LAYERS']['meta-yocto-bsp']['branch']
               meta_yocto_bsp_commit = report[key]['configuration']['LAYERS']['meta-yocto-bsp']['commit']

               if not (meta_branch == branch and meta_poky_branch == branch and meta_yocto_bsp_branch == branch):
                   bogus.append("branch")
               if not (meta_commit == commit and meta_poky_commit == commit and meta_yocto_bsp_commit == commit):
                   bogus.append("commit")
               if len(bogus) == 1:
                   print("Bogus %s in %s" %(bogus[0], filename))
               elif len(bogus) == 2:
                   print("Both a bogus branch and commit in %s" %filename)
               if len(bogus) > 0:
                   print("meta \t\t branch: %s \t commit: %s" %(meta_branch, meta_commit))
                   print("meta-poky \t branch: %s \t commit: %s" %(meta_poky_branch, meta_poky_commit))
                   print("meta-yocto_bsp \t branch: %s \t commit: %s" %(meta_yocto_bsp_branch, meta_yocto_bsp_commit))
                   status = "BAD"
                   print
   return status

def do_testreport(report_file, header_path):
    # Generate the testreport.
    outfile = open(report_file, 'a')
    print("Generating the %s file." %report_file)
    if os.path.isfile(header_path):
        infile = open(header_path, 'r')
    else:
        header_path = os.path.join(CONTRIB_PATH, "header.txt")
        if os.path.isfile(header_path):
            infile = open(header_path, 'r')
        else:
            print("Can't find a header file. Quitting.")
            sys.exit()
    all_the_things = infile.read()
    infile.close()
    outfile.writelines("%s\n" %all_the_things)
    outfile.flush()
    subprocess.call([RESULT_TOOL, "report", RELEASE_DIR], stdout=outfile)
    outfile.close()
    print("Done.\n")
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
                      help="Required for Major and Point releases. i.e. thud, warrior, zeus, etc. Milestones use the codename for the major release. i.e. 2.8_M1 would use zeus.")
    (options, args) = parser.parse_args()

    if not (options.build and options.branch):
        print("You must specify the RC and the codename/branch.")
        print("Note that milestones need the release codename. i.e. 2.8_M1 would use zeus.")
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
       RELEASE_DIR = os.path.join(AB_BASE, RELEASE)
    else:
       print("Build ID is a required argument.")
       print("Please use -h or --help for options.")
       sys.exit()

    if REL_TYPE == "milestone":
        if options.branch == "master":
            print("I need the release line for the milestone.")
            print("i.e. For 2.8_M1 it would be zeus. For 2.7_M1, it woutld be warrior. Etc.")
            sys.exit()
        else:
            POKY_BRANCH = "master"
            CODENAME = options.branch
    else:
        POKY_BRANCH = options.branch
        CODENAME = POKY_BRANCH

    HOME = os.getcwd()
    POKY_REPO = "git://git.yoctoproject.org/poky"
    CONTRIB_REPO = "git://git.yoctoproject.org/yocto-testresults-contrib"
    RESULTS_REPO = "git://git.yoctoproject.org/yocto-testresults"
    POKY_PATH = os.path.join(HOME, "poky")
    CONTRIB_PATH = os.path.join(HOME, "yocto-testresults-contrib")
    SACRED_PATH = os.path.join(HOME, "yocto-testresults")
    RESULT_TOOL = os.path.join(POKY_PATH, "scripts/resulttool")
    RESULTS_DIR = os.path.join(CONTRIB_PATH, "testresults-intel")
    HEADER_INTEL = "header-intel.txt"
    HEADER_PATH = os.path.join(CONTRIB_PATH, HEADER_INTEL)
    REPORT_FILE = os.path.join(RELEASE_DIR, "testreport.txt")
    BUILD_RESULTS = os.path.join(RELEASE_DIR, "testresults")
    INTEL_RESULTS = os.path.join(RELEASE_DIR, "testresults-intel")
    TEST_FILE = "testresults.json"
    STORE_FILE = "store" + "-" + REL_ID + ".log"
    STORE_LOG = os.path.join(HOME, STORE_FILE)

    # Check to make sure that the release dir exists. If not, quit. Have to stage first.
    if not os.path.exists(RELEASE_DIR):
        print("Can't find a %s release directory. Have you run the release.py script? Quitting." %RELEASE_DIR)
        sys.exit()
    # Check for testresults dir generated by the build. If not there, something is wrong with the build artefacts.
    if not os.path.exists(BUILD_RESULTS):
        print("I can't find the build testresults directory. Can't continue. Check the build artefacts.")
        sys.exit()
    if not os.listdir(BUILD_RESULTS):
        print("The build testresults directory appears to be empty. Can't continue. Check the build artefacts.")
        sys.exit()
    if os.path.exists(INTEL_RESULTS):
        print("I found an existing testresults-intel directory. Refusing to clobber.")
        sys.exit()
    if os.path.isfile(REPORT_FILE):
       print("I found an existing testreport.txt file. Refusing to clobber.")
       sys.exit()
  
    # Get the repos
    # We always use master for poky because we want the resulttool from master.
    poky_repo = get_repo(POKY_REPO, "master")     # would we want this to be master-next? What id definitive version of resulttool?
    contrib_repo = get_repo(CONTRIB_REPO, CODENAME)
    results_repo = get_repo(RESULTS_REPO, POKY_BRANCH)


    # Get the poky build hash
    POKY_HASH = get_poky_hash(RELEASE_DIR, REL_TYPE, POKY_BRANCH)
    print("POKY_HASH: %s" %POKY_HASH)
    print("POKY_BRANCH: %s" %POKY_BRANCH)
    
    # Now check for bad hashes, bogus branch names. The ONLY branch and commit has we should see
    # are the ones we just got above: POKY_HASH and _POKY_BRANCH.
    bogus = find_bogus(RESULTS_DIR, POKY_BRANCH, POKY_HASH)
    if bogus == "BAD":
        print("Can't continue with bogus branch names or commits in testresults. Quitting.\n")
        sys.exit()
    else:
        print("No issues found.\n")

    # Get the testresults from the contrib repo and put them in the RELEASE_DIR.
    copytree(RESULTS_DIR, INTEL_RESULTS)

    # Generate the testreport
    do_testreport(REPORT_FILE, HEADER_PATH)
    
    # If we made it this far without dying, there should be only ONE revision in the resulttool output.
    print("Running the resultool store command.")
    if os.path.exists(STORE_LOG):
        os.remove(STORE_LOG)
    store_log = open(STORE_LOG, "a")
    subprocess.call([RESULT_TOOL, "store", RESULTS_DIR, SACRED_PATH, "-x", "Intel QA"], stderr=store_log)
    store_log.close()

   # See how many revisions we have as a final sanity check.
    revisions = get_revisions(STORE_LOG)
    print("Revisions found: %s" %revisions)
    if revisions != "1":
        print("We should have ONLY ONE revision. Something is super wrong. Quitting.\n")
        sys.exit()
    else:
        print("\nCheck the resulttool store log and make sure things look right.")
        print
        store_log = open(STORE_LOG, "r")
        tool_output = store_log.read()
        print(tool_output)
