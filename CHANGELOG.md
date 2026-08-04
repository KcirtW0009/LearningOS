# Changelog

All notable changes to this project will be documented in this file.

## [1.0.2] - 2026-08-04

### Fixed

- **进程清理**: 修复关闭应用后后端进程（backend.exe）和学习OS进程残留的问题
  - 将 `cleanup` 函数改为异步，支持优雅关闭（SIGTERM）与强制终止
  - 添加 `before-quit` 事件拦截，确保任何退出路径都触发清理
  - 实现三层进程清理策略：PID进程树终止 → 进程名匹配 → 端口扫描兜底
  - 添加 `quitRequested` 标志防止重复触发 `app.quit()`
  - 增加 8 秒安全网超时，确保即使清理异常也能强制退出
  - 在 Windows 上使用 `taskkill /F /T` 替代无效的 SIGTERM 信号

### Changed

- 无重大变更

### Added

- 进程清理辅助函数：`killByPidTree()`、`killByName()`、`killByPort()`

## [1.0.1] - 2026-08-03

### Changed

- 初始发布版本

[1.0.2]: https://github.com/KcirtW0009/LearningOS/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/KcirtW0009/LearningOS/releases/tag/v1.0.1