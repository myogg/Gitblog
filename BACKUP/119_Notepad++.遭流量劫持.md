# [Notepad++ 遭流量劫持](https://github.com/myogg/Gitblog/issues/119)

[Notepad++ 遭流量劫持，更新程序被植入恶意程序](https://notepad-plus-plus.org/news/v889-released/)

Notepad++ 发布安全警告，它遭遇了流量劫持，部分地区的更新程序被植入恶意程序。

![](https://pic.imgdd.cc/item/693ab6f38e53870ab51788d0.jpg)


调查发现，Notepad++ 更新程序 WinGUp 的流量被劫持到恶意服务器，下载恶意可执行文件。

更新程序使用版本检查功能查询 URL“https://notepad-plus-plus.org/update/getDownloadUrl.php”并评估返回的 XML 文件。更新程序使用 XML 文件中列出的 Download-URL，将文件保存到 %TEMP% 文件夹并执行。任何能拦截和篡改此流量的攻击者都可以更改 Download-URL。

Notepad++ v8.8.7 之前的版本使用了自签名证书，允许攻击者创建篡改后的更新并将其推送给受害者。从 v8.8.7 开始 Notepad++ 使用了来自 GlobalSign 签发的合法证书进行签名。

