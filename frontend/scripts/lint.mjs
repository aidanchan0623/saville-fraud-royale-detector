import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

const root = fileURLToPath(new URL("../src", import.meta.url));
const files = [];

function collect(dir) {
  for (const entry of readdirSync(dir)) {
    const path = join(dir, entry);
    if (statSync(path).isDirectory()) collect(path);
    else if (/\.(ts|tsx)$/.test(path)) files.push(path);
  }
}

collect(root);

for (const file of files) {
  const source = readFileSync(file, "utf8");
  assert(!source.includes("Supporting Evidence"), `${file} reintroduced the old Supporting Evidence section`);
  assert(!source.match(/\bbrainless\b|\bno-skill\b|\bno skill\b/i), `${file} contains prohibited score wording`);
}

const app = readFileSync(join(root, "App.tsx"), "utf8");
assert(app.split("\n").length <= 200, "App.tsx should stay below 200 lines");
console.log(`lint checks passed for ${files.length} source files`);
