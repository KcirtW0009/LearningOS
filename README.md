# LearningOS

一个基于知识图谱的学习管理系统，帮助你构建和追踪学习路径。

## ✨ 功能特性

- 🗺️ **知识图谱**: 将学习内容组织成可视化的技能树，支持拖拽平移导航
- 🎯 **任务模式**: 设定学习目标，自动规划最优路径，支持直接双击节点激活
- 📊 **进度追踪**: 记录学习进度，支持实时学习记录和评分
- ⭐ **XP 系统**: 经验值与等级系统，完成节点获得经验值
- 👑 **Boss 奖励**: 完成里程碑节点获得额外经验值加成
- 🏆 **成就系统**: 约 20 个成就，展示学习成果
- 📈 **熟练度系统**: 5 级熟练度（完成/熟悉/掌握/熟练/精通），影响 XP 加成
- ↩️ **撤销功能**: 支持无限步撤回，包含级联撤销
- 🌐 **多语言**: 中英文切换支持
- 📱 **桌面应用**: 支持 Windows/macOS 桌面客户端 (Electron)
- 🔄 **自动更新**: Electron 应用自动更新支持

## 🛠️ 技术架构

- **前端**: Next.js + React + TypeScript + TailwindCSS
- **后端**: FastAPI + Python
- **桌面**: Electron

## 🚀 快速开始

### 开发模式

```bash
# 安装依赖
npm run install:all

# 启动后端 (终端1)
cd runtime
python -m uvicorn los.api.server:app --host 127.0.0.1 --port 8000 --reload

# 启动前端 (终端2)
cd frontend
npm run dev

# 访问
# 前端: http://localhost:3000
# API文档: http://localhost:8000/docs
```

### Electron 开发模式

```bash
npm run electron:dev
```

## 📁 项目结构

```
LearningOS/
├── frontend/           # Next.js 前端
│   ├── src/
│   │   ├── app/        # 页面 (page.tsx, globals.css)
│   │   ├── components/ # 组件 (SkillTree, Onboarding, LearningRecord)
│   │   └── lib/        # 工具函数 (i18n, cache)
│   ├── public/         # 静态资源
│   └── next.config.js  # Next.js 配置
├── runtime/            # Python 后端
│   ├── los/
│   │   ├── api/        # API 接口 (server.py)
│   │   ├── engine/     # 引擎逻辑 (xp.py, resolver.py, recommender.py, achievements.py)
│   │   ├── graph/      # 图模型 (models.py, loader.py, validator.py)
│   │   ├── runtime/    # 运行时实例 (runtime_instance.py, runtime_manifest.py)
│   │   ├── state/      # 状态管理 (models.py, engine.py)
│   │   └── storage/    # 存储适配 (adapter.py)
│   └── data/           # 用户数据
├── electron/           # Electron 桌面应用
│   ├── main.js         # 主进程
│   └── preload.js      # 预加载脚本
├── graphs/             # 知识图谱包
├── tests/              # 测试用例
└── spec/               # 规格文档
```

## 🎮 核心概念

- **Node**: 节点，代表概念、技能、项目或里程碑
- **Edge**: 边，定义节点之间的依赖关系
- **Graph**: 图，由节点和边组成的知识图谱
- **UserState**: 用户状态，记录学习进度

## 📊 XP 系统

完成节点可获得经验值 (XP)，积累经验值可提升等级。

### XP 计算公式

```
XP = BASE_XP(25) × score_factor(score//5) × difficulty(1/1.5/2) × proficiency_factor(1.0/1.2/1.5/2.0/3.0)
```

### 等级计算

```
Level = floor(sqrt(xp / 50)) + 1
```

| 等级 | 需要 XP |
|------|--------|
| Lv.1 | 0 |
| Lv.2 | 50 |
| Lv.3 | 200 |
| Lv.4 | 450 |
| Lv.5 | 800 |

## 📈 熟练度系统

5 个熟练度等级，通过评分提升：

| 等级 | 英文 | 分数 | 图标 | 颜色 | XP加成 |
|------|------|------|------|------|--------|
| 完成 | Done | 5 | ✓ | 灰绿 | 1.0x |
| 熟悉 | Known | 10 | ◈ | 蓝 | 1.2x |
| 掌握 | Skilled | 20 | ◆ | 紫 | 1.5x |
| 熟练 | Expert | 50 | ★ | 金 | 2.0x |
| 精通 | Master | 80 | ⬡ | 红金 | 3.0x |

## 🔧 构建

### 构建前端

```bash
cd frontend
npm run build
```

### 构建后端 (Windows)

```bash
cd runtime
pyinstaller -F --name backend --add-data "los;los" --add-data "graphs;graphs" --add-data "data;data" los/api/server.py
```

### 构建桌面应用

```bash
npm run electron:build
```

## 📜 许可证

MIT