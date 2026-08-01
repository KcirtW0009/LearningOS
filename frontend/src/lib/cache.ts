// IndexedDB cache module for LearningOS
// Caches graph data and learning progress for offline access and faster loads.

const DB_NAME = "learningos-cache";
const DB_VERSION = 1;

interface CacheEntry {
  key: string;
  value: any;
  timestamp: number;
  ttl: number; // time-to-live in ms, 0 = never expire
}

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains("cache")) {
        db.createObjectStore("cache", { keyPath: "key" });
      }
      if (!db.objectStoreNames.contains("progress")) {
        db.createObjectStore("progress", { keyPath: "id" });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

// ── Generic Cache ──────────────────────────────────────────────────────

export async function cacheGet(key: string): Promise<any | null> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("cache", "readonly");
    const store = tx.objectStore("cache");
    const request = store.get(key);
    request.onsuccess = () => {
      const entry = request.result as CacheEntry | undefined;
      if (!entry) {
        resolve(null);
        return;
      }
      if (entry.ttl > 0 && Date.now() - entry.timestamp > entry.ttl) {
        // Expired — delete and return null
        const delTx = db.transaction("cache", "readwrite");
        delTx.objectStore("cache").delete(key);
        resolve(null);
        return;
      }
      resolve(entry.value);
    };
    request.onerror = () => reject(request.error);
  });
}

export async function cacheSet(key: string, value: any, ttlMs: number = 0): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("cache", "readwrite");
    const store = tx.objectStore("cache");
    const entry: CacheEntry = {
      key,
      value,
      timestamp: Date.now(),
      ttl: ttlMs,
    };
    store.put(entry);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function cacheDelete(key: string): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("cache", "readwrite");
    tx.objectStore("cache").delete(key);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

// ── Progress Cache ─────────────────────────────────────────────────────

export interface ProgressCacheEntry {
  id: string;
  graphId: string;
  data: any;
  updatedAt: string;
}

export async function progressGet(graphId: string): Promise<ProgressCacheEntry | null> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("progress", "readonly");
    const store = tx.objectStore("progress");
    const request = store.get(`progress-${graphId}`);
    request.onsuccess = () => resolve(request.result || null);
    request.onerror = () => reject(request.error);
  });
}

export async function progressSet(graphId: string, data: any): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("progress", "readwrite");
    const store = tx.objectStore("progress");
    const entry: ProgressCacheEntry = {
      id: `progress-${graphId}`,
      graphId,
      data,
      updatedAt: new Date().toISOString(),
    };
    store.put(entry);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function progressDelete(graphId: string): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("progress", "readwrite");
    tx.objectStore("progress").delete(`progress-${graphId}`);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

// ── Graph Data Cache ───────────────────────────────────────────────────

const GRAPH_TTL = 30 * 60 * 1000; // 30 minutes

export async function cacheGraphData(graphId: string, nodes: any[], edges: any[]): Promise<void> {
  await cacheSet(`graph-nodes-${graphId}`, nodes, GRAPH_TTL);
  await cacheSet(`graph-edges-${graphId}`, edges, GRAPH_TTL);
}

export async function getCachedGraphNodes(graphId: string): Promise<any[] | null> {
  return cacheGet(`graph-nodes-${graphId}`);
}

export async function getCachedGraphEdges(graphId: string): Promise<any[] | null> {
  return cacheGet(`graph-edges-${graphId}`);
}

// ── Onboarding State ───────────────────────────────────────────────────
// Uses both IndexedDB and localStorage for robustness across sessions.
// localStorage is synchronous and survives abrupt app termination.

const ONBOARDING_KEY = "onboarding-completed";
const ONBOARDING_LS_KEY = "learningos-onboarding-seen";

export async function hasSeenOnboarding(): Promise<boolean> {
  // Fast synchronous check via localStorage first
  if (typeof localStorage !== "undefined" && localStorage.getItem(ONBOARDING_LS_KEY) === "1") {
    return true;
  }
  // Fallback to IndexedDB
  const val = await cacheGet(ONBOARDING_KEY);
  if (val === true) {
    // Sync to localStorage for future fast access
    try { localStorage.setItem(ONBOARDING_LS_KEY, "1"); } catch { /* ignore */ }
    return true;
  }
  return false;
}

export async function markOnboardingSeen(): Promise<void> {
  // Write to localStorage first (synchronous, reliable)
  try { localStorage.setItem(ONBOARDING_LS_KEY, "1"); } catch { /* ignore */ }
  // Also write to IndexedDB
  await cacheSet(ONBOARDING_KEY, true, 0);
}
