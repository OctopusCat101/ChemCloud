# Chem Cloud

Chem 模块与安装器的发布仓库。目前只提供小米手环 9、固件 3.1.35 的目标。

```text
index.json
xiaomi-band-9/
  3.1.35/
    chem-loader/Chem-Band9-3.1.35.face
    NoirMusic/NoirMusic-Band9-3.1.35.chem
```

模块和对应加载器按「设备 / 固件 / 名称」同级存放，每个目录只保留当前发布文件。其他型号或固件使用独立目录，不混用安装器、偏移或模块。

`index.json` 描述目标、固件摘要、安装器表盘 ID、版本，以及所有下载文件的长度和 SHA-256。`.chem` 内含原生 ELF、Ed25519 签名凭据、模块清单和资源。客户端与手环分别验证，目标或固件不匹配时拒绝安装。

远程仓库尚未创建，`repository.json` 中的地址保留为空。创建 GitHub 仓库并上传这些文件后，将 ChemClient 的 `cloud.json` 中 `repository_url` 设置为可直接读取 `index.json` 的 HTTPS 根目录，例如 `https://raw.githubusercontent.com/OWNER/REPO/main`，重新打包客户端。客户端不会向空地址发送网络请求。

发布流程：先构建 Chem 安装器和 NoirMusic 模块，再运行 `D:/Chem/scripts/publish-cloud.py`。脚本更新本地索引、文件摘要和客户端随包目标索引，不执行提交或推送。每次发布新版加载器必须同时更新原生构建号和九位表盘 ID，避免把旧安装器认作最新。

连接后客户端会检查安装器、必要时加入 Astro 上传队列，检测实际安装完成后切换，等待用户在手环运行。Astro API 4 仅开放添加上传队列，没有开始上传和上传完成接口；如宿主没有自动开始，需在宿主队列开始上传。普通 `.chem` 模块不使用表盘上传队列。
