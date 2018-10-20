'''
Created on August 7, 2018

__author__ = "Tracy Graydon"
__copyright__ = "Copyright 2018 Intel Corp."
__credits__ = ["Tracy Graydon"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Tracy Graydon"
__email__ = "tracy.graydon@intel.com"

This script taks a specific poky commit/build has for a uninative (buildtools) release, and finds the corresponding OE-Core revision.

'''

import os
import re
import sys
import pygit2
from pygit2 import Repository, RemoteCallbacks, clone_repository
from pygit2 import GIT_SORT_TOPOLOGICAL

class MyRemoteCallbacks(pygit2.RemoteCallbacks):
    def credentials(self, url, username_from_url, allowed_types):
        if allowed_types & pygit2.credentials.GIT_CREDTYPE_SSH_KEY:
            return pygit2.Keypair(username_from_url, KEY_PUB, KEY, SECRET)
        else:
            return None

def main(hash):
    KEY = "/home/pokybuild/.ssh/id_rsa"
    KEY_PUB = "/home/pokybuild/.ssh/id_rsa.pub"
    SECRET = ""
    repo_url = 'ssh://git@git.yoctoproject.org/poky'
    CWD = os.getcwd()
    repo_path = os.path.join(CWD,'poky')
    print "repo_path: %s" %repo_path
    if not os.path.exists(repo_path):
        print "Repo doesn't exist."
        print "Cloning the poky repo."       
        repo = clone_repository(repo_url, repo_path, checkout_branch='master', callbacks=MyRemoteCallbacks()) 
    else:
        print "Found an existing poky repo. Reusing it.\n"
        repo = Repository(repo_path)

    print "Build hash: %s" %hash
    start = repo.get(hash)
    for commit in repo.walk(start.hex, GIT_SORT_TOPOLOGICAL):
        if 'OE-Core rev' in commit.message:
            raw = str(commit.message.rstrip())
            raw = raw.replace("\'", "\\")
            # We don't actually NEED the following commit, but it makes finding it in the git log easier should we want to look at the actual commit.
            print "Poky Commit with OE-Core Rev: %s" %commit.hex
            foo = raw.splitlines()
            for thing in foo:
                if 'OE-Core rev' in thing:
                    thing = thing.replace('(From ', '')
                    thing = thing.replace(')', '')
                    print thing
            sys.exit()


if __name__ == '__main__':

    os.system("clear")
    
    if len(sys.argv) != 2:
        print("USAGE: {0} <poky hash>".format(__file__))
        sys.exit(0)
 
    main(sys.argv[1])
