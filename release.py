# SPDX-License-Identifier: GPL-2.0-only
'''
Created on Jan 7, 2016

__author__ = "Tracy Graydon"
__copyright__ = "Copyright 2016-2019 Intel Corp."
__credits__ = ["Tracy Graydon"]
__license__ = "GPL"
__version__ = "2.0"
__maintainer__ = "Tracy Graydon"
__email__ = "tracy.graydon@intel.com"
'''

import logging
import os
import socket
import optparse
import sys
import hashlib
import glob
import os.path
import shutil
import tarfile
from shutil import rmtree, copy, copyfile, move
from subprocess import call
from utils import where_am_i, sanity_check, sync_it, get_list, split_thing, rejoin_thing, get_sha256sum, gen_sha256sum, gen_rel_sha256
from rel_type import release_type

def make_tarfile(target_blob, source_dir):
        with tarfile.open(target_blob, "w:bz2") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))
        tar.close()
        return

def fix_tarballs():
    print
    print("Repackaging the release tarballs.")
    logging.info('Repackaging the release tarballs.')
    os.chdir(RELEASE_DIR)
    if not os.path.exists(TARBALL_DIR):
        os.mkdir(TARBALL_DIR)
    for thing in glob.glob("*.tar.bz2"):
            move(thing, TARBALL_DIR)
    for thing in glob.glob("*.md5sum"):
            os.remove(thing)
    for thing in glob.glob("*.sha256sum"):
            os.remove(thing)
    os.chdir(TARBALL_DIR)
    dirlist = get_list(TARBALL_DIR)
    for blob in dirlist:
        # Get the tarball toplevel subdir name.
        # This can vary between release lines or otherwise change, so we will extract it from the given tarball.
        tarball = tarfile.open(blob, mode='r')
        tar_dir = os.path.commonprefix(tarball.getnames())
        # Generate the new tarball name
        print("Oringinal Tarball: %s" %blob)
        chunks = split_thing(blob, ".")
        filename = chunks[0]
        dirname = split_thing(filename, "-")
        dirname.pop()
        dirname = rejoin_thing(dirname, "-")
        basename = "-".join([dirname, BRANCH, POKY_VER])
        chunks[0] = basename
        new_blob = rejoin_thing(chunks, ".")
        print("New Tarball: %s" %new_blob)
        logging.info('New blob is %s' %new_blob)
        tarball.extractall()
        tarball.close()
        os.rename(tar_dir, basename)
        os.system("rm -rf %s/.git*" %basename)
        os.remove(blob)
        make_tarfile(new_blob, basename)
        rmtree(basename)
        os.symlink(new_blob, blob)
        os.system("sha256sum %s > %s.sha256sum" %(new_blob, new_blob))
        logging.info('Successful.')
        print
    logging.info('Moving new blobs to release dir and cleaning up.')
    os.system("mv * %s" %RELEASE_DIR)
    os.chdir(RELEASE_DIR)
    rmtree(TARBALL_DIR)
    logging.info('Successful.')
    print
    return

def convert_symlinks(dirname):
    thing = os.path.split(dirname)[1]
    if thing == "qemu":
        dirlist = get_list(dirname)
        for dir in dirlist:
            qemu_dir = os.path.join(MACHINES, dirname, dir)
            print("Converting symlinks in %s" %qemu_dir)
            convert_symlinks(qemu_dir)
    else:
        print("Converting symlinks in %s" %dirname)
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
                print("Error: %s is missing or isn\'t a real file" %line[1])
            else:
                print(line[0])
        for line in link_list:
            if os.path.exists(line[1]):
               os.remove(line[1])
    print
    return

def find_dupes(dirname, platform):
    print("\nLooking for duplicate files in %s" %dirname)
    file_list = []
    sha256sum_list = []
    for root, dirs, files in os.walk(dirname, topdown=True):
        for name in files:
            filename = (os.path.join(root, name))
            sha256sum = get_sha256sum(filename)
            file_list.append((filename, sha256sum))
            sha256sum_list.append(sha256sum)
    s=set(sha256sum_list)
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
                    print("Deleting %s" %tup[0])
                    os.remove(tup[0])
    return

def make_bsps(bsp_list, bsp_dir):
    print("\nCreating bsps.....\n")
    if not os.path.exists(bsp_dir):
        os.mkdir(bsp_dir)
        print("Created bsp_dir")
    else:
        print("BSP tarball dir exists! Skipping BSP creation.")
        return
    poky_blob = os.path.join(RELEASE_DIR, POKY_TARBALL)
    blob_dir = split_thing(POKY_TARBALL, ".")
    blob_dir = rejoin_thing(blob_dir[:-2], ".")
    os.chdir(bsp_dir)
    for dirname in bsp_list:
        platform_dir = os.path.join(MACHINES, dirname)
        if os.path.exists(platform_dir):
            if not os.path.exists(dirname):
                print("Creating %s bsp dir" %dirname)
                os.mkdir(dirname)
            target = os.path.join(dirname, POKY_TARBALL)
            oldblob = POKY_TARBALL
            chunks = split_thing(oldblob, "-")
            chunks[0] = dirname
            new_blob = rejoin_thing(chunks, "-")
            print("BSP tarball: %s" %new_blob)
            new_dir = split_thing(blob_dir, "-")
            new_dir[0] = dirname
            new_dir = rejoin_thing(new_dir, "-")
            bin_dir = os.path.join(new_dir, "binary")
            copyfile(poky_blob, target)
            os.chdir(dirname)
            print("Unpacking poky tarball.")
            tarball = tarfile.open(POKY_TARBALL, mode='r')
            tarball.extractall()
            tarball.close()
            shutil.move(blob_dir, new_dir)
            os.remove(POKY_TARBALL)
            if not os.path.exists(bin_dir):
                os.mkdir(bin_dir)
            print("Getting binary files")
            os.system("rsync -arl %s/%s/ %s" %(MACHINES, dirname, bin_dir))
            bsp_bin = os.path.join(bsp_dir, dirname, bin_dir)
            nuke_cruft(bin_dir, BSP_JUNK)
            bsp_path = os.path.join(bsp_dir, dirname, bin_dir)
            find_dupes(bsp_path, dirname)
            print("Creating BSP tarball")
            make_tarfile(new_blob, new_dir)
            rmtree(new_dir)
            print("Generating the sha256sum.")
            os.system("sha256sum %s > %s.sha256sum" %(new_blob, new_blob))
            print("Copying %s BSP to platform dir" %dirname)
            os.system("mv * %s" %platform_dir)
            os.chdir(bsp_dir)
        print
    os.chdir(RELEASE_DIR)
    rmtree(bsp_dir)
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
            print("Deleting %s files" %ext)
            os.system("rm -f %s/%s" %(dirname, ext))
    print
    return

def pub_eclipse(EDIR, PDIR):
    print("\nPublishing Eclipse plugins.")
    sanity_check(EDIR, PDIR)
    os.system("mkdir -p %s" %PDIR)
    for root, dirs, files in os.walk(EDIR, topdown=True):
        for name in dirs:
            target_dir = os.path.join(PDIR, name)
            os.system("mkdir -p %s" %target_dir)
            source_dir = os.path.join(EDIR, name)
            filelist = get_list(source_dir)
            foo = [ x for x in filelist if "sha256sum" not in x ]
            found = filter(lambda x: 'archive.zip' in x, foo).pop()
            source = os.path.join(EDIR, name, found)
            target = os.path.join(target_dir, found)
            print("Source: %s" %source)
            print("Target: %s" %target)
            copyfile(source, target)
            os.chdir(target_dir)
            print("Unzipping %s" %found)
            os.system("unzip -o '%s'" %found)
            os.system("rm -vf %s" %found)
            print
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
    print("VHOSTS: %s" %VHOSTS)
    print("AB_HOME: %s" %AB_HOME)
    print("AB_BASE: %s" %AB_BASE)
    print("DL_HOME: %s" %DL_HOME)
    print("DL_BASE: %s" %DL_BASE)
   
    # List of the files in machines directories that we delete from all releases
    CRUFT_LIST = ['*.md5sum', '*.tar.gz', '*.iso', '*.sha256sum']
    # List of the platforms for which we want to generate BSP tarballs. Major and point releases.
    BSP_LIST = ['beaglebone-yocto', 'edgerouter', 'genericx86', 'genericx86-64', 'mpc8315e-rdb']
    # List of files we do not want to include in the BSP tarballs.
    BSP_JUNK = ['*.manifest', '*.tar.bz2', '*.tgz', '*.iso', '*.md5sum', '*.tar.gz', '*-dev-*', '*-sdk-*', '*.sha256sum']

    parser = optparse.OptionParser()
    parser.add_option("-i", "--build-id",
                      type="string", dest="build",
                      help="Required. Release candidate name including rc#. i.e. yocto-2.0.rc1, yocto-2.1_M1.rc3, etc.")
    parser.add_option("-b", "--branch",
                      type="string", dest="branch",
                      help="Required for Major and Point releases. i.e. daisy, fido, jethro, etc.")
    parser.add_option("-p", "--poky-ver",
                      type="string", dest="poky",
                      help="Required for Major and Point releases. i.e. 14.0.0")
    (options, args) = parser.parse_args()

    if options.poky:
        POKY_VER = options.poky
    else:
        POKY_VER = ""
    if options.branch:
        BRANCH = options.branch
    else:
        BRANCH = ""

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

    for thing in ['RC_DIR', 'RELEASE', 'RC', 'REL_ID', 'REL_TYPE', 'MILESTONE']:
        print("%s: %s" %(thing, VARS[thing]))
    print("RC_SOURCE: %s" %RC_SOURCE)
    print("RELEASE_DIR: %s" %RELEASE_DIR)

    PLUGIN_DIR = os.path.join(DL_HOME, "eclipse-plugin", REL_ID)
    MACHINES = os.path.join(RELEASE_DIR, "machines")
    BSP_DIR = os.path.join(RELEASE_DIR, 'bsptarballs')
    TARBALL_DIR = os.path.join(RELEASE_DIR, "tarballs")
    POKY_TARBALL = "poky-" + BRANCH + "-" + POKY_VER + ".tar.bz2"
    ECLIPSE_DIR = os.path.join(RELEASE_DIR, "eclipse-plugin")
    BUILD_APP_DIR = os.path.join(RELEASE_DIR, "build-appliance")
    REL_SHA_FILE = RELEASE + ".sha256sum"

    print("BSP_DIR: %s" %BSP_DIR)
    print("MACHINES: %s" %MACHINES)
    print("TARBALL_DIR: %s" %TARBALL_DIR)
    print("POKY_TARBALL: %s" %POKY_TARBALL)
    logfile = ".".join(['staging-log', RELEASE])
    print("Logfile: %s" %logfile)
    try:
        os.remove(logfile)
    except OSError:
        pass
    logging.basicConfig(format='%(levelname)s:%(message)s',filename=logfile,level=logging.INFO)

    # For all releases:
    # 1) Rsync the rc candidate to a staging dir where all work happens
    logging.info('Start rsync.')
    print("Doing the rsync for the staging directory.")
    sync_it(RC_SOURCE, RELEASE_DIR)
    logging.info('Successful.')

    # 2) Convert the symlinks in build-appliance dir.
    print("Converting the build-appliance symlink.")
    logging.info('Converting build-appliance symlink.')
    convert_symlinks(BUILD_APP_DIR)
    logging.info('Successful.')

    # 3) In machines dir, convert the symlinks, delete the cruft
    print("Cleaning up the machines dirs, converting symlinks.")
    logging.info('Machines dir cleanup started.')
    dirlist = get_list(MACHINES)
    for dirname in dirlist:
        dirname = os.path.join(MACHINES, dirname)
        logging.info('Converting symlinks in %s' %dirname)
        convert_symlinks(dirname)
        logging.info('Successful.')
        logging.info('Nuking cruft in %s' %dirname)
        nuke_cruft(dirname, CRUFT_LIST)
        logging.info('Successful.')
    print("Generating fresh sha256sums.")
    logging.info('Generating fresh sha256sums.')
    gen_sha256sum(MACHINES)
    logging.info('Successful.')

    # For major and point releases
    if REL_TYPE == "major" or REL_TYPE == "point":
        # 4) Fix up the various tarballs
        print("Cleaning up the poky and other tarballs.")
        logging.info('Fixing tarballs.')
        fix_tarballs()

        # As of 2.6.2 we are no longer supporting eclipse
        # plugins. There is an off chance that we might
        # need to include them for some reason, so we'll
        # make it conditional for now.
        #5) Publish the eclipse stuff
        print("Checking for Eclipse Plugins....")
        if os.path.isdir(ECLIPSE_DIR) and os.listdir(ECLIPSE_DIR):
            print("Found Eclipse plugins. Publishing.")
            logging.info('Publishing eclipse plugins.')
            pub_eclipse(ECLIPSE_DIR, PLUGIN_DIR)
            logging.info('Successful.')
        else:
            print("No Eclipse Plugins Found. If that is not what you are expecting, check on that.")
            logging.info('No Eclipse Plugins Found. Nothing to publish.')

        # 6) Make the bsps
        print("Generating the BSP tarballs.")
        logging.info('Generating BSP tarballs.')
        make_bsps(BSP_LIST, BSP_DIR)
        logging.info('Successful.')

        # 7) Generate the master sha256sum file for the release (for all releases, except milestones)
        print("Generating the master sha256sum table.")
        logging.info('Generating the master sha256sum table.')
        gen_rel_sha256(RELEASE_DIR, REL_SHA_FILE)
        logging.info('Successful.')
