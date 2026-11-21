# Chem Cloud

Chem 安装器、原生模块及资源包的发布仓库。支持 **小米手环 9 / 固件 3.1.35** 与 **小米手环 10 NFC / 固件 3.1.28**，安装时请选择对应固件。

当前发布：xiaomi-band-9 / 3.1.35：Chem `0x26112201`、安装器 ID `913211316`、NoirMusic `0.4.60 / code92`、Magic `0.2.16 / code23`；xiaomi-band-10-nfc / 3.1.28：Chem `0x26112201`、安装器 ID `913211316`、Magic `0.2.16 / code23`，ABI 2.0。客户端插件单独分发。

## 下载与安装

在 ChemClient 连接手环并刷新，获取云端可安装模块。安装或更新由用户点击触发；`.chem` 直接导入模块，不经过 Astro 表盘上传队列。

| 项目 | 用途 | 文件 |
| --- | --- | --- |
| Chem | 原生模块加载与管理 | [安装器](xiaomi-band-9/3.1.35/chem-loader/Chem-Band9-3.1.35.face) |
| NoirMusic | 蓝牙音乐管理与播放 | [模块](xiaomi-band-9/3.1.35/NoirMusic/NoirMusic-Band9-3.1.35.chem) |
| Magic | 图标、字体、日历与背景资源包管理 | [模块与资源包说明](xiaomi-band-9/3.1.35/Magic/README.md) |

Magic 0.2.16 使用配套 Chem 构建 `0x26111504`，NFC 通信和首次导入目录修复需要同时更新 Chem。本版修复 NFC 页面跳转与返回接口。手环端点击资源包进入详情，保留紫色开关与确认删除；已导入资源包可离线使用。背景模糊独立管理，可按四个区域分别控制。

更新 Chem 后请重启手环，再打开新版安装器并点击「启动」。更新 Magic 后同样需要重启并启动 Chem，以释放旧回调并保留已有资源包。手环 9 的新版安装器会清理旧自启动文件，保留模块和配置。

Chem `0x26112201` 已通过两款表盘打包、ELF 校验、原生交付及安装相关回归。手环 10 NFC 的系统设置入口仍待实机验证。此前的 Magic 导入反馈对应原配套版本。

手环 10 NFC： [Chem 安装器](xiaomi-band-10-nfc/3.1.28/chem-loader/Chem-Band10NFC-3.1.28.face) · [Magic 模块](xiaomi-band-10-nfc/3.1.28/Magic/Magic-Band10NFC-3.1.28.chem)。不将手环 9 资源示例自动发布为 NFC 资源。NoirMusic 保留原发布版本，本轮未发布 NFC 音乐模块。

## 目录与校验

```text
index.json
repository.json
xiaomi-band-9/3.1.35/
  chem-loader/Chem-Band9-3.1.35.face
  NoirMusic/NoirMusic-Band9-3.1.35.chem
  Magic/
    Magic-Band9-3.1.35.chem
    VioletCalendar.magic
    resources.json
    README.md
    CHANGELOG.md
    NOTICE.md
    LICENSE
```

加载器和模块按「设备 / 固件 / 名称」同级存放，只保留当前发布文件。`index.json` 记录固件摘要、安装器 ID、模块版本、文件长度与 SHA-256；`.chem` 内含 ELF、Ed25519 签名凭据、清单和资源，客户端与手环分别验证。

Magic 的自有 `.magic` 示例从仓库下载后，在 ChemClient 的 Magic 导入页导入；当前云端模块列表只负责 `.chem` 安装。示例包长度与 SHA-256 单列在 `Magic/resources.json`。ABMF 与 Glaze UI 为付费第三方资源，不随公开仓库分发；合法持有的本地资源包可自行导入。

仓库：https://github.com/OctopusCat101/ChemCloud

默认镜像根地址：`https://gh-proxy.com/https://raw.githubusercontent.com/OctopusCat101/ChemCloud/main`。客户端每次连接检查或刷新时获取清单，按文件摘要校验下载；Git 提交与推送使用仓库原地址。镜像可能存在缓存。

## 统一管理与发布

上传、清单同步、多项目管理工具均在本仓库，业务项目只保留自己的构建工具。路径及构建命令集中在 [projects.toml](projects.toml)，机器特有路径可放在忽略提交的 `projects.local.toml`。

```powershell
# 查看所有项目状态
python D:/ChemCloud/workspace.py status

# 构建、验证并发布 Magic；也可选择 chem、music 或 all
python D:/ChemCloud/release.py magic

# 一次发布多个项目
python D:/ChemCloud/release.py chem magic

# 已构建并验证，只同步、提交、上传现有产物
python D:/ChemCloud/release.py

# 只预检，不构建、不提交、不上传
python D:/ChemCloud/release.py --dry-run
```

指定项目发布不会把未选择模块的本地构建一起上传；其他设备目标和模块保留。发布前需递增修改模块自身的版本号；Chem 构建号和表盘 ID 在选择构建 Chem 时自动递增。客户端插件仍单独分发，可用 `workspace.py build client` 构建。

源码仓库也可一次处理，不必逐个切目录：

```powershell
python D:/ChemCloud/workspace.py commit chem client -m "Improve module management"
python D:/ChemCloud/workspace.py push chem client
```

`commit` 会暂存所选仓库内全部未被忽略的更改，执行前先查看 `status`；源码提交与云端产物发布分别选择。`all` 可处理所有已注册仓库，未初始化 Git 的目录会提示并跳过。

Magic 已纳入独立私有源码仓库，并可通过上述命令统一提交和推送。新项目可执行 `python D:/ChemCloud/workspace.py init <项目名>` 初始化，再配置自己的 `origin`。

完整用法、目录职责和失败恢复见 [发布与多项目管理](docs/RELEASING.md)。Git 网络操作使用系统代理、HTTP/1.1、超时与重试，失败保留已完成工作，不强推。不上传签名私钥、设备固件或构建中间文件。
