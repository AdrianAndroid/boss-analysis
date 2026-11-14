import { createHash } from "node:crypto";

// 岗位编号模式：MJ011054 / XJ003154 等字母+数字编号
const CODE_RE = /[A-Za-z]{2,}\d{3,}/;

function normalize(s) {
  return (s || "")
    .toLowerCase()
    .replace(/\s+/g, "")
    .replace(/[（）()]/g, "")
    .trim();
}

/**
 * 生成岗位身份键 job_key（SPEC 3.3）
 * 1. 优先标题内岗位编号；
 * 2. 缺失时用 公司+标题+地点+经验 归一化后 md5 取前 12 位。
 * @param {{title:string, company:string, location:string, exp:string}} job
 * @returns {string}
 */
export function jobKey(job) {
  const code = (job.title || "").match(CODE_RE);
  if (code) return `code:${code[0].toUpperCase()}`;
  const base = [job.company, job.title, job.location, job.exp]
    .map(normalize)
    .join("|");
  return `hash:${createHash("md5").update(base).digest("hex").slice(0, 12)}`;
}
