# [Chorus: 多模型 AI 对话的轻量级桌面应用](https://github.com/myogg/Gitblog/issues/4)

在一个界面同时对话多个 AI 模型，获取不同视角的答案

<!-- more -->

[官网](https://chorus.sh/) ｜ [Github](https://github.com/meltylabs/chorus)

---
![IMG_20260128_125104_024.jpg](https://i.829259.xyz/api/rfile/IMG_20260128_125104_024.jpg)

✨ 特点

• 多模型并行对话：同时向 Claude Sonnet 4、o3-mini、Gemini 2.5 Pro、DeepSeek R1 等多个模型提问，实时对比不同模型的回答
• Ambient Chat：可以从任何地方启动对话，Chorus 能看到你的屏幕，了解你正在做什么，无需额外解释
• MCP 支持：运行任何 MCP 服务器，支持网页搜索、终端命令执行、GitHub 集成等
• 本地和云端模型兼容：支持 OpenAI、Anthropic、Google、OpenRouter 以及通过 Ollama 运行的本地开源模型
• 文档处理：URL 自动提取、PDF/图片/文档上传、全文搜索
• Magic Projects：对话之间自动共享上下文
• BYOK：自带 API 密钥或使用代理服务
• 极速体验：毫秒级全文搜索、完整键盘快捷键支持、代码和 LaTeX 语法高亮

⚙️ 机制

• 前端：React 18.3 + Vite 5.4 + TypeScript 5.8
• 后端：Rust (Tauri 2.5) + SQLite
• UI 组件：Radix UI + Tailwind CSS 3.4
• 状态管理：Zustand + TanStack Query
• 桌面框架：Tauri 2（使用系统 WebView，不打包 Chromium）

主要依赖

- AI SDK：@anthropic-ai/sdk、@google/genai、openai、@modelcontextprotocol/sdk
- 实用工具：pdfjs-dist（PDF 处理）、cheerio（HTML 解析）、highlight.js（代码高亮）、katex（LaTeX 渲染）
- 开发工具：ESLint、Prettier、Vitest、Husky

数据存储

- 本地 SQLite 数据库存储所有数据
- 隐私优先：数据不离开设备
- 支持文件系统监控

👨🏻‍💻 使用场景

• 技术问题调试：同时询问多个模型，一个模型可能遗漏的错误，其他模型能发现
• 学术写作：避免单一模型的幻觉或道歉循环，通过多模型对比获得更可靠的答案
• 研究和学习：对比不同 AI 的观点和解释方式，获得更全面的理解
• 内容创作：利用不同模型的优势，Claude 擅长写作，GPT 擅长结构化，Gemini 擅长多语言
• 大文档分析：通过 URL 提取和 PDF 上传处理文档，配合全文搜索快速定位信息

🛣️ 路线图

根据 GitHub issues 和社区反馈，团队正在关注：

• RAG 模式：社区提出详细的大文档处理方案（40k+ tokens），可能采用云端 RAG 或本地向量数据库
• Ollama 优化：增强本地模型支持，自定义 API 地址配置
• 语音集成：类似 qspeak.app 的语音交互功能
• 本地爬虫：替代 Firecrawl 的本地网页抓取方案
• 成本追踪增强：已实现 OpenRouter 成本跟踪，未来可能支持更多提供商

💬 社区评价

Chorus 在 GitHub 上获得了 575+ 星标和 73 个 fork，开源仅两个月就积累了活跃的开发者社区。项目有 25+ 个 issues 讨论。

Garry Tan（Y Combinator 总裁兼 CEO）评价道：「这是关于 AI 如何改变个人计算的一个很酷的尝试。」

Hamel Husain（Answer.AI）称赞说：「Chorus 真的很酷。这是一个非常精致的应用，让你并排使用所有模型，'环境聊天'功能允许模型看到你电脑上正在做的一切。它就是好用。」

Alex Volkov（Thursd/AI）表示：「Chorus 对我来说已经成为不可或缺的 AI 工具！出色的键盘快捷键支持、对比模式、MCP、环境聊天、自带密钥支持、本地模型支持。它真的应有尽有！」

从社区反馈来看，用户最喜欢的是多模型并行对比功能和 Ambient Chat 的便利性，键盘快捷键和 MCP 集成也备受好评。不过也有改进空间：Windows 版本尚未发布（仅支持 Mac），MCP 服务器配置对新手有一定门槛，部分用户期待的 RAG 模式功能还在社区讨论阶段。总体而言，社区对产品持积极态度，维护者响应迅速，用户提出的成本追踪等功能已快速实现。

🖊️ 作者背景

Charlie Holtz - 联合创始人兼 CEO

• 教育：Brown University 计算认知神经科学学士（荣誉学位）
• 职业经历：
  - Replicate 工程师（领导增长，构建数百万用户应用）
  - Point72 量化研究员（最年轻的量化开发者，管理数十亿美元投资组合）
  - Brown University Serre Lab 计算视觉研究助理
• 背景：结合技术专长和认知神经科学洞察，前飞盘运动员

Jackson de Campos - 联合创始人

• 教育：Brown University 计算机科学学士
• 职业经历：
  - Netflix 机器学习软件工程师（扩展 Netflix 整个目录的视频理解模型推理）
  - Amazon SDE 实习生
  - Brown University 教学助理（逻辑系统课程）
• 背景：机器学习和大规模基础设施专家

公司：Melty Labs

- Y Combinator S24 批次
- 种子轮融资：50 万美元（2024）
- 团队规模：1-10 人
- 总部：旧金山，加州
- 产品线：Melty（AI 代码编辑器）→ Chorus（多模型 AI 对话应用）
- 哲学：开源优先、本地优先、隐私优先

团队特色

两位创始人在 Brown University 打飞盘时相识，共同的技术热情和互补的专业背景（认知神经科学 + 机器学习）为产品注入了独特视角。他们使用 Claude Code 构建产品，在博客中甚至把 Claude 称为「本月最佳员工」。

💰 定价

完全免费 + 开源

- MIT 许可证
- 自带 API 密钥（BYOK）：用户直接向 AI 提供商付费
- 可选代理服务：使用 Chorus 的代理
- 无订阅费用
