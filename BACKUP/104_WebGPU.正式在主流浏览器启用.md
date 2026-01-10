# [WebGPU 正式在主流浏览器启用](https://github.com/myogg/Gitblog/issues/104)

WebGPU 已在 Chrome、Edge、Firefox 与 Safari 上获得正式支持，标志着网页原生高性能图形与 GPU 通用计算能力的全面落地。这一里程碑来自 W3C GPU for the Web 工作组多年的协作，参与方包括 Apple、Google、Intel、Microsoft 与 Mozilla。

WebGPU 提供较 WebGL 更现代、性能更高的接口，允许浏览器直接利用当代 GPU 特性，用于高端 3D 图形渲染与通用计算任务。其计算管线进一步提升机器学习推理、视频处理、物理仿真等重型工作负载的效率，使网页端获得接近桌面级的性能。

多项 AI 与图形框架已基于 WebGPU 实现加速，包括 ONNX Runtime、Transformers.js、Babylon.js、Three.js 等。借助 Render Bundles 等新机制，渲染场景的 CPU 负载可显著降低，性能提升可达数量级。

在平台覆盖方面，WebGPU 已在 Windows、macOS、ChromeOS、iOS、iPadOS、visionOS，以及部分 Android 设备上线；Linux 与更多平台的支持仍在推进中。
