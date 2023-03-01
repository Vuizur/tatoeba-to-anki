// This uploads all apkg files in the current directory to a release on GitHub.
// Note that this is currently broken

import { Octokit } from "@octokit/rest";
import * as fs from "fs";

async function uploadReleases() {

    // Load the GitHub token from the PASSWORD file in the current directory
    //const token = await fs.readFile("../.env", "utf8");
    const token_str = fs.readFileSync("../.env", "utf8");

    const token = token_str.split("=")[1];

    // Create an Octokit client
    const octokit = new Octokit({
        auth: token,
    });

    // Change directory to the directory one level above the current directory
    process.chdir("..");

    //Print the current directory
    console.log(`Current directory: ${process.cwd()}`);
    // Get the list of files in the current directory
    const files = fs.readdirSync(".");
    // Filter the list to only include .apkg files
    let apkgFiles = files.filter((file) => file.endsWith(".apkg"));

    // Get the list of releases
    const releases = await octokit.repos.listReleases({
        owner: "Vuizur",
        repo: "tatoeba-to-anki",
    });

    // Find the release with the name "latest"
    let latestRelease = releases.data.find((release) => release.name === "latest");

    // If there is no release with the name "latest", create one
    if (latestRelease === undefined) {
        console.log("Creating a new release");
        await octokit.repos.createRelease({
            owner: "Vuizur",
            repo: "tatoeba-to-anki",
            tag_name: "latest",
            name: "latest",
            body: "The latest flashcard decks for all languages.",
            draft: false,
            prerelease: false,
        });
    }

    latestRelease = releases.data.find((release) => release.name === "latest");

    // Get the list of assets in the release
    const assets = await octokit.repos.listReleaseAssets({
        owner: "Vuizur",
        repo: "tatoeba-to-anki",
        release_id: latestRelease!.id,
    });

    // Delete all assets in the release
    for (const asset of assets.data) {
        await octokit.repos.deleteReleaseAsset({
            owner: "Vuizur",
            repo: "tatoeba-to-anki",
            asset_id: asset.id,
        });
    }

    console.log("Deleted all files in the release");

    const num_files = apkgFiles.length;
    console.log(`Uploading ${num_files} files`);

    //apkgFiles = ["cat_eng.apkg"]

    // Upload all apkg files to the release
    for (const file of apkgFiles) {
        const data = fs.readFileSync(file);
        const stats = fs.statSync(file);
        console.log(`Uploading ${file} (${stats.size} bytes)`);
        // Upload the file
        await octokit.repos.uploadReleaseAsset({
            "owner": "Vuizur",
            "repo": "tatoeba-to-anki",
            "release_id": latestRelease!.id,
            "name": file,
            "data": data as unknown as string,
            "headers": {
                "content-type": "application/zip",
                "content-length": stats.size.toString(),
            }
        });
        console.log(`Uploaded ${file}`);
    }

}
uploadReleases();