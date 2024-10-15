# SPDX-License-Identifier: GPL-2.0-only
'''
Created on Oct 16, 2018

__author__ = "Tracy Graydon"
__copyright__ = "Copyright 2018 - 2019, Intel Corp."
__credits__ = ["Tracy Graydon"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Tracy Graydon"
__email__ = "tracy.graydon@intel.com"
'''

import os
import os.path
import pwd
import socket
import sys
import hashlib
import glob

def where_am_i():
    hosts = ["debian12-vk-6", "debian12-vk-7", "debian12-vk-8", "debian12-vk-9",
             "ubuntu2404-vk-1","ubuntu2404-vk-2", "ubuntu2404-vk-3"]

    abhost = socket.getfqdn()
    if "yocto.io" in abhost or abhost in hosts:
        VHOSTS = "/srv/autobuilder"
    elif "autobuilder.yoctoproject.org" in abhost:
        VHOSTS = "/srv/www/vhosts"
    else:
        print("I don't recognize this host, so defaulting to /srv/www/vhosts.")
        # Uncomment this if you want to use /srv/autobuilder as the VHOSTS dir. It's useful for testing.
        #VHOSTS = "/srv/autobuilder"
        VHOSTS = "/srv/www/vhosts"
        print("Setting VHOSTS to %s" %VHOSTS)
    AB_HOME = os.path.join(VHOSTS, "valkyrie.yocto.io/pub") # uninative release (uninative.py) uses this
    AB_BASE = os.path.join(AB_HOME, "releases") # all RC candidates live here
    DL_HOME = os.path.join(VHOSTS, "downloads.yoctoproject.org/releases") # uninative release (uninative.py) uses this
    DL_BASE = os.path.join(DL_HOME, "yocto") # all other releases use this
    path_dict = {'VHOSTS': VHOSTS, 'AB_HOME': AB_HOME, 'AB_BASE': AB_BASE, 'DL_HOME': DL_HOME, 'DL_BASE': DL_BASE}
    return path_dict

def who_am_i():
    I_AM = pwd.getpwnam(os.getlogin())
    return I_AM

def signature():
   me = who_am_i()
   pwd_email = me[4]
   # There can be at least two formats for the email portion:
   # Case 1: FULL NAME <foo@somewhere.com>
   # or
   # Case 2: foo@somewhere.com
   # Account for both. Add new formats if we discover more.
   # Case 1
   email_chunks = split_thing(pwd_email, " ")
   if len(email_chunks) == 1:
       email = pwd_email
   elif len(email_chunks) > 1:
       # Case 2
       email = email_chunks[-1].replace("<", "").replace(">", "")
   #print "Email: %s" %email
   chunks = split_thing(email, "@")
   chunks = chunks[0]
   name_chunks = split_thing(chunks, ".")
   firstname = name_chunks[0]
   lastname = name_chunks.pop()
   full_name = " ".join([firstname.capitalize(), lastname.capitalize()])
   return [full_name, email]

def get_list(dirname):
    dirlist = os.listdir(dirname)
    dirlist.sort()
    return dirlist

def split_thing(thing, marker):
    filebits = thing.split(marker)
    return filebits

def rejoin_thing(thing, marker):
    filebits = marker.join(thing)
    return filebits

def sanity_check(source, target):
    if not os.path.exists(source):
       print
       print("SOURCE dir %s does NOT EXIST." %source)
       print
       sys.exit()
    if not os.listdir(source):
       print
       print("SOURCE dir %s is EMPTY" %source)
       print
    if os.path.exists(target):
       print
       print("The TARGET directory %s already exists! " %target)
       print
       sys.exit()
    return

def sync_it(source, target):
    print("Syncing %s to %s" %(source, target))
    sanity_check(source, target)
    source = source + "/"
    os.system("rsync -avrl '%s' '%s'" %(source, target))
    print
    return

def check_rc(rc_source):
    if not os.path.isdir(rc_source):
        print("I cannot find %s. Please check your RC name." %rc_source)
        print("Please use -h or --help for options.")
        found = "False"
    else:
        print("Found RC dir %s." %rc_source)
        found = "True"
    return found

def get_sha256sum(path, blocksize = 4096):
    f = open(path, 'rb')
    sha256sum = hashlib.sha256()
    buffer = f.read(blocksize)
    while len(buffer) > 0:
        sha256sum.update(buffer)
        buffer = f.read(blocksize)
    f.close()
    return sha256sum.hexdigest()

def gen_sha256sum(dirname):
    print
    print("Generating sha256sums for files in %s...." %dirname)
    for root, dirs, files in os.walk(dirname, topdown=True):
        for name in files:
            filename = (os.path.join(root, name))
            if not os.path.islink(filename):
                sha256sum = get_sha256sum(filename)
                sha256_file = ".".join([filename, 'sha256sum'])
                sha256str = sha256sum + " " + name
                print(sha256str)
                f = open(sha256_file, 'w')
                f.write(sha256str)
                f.close()
    return

def gen_rel_sha256(dirname, sha256_file):
    os.chdir(dirname)
    print("Generating master sha256sum file %s" %sha256_file)
    f = open(sha256_file, 'w')
    for root, dirs, files in os.walk(dirname, topdown=True):
        for name in files:
            filename = (os.path.join(root, name))
            ext = split_thing(name, ".")[-1]
            if not (ext == "md5sum" or ext == "sha256sum" or ext == "txt"):
                relpath = split_thing(filename, dirname)
                relpath.pop(0)
                relpath = relpath[0]
                relpath = split_thing(relpath, "/")
                relpath.pop(0)
                relpath = rejoin_thing(relpath, "/")
                relpath = "./" + relpath
                print(relpath)
                sha256sum = get_sha256sum(filename)
                print(sha256sum)
                sha256str = sha256sum + " " + relpath
                print(sha256str)
                f.write(sha256str + '\n')
    f.close()
    return

def get_hashes(rc_name):
    from rel_type import release_type 
    
    PATH_DICT = where_am_i()
    AB_BASE = PATH_DICT['AB_BASE']

    VARS = release_type(rc_name)
    RELEASE = VARS['RELEASE']
    RC_DIR = VARS['RC_DIR']
    RC_SOURCE = os.path.join(AB_BASE, RC_DIR)
    RELEASE_DIR = os.path.join(AB_BASE, RELEASE)

    HOME = os.getcwd()
    HASH_FILE = ".".join(["HASHES", RELEASE])
    outpath = os.path.join(HOME, HASH_FILE)

    os.chdir(RC_SOURCE)
    files = glob.glob('*.bz2')
    filelist = list(filter(lambda f: os.path.isfile(f), files))
    filelist.sort()
    outfile = open(outpath, 'w')
    for item in filelist:
        chunks = split_thing(item, ".")
        new_chunk = split_thing(chunks[0], '-')
        hash = new_chunk.pop()
        RELEASE_NAME = rejoin_thing(new_chunk, "-")
        outfile.write("%s: %s\n" %(RELEASE_NAME, hash))
    outfile.close()
    print("Hashes written to %s\n" %HASH_FILE)
    return HASH_FILE
