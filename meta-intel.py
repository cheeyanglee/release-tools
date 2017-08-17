'''
Created on Aug 16, 2017

__author__ = "Tracy Graydon"
__copyright__ = "Copyright 2017 Intel Corp."
__credits__ = ["Tracy Graydon"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Tracy Graydon"
__email__ = "tracy.graydon@intel.com"
'''

import logging
import os
import optparse
import sys
import hashlib
import glob
import os.path
import fnmatch
import shutil
from shutil import rmtree, copyfile
from subprocess import call

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
       print "I can't let you do it, Jim. The TARGET directory %s exists." %target
       print
       sys.exit()
    return

def sync_it(source, target, exclude_list):
    print "Syncing %s to %s" %(source, target)
    sanity_check(source, target)
    source = source + "/"
    if exclude_list:
        exclusions = ['--exclude=%s' % x.strip() for x in exclude_list]
        print "Exclusions: %s" %exclusions
        print
        exclude = "--exclude=" + os.path.join(RELEASE_DIR, exclude_list[0])
        length = len(exclude_list)
        for i in range(1, length):
            exclude = exclude + " " + "--exclude=" + os.path.join(RELEASE_DIR, exclude_list[i])
        print "Exclude: %s" %exclude
        command = 'rsync -avrl ' + str(exclude) + " " + str(source) + " " + str(target)
        os.system(command)
    else:
        os.system("rsync -avrl '%s' '%s'" %(source, target))
    print
    return

def purge_unloved():
    print
    print "Purging unwanted directories..."
    for target in UNLOVED:
        target = target.rstrip()
        print "Deleting: %s/%s" %(RELEASE_DIR, target)
        os.system('rm -rf %s/%s' %(RELEASE_DIR, target))
    return

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

def fix_tarballs():
    print
    print "Repackaging poky and eclipse tarballs...."
    logging.info('Repackaging poky and eclipse tarballs.')
    os.chdir(RELEASE_DIR)
    os.mkdir(TARBALL_DIR)
    os.system("mv %s/*.tar.bz2 %s" %(RELEASE_DIR, TARBALL_DIR))
    os.system("rm *.md5sum")
    os.chdir(TARBALL_DIR)
    dirlist = get_list(TARBALL_DIR)
    for blob in dirlist:
        print "Original Tarball: %s" %blob
        logging.info('Repackaging %s' %blob)
        chunks = split_thing(blob, ".")
        filename = chunks[0]
        basename = split_thing(filename, "-")
        index = len(basename)-1
        basename[index] = "-".join([BRANCH, META_VER])
        new_name = rejoin_thing(basename, "-")
        chunks[0] = new_name
        new_blob = rejoin_thing(chunks, ".")
        print "New Tarball: %s" %new_blob
        logging.info('New blob is %s' %new_blob)
        os.system("tar jxf %s" %blob)
        os.system("mv %s %s" %(filename, new_name))
        os.system("rm -rf %s/.git*" %new_name)
        os.remove(blob)
        os.system("tar jcf %s %s" %(new_blob, new_name))
        rmtree(new_name)
        os.symlink(new_blob, blob)
        os.system("md5sum %s > %s.md5sum" %(new_blob, new_blob))
        logging.info('Successful.')
        print
    logging.info('Moving new blobs to release dir and cleaning up.')
    os.system("mv * %s" %RELEASE_DIR)
    os.chdir(RELEASE_DIR)
    os.rmdir(TARBALL_DIR)
    logging.info('Successful.')
    print
    return

def get_md5sum(path, blocksize = 4096):
    f = open(path, 'rb')
    md5sum = hashlib.md5()
    buffer = f.read(blocksize)
    while len(buffer) > 0:
        md5sum.update(buffer)
        buffer = f.read(blocksize)
    f.close()
    return md5sum.hexdigest()

def convert_symlinks(dirname):
    thing = os.path.split(dirname)[1]
    if thing == "qemu":
        dirlist = get_list(dirname)
        for dir in dirlist:
            qemu_dir = os.path.join(MACHINES, dirname, dir)
            print "Converting symlinks in %s" %qemu_dir
            convert_symlinks(qemu_dir)
    else:
        print "Converting symlinks in %s" %dirname
        link_list = []
        for root, dirs, files in os.walk(dirname, topdown=True):
            for name in files:
                filename = (os.path.join(root, name))
                if os.path.islink(filename):
                    src_file = os.path.realpath(filename)
                    link_list.append([filename, src_file])
        for line in link_list:
            os.remove(line[0])
            try:
               copyfile(line[1], line[0])
            except IOError:
                print "Error: %s is missing or isn\'t a real file" %line[1]
            else:
                print line[0]
        for line in link_list:
            if os.path.exists(line[1]):
               os.remove(line[1])
    print
    return

def find_dupes(dirname, platform):
    print "\nLooking for duplicate files in %s" %dirname
    file_list = []
    md5sum_list = []
    for root, dirs, files in os.walk(dirname, topdown=True):
        for name in files:
            filename = (os.path.join(root, name))
            md5sum = get_md5sum(filename)
            file_list.append((filename, md5sum))
            md5sum_list.append(md5sum)
    s=set(md5sum_list)
    d=[]
    for x in file_list:
        if x[1] in s:
            s.remove(x[1])
        else:
            d.append(x[1])
    for dupe in d:
        for tup in file_list:
            if tup[1] == dupe:
                dupe_name = split_thing(tup[0],"/")
                filename = dupe_name[-1]
                if filename.find(platform) == -1:
                    print "Deleting %s" %tup[0]
                    os.remove(tup[0])
    return

def nuke_cruft(dirname, ext_list):
    thing = os.path.split(dirname)[1]
    if thing == "qemu":
        dirlist = get_list(dirname)
        for dir in dirlist:
            qemu_dir = os.path.join(MACHINES, dirname, dir)
            nuke_cruft(qemu_dir, CRUFT_LIST)
    else:
        for ext in ext_list:
            print "Deleting %s files" %ext
            os.system("rm -f %s/%s" %(dirname, ext))
    print
    return


def gen_md5sum(dirname):
    print
    print "Generating md5sums for files in %s...." %dirname
    for root, dirs, files in os.walk(dirname, topdown=True):
        for name in files:
            filename = (os.path.join(root, name))
            md5sum = get_md5sum(filename)
            md5_file = ".".join([filename, 'md5sum'])
            md5str = md5sum + " " + name
            print md5str
            f = open(md5_file, 'w')
            f.write(md5str)
            f.close()
    return


if __name__ == '__main__':

    os.system("clear")
    print

    #TODO: set up the logging
    #logfile = 'staging.log'
    #try:
    #    os.remove(logfile)
    #except OSError:
    #    pass

    #logging.basicConfig(format='%(levelname)s:%(message)s',filename=logfile,level=logging.INFO)

    VHOSTS = "/srv/www/vhosts"
    AB_BASE = os.path.join(VHOSTS, "autobuilder.yoctoproject.org/pub/releases")

    parser = optparse.OptionParser()
    parser.add_option("-i", "--build-id",
                      type="string", dest="build",
                      help="Required. Release candidate name including rc#. i.e. yocto-2.0.rc1, yocto-2.1_M1.rc3, etc.")
    parser.add_option("-b", "--branch",
                      type="string", dest="branch",
                      help="Required. i.e. daisy, fido, jethro, etc.")
    parser.add_option("-p", "--meta-intel-ver",
                      type="string", dest="meta",
                      help="Required. i.e. 6.0, 7.0, 8.0.")
    parser.add_option("-s", "--source-only",
                      type="string", dest="source_only",
                      help="Release only the source, no binaries. i.e. -s true")

    (options, args) = parser.parse_args()

    REL_TYPE = ""
    MILESTONE = ""
    if options.meta:
        META_VER = options.meta
    else:
        META_VER = ""
    if options.branch:
        BRANCH = options.branch
    else:
        BRANCH = ""

    if options.build:
        # Figure out the release name, type of release, and generate some vars, do some basic validation
        options.build = options.build.lower()
        RC = split_thing(options.build, ".")[-1]
        chunks = split_thing(options.build, ".") # i.e. split yocto-2.1_m1.rc1
        chunks.pop()
        chunks[1] = chunks[1].upper()
        RELEASE = rejoin_thing(chunks, ".")  # i.e. yocto-2.1_m1
        REL_ID = split_thing(RELEASE, "-")[-1].upper()
        RC_DIR = rejoin_thing([RELEASE, RC], ".")
        RC_SOURCE = os.path.join(AB_BASE, RC_DIR)
        if not os.path.exists(RC_SOURCE):
            print "%s does not appear to be a valid RC dir. Check your args." %RC_SOURCE
            sys.exit()
        relstring = split_thing(REL_ID, "_")
        if len(relstring) == 1:
            thing = split_thing(relstring[0], ".")
            if len(thing) == 3:
                REL_TYPE = "point"
            elif len(thing) == 2:
                REL_TYPE = "major"
            if options.meta and options.branch:
                META_VER = options.meta
                BRANCH = options.branch
            else:
                print "Meta-intel version is REQUIRED. Check your args."
                print "Please use -h or --help for options."
                sys.exit()
        else:
            MILESTONE = relstring.pop()
            REL_TYPE = "milestone"
    else:
        print "Build ID is a required argument."
        print "Please use -h or --help for options."
        sys.exit()

    if not (RELEASE and RC and REL_ID and REL_TYPE):
        print "Can't determine the release type. Check your args."
        print "You gave me: %s" %options.build
        sys.exit()

    print "RC_DIR: %s" %RC_DIR
    print "RELEASE: %s" %RELEASE
    print "RC: %s" %RC
    print "REL_ID: %s" %REL_ID
    print "REL_TYPE: %s" %REL_TYPE
    if MILESTONE:
        print "MILESTONE: %s" %MILESTONE
    print

    RELEASE_DIR = os.path.join(AB_BASE, RELEASE)
    META_TARBALL = "meta-intel-" + META_VER + "-" + BRANCH + "-" + REL_ID + ".tar.bz2"

    # Not using these at the moment, but we will.
    #MACHINES = os.path.join(RELEASE_DIR, "machines")
    #BSP_DIR = os.path.join(RELEASE_DIR, 'bsptarballs')

    SOURCE_ONLY = options.source_only.lower()

    if SOURCE_ONLY == "true":
        print "Releasing SOURCE ONLY.\n"
        print "Creating the staging directory.\n"
        # Create the staging directory
        if not os.path.exists(RELEASE_DIR):
           os.mkdir(RELEASE_DIR)
        else:
            print "Staging dir exists! Quitting."
            sys.exit()
        # Copy the meta-intel blob over to staging
        print "Finding the meta-intel blob."
        for file in os.listdir(RC_SOURCE):
            if fnmatch.fnmatch(file, 'meta-intel-*.tar.bz2'):
                blob = file
                blob_source = (os.path.join(RC_SOURCE, file))
        blob_dir = split_thing(blob, ".")
        blob_dir = rejoin_thing(blob_dir[:-2], ".")
        print "Copying the meta-intel blob to the staging directory."
        os.system("cp -v %s %s" %(blob_source, RELEASE_DIR))
        os.chdir(RELEASE_DIR)
        print "Creating the new meta-intel blob."
        os.system("tar jxf %s" %blob)
        meta_dir = split_thing(META_TARBALL, ".")
        meta_dir = rejoin_thing(meta_dir[:-2], ".")
        shutil.move(blob_dir, meta_dir)
        os.remove(blob)
        os.system("tar jcf %s %s" %(META_TARBALL, meta_dir))
        rmtree(meta_dir)
        print "Creating new symlink."
        os.symlink(META_TARBALL, blob)
        print "Generating the md5sum."
        os.system("md5sum %s > %s.md5sum" %(META_TARBALL, META_TARBALL))
    elif SOURCE_ONLY == "false":
        print "Releasing the whole enchilada."
        # But not really cuz not only does that not work yet, we aren't currently releasing binaries at all for meta-intel
        print "Well...I would if I could, but I can't, so I won't."
        sys.exit()
    else:
        print "I don't know what you want. Check your source_only argument."
        sys.exit()
