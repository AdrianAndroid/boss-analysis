import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { PATHS } from "./config.mjs";

function readJson(path, fallback) {
  if (!existsSync(path)) return fallback;
  return JSON.parse(readFileSync(path, "utf-8"));
}

function writeJson(path, data) {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, JSON.stringify(data, null, 2), "utf-8");
}

// ---------- 列表快照 ----------
export function loadList(dateDir) {
  return readJson(join(dateDir, "jobs_list.json"), { city: "", collected_at: "", tabs: {} });
}

export function saveList(dateDir, list) {
  writeJson(join(dateDir, "jobs_list.json"), list);
}

/** 按 job_key 合并单 tab 岗位，保留已有记录 */
export function mergeTabJobs(tabJobs, incoming) {
  const byKey = new Map(tabJobs.map((j) => [j.job_key, j]));
  for (const j of incoming) {
    if (!byKey.has(j.job_key)) byKey.set(j.job_key, j);
  }
  return [...byKey.values()];
}

// ---------- 详情快照 ----------
export function loadDetail(dateDir) {
  return readJson(join(dateDir, "jobs_detail.json"), []);
}

export function saveDetail(dateDir, detail) {
  writeJson(join(dateDir, "jobs_detail.json"), detail);
}

export function mergeDetail(detail, incoming) {
  const byKey = new Map(detail.map((j) => [j.job_key, j]));
  for (const j of incoming) {
    if (!byKey.has(j.job_key)) byKey.set(j.job_key, j);
  }
  return [...byKey.values()];
}

// ---------- checkpoint ----------
export function loadCheckpoint() {
  const p = join(PATHS.progress, "checkpoint.json");
  return readJson(p, { phases: {}, collection: { tabs: {}, detail: {} }, validation: {} });
}

export function saveCheckpoint(cp) {
  writeJson(join(PATHS.progress, "checkpoint.json"), cp);
}
