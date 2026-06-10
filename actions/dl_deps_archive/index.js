const tc = require("@actions/tool-cache");
const core = require("@actions/core");
const path = require("path");
const os = require("os");
const fs = require("fs");

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

function exists(inputPath) {
  return inputPath && fs.existsSync(inputPath);
}

function unique(items) {
  return [...new Set(items.filter(exists))];
}

function listBuildDirs(root) {
  if (!exists(root)) {
    return [];
  }
  return fs
    .readdirSync(root, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && entry.name.startsWith("BUILD_"))
    .map((entry) => path.join(root, entry.name))
    .filter((buildDir) => exists(path.join(buildDir, "INSTALL")))
    .sort((a, b) => {
      if (path.basename(a) === "BUILD_neutral") return 1;
      if (path.basename(b) === "BUILD_neutral") return -1;
      return a.localeCompare(b);
    });
}

function findLibDirs(installDir) {
  const dirs = [path.join(installDir, "lib"), path.join(installDir, "lib64")];
  const libDir = path.join(installDir, "lib");
  if (exists(libDir)) {
    for (const entry of fs.readdirSync(libDir, { withFileTypes: true })) {
      if (entry.isDirectory() && entry.name !== "pkgconfig") {
        dirs.push(path.join(libDir, entry.name));
      }
    }
  }
  return unique(dirs);
}

function findPkgConfigDirs(installDir) {
  return unique(findLibDirs(installDir).map((dir) => path.join(dir, "pkgconfig")));
}

function findFirstFile(buildDirs, fileName) {
  for (const buildDir of buildDirs) {
    const filePath = path.join(buildDir, fileName);
    if (exists(filePath)) {
      return filePath;
    }
  }
  return "";
}

function setArchiveOutputs(extractDir, archiveDir, ignoredBuildDirs = []) {
  const roots = unique([archiveDir, extractDir]);
  const ignored = new Set(ignoredBuildDirs);
  const buildDirs = unique(roots.flatMap(listBuildDirs)).filter(
    (buildDir) => !ignored.has(buildDir),
  );
  const mesonCrossFile = findFirstFile(buildDirs, "meson_cross_file.txt");
  const cmakeToolchainFile = findFirstFile(buildDirs, "cmake_cross_file.txt");
  const buildDir = mesonCrossFile
    ? path.dirname(mesonCrossFile)
    : cmakeToolchainFile
      ? path.dirname(cmakeToolchainFile)
      : buildDirs[0] || "";
  const installDir = buildDir ? path.join(buildDir, "INSTALL") : "";
  const installDirs = buildDirs.map((dir) => path.join(dir, "INSTALL"));
  const includeDirs = unique(installDirs.map((dir) => path.join(dir, "include")));

  core.setOutput("extract-dir", archiveDir || extractDir);
  core.setOutput("build-dir", buildDir);
  core.setOutput("install-dir", exists(installDir) ? installDir : "");
  core.setOutput("pkg-config-path", unique(installDirs.flatMap(findPkgConfigDirs)).join(path.delimiter));
  core.setOutput("ld-library-path", unique(installDirs.flatMap(findLibDirs)).join(path.delimiter));
  core.setOutput("cppflags", includeDirs.map((dir) => `-I${dir}`).join(" "));
  core.setOutput("meson-cross-file", mesonCrossFile);
  core.setOutput("cmake-toolchain-file", cmakeToolchainFile);
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
    const preExistingBuildDirs = listBuildDirs(extract_dir);

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

    process.stdout.write("Extracting " + archivePath + " to " + extract_dir + "\n");
    const archive_dir = await tc.extractTar(archivePath, extract_dir);
    process.stdout.write("Extracted to " + archive_dir + "\n");
    setArchiveOutputs(extract_dir, archive_dir, preExistingBuildDirs);
  } catch (error) {
    core.setFailed(error.message);
  }
}

if (os.platform() === "win32") {
  addLocalPath("C:\\Program Files\\Git\\usr\\bin");
}
core.setCommandEcho(true);

run();
