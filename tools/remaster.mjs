import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const mode = process.argv[2];
const episode = process.argv.slice(3).find((value) => /^EP\d{3}$/i.test(value));

if (mode === "episode" && !episode) {
  console.error("Usage: npm run remaster:episode -- EP001");
  process.exit(2);
}

const args = [
  path.join(root, "tools", "remaster_pipeline.py"),
  mode === "all" ? "--all" : "--episode",
];
if (episode) args.push(episode.toUpperCase());

const candidates = process.env.PYTHON
  ? [[process.env.PYTHON, []]]
  : [["python", []], ["py", ["-3"]]];

for (const [command, prefix] of candidates) {
  const result = spawnSync(command, [...prefix, ...args], {
    cwd: root,
    stdio: "inherit",
    windowsHide: true
  });
  if (!result.error) process.exit(result.status ?? 1);
}

console.error("Python 3 est introuvable. Définissez la variable PYTHON.");
process.exit(1);
