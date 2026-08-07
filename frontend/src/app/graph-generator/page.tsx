"use client";

import { useState, useCallback, useRef, ChangeEvent } from "react";

const getApiUrl = () => {
  if (typeof window !== 'undefined') {
    return (window as any).__API_URL__ || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
};

// ── Types ──────────────────────────────────────────────────────────────

interface PreviewData {
  valid: boolean;
  package_id: string;
  name: string;
  node_count: number;
  edge_count: number;
  nodes: { id: string; title: string; type: string; difficulty: string }[];
  edges: { from: string; to: string; relation: string }[];
  errors: string[];
}

// ── Helpers ────────────────────────────────────────────────────────────

async function api(path: string, options?: RequestInit) {
  let res: Response;
  try {
    res = await fetch(`${getApiUrl()}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch (fetchErr: any) {
    // Network-level error (CORS, connection refused, etc.)
    if (fetchErr?.message?.includes("Failed to fetch")) {
      throw new Error(
        "无法连接到后端服务。请确保 LearningOS 后端已启动（http://localhost:8000），然后重试。"
      );
    }
    throw new Error(`网络请求失败: ${fetchErr?.message || "未知错误"}`);
  }

  if (!res.ok) {
    let body: any;
    try {
      body = await res.json();
    } catch {
      throw new Error(`HTTP ${res.status} ${res.statusText}`);
    }
    const err = body?.error || body;
    const message = err?.message || body?.detail || `HTTP ${res.status}`;
    const suggestion = err?.suggestion ? ` (${err.suggestion})` : "";
    throw new Error(`${message}${suggestion}`);
  }

  return res.json();
}

// ── Template Content ───────────────────────────────────────────────────

const GRAPH_TEMPLATE = `# LearningOS Graph Template
# Copy this template and provide it to your external AI assistant.
# The AI should fill in the nodes and edges sections.

# === manifest.yaml ===
package_id: my-learning-graph
name: My Learning Graph
version: 1.0.0
author: your-name

# === graph.yaml ===
nodes:
  - id: intro-basics
    title: Introduction to Basics
    description: Foundational concepts and terminology.
    type: concept
    difficulty: beginner
    resources:
      - type: url
        uri: https://example.com/intro
        label: Official Guide

  - id: hands-on-practice
    title: Hands-on Practice
    description: Apply what you learned through guided exercises.
    type: skill
    difficulty: beginner

  - id: advanced-topics
    title: Advanced Topics
    description: Deep dive into complex subjects building on foundations.
    type: concept
    difficulty: intermediate

edges:
  - from: intro-basics
    to: hands-on-practice
    relation: prerequisite

  - from: hands-on-practice
    to: advanced-topics
    relation: progression

# === Node Fields ===
# id:          Unique ID, lowercase, hyphen-separated (e.g. "python-basics")
# title:       Human-readable name
# description: What this learning unit covers
# type:        concept | skill | project | milestone
# difficulty:  beginner | intermediate | advanced
# resources:   (optional) list of {type: url|file|markdown, uri: ..., label: ...}

# === Edge Fields ===
# from:        Source node ID
# to:          Target node ID
# relation:    prerequisite | dependency | progression (blocking)
#              association | alternative (non-blocking)
`;

const AI_PROMPT_TEMPLATE = `I need you to generate a learning graph in YAML format for the LearningOS platform. 

The graph should follow this exact format:

\`\`\`yaml
# Graph YAML - combine manifest + graph into one template

package_id: <unique-id>
name: <Human Readable Name>
version: 1.0.0
author: <author-name>

nodes:
  - id: <node-id>
    title: <Node Title>
    description: <Description of what this learning unit covers>
    type: concept          # concept | skill | project | milestone
    difficulty: beginner   # beginner | intermediate | advanced

  - id: <next-id>
    title: <Next Title>
    description: <Description>
    type: skill
    difficulty: beginner

edges:
  - from: <node-id>
    to: <next-id>
    relation: prerequisite  # prerequisite | dependency | progression | association | alternative
\`\`\`

Rules:
1. Node IDs must be unique, lowercase, hyphen-separated
2. Every edge must reference existing node IDs
3. Use 'prerequisite', 'dependency', or 'progression' for blocking edges (must complete source before target)
4. Use 'association' or 'alternative' for non-blocking edges (related but not required)
5. Fields type and difficulty are optional but recommended

My topic is: `;

// ── Component ──────────────────────────────────────────────────────────

export default function GraphGeneratorPage() {
  const [activeTab, setActiveTab] = useState<"template" | "generator" | "preview">("template");
  const [yamlInput, setYamlInput] = useState("");
  const [copiedPrompt, setCopiedPrompt] = useState(false);
  const [copiedTemplate, setCopiedTemplate] = useState(false);
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [saving, setSaving] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [importedFileName, setImportedFileName] = useState<string>("");

  const handleFileImport = useCallback(async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!/\.(txt|yaml|yml)$/i.test(file.name)) {
      setError(`不支持的文件格式: ${file.name}。请上传 .txt, .yaml 或 .yml 文件。`);
      return;
    }

    try {
      const text = await file.text();
      if (!text.trim()) {
        setError(`文件 ${file.name} 为空，请检查内容。`);
        return;
      }
      setYamlInput(text);
      setImportedFileName(file.name);
      setError("");
      setPreview(null);
    } catch (e: any) {
      setError(`读取文件失败: ${e.message}`);
    }

    // Reset the input so the same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, []);

  const handlePreview = useCallback(async () => {
    setLoading(true);
    setError("");
    setPreview(null);
    try {
      const data = await api("/graph/preview", {
        method: "POST",
        body: JSON.stringify({ yaml: yamlInput }),
      });
      setPreview(data);
      setActiveTab("preview");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [yamlInput]);

  const handleSave = useCallback(async () => {
    if (!preview?.valid) return;
    setSaving(true);
    setError("");
    setSuccessMsg("");
    try {
      const data = await api("/graph/save", {
        method: "POST",
        body: JSON.stringify({
          yaml: yamlInput,
          package_id: preview.package_id,
        }),
      });
      setSuccessMsg(`Graph "${data.name}" saved to graphs/${data.package_id}/`);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }, [yamlInput, preview]);

  const handleCopyPrompt = () => {
    navigator.clipboard.writeText(AI_PROMPT_TEMPLATE);
    setCopiedPrompt(true);
    setTimeout(() => setCopiedPrompt(false), 2000);
  };

  const handleCopyTemplate = () => {
    navigator.clipboard.writeText(GRAPH_TEMPLATE);
    setCopiedTemplate(true);
    setTimeout(() => setCopiedTemplate(false), 2000);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <a href="/" className="text-slate-400 hover:text-primary-600 transition-colors" title="Back to LearningOS">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M15 18l-6-6 6-6" />
              </svg>
            </a>
            <h1 className="text-lg font-semibold text-slate-800">图谱生成器</h1>
            <span className="text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full font-medium">外部 AI 接口</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="7" cy="7" r="6"/><path d="M7 4v4M7 10h.005"/></svg>
            <span>独立交互界面 &mdash; 不占用主面板</span>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        {/* Tabs */}
        <div className="flex gap-1 bg-slate-100 rounded-xl p-1 mb-8 w-fit">
          {(["template", "generator", "preview"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab
                  ? "bg-white text-slate-800 shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              {tab === "template" && "1. 模板说明"}
              {tab === "generator" && "2. 导入生成"}
              {tab === "preview" && (preview ? `3. 预览 (${preview.node_count} 节点)` : "3. 预览")}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === "template" && (
          <div className="space-y-6 animate-fade-in">
            <div className="panel p-6">
              <h2 className="text-xl font-bold text-slate-800 mb-2">使用说明</h2>
              <div className="flex gap-6 mt-4">
                {[
                  { step: "1", title: "复制提示词", desc: "复制下方的 AI 提示词模板，粘贴给任何外部 AI（ChatGPT、Claude 等），并附上你的学习主题。" },
                  { step: "2", title: "获取 YAML", desc: "AI 将生成符合 LOS 规范的完整 YAML 图谱定义文件。" },
                  { step: "3", title: "导入生成", desc: "在「导入生成」标签页上传文件或粘贴 YAML，系统自动验证并预览图谱结构。" },
                  { step: "4", title: "保存加载", desc: "一键保存图谱到本地 graphs/ 目录，然后在 LearningOS 中加载即可开始学习！" },
                ].map((item) => (
                  <div key={item.step} className="flex-1 bg-slate-50 rounded-xl p-4 border border-slate-100">
                    <div className="w-7 h-7 rounded-full bg-primary-600 text-white text-xs font-bold flex items-center justify-center mb-3">{item.step}</div>
                    <h3 className="font-semibold text-slate-800 text-sm mb-1">{item.title}</h3>
                    <p className="text-xs text-slate-500 leading-relaxed">{item.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="panel p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-slate-800">AI 提示词模板</h2>
                <button onClick={handleCopyPrompt} className={`btn-ghost text-xs px-3 py-1.5 rounded-lg ${copiedPrompt ? "text-green-600" : "text-slate-500"}`}>
                  {copiedPrompt ? "已复制!" : "复制提示词"}
                </button>
              </div>
              <p className="text-sm text-slate-500 mb-4">
                复制完整提示词，粘贴给外部 AI，然后在末尾加上你的学习主题。
              </p>
              <pre className="bg-slate-900 text-slate-100 p-5 rounded-xl text-xs leading-relaxed overflow-auto max-h-96 scrollbar-thin whitespace-pre-wrap">
                {AI_PROMPT_TEMPLATE}
              </pre>
            </div>

            <div className="panel p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-slate-800">图谱格式规范</h2>
                <button onClick={handleCopyTemplate} className={`btn-ghost text-xs px-3 py-1.5 rounded-lg ${copiedTemplate ? "text-green-600" : "text-slate-500"}`}>
                  {copiedTemplate ? "已复制!" : "复制模板"}
                </button>
              </div>
              <p className="text-sm text-slate-500 mb-4">
                完整的字段说明、类型定义和示例。
              </p>
              <pre className="bg-slate-900 text-slate-100 p-5 rounded-xl text-xs leading-relaxed overflow-auto max-h-96 scrollbar-thin whitespace-pre-wrap">
                {GRAPH_TEMPLATE}
              </pre>
            </div>
          </div>
        )}

        {activeTab === "generator" && (
          <div className="space-y-6 animate-fade-in">
            <div className="panel p-6">
              <h2 className="text-xl font-bold text-slate-800 mb-2">导入或粘贴图谱 YAML</h2>
              <p className="text-sm text-slate-500 mb-4">
                可以直接上传 <code className="px-1.5 py-0.5 bg-slate-100 rounded text-xs font-mono">.txt</code> / <code className="px-1.5 py-0.5 bg-slate-100 rounded text-xs font-mono">.yaml</code> 文件，或手动粘贴 YAML 内容。系统将自动验证并预览图谱结构。
              </p>
              
              {/* File Import Section */}
              <div className="mb-4 p-4 border-2 border-dashed border-slate-300 rounded-xl bg-slate-50 hover:border-primary-400 transition-colors">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-primary-100 text-primary-600 flex items-center justify-center shrink-0">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                      <polyline points="17 8 12 3 7 8" />
                      <line x1="12" y1="3" x2="12" y2="15" />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    {importedFileName ? (
                      <div>
                        <div className="text-sm font-medium text-slate-800">{importedFileName}</div>
                        <div className="text-xs text-slate-500 mt-0.5">文件已加载，可以点击「预览图谱」进行验证</div>
                      </div>
                    ) : (
                      <div>
                        <div className="text-sm font-medium text-slate-700">上传 YAML 文件</div>
                        <div className="text-xs text-slate-500 mt-0.5">支持 .txt, .yaml, .yml 格式 — 包含 package_id、nodes、edges 的完整图谱定义</div>
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".txt,.yaml,.yml"
                      onChange={handleFileImport}
                      className="hidden"
                    />
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors"
                    >
                      选择文件
                    </button>
                    {yamlInput && (
                      <button
                        onClick={() => {
                          setYamlInput("");
                          setImportedFileName("");
                          setPreview(null);
                        }}
                        className="px-3 py-2 text-xs text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                      >
                        清空
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* YAML Textarea */}
              <textarea
                value={yamlInput}
                onChange={(e) => { setYamlInput(e.target.value); setImportedFileName(""); }}
                placeholder={`# 粘贴 AI 生成的图谱 YAML，或通过上方按钮导入文件\n# 应包含 package_id, name, version, nodes[], edges[]\n\npackage_id: my-graph\nname: My Graph\nversion: 1.0.0\n\nnodes:\n  - id: my-node\n    title: My Node\n    description: ...\n\nedges:\n  - from: ...\n    to: ...\n    relation: ...`}
                className="w-full h-80 bg-slate-900 text-slate-100 p-5 rounded-xl text-sm font-mono leading-relaxed resize-y border-2 border-slate-200 focus:border-primary-500 focus:ring-0 outline-none transition-colors"
                spellCheck={false}
              />
              <div className="flex items-center gap-3 mt-4">
                <button
                  onClick={handlePreview}
                  disabled={loading || !yamlInput.trim()}
                  className="btn-primary px-5 py-2.5 text-sm font-medium rounded-lg disabled:opacity-50"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <svg className="animate-spin w-4 h-4" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="2" opacity="0.2"/><path d="M1 8a7 7 0 017-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
                      验证中...
                    </span>
                  ) : (
                    "预览图谱"
                  )}
                </button>
                <button
                  onClick={() => { setYamlInput(GRAPH_TEMPLATE.replace(/^# .*\n/gm, "").replace(/^# .*\n/gm, "")); setImportedFileName(""); }}
                  className="btn-ghost text-xs px-3 py-1.5 rounded-lg"
                >
                  加载示例
                </button>
                <span className="text-xs text-slate-400 ml-auto">
                  字符数: {yamlInput.length}
                </span>
              </div>
              {error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>
              )}
            </div>
          </div>
        )}

        {activeTab === "preview" && preview && (
          <div className="space-y-6 animate-fade-in">
            {/* Summary Card */}
            <div className="panel p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-slate-800">
                  {preview.valid ? "图谱预览" : "验证错误"}
                </h2>
                {preview.valid && (
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="btn-primary px-5 py-2.5 text-sm font-medium rounded-lg disabled:opacity-50"
                  >
                    {saving ? "保存中..." : `保存到 graphs/${preview.package_id}/`}
                  </button>
                )}
              </div>

              {successMsg && (
                <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
                  <div className="flex items-start gap-2 flex-wrap">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" className="mt-0.5 shrink-0"><path d="M3 8l3 3 7-7" strokeLinecap="round" strokeLinejoin="round"/></svg>
                    <div className="flex-1 min-w-[200px]">{successMsg}</div>
                    <div className="flex gap-2 shrink-0">
                      <a
                        href={`/?graph=${encodeURIComponent(preview?.package_id || "")}`}
                        className="px-3 py-1.5 rounded-lg bg-green-600 text-white text-xs font-medium hover:bg-green-700 transition-colors inline-flex items-center gap-1"
                      >
                        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2"><path d="M2 6h7M6 2l4 4-4 4" strokeLinecap="round" strokeLinejoin="round"/></svg>
                        一键加载并跳转
                      </a>
                      <a
                        href="/"
                        className="px-3 py-1.5 rounded-lg border-2 border-green-200 text-green-700 text-xs font-medium hover:bg-green-100 transition-colors"
                      >
                        打开 LearningOS
                      </a>
                    </div>
                  </div>
                  <p className="mt-2 text-[11px] text-green-600/80 ml-6">
                    💡 也可以在 LearningOS 主界面点击「⟳ 刷新图谱」按钮手动刷新列表
                  </p>
                </div>
              )}

              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>
              )}

              <div className="grid grid-cols-4 gap-4 mb-6">
                <div className="bg-slate-50 rounded-xl p-4 text-center">
                  <div className="text-2xl font-bold text-slate-800">{preview.node_count}</div>
                  <div className="text-xs text-slate-500 mt-1">节点数</div>
                </div>
                <div className="bg-slate-50 rounded-xl p-4 text-center">
                  <div className="text-2xl font-bold text-slate-800">{preview.edge_count}</div>
                  <div className="text-xs text-slate-500 mt-1">边数</div>
                </div>
                <div className="bg-slate-50 rounded-xl p-4 text-center">
                  <div className="text-lg font-bold text-slate-800 truncate">{preview.name}</div>
                  <div className="text-xs text-slate-500 mt-1">图谱名称</div>
                </div>
                <div className="bg-slate-50 rounded-xl p-4 text-center">
                  <div className="text-lg font-bold text-slate-800 truncate">{preview.package_id}</div>
                  <div className="text-xs text-slate-500 mt-1">包 ID</div>
                </div>
              </div>

              {!preview.valid && preview.errors.length > 0 && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg mb-4">
                  <h3 className="font-semibold text-red-800 text-sm mb-2">验证错误:</h3>
                  <ul className="list-disc list-inside space-y-1">
                    {preview.errors.map((err, i) => (
                      <li key={i} className="text-sm text-red-700">{err}</li>
                    ))}
                  </ul>
                  <button
                    onClick={() => setActiveTab("generator")}
                    className="mt-3 text-sm text-red-700 underline"
                  >
                    返回修改
                  </button>
                </div>
              )}
            </div>

            {/* Node List */}
            {preview.nodes.length > 0 && (
              <div className="panel p-6">
                <h3 className="text-lg font-bold text-slate-800 mb-4">节点列表 ({preview.nodes.length})</h3>
                <div className="grid grid-cols-2 gap-2">
                  {preview.nodes.map((node) => (
                    <div key={node.id} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg border border-slate-100 hover:border-slate-200 transition-colors">
                      <div className={`w-2 h-2 rounded-full ${
                        node.type === "concept" ? "bg-blue-400" :
                        node.type === "skill" ? "bg-green-400" :
                        node.type === "project" ? "bg-purple-400" :
                        node.type === "milestone" ? "bg-amber-400" : "bg-slate-400"
                      }`} />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-slate-800 truncate">{node.title}</div>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-[10px] text-slate-400">{node.id}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-200 text-slate-500">{node.type}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-200 text-slate-500">{node.difficulty}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Edge List */}
            {preview.edges.length > 0 && (
              <div className="panel p-6">
                <h3 className="text-lg font-bold text-slate-800 mb-4">边列表 ({preview.edges.length})</h3>
                <div className="space-y-1">
                  {preview.edges.map((edge, i) => (
                    <div key={i} className="flex items-center gap-3 p-2.5 bg-slate-50 rounded-lg border border-slate-100 text-sm">
                      <span className="font-mono text-slate-600">{edge.from}</span>
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-slate-400"><path d="M3 7h7M9 4l3 3-3 3" strokeLinecap="round" strokeLinejoin="round"/></svg>
                      <span className="font-mono text-slate-600">{edge.to}</span>
                      <span className={`ml-auto text-[10px] px-1.5 py-0.5 rounded ${
                        ["prerequisite", "dependency", "progression"].includes(edge.relation)
                          ? "bg-amber-100 text-amber-700"
                          : "bg-blue-100 text-blue-700"
                      }`}>
                        {edge.relation}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "preview" && !preview && (
          <div className="panel p-12 text-center animate-fade-in">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-slate-100 flex items-center justify-center">
              <svg width="28" height="28" viewBox="0 0 28 28" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-slate-400"><circle cx="14" cy="14" r="12"/><circle cx="14" cy="10" r="2"/><path d="M10 20c2-3 6-3 8 0" strokeLinecap="round"/></svg>
            </div>
            <h3 className="text-lg font-semibold text-slate-600 mb-2">暂无预览</h3>
            <p className="text-sm text-slate-400 mb-4">前往「导入生成」标签页，上传文件或粘贴 YAML 内容，然后点击「预览图谱」。</p>
            <button onClick={() => setActiveTab("generator")} className="btn-primary px-4 py-2 text-sm rounded-lg">
              前往导入生成
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
