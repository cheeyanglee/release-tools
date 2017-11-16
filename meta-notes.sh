#!/bin/bash

# This is a quick and ugly script to generate the release notes draft.
#
# Usage: ./meta-notes.sh <release_ID> <rc#> <branch> <meta-intel-ver>
# i.e. ./meta-intel.sh yocto-2.4 rc2 rocko 8.0-rocko-2.4 7.0-pyro-2.3..HEAD
#

clear
REL_ID=$1
RC=$2
BRANCH=$3
META_VER=$4
REVISIONS=$5
RELEASE=$REL_ID
VHOSTS="/srv/www/vhosts"
AB_BASE="$VHOSTS/autobuilder.yoctoproject.org/pub/releases"
DL_BASE="$VHOSTS/downloads.yoctoproject.org/releases"
RC_SOURCE="$AB_BASE/$RELEASE.$RC"
RELEASE_DIR="$AB_BASE/$RELEASE"
RELEASENOTES="RELEASENOTES.${META_VER}"
echo "RELEASENOTES: $RELEASENOTES"
HOME=$PWD
PREFIX="meta-intel"

echo "REL_ID: $REL_ID"
echo "RC: $RC"
echo "BRANCH: $BRANCH"
echo "META_VER: $META_VER"
echo "RELEASE: $RELEASE"
echo "RELEASE_DIR: $RELEASE_DIR"
echo "REVISIONS: $REVISIONS"
echo

if [[ -e $HOME/$RELEASENOTES ]]; then
    rm -v $HOME/$RELEASENOTES
fi
if [[ -e $HOME/CVE ]]; then
    rm -v $HOME/CVE
fi
if [[ -e $HOME/FIXES ]]; then
    rm -v $HOME/FIXES
fi
if [[ -d $HOME/meta-intel ]]; then
    rm -rf $HOME/meta-intel
fi
echo


RELEASE_NAME="$PREFIX-$META_VER"
tarball="$RELEASE_NAME.tar.bz2"
DOWNLOAD="http://downloads.yoctoproject.org/releases/yocto/$RELEASE/$tarball"
MIRROR="http://mirrors.kernel.org/yocto/yocto/$RELEASE/$tarball"
REPO="git://git.yoctoproject.org/meta-intel"
hash_file=`find $RELEASE_DIR -type l`
HASH=`basename $hash_file | sed 's/meta-intel-//' | sed 's/\.tar\.bz2//'`
MD5=`cat $RELEASE_DIR/$tarball.md5sum | awk '{print $1}'`


echo -e "\n---------------------\n $META_VER ERRATA \n---------------------\n" | tee -a $HOME/$RELEASENOTES
echo "Release Name: $RELEASE_NAME" | tee -a $HOME/$RELEASENOTES
echo "Repo: $REPO" | tee -a $HOME/$RELEASENOTES
echo "Branch: $BRANCH" | tee -a $HOME/$RELEASENOTES
echo "Tag: $META_VER" | tee -a $HOME/$RELEASENOTES
echo "Hash: $HASH" | tee -a $HOME/$RELEASENOTES
echo "md5: $MD5" | tee -a $HOME/$RELEASENOTES
echo "Download Locations:" | tee -a $HOME/$RELEASENOTES
echo "$DOWNLOAD" | tee -a $HOME/$RELEASENOTES
echo "$MIRROR"| tee -a $HOME/$RELEASENOTES

echo -e "\n----------------------\n Features/Enhancements \n----------------------\n" | tee -a $HOME/$RELEASENOTES

echo -e "\n----------------------\n Known Issues \n----------------------\n" | tee -a $HOME/$RELEASENOTES

# Get the CVE and Fixes from previous relevant release to HEAD
git clone $REPO;
cd meta-intel
git checkout $BRANCH;
echo -e "\n------------\nSecurity Fixes\n------------" >> $HOME/CVE;
git log --pretty=format:"%s" $REVISIONS |grep CVE >> $HOME/CVE;
echo -e "\n-------\nFixes\n-------" >> $HOME/FIXES;
git log --pretty=format:"%s" $REVISIONS |grep -v CVE >> $HOME/FIXES;
cat $HOME/CVE >> $HOME/$RELEASENOTES; cat $HOME/FIXES >> $HOME/$RELEASENOTES
cd $HOME



