# [DeepSeek 发布 DeepGEMM 重大更新：推出 Mega MoE 融合算子并支持 FP4 精度](https://github.com/myogg/gitblog/issues/19)

DeepSeek 旗下高性能算子库 DeepGEMM 于 2026 年 4 月 16 日发布重大更新，正式推出 Mega MoE 融合算子。

![IMG_20260416_204442_784.jpg](https://i.829259.xyz/api/rfile/IMG_20260416_204442_784.jpg)

该算子通过将 dispatch、SwiGLU 等多个计算步骤与 NVLink 通信重叠，实现了计算与通信的高效融合。此外，本次更新还新增了 FP8xFP4 GEMM 算子、FP4 Indexer 以及 PDL（程序化依赖启动）支持，并显著提升了 JIT 编译速度。

DeepGEMM 是专为现代大模型设计的 CUDA 内核库，支持 NVIDIA SM90 和 SM100 架构。其核心优势在于轻量化设计与运行时即时编译，无需在安装阶段进行复杂编译。目前，该库已在 H800 等显卡上展现出极高的算力利用率，其 Mega MoE 算子通过对称内存技术进一步优化了多专家模型在推理和训练中的性能表现。

https://github.com/deepseek-ai/DeepGEMM/tree/public-release-260416

