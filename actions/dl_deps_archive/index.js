const tc = require("@actions/tool-cache");
const core = require("@actions/core");
const path = require("path");
const os = require("os");

function getInput(name, dflt) {
  const val = process.env[`INPUT_${name.replace(/ /g, "_").toUpperCase()}`];
  if (!val) {
    return dflt;
  }
  return val;
}

function addLocalPath(inputPath) {
  process.env["PATH"] = `${inputPath}${path.delimiter}${process.env["PATH"]}`;
}

async function run() {
  try {
    const base_url = core.getInput("base_url");
    const target = core.getInput("target_platform");
    const project = getInput(
      "project",
      process.env["GITHUB_REPOSITORY"].split("/")[1],
    );
    const branch = getInput(
      "branch",
      process.env["GITHUB_HEAD_REF"] || process.env["GITHUB_REF_NAME"],
    );
    const extract_dir = getInput(
      "extract_dir",
      process.env["HOME"] || process.env["GITHUB_WORKSPACE"],
    );

    let archivePath;
    try {
      const archive_url = `${base_url}/dev_preview/${branch}/deps_${target}_${project}.tar.gz`;
      process.stdout.write("Downloading " + archive_url + "\n");
      archivePath = await tc.downloadTool(archive_url);
    } catch (error) {
      const archive_url = `${base_url}/deps_${target}_${project}.tar.gz`;
      process.stdout.write("Downloading " + archive_url + "\n");
      archivePath = await tc.downloadTool(archive_url);
    }

    process.stdout.write("Extracting " + archivePath + " to " + extract_dir);
    const archive_dir = await tc.extractTar(archivePath, extract_dir);
    process.stdout.write("Extracted to " + archive_dir);
  } catch (error) {
    core.setFailed(error.message);
  }
}

if (os.platform() === "win32") {
  addLocalPath("C:\\Program Files\\Git\\usr\\bin");
}
core.setCommandEcho(true);

run();
