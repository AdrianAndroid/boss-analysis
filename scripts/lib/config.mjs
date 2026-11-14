import { readFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");

export const PATHS = {
  root: ROOT,
  config: join(ROOT, "config"),
  data: join(ROOT, "data"),
  raw: join(ROOT, "data", "raw"),
  reports: join(ROOT, "reports"),
  auth: join(ROOT, "auth"),
  progress: join(ROOT, "progress"),
};

export function loadTabsConfig() {
  return JSON.parse(readFileSync(join(PATHS.config, "tabs.json"), "utf-8"));
}

export function todayDir() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const dir = join(PATHS.raw, `${y}-${m}-${day}`);
  mkdirSync(dir, { recursive: true });
  return dir;
}
