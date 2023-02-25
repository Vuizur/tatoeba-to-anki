# This uploads all apkg files in the current directory to a release on GitHub.

import github
import dotenv
import os
import glob

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
        "latest",
        draft=False,
        prerelease=False,
    )

# Now delete all files in the release
for asset in release.get_assets():
    asset.delete_asset()
print("Deleted all files in the release")

# Now upload all files in the current directory
for file in glob.glob("*.apkg"):
    print(f"Uploading {file}")
    release.upload_asset(file)
