#!/usr/bin/python3

import os
import argparse
import re
import requests
import git
import shutil

def get_request(url):
    # try request for 3 time max 
    count = 0
    while(count < 3):
        try:
            print("checking request %s ..." % url)
            req = requests.get(url, timeout=20)
            break
        except:
            count += 1
    return req

def cast_cve_to_rst_format(line):
    cve_exist = re.search(r"(?P<cve>cve-[0-9]*-[0-9]*)( +|$)", line, flags=re.I)
    component = re.search(r"^(?P<comp>.*( +)?:( +)?(Fix|Ignore))", line, flags=re.I)
    if cve_exist:
        cve_line = []
        for m in re.finditer(r"(?P<cve>cve-[0-9]*-[0-9]*)( +|$)", line, flags=re.I):
            cve_line.append(m.group("cve"))
        #cve_line.sort()
        cves = []
        rline = line
        for cve in cve_line:
            print("Checking %s ..." % cve.upper())
            nvd = get_request('https://nvd.nist.gov/vuln/detail/%s' % cve.upper())
            mitre = get_request('https://cve.mitre.org/cgi-bin/cvename.cgi?name=%s' % cve.upper())

            tmp = cve
            if mitre:
                if not "Could not find a CVE Record for" in mitre.text:
                    tmp = "%s`" % re.sub("cve-",":cve_mitre:`", cve, flags=re.I)
            if nvd:
                if not "CVE ID Not Found" in nvd.text and not "Invalid Parameters" in nvd.text:
                    tmp = "%s`" % re.sub("cve-",":cve_nist:`", cve, flags=re.I)
            cves.append(tmp)
            
            rline = re.sub(cve, tmp, line, flags=re.I)
        if component and len(cves) > 1:
            rline = component.group("comp")
            for index, cve in enumerate(cves):
                if index == 0:
                    rline += " %s" % cve
                elif len(cves) - 1  == index:
                    rline += " and %s\n" % cve
                else:
                    rline += ", %s" % cve
        return rline
    else:
        return line


def get_all_term(poky_repo):
    all_terms = []
    # the all_term_patterns in dictionary with {"pattern": "rst term format"}
    # eg: { "'SRC_URI'" : ":term:`SRC_URI`"}
    all_terms_patterns = {}
    try:
        variables_rst_file = open("%s/documentation/ref-manual/variables.rst" % poky_repo.working_tree_dir , "r")
    except:
        raise("Failed to read for variable from %s/documentation/ref-manual/variables.rst" % poky_repo.working_tree_dir)

    variables_rst = variables_rst_file.read()

    term_pattern = re.compile(r":term:`(?P<term>[A-Z_]+)`")
    
    for term_match in term_pattern.finditer(variables_rst):
        print("Found term : %s" % term_match.group("term"))
        all_terms.append(term_match.group("term"))

    # remove duplicates
    set_all_terms =  set(all_terms)
    for term in set_all_terms:
        all_terms_patterns.update({"( +)%s( +|$)" % term : " :term:`%s` " % term })
        all_terms_patterns.update({"'%s'" % term : " ':term:`%s`' " % term })

    return all_terms_patterns


def get_repo(codename):
    repo_url = 'https://git.yoctoproject.org/poky'
    CWD = os.getcwd()
    repo_path = os.path.join(CWD,'poky')
    if os.path.exists(repo_path):
        print("\nFound an existing poky repo. Nuking it.")
        shutil.rmtree(repo_path)
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

ap = argparse.ArgumentParser(description="input file and cast into half baked rst file")

ap.add_argument('--input', action='store', default=None, required=True,
        help='input text file to cast to rst')

ap.add_argument('--output', action='store', default=None, required=False,
        help='output rst file, if this is not set output file will be <input file>.rst ')

ap.add_argument('--branch', action='store', default=None, required=True,
        help='poky branch to refer for variable term convertion ')

args = ap.parse_args()

poky_repo = get_repo(args.branch)
all_terms_patterns = get_all_term(poky_repo)

if os.path.exists( args.input ):
    infile_path = args.input
    infile = open( args.input , 'r')
else:
    infile_path = os.path.join( os.getcwd(), args.input)
    if os.path.exists(infile_path):
        infile = open(infile_path, 'r')
    else:
        sys.exit("unable to find input file: %s" % args.input)

if args.output:
    outfile = open(args.output, 'w')
else:
    outfile = open( "%s.rst" % infile_path , 'w')

lines = infile.readlines()
for line in lines:
    l = line
    if 'CVE' in line:
        l = cast_cve_to_rst_format(line)

    for x, pat in enumerate(all_terms_patterns):
        l = re.sub(pat,all_terms_patterns[pat] ,l)

    outfile.write("-  %s" % l )

infile.close()
outfile.close()

