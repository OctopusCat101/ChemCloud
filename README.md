# Chem Cloud

Chem 安装器、原生模块及资源包的发布仓库。当前支持 **小米手环 9 / 固件 3.1.35**。

当前发布：Chem 构建号 `0x26111309`、安装器 ID `913211309`、NoirMusic `0.4.58 / code90`、Magic `0.2.5 / code7`，ABI 2.0。客户端插件单独分发。

## 下载与安装

在 ChemClient 连接手环并刷新，获取云端可安装模块。安装或更新由用户点击触发；`.chem` 直接导入模块，不经过 Astro 表盘上传队列。

| 项目 | 用途 | 文件 |
| --- | --- | --- |
| Chem | 原生模块加载与管理 | [安装器](xiaomi-band-9/3.1.35/chem-loader/Chem-Band9-3.1.35.face) |
| NoirMusic | 蓝牙音乐管理与播放 | [模块](xiaomi-band-9/3.1.35/NoirMusic/NoirMusic-Band9-3.1.35.chem) |
| Magic | 图标、字体、日历与背景资源包管理 | [模块与资源包说明](xiaomi-band-9/3.1.35/Magic/README.md) |

Magic 需要本次配套的 Chem 构建 `0x26111309` 或更新的兼容构建。手环端点击资源包进入详情，保留紫色开关与确认删除；已导入资源包可离线使用。ABMF 示例仅在应用列表和下拉通知菜单启用静态毛玻璃。

更新 Chem 后需手动运行安装器，使驻留环境生效；更新 Magic 后需重启手环并运行 Chem，以释放旧回调，无需清空资源包。自动启动在熄屏且系统就绪时推进；升级不会静默清除已有安全模式或失败记录。

本地构建、签名校验与相关回归通过；Magic 0.2.5 的实机显示和操作效果仍待验收。各文件仅适用于指定设备及精确固件。

## 目录与校验

```text
index.json
repository.json
xiaomi-band-9/3.1.35/
  chem-loader/Chem-Band9-3.1.35.face
  NoirMusic/NoirMusic-Band9-3.1.35.chem
  Magic/
    Magic-Band9-3.1.35.chem
    ABMF-Band9-3.1.35.magic
    VioletCalendar.magic
    resources.json
    README.md
    CHANGELOG.md
    NOTICE.md
    LICENSE
```

加载器和模块按「设备 / 固件 / 名称」同级存放，只保留当前发布文件。`index.json` 记录固件摘要、安装器 ID、模块版本、文件长度与 SHA-256；`.chem` 内含 ELF、Ed25519 签名凭据、清单和资源，客户端与手环分别验证。

Magic 的 `.magic` 示例从仓库下载后，在 ChemClient 的 Magic 导入页导入；当前云端模块列表只负责 `.chem` 安装。示例包长度与 SHA-256 单列在 `Magic/resources.json`。

仓库：https://github.com/OctopusCat101/ChemCloud

默认镜像根地址：`https://gh-proxy.com/https://raw.githubusercontent.com/OctopusCat101/ChemCloud/main`。客户端每次连接检查或刷新时获取清单，按文件摘要校验下载；Git 提交与推送使用仓库原地址。镜像可能存在缓存。

## 一条命令发布

先完成需要更新的模块构建与测试，再执行：

```powershell
python D:/Chem/scripts/release-cloud.py --skip-build
```

此命令同步远端，校验已有 Chem、NoirMusic、Magic 及资源包，更新清单与说明，然后提交并推送。不带 `--skip-build` 会递增版本并构建、测试 Chem；仅更新模块时无需重建客户端或其他模块。Magic 位于相邻的 `D:/Magic`。

仅检查当前构建，不修改或上传：

```powershell
python D:/Chem/scripts/release-cloud.py --dry-run
```

只同步本地发布目录，不提交：

```powershell
python D:/Chem/scripts/publish-cloud.py
```

发布脚本保留清单中的其他模块与设备目标，拒绝降级及同版本替换文件。新版 Chem 必须同时递增原生构建号和九位表盘 ID。Git 网络请求使用系统代理、HTTP/1.1、超时与重试；失败保留本地修改，不强推或自动回滚。

不上传签名私钥、设备固件或构建中间文件。Magic 的来源和许可随模块提供。
