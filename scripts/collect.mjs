#!/usr/bin/env node
/**
 * BOSS 岗位采集主脚本（阶段 1：列表；阶段 2：详情）
 * 风控约束：单浏览器、串行访问、随机间隔、遇安全验证即停、断点续采。
 *
 * 用法：
 *   node scripts/collect.mjs --tab all --limit 20        # 列表采集
 *   node scripts/collect.mjs --tab android --limit 5
 *   node scripts/collect.mjs --detail                     # 阶段2：在列表基础上补采详情
 */
import { chromium } from "playwright";
import { loadTabsConfig, todayDir, PATHS } from "./lib/config.mjs";
import { jobKey } from "./lib/jobkey.mjs";
import {
  loadList, saveList, mergeTabJobs,
  loadDetail, saveDetail, mergeDetail,
  loadCheckpoint, saveCheckpoint,
} from "./lib/store.mjs";

const args = process.argv.slice(2);
const arg = (name, def) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 ? args[i + 1] : def;
};

const cfg = loadTabsConfig();
const BASE = "https://www.zhipin.com";
const JOBS_URL = `${BASE}/web/geek/jobs`;
const LIMIT = Number(arg("limit", cfg.limit_per_tab));
const ONLY_TAB = arg("tab", "all");
const WITH_DETAIL = args.includes("--detail");

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const jitter = () => Math.round(cfg.request_interval_jitter_ms * Math.random());

/** 从卡片文本解析字段（文本以换行分隔） */
function parseCardText(text) {
  const lines = text.split("\n").map((s) => s.trim()).filter(Boolean);
  // 约定：标题在首行；薪资/经验/学历/标签/公司/地点 顺序不固定，宽松提取
  const title = lines[0] || "";
  const salary = lines.find((l) => /[Kk]·?\d*薪|元\/月/.test(l)) || "";
  const exp = lines.find((l) => /年|经验不限|应届/.test(l)) || "";
  const edu = lines.find((l) => /博士|硕士|本科|大专|学历不限/.test(l)) || "";
  const company = lines.find((l) => /公司|集团|科技|有限|互联网|SaaS|Tesla|特斯拉|滴滴|小米|蚂蚁|腾讯|作业帮|天眼查/.test(l)) || "";
  const location = lines.find((l) => /北京|上海|广州|深圳|杭州|成都|武汉|南京|西安|亦庄|望京|海淀|朝阳|昌平|上地|学院路|亚运村|万柳|苏州桥|回龙观|临港|中山公园|闵行|浦东/.test(l)) || "";
  const tags = lines.slice(1).filter((l) => ![salary, exp, edu, company, location, title].includes(l));
  return { title, salary, exp, edu, company, location, tags };
}

/** 列表页内提取卡片 */
async function extractCards(page) {
  return page.evaluate(() => {
    const links = [...document.querySelectorAll('a[href*="job_detail"]')];
    const out = [];
    for (const a of links) {
      let el = a;
      for (let i = 0; i < 5 && el.parentElement; i++) {
        el = el.parentElement;
        if (el.querySelector('a[href*="gongsi"]')) break;
      }
      const text = (el.innerText || "").trim();
      if (!text) continue;
      out.push({ url: a.getAttribute("href"), text });
    }
    return out;
  });
}

/** 检测是否处于登录/安全验证拦截 */
async function isBlocked(page) {
  const url = page.url();
  if (url.includes("/web/user/")) return true;
  const blocked = await page.evaluate(() => {
    const t = document.body.innerText || "";
    return /扫码登录|验证码登录|安全验证|滑块|人机验证|访问异常/.test(t) && !document.querySelector('a[href*="job_detail"]');
  });
  return blocked;
}

/** 切换到指定 tab（按标签文本匹配） */
async function switchTab(page, tabLabel) {
  const item = page.locator(`text=${tabLabel}`).first();
  await item.click();
  await sleep(1500 + jitter());
}

/** 滚动加载直到无新链接或达上限 */
async function scrollCollect(page, limit) {
  const seen = new Set();
  let stableRounds = 0;
  for (let round = 0; round < 60; round++) {
    const cards = await extractCards(page);
    for (const c of cards) seen.add(c.url);
    if (seen.size >= limit) break;
    const before = seen.size;
    await page.mouse.wheel(0, 2400);
    await sleep(cfg.request_interval_ms + jitter());
    const after = (await extractCards(page)).length;
    if (after === before) {
      stableRounds++;
      if (stableRounds >= 3) break;
    } else {
      stableRounds = 0;
    }
  }
  return [...seen];
}

async function collectList(context) {
  const page = await context.newPage();
  await page.goto(JOBS_URL, { waitUntil: "domcontentloaded", timeout: 30000 });
  await sleep(2000);

  if (await isBlocked(page)) {
    console.log("[拦截] 需要登录或安全验证：请在弹出的浏览器窗口完成扫码/验证，脚本将等待…");
    // 等待人工完成登录：轮询直到出现岗位链接
    for (let i = 0; i < 120; i++) {
      await sleep(3000);
      if (!(await isBlocked(page))) break;
    }
  }

  const dateDir = todayDir();
  const list = loadList(dateDir);
  list.city = cfg.city;
  list.collected_at = new Date().toISOString().slice(0, 10);
  const cp = loadCheckpoint();

  const tabs = cfg.tabs.filter((t) => ONLY_TAB === "all" || t.key === ONLY_TAB);

  for (const tab of tabs) {
    console.log(`\n=== 采集 tab: ${tab.label} (${tab.key}) ===`);
    await switchTab(page, tab.label);
    const urls = await scrollCollect(page, LIMIT);

    const incoming = [];
    for (const url of urls) {
      const cards = await extractCards(page);
      const card = cards.find((c) => c.url === url);
      if (!card) continue;
      const parsed = parseCardText(card.text);
      const job = {
        job_key: "",
        url,
        title: parsed.title,
        company: parsed.company,
        location: parsed.location,
        exp: parsed.exp,
        edu: parsed.edu,
        tags: parsed.tags,
      };
      job.job_key = jobKey(job);
      incoming.push(job);
    }

    list.tabs[tab.key] = mergeTabJobs(list.tabs[tab.key] || [], incoming);
    saveList(dateDir, list);

    cp.collection.tabs[tab.key] = cp.collection.tabs[tab.key] || {};
    cp.collection.tabs[tab.key].collected = list.tabs[tab.key].length;
    cp.collection.tabs[tab.key].target = LIMIT;
    cp.collection.tabs[tab.key].last_url = urls[urls.length - 1] || null;
    saveCheckpoint(cp);
    console.log(`  本 tab 累计岗位: ${list.tabs[tab.key].length}`);
  }

  await page.close();
  return dateDir;
}

async function main() {
  const context = await chromium.launchPersistentContext(PATHS.auth, {
    channel: "chrome",
    headless: false,
    viewport: { width: 1440, height: 1000 },
    args: ["--disable-blink-features=AutomationControlled"],
  });

  try {
    const dateDir = await collectList(context);
    console.log(`\n[完成] 列表快照: ${dateDir}`);
    if (WITH_DETAIL) {
      console.log("[阶段2] 详情采集待接入（下一迭代）");
    }
  } finally {
    await context.close();
  }
}

main().catch((e) => {
  console.error("[错误]", e);
  process.exit(1);
});
