"use client";

// LearningOS i18n module — lightweight, no external dependencies
// Supports: zh-CN (default), en-US
// Language detection order: localStorage "los-lang" > navigator.language > zh-CN

export type LangCode = "zh-CN" | "en-US";

export type DictKey = string;

// ── Dictionaries ───────────────────────────────────────────────────────

const ZH_CN: Record<string, string> = {
  // Onboarding
  "onboarding.step1.title": "欢迎使用 LearningOS",
  "onboarding.step1.desc":
    "一款基于知识图谱的渐进式学习引擎。适用场景：自主学习路径规划、技能体系可视化追踪、知识掌握度自评。面向自学者、终身学习者、希望体系化记录学习成果的人。",
  "onboarding.step1.icon": "🎓",

  "onboarding.step2.title": "选择你的学习路径",
  "onboarding.step2.desc":
    "在启动页选择一张知识图谱。每张图谱都是一套精心设计的技能树。从「可学习」的绿色节点开始，逐步向上攀登。",
  "onboarding.step2.icon": "🗺️",

  "onboarding.step3.title": "学习 & 追踪进度",
  "onboarding.step3.desc":
    "点击节点查看详情、学习资源和前置依赖。完成节点时给出自评分数。所有进度保存在本机——无需云端，完全离线可用。",
  "onboarding.step3.icon": "📊",

  "onboarding.step4.title": "评分系统",
  "onboarding.step4.desc":
    "学习后给自己打分：了解一下(1)、认真学了(5)、动手实践(10)、举一反三(20)、项目实战(50)、传授他人(80)。不同分数对应不同熟练度等级。",
  "onboarding.step4.icon": "⭐",

  "onboarding.step5.title": "进度追踪",
  "onboarding.step5.desc":
    "左侧面板实时显示学习进度。可查看已完成节点数、当前等级和累计XP。点击操作历史可随时撤回已完成的学习记录。",
  "onboarding.step5.icon": "📊",

  "onboarding.step6.title": "创建自定义图谱",
  "onboarding.step6.desc":
    "点击右上角「+ 创建图谱」按钮，可以生成新的知识图谱。通过外部AI接口提交YAML格式的图谱定义，系统会自动验证并保存到图谱库中。",
  "onboarding.step6.icon": "🔨",

  "onboarding.step7.title": "技能树视图导航",
  "onboarding.step7.desc":
    "在技能树视图中，使用鼠标拖拽平移画布、Shift+滚轮水平滚动。双击任意节点可直接设为学习目标，开启任务模式。悬浮节点可查看熟练度等级和详细信息。",
  "onboarding.step7.icon": "🌳",

  "onboarding.step8.title": "撤回与操作历史",
  "onboarding.step8.desc":
    "左侧面板的「操作历史」支持无限步撤回。点击节点标题查看详情，点击 ↩ 撤回单步或批量操作。级联撤回功能会同时重置受影响的后续节点，确保图谱一致性。",
  "onboarding.step8.icon": "↩️",

  "onboarding.skip": "跳过教程",
  "onboarding.back": "上一步",
  "onboarding.next": "下一步",
  "onboarding.start": "立即开始",

  // Reset state
  "state.reset.confirm.title": "确认重置所有本地数据？",
  "state.reset.confirm.desc":
    "此操作将清除本设备上保存的所有学习进度、新手教程状态及本地缓存。此操作不可撤销。",
  "state.reset.confirm.btn": "确认重置",
  "state.reset.cancel": "取消",
  "state.reset.success": "已重置所有本地数据，页面即将刷新...",
  "state.reset.label": "重置本地数据",

  // Common
  "common.loading": "加载中...",
  "common.success": "操作成功",
  "common.error": "操作失败",
  "common.cancel": "取消",
  "common.confirm": "确认",
};

const EN_US: Record<string, string> = {
  "onboarding.step1.title": "Welcome to LearningOS",
  "onboarding.step1.desc":
    "A graph-driven learning runtime. Use cases: self-directed learning path planning, skill system visualization & tracking, knowledge mastery self-assessment. For self-learners, lifelong learners, and anyone who wants to systematically record learning achievements.",
  "onboarding.step1.icon": "🎓",

  "onboarding.step2.title": "Choose Your Path",
  "onboarding.step2.desc":
    "Select a learning graph from the landing screen. Each graph is a curriculum designed as a skill tree. Start with available nodes (green) and work your way up.",
  "onboarding.step2.icon": "🗺️",

  "onboarding.step3.title": "Learn & Track Progress",
  "onboarding.step3.desc":
    "Click a node to see its details, resources, and prerequisites. Complete nodes by scoring them. Your progress is saved locally — no cloud required.",
  "onboarding.step3.icon": "📊",

  "onboarding.step4.title": "Scoring System",
  "onboarding.step4.desc":
    "Rate your learning progress: Glance (1), Studied (5), Practiced (10), Applied (20), Project (50), Teach (80). Different scores unlock different proficiency levels.",
  "onboarding.step4.icon": "⭐",

  "onboarding.step5.title": "Progress Tracking",
  "onboarding.step5.desc":
    "The left panel shows real-time progress. View completed nodes, current level, and total XP. Click Operation History to undo completed learning records at any time.",
  "onboarding.step5.icon": "📊",

  "onboarding.step6.title": "Create Custom Graphs",
  "onboarding.step6.desc":
    "Click the '+ Create Graph' button in the top right to generate new knowledge graphs. Submit YAML-format graph definitions via external AI APIs and the system will validate and save them to your graph library.",
  "onboarding.step6.icon": "🔨",

  "onboarding.step7.title": "Skill Tree Navigation",
  "onboarding.step7.desc":
    "In the Skill Tree view, drag to pan the canvas and use Shift+Wheel for horizontal scrolling. Double-click any node to set it as a learning target and start Task Mode. Hover over nodes to see proficiency levels and details.",
  "onboarding.step7.icon": "🌳",

  "onboarding.step8.title": "Undo & Operation History",
  "onboarding.step8.desc":
    "The 'Operation History' panel on the left supports unlimited undo. Click node titles to view details, click ↩ to undo single or batch operations. Cascade undo will also reset affected downstream nodes to maintain graph consistency.",
  "onboarding.step8.icon": "↩️",

  "onboarding.skip": "Skip tutorial",
  "onboarding.back": "Back",
  "onboarding.next": "Next",
  "onboarding.start": "Get Started",

  "state.reset.confirm.title": "Reset all local data?",
  "state.reset.confirm.desc":
    "This will erase all learning progress, onboarding state, and local caches on this device. This action cannot be undone.",
  "state.reset.confirm.btn": "Reset Everything",
  "state.reset.cancel": "Cancel",
  "state.reset.success": "All local data reset. Page will reload...",
  "state.reset.label": "Reset Local Data",

  "common.loading": "Loading...",
  "common.success": "Success",
  "common.error": "Error",
  "common.cancel": "Cancel",
  "common.confirm": "Confirm",
};

const DICTS: Record<LangCode, Record<string, string>> = {
  "zh-CN": ZH_CN,
  "en-US": EN_US,
};

// ── Language detection ─────────────────────────────────────────────────

const STORAGE_KEY = "los-lang";

function detectLanguage(): LangCode {
  if (typeof window === "undefined") return "zh-CN";
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && (stored === "zh-CN" || stored === "en-US")) {
      return stored;
    }
  } catch { /* ignore */ }
  try {
    const nav = (navigator.language || "zh-CN").toLowerCase();
    if (nav.startsWith("zh")) return "zh-CN";
    return "en-US";
  } catch {
    return "zh-CN";
  }
}

let currentLang: LangCode = detectLanguage();
const listeners: Set<(lang: LangCode) => void> = new Set();

export function getLang(): LangCode {
  return currentLang;
}

export function setLang(lang: LangCode): void {
  if (lang !== "zh-CN" && lang !== "en-US") return;
  currentLang = lang;
  try {
    localStorage.setItem(STORAGE_KEY, lang);
  } catch { /* ignore */ }
  listeners.forEach((l) => l(lang));
}

export function onLangChange(fn: (lang: LangCode) => void): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

// ── Translation helpers ────────────────────────────────────────────────

export function t(key: DictKey, fallback?: string): string {
  const dict = DICTS[currentLang] || ZH_CN;
  const v = dict[key];
  if (typeof v === "string") return v;
  if (typeof fallback === "string") return fallback;
  // Fallback to English dict, then to raw key
  const en = DICTS["en-US"]?.[key];
  if (typeof en === "string") return en;
  return key;
}

// ── Clear ALL local data (progress + onboarding + graph caches) ────────

export async function clearAllLocalData(): Promise<void> {
  try {
    const w = window as unknown as { electronAPI?: { clearAllData?: () => Promise<{ success: boolean; message: string }> } };
    if (typeof w !== "undefined" && w.electronAPI && w.electronAPI.clearAllData) {
      await w.electronAPI.clearAllData();
    }
  } catch { /* ignore - not running in Electron */ }
  
  // 2. Clear IndexedDB entries used by cache.ts:
  //    - onboarding-completed
  //    - graph-nodes-*, graph-edges-*
  //    - progress-*
  if (typeof indexedDB !== "undefined") {
    try {
      await new Promise<void>((resolve, reject) => {
        const req = indexedDB.open("learningos-cache", 1);
        req.onsuccess = () => {
          const db = req.result;
          let pending = 2;
          const done = () => { if (--pending === 0) resolve(); };
          try {
            const c1 = db.transaction(["cache"], "readwrite").objectStore("cache").clear();
            c1.onsuccess = done;
            c1.onerror = () => done();
          } catch { done(); }
          try {
            const c2 = db.transaction(["progress"], "readwrite").objectStore("progress").clear();
            c2.onsuccess = done;
            c2.onerror = () => done();
          } catch { done(); }
          setTimeout(resolve, 1000);
        };
        req.onerror = () => reject(req.error);
        setTimeout(resolve, 2000);
      });
    } catch { /* ignore */ }
  }
  
  // 3. Clear localStorage entries
  try {
    localStorage.removeItem("los-onboarding-completed");
  } catch { /* ignore */ }
}
