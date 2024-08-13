import json
import subprocess
import sys
import tempfile

# Embedded JSON data
data = {
  "Version" : [

   {"version_string": "kirkstone",
   "yocto_version": "4.0",
   "date_string": "2022-04",
   "bitbake_version": "2.0",
   "repos": [
    {"git_url" : "https://git.yoctoproject.org/poky" ,
     "tags" : [ "version_string-yocto_version.minor_version",  "yocto-yocto_version.minor_version"] },
    {"git_url" : "https://git.yoctoproject.org/yocto-docs" ,
     "tags" : [ "version_string-yocto_version.minor_version",  "yocto-yocto_version.minor_version"] },
    {"git_url" : "https://git.yoctoproject.org/meta-mingw" ,
     "tags" : [ "version_string-yocto_version.minor_version",  "yocto-yocto_version.minor_version"] },
    {"git_url" : "https://git.yoctoproject.org/meta-gplv2" ,
     "tags" : [ "version_string-yocto_version.minor_version",  "yocto-yocto_version.minor_version"] },	 
    {"git_url" : "https://git.openembedded.org/bitbake" ,
     "tags" : [ "yocto-yocto_version.minor_version", "date_string.minor_version-version_string", "bitbake_version.minor_version"] },	
    {"git_url" : "https://git.openembedded.org/openembedded-core" ,
     "tags" : [ "yocto-yocto_version.minor_version", "date_string.minor_version-version_string", "date_string.minor_version"] },
    {"git_url" : "https://git.yoctoproject.org/yocto-testresults" ,
     "tags" : [ "version_string-yocto_version.minor_version",  "yocto-yocto_version.minor_version"] },
    {"git_url" : "https://git.yoctoproject.org/yocto-testresults-contrib" ,
     "tags" : [ "version_string-yocto_version.minor_version",  "yocto-yocto_version.minor_version"] }
	 ] },

   {"version_string": "nanbield",
   "yocto_version": "4.3",
   "date_string": "2023-10",
   "bitbake_version": "2.6",
   "repos": [
    {"git_url" : "https://git.yoctoproject.org/poky" ,
     "tags" : [ "version_string-yocto_version.minor_version",  "yocto-yocto_version.minor_version"] },
    {"git_url" : "https://git.yoctoproject.org/yocto-docs" ,
     "tags" : [ "version_string-yocto_version.minor_version",  "yocto-yocto_version.minor_version"] },
    {"git_url" : "https://git.yoctoproject.org/meta-mingw" ,
     "tags" : [ "version_string-yocto_version.minor_version",  "yocto-yocto_version.minor_version"] },
    {"git_url" : "https://git.openembedded.org/bitbake" ,
     "tags" : [ "yocto-yocto_version.minor_version", "date_string.minor_version-version_string", "bitbake_version.minor_version"] },	
    {"git_url" : "https://git.openembedded.org/openembedded-core" ,
     "tags" : [ "yocto-yocto_version.minor_version", "date_string.minor_version-version_string", "date_string.minor_version"] },
    {"git_url" : "https://git.yoctoproject.org/yocto-testresults" ,
     "tags" : [ "version_string-yocto_version.minor_version",  "yocto-yocto_version.minor_version"] },
    {"git_url" : "https://git.yoctoproject.org/yocto-testresults-contrib" ,
     "tags" : [ "version_string-yocto_version.minor_version",  "yocto-yocto_version.minor_version"] }
   ] },

   {"version_string": "scarthgap",
   "yocto_version": "5.0",
   "date_string": "2024-04",
   "bitbake_version": "2.8",
   "repos": [
    {"git_url" : "https://git.yoctoproject.org/poky" ,
     "tags" : [ "version_string-yocto_version.minor_version",  "yocto-yocto_version.minor_version"] },
    {"git_url" : "https://git.yoctoproject.org/yocto-docs" ,
     "tags" : [ "version_string-yocto_version.minor_version",  "yocto-yocto_version.minor_version"] },
    {"git_url" : "https://git.yoctoproject.org/meta-mingw" ,
     "tags" : [ "version_string-yocto_version.minor_version",  "yocto-yocto_version.minor_version"] },
    {"git_url" : "https://git.openembedded.org/bitbake" ,
     "tags" : [ "yocto-yocto_version.minor_version", "date_string.minor_version-version_string", "bitbake_version.minor_version"] },
    {"git_url" : "https://git.openembedded.org/openembedded-core" ,
     "tags" : [ "yocto-yocto_version.minor_version", "date_string.minor_version-version_string", "date_string.minor_version"] },
    {"git_url" : "https://git.yoctoproject.org/yocto-testresults" ,
     "tags" : [ "version_string-yocto_version.minor_version",  "yocto-yocto_version.minor_version"] },
    {"git_url" : "https://git.yoctoproject.org/yocto-testresults-contrib" ,
     "tags" : [ "version_string-yocto_version.minor_version",  "yocto-yocto_version.minor_version"] }
   ] },


   {"version_string": "milestone",
   "yocto_version": "5.1",
   "repos": [
    {"git_url" : "https://git.yoctoproject.org/poky" ,
     "tags" : [ "yocto_version_minor_version"] },
    {"git_url" : "https://git.yoctoproject.org/meta-mingw" ,
     "tags" : [ "yocto_version_minor_version"] },
    {"git_url" : "https://git.yoctoproject.org/yocto-testresults" ,
     "tags" : [ "yocto_version_minor_version"] },
    {"git_url" : "https://git.yoctoproject.org/yocto-testresults-contrib" ,
     "tags" : [ "yocto_version_minor_version"] }
   ] }
 ]
}


# Function to clone, verify, and remove the repository tag
def clone_verify(repo_url, tag):
    with tempfile.TemporaryDirectory(dir='/tmp') as tmpdirname:
        clone_dir = tempfile.mkdtemp(dir=tmpdirname)
        try:
            # Clone the repository with the specific tag (shallow clone)
            subprocess.run(["git", "clone", "--depth", "1", "--branch", tag, repo_url, clone_dir], check=True)
            # Get the current HEAD commit hash
            commit_hash_result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=clone_dir, \
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            commit_hash = commit_hash_result.stdout.strip()
            # Verify the tag
            result = subprocess.run(["git", "verify-tag", tag], cwd=clone_dir, \
                     text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out = result.stdout
            if 'Good signature from "Yocto Build and Release <releases@yoctoproject.org>"' in out:
                return (repo_url, tag, "Good", commit_hash)
            else:
                return (repo_url, tag, "Bad", commit_hash)
        except subprocess.CalledProcessError as e:
            return (repo_url, tag, "Error", commit_hash)

# Main function to process user input and perform actions
def main(version_string, minor_version):
    verification_results = []
    version_obj = next((item for item in data["Version"] if item["version_string"] == version_string), None)
    if not version_obj:
        print(f"No matching version found for version_string: {version_string}")
        return

    for repo in version_obj["repos"]:
        for tag_template in repo["tags"]:
            tag = tag_template.replace("version_string", version_string) \
                              .replace("yocto_version", version_obj["yocto_version"]) \
                              .replace("minor_version", minor_version) \
                              .replace("bitbake_version", version_obj["bitbake_version"] or "") \
                              .replace("date_string", version_obj["date_string"] or "")
            result = clone_verify(repo["git_url"], tag)
            verification_results.append(result)

    # Display final results
    print("\nFinal Results:")
    for repo_url, tag, status, commit_hash in verification_results:
        print(f"Repo: {repo_url}, Hash:{commit_hash}  Tag: {tag}, Status: {status}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <version_string> <minor_version>")
        sys.exit(1)

    version_string_input = sys.argv[1]
    minor_version_input = sys.argv[2]
    main(version_string_input, minor_version_input)
