# This uploads all apkg files in the current directory to a release on GitHub.

import github
import dotenv
import os
import glob
import requests

requests.packages.urllib3.util.connection.HAS_IPV6 = False

dotenv.load_dotenv()

g = github.Github(os.getenv("GITHUB_TOKEN"))

repo = g.get_repo("Vuizur/tatoeba-to-anki")

# Now look if there is a release with the name "latest"
# If yes, replace all files in that release with the new ones
# If no, create a new release with the new files

release = None
for r in repo.get_releases():
    if r.title == "latest":
        print("Found a release with the name 'latest'")
        release = r
        break

if release is None:
    print("Creating a new release")
    release = repo.create_git_release(
        "latest",
        "latest",
        "The latest flashcard decks for all languages.",
        draft=False,
        prerelease=False,
    )

# Now delete all files in the release
for asset in release.get_assets():
    asset.delete_asset()
print("Deleted all files in the release")

print(f"Uploading {len(glob.glob('*.apkg'))} files to the release...")

# Now upload all files in the current directory
for file in glob.glob("*.apkg"):
    print(f"Uploading {file}")
    release_id = release.id
     #release.upload_asset(file)
    #file = "cat_eng.apkg"
    # Send a request because the upload_asset method is not working
    url = f"https://uploads.github.com/repos/Vuizur/tatoeba-to-anki/releases/{release_id}/assets?name={file}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # apkg files are zip files
        "Content-Type": "application/octet-stream",
        # the authorization token
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
    }
    request_num = 0
    while request_num < 5:
        request_num += 1
        try:
            with open(file, "rb") as f:
        
                response = requests.post(url, headers=headers, data=f, timeout=20) # Not sure about the optimal value, I only know that 0.1 is too small
                print(response)
        except requests.exceptions.Timeout:
            break
        except requests.exceptions.ConnectionError:
            print("Connection error, retrying...")
            continue
    

    print(f"Finished uploading {file}")
