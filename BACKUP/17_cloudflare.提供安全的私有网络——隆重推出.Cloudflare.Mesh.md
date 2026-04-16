# [cloudflare 提供安全的私有网络——隆重推出 Cloudflare Mesh](https://github.com/myogg/gitblog/issues/17)

Cloudflare Mesh：一个面向用户、节点和代理的私有网络

![BLOG-3215_1.png](https://i.829259.xyz/api/cfile/AgACAgUAAx0ER6IxDQACTsRp4IfU1CYla1Zwy-AWcB2eM8GFYgAClRBrG8_VAVfRIzrEbxXS-wEAAwIAA3cAAzsE)

Cloudflare Mesh 是一款对开发者友好的私有网络解决方案。只需一个轻量级连接器和一个二进制文件，即可连接所有设备：您的个人设备、远程服务器和用户终端。您无需为每种连接模式安装单独的工具。网络中只需一个连接器，即可支持所有访问模式。

连接后，您私有网络中的设备可以通过私有 IP 地址相互通信，这些 IP 地址通过 Cloudflare 的全球网络路由到 330 多个城市，从而提高网络的可靠性和控制力。

现在，有了 Mesh，一个解决方案就可以解决我们上面提到的所有代理场景：

在您的手机上使用适用于 iOS 的 Cloudflare One Client，您可以通过 Mesh 专用网络将您的移动设备安全地连接到运行 OpenClaw 的本地 Mac mini。

在笔记本电脑上安装适用于 macOS 的 Cloudflare One Client，即可将笔记本电脑连接到私有网络，以便您的编码代理可以访问暂存数据库或 API 并进行查询。

借助Linux 服务器上的Mesh 节点，您可以将外部云中的 VPC 连接在一起，让代理访问外部私有网络中的资源和 MCP。

[由于 Mesh 由Cloudflare One Client](https://developers.cloudflare.com/cloudflare-one/team-and-resources/devices/cloudflare-one-client/)提供支持，因此每个连接都继承了 Cloudflare One 平台的安全控制。网关策略适用于 Mesh 流量。设备状态检查可验证连接设备。DNS 过滤可捕获可疑的查询。无需额外配置即可实现这些功能：保护用户流量的策略同样适用于代理流量。

网状结构与隧道结构之间的选择
随着 Mesh 的推出，您可能会问：何时应该使用 Mesh 而不是 Tunnel？两者都能将外部网络私密地连接到 Cloudflare，但它们的用途不同。Cloudflare [Tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/)是单向流量的理想解决方案，Cloudflare 会将来自边缘的流量代理到特定的私有服务（例如 Web 服务器或数据库）。 

另一方面，Cloudflare Mesh 提供了一个完整的双向多对多网络。Mesh 中的每个设备和节点都可以使用其私有 IP 地址相互访问。网络中运行的应用程序或代理可以发现并访问 Mesh 上的任何其他资源，而无需每个资源都拥有自己的隧道。 

利用 Cloudflare 网络的强大功能
Cloudflare Mesh 为您提供网状网络的优势（弹性、高可扩展性、低延迟和高性能），但通过 Cloudflare 路由所有内容，它解决了网状网络的一个关键挑战：NAT 穿越。

<audio src="https://i.829259.xyz/api/cfile/CQACAgUAAx0ER6IxDQACTsNp4ITny5jlyHDxrs0YF59RInKY2gACNx0AAs_VAVeS_3pEWyhTRjsE" controls></audio>