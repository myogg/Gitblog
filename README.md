# 北方的博客 (React 版)

这是一个基于 React 19 + Vite + TypeScript 构建的现代化静态博客系统。它直接使用 GitHub Issues 作为 CMS（内容管理系统），无需后端数据库。

## ✨ 特性

- **无后端依赖**：直接对接 GitHub Issues API，发布 Issue 即发布文章。
- **实时更新**：利用 GitHub API 实时拉取最新内容（含简单的客户端缓存）。
- **全功能复刻**：
  - 首页时间轴布局
  - 标签筛选与归档
  - 实时搜索（基于 GitHub Search API）
  - 评论系统（直接显示 GitHub Issue 评论）
- **现代化体验**：
  - 响应式设计（完美适配移动端）
  - 深色模式（Dark Mode）支持
  - 极致的加载速度 (Vite 构建)

## 🚀 快速开始

### 1. 本地开发

```bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

### 2. 配置

在 `src/config.ts` 或 `.env` 中配置你的 GitHub 仓库信息：

```env
VITE_GITHUB_USERNAME=myogg
VITE_GITHUB_REPO=Gitblog
VITE_BLOG_TITLE=北方的博客
```

### 3. 部署

本项目预置了 GitHub Actions 工作流 (`.github/workflows/deploy.yml`)，可一键部署到 GitHub Pages。

1. 将代码推送到你的 GitHub 仓库。
2. 在仓库 Settings -> Pages 中，Build and deployment source 选择 **GitHub Actions**。
3. 等待 Actions 跑完，即可访问。

## 🛠️ 技术栈

- **Framework**: React 19, Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4, shadcn/ui
- **Icons**: Lucide React
- **Router**: wouter
- **Markdown**: react-markdown + github-markdown-css

---
Designed and developed by AnyGen.
