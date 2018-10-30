'''
Created on Oct 16, 2018

__author__ = "Tracy Graydon"
__copyright__ = "Copyright 2018 Intel Corp."
__credits__ = ["Tracy Graydon"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Tracy Graydon"
__email__ = "tracy.graydon@intel.com"
'''

import os
import os.path
import socket
import sys
import hashlib
import glob
#import shutil
#from shutil import rmtree, copyfile
#from subprocess import call

def where_am_i():
    abhost = socket.getfqdn()
    print "ABHOST: %s" %abhost
    if "yocto.io" in abhost:
        VHOSTS = "/srv/autobuilder"
    elif "autobuilder.yoctoproject.org" in abhost:
        VHOSTS = "/srv/www/vhosts"
    else:
        print "I don't recognize this host, so defaulting to /srv/www/vhosts."
        # Uncomment this if you want to use /srv/autobuilder as the VHOSTS dir. It's useful for testing.
        #VHOSTS = "/srv/autobuilder"
        VHOSTS = "/srv/www/vhosts"
        print "Setting VHOSTS to %s" %VHOSTS
    AB_HOME = os.path.join(VHOSTS, "autobuilder.yoctoproject.org/pub") # uninative release (uninative.py) uses this
    AB_BASE = os.path.join(AB_HOME, "releases") # all RC candidates live here
    DL_HOME = os.path.join(VHOSTS, "downloads.yoctoproject.org/releases") # uninative release (uninative.py) uses this
    DL_BASE = os.path.join(DL_HOME, "yocto") # all other releases use this
    path_dict = {'VHOSTS': VHOSTS, 'AB_HOME': AB_HOME, 'AB_BASE': AB_BASE, 'DL_HOME': DL_HOME, 'DL_BASE': DL_BASE}
    return path_dict

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
       print "SOURCE dir %s does NOT EXIST." %source
       print
       sys.exit()
    if not os.listdir(source):
       print
       print "SOURCE dir %s is EMPTY" %source
       print
    if os.path.exists(target):
       print
       print "The TARGET directory %s already exists! " %target
       print
       sys.exit()
    return

def sync_it(source, target):
    print "Syncing %s to %s" %(source, target)
    sanity_check(source, target)
    source = source + "/"
    os.system("rsync -avrl '%s' '%s'" %(source, target))
    print
    return

def check_rc(rc_source):
    if not os.path.isdir(rc_source):
        print "I cannot find %s. Please check your RC name." %rc_source
        print "Please use -h or --help for options."
        found = "False"
    else:
        print "Found RC dir %s." %rc_source
        found = "True"
    return found

def get_md5sum(path, blocksize = 4096):
    f = open(path, 'rb')
    md5sum = hashlib.md5()
    buffer = f.read(blocksize)
    while len(buffer) > 0:
        md5sum.update(buffer)
        buffer = f.read(blocksize)
    f.close()
    return md5sum.hexdigest()

def gen_md5sum(dirname):
    print
    print "Generating md5sums for files in %s...." %dirname
    for root, dirs, files in os.walk(dirname, topdown=True):
        for name in files:
            filename = (os.path.join(root, name))
            if not os.path.islink(filename):
                md5sum = get_md5sum(filename)
                md5_file = ".".join([filename, 'md5sum'])
                md5str = md5sum + " " + name
                print md5str
                f = open(md5_file, 'w')
                f.write(md5str)
                f.close()
    return

def gen_rel_md5(dirname, md5_file):
    os.chdir(RELEASE_DIR)
    print "Generating master md5sum file %s" %md5_file
    f = open(md5_file, 'w')
    for root, dirs, files in os.walk(dirname, topdown=True):
        for name in files:
            filename = (os.path.join(root, name))
            ext = split_thing(name, ".")[-1]
            if not (ext == "md5sum" or ext == "txt"):
                relpath = split_thing(filename, RELEASE_DIR)
                relpath.pop(0)
                relpath = relpath[0]
                relpath = split_thing(relpath, "/")
                relpath.pop(0)
                relpath = rejoin_thing(relpath, "/")
                relpath = "./" + relpath
                print relpath
                md5sum = get_md5sum(filename)
                print md5sum
                md5str = md5sum + " " + relpath
                print md5str
                f.write(md5str + '\n')
    f.close()
    return
