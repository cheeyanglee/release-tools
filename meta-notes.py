import os
import os.path
import optparse
import sys
import re
from shutil import rmtree
from pygit2 import Repository, clone_repository
from pygit2 import GIT_SORT_TIME
from utils import where_am_i, split_thing, rejoin_thing
reload(sys)
sys.setdefaultencoding('utf-8')

def get_repo(codename):
    repo_url = 'http://git.yoctoproject.org/git/meta-intel'
    CWD = os.getcwd()
    repo_path = os.path.join(CWD,'meta-intel')
    if os.path.exists(repo_path):
        print "\nFound an existing meta-intel repo. Nuking it."
        rmtree(repo_path)
    print "Cloning the meta-intel repo."
    # If you pass in a non-existent branch, this will fail spectacularly. So let's catch that and die gracefully.
    try:
        meta_repo =clone_repository(repo_url, repo_path, checkout_branch=codename)
    except:
        print "Couldn't check out the meta-intel repo with branch %s. Check the branch name you passed in." %codename
        sys.exit()
    # Are we where we think we are?
    head = meta_repo.head
    branch_name = head.name
    print "We are now on branch: %s\n" %branch_name
    return meta_repo

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
  
    PATH_VARS = where_am_i()
    VHOSTS = PATH_VARS['VHOSTS']
    AB_HOME = PATH_VARS['AB_HOME']
    AB_BASE = PATH_VARS['AB_BASE']
    DL_HOME = PATH_VARS['DL_HOME']
    DL_BASE = PATH_VARS['DL_BASE']
    print "VHOSTS: %s" %VHOSTS
    print "AB_HOME: %s" %AB_HOME
    print "AB_BASE: %s" %AB_BASE
    print "DL_HOME: %s" %DL_HOME
    print "DL_BASE: %s" %DL_BASE
    print
    print "Build ID: %s" %options.build
    print "Revisions: %s" %options.revs
    print

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
    DL_URL = "http://downloads.yoctoproject.org/releases/yocto"
    MIRROR_URL = "http://mirrors.kernel.org/yocto/yocto"
    HOME = os.getcwd()
    SEC_INFO = os.path.join(HOME, "meta-intel-sec-info.txt")

    # Running through the dictionary to print var values results in random order, making it hard to read. So loop through values in desired order.
    for thing in ['RC_DIR', 'RELEASE', 'REL_TYPE', 'META_VER', 'YP_VER', 'YP_NAME', 'RC', 'BRANCH', 'TAG', 'RC_SOURCE', 'RELEASE_DIR']:
        print "%s: %s" %(thing, VARS[thing])
    print "RELEASENOTES file: %s" %RELEASE_NOTES
    print "META_TARBALL: %s" %META_TARBALL
    print "MD5FILE: %s" %MD5FILE

    # Now we have branch name and stuff, so let's clone the repo
    repo = get_repo(BRANCH)

    # Make sure the starting revision/tag exists.
    rev_chunks = split_thing(REVISIONS, "..")
    tag_rev = rev_chunks[0]  # The tag of the previous release
    head_rev = rev_chunks[1] # This is usually going to be the HEAD of the release branch we are on
    regex = re.compile('^refs/tags')
    tag_list = filter(lambda r: regex.match(r), repo.listall_references())
    if not tag_rev in str(tag_list):
        print "I can't find a tag matching %s. Check your revisions." %tag_rev
        sys.exit()

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
    DL_URL = "/".join([DL_URL, YP_NAME, blob]).strip()
    MIRROR_URL = "/".join([MIRROR_URL, YP_NAME, blob]).strip()
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

    print "Writing out the Security Info."
    outfile.write("\n---------------\nSecurity Fixes\n---------------\n")
    if os.path.isfile(SEC_INFO):
        infofile = open(SEC_INFO, 'r')
        all_the_things = infofile.read()
        infofile.close()
        outfile.writelines(all_the_things)

    print "Getting the Fixes for this release."
    outfile.write("\n\n---------------\nFixes\n---------------\n")

    start = repo.revparse_single(head_rev)
    release_tag = repo.revparse_single(tag_rev)

    print "Start ID: %s" %start.id
    print "Release_tag: %s" %release_tag.id

    walker = repo.walk(start.id, GIT_SORT_TIME)
    walker.hide(release_tag.id)
    for commit in walker:
        commit_id = str(commit.id)
        raw_message = str(commit.message.rstrip())
        # print "%s: %s" %(commit_id[0:8], raw_message.splitlines()[0])
        # If you want to include the commit hash, uncomment this one.
        #outfile.write("%s: %s\n" %(commit_id[0:8], raw_message.splitlines()[0]))
        outfile.write("%s\n" %raw_message.splitlines()[0])
    outfile.close()
    print "DONE!"
