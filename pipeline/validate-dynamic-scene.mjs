// pipeline/validate-dynamic-scene.mjs
// Validate a dynamic scene-plan JSON file without generating voice, images or video.
import fs from "node:fs/promises";
import path from "node:path";
import { validateDynamicScenePlan } from "./dynamic-scene-gate.mjs";

const inputPath = process.argv[2] ? path.resolve(process.argv[2]) : null;
if (!inputPath) {
  console.error("Usage: node pipeline/validate-dynamic-scene.mjs <dynamic-scene-plan.json>");
  process.exit(2);
}

try {
  const project = JSON.parse(await fs.readFile(inputPath, "utf8"));
  const result = validateDynamicScenePlan(project);
  console.log(JSON.stringify(result, null, 2));
  if (!result.passed) process.exitCode = 1;
} catch (error) {
  console.error(`Could not validate dynamic scene plan: ${error.message}`);
  process.exitCode = 2;
}
