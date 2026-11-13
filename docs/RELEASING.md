# 发布与多项目管理

## 目录职责

- `Chem`：SDK、固件适配、加载器和原生管理器，保留模块打包与本项目构建工具。
- `NoirMusic`、`Magic`：各自模块源码、资源和测试。
- `ChemClient`：Astro 客户端插件源码与构建。
- `ChemCloud`：唯一的云端目录、发布入口、跨项目操作和发布文档。

无需把所有源码硬塞进一个仓库，也不需要搬动现有目录。`projects.toml` 注册路径、构建命令、测试命令和是否参与模块云端发布；路径相对 ChemCloud 解析。新机器可用不提交的 `projects.local.toml` 覆盖路径，例如：

```toml
[projects.magic]
path = "E:/Projects/Magic"
```

## 常用命令

以下命令均可在任意目录运行：

```powershell
# 所有项目的分支、修改和未推送状态
python D:/ChemCloud/workspace.py status

# 只构建或测试，不做 Git 操作
python D:/ChemCloud/workspace.py build magic client
python D:/ChemCloud/workspace.py check magic cloud

# 一条命令构建、测试、提交发布文件并推送
python D:/ChemCloud/release.py magic
python D:/ChemCloud/release.py chem music magic
python D:/ChemCloud/release.py all

# 不构建，发布当前已验证产物；指定项目可以缩小发布范围
python D:/ChemCloud/release.py
python D:/ChemCloud/release.py magic --skip-build

# 只预检现有产物，不修改版本或发布文件
python D:/ChemCloud/release.py magic --dry-run

# 本地提交发布结果，暂不上传
python D:/ChemCloud/release.py magic --skip-build --no-push
```

选择 `chem` 构建时，自动递增原生构建号和表盘 ID，再执行 Flash 与启动持久化回归。模块自身版本需在各项目配置中递增；同版本改变二进制会拒绝发布。未选择项目的本地产物不会被顺带发布，已有其他模块与目标不会被清单覆盖。

模块签名、固件摘要、资源大小与 SHA-256、Magic 示例包和编辑源一致性均在同步前检查。`--dry-run` 不构建、不改版本、不提交、不推送。只有 Chem 变化时，不重建客户端或其他模块。

## 批量处理源码

```powershell
python D:/ChemCloud/workspace.py status
python D:/ChemCloud/workspace.py commit chem client -m "Improve connection handling"
python D:/ChemCloud/workspace.py push chem client
```

`commit` 暂存所选仓库全部未被忽略的更改，包括新增和删除文件。先检查状态，确保这些更改属于这次提交；不要把签名私钥、固件和临时文件放进可提交范围。工具不改写历史、不强推，提交与推送是两个明确动作。

项目名可用 `chem`、`music`、`magic`、`client`、`cloud`；`all` 处理所有注册项目。独立仓库保留各自提交历史，批量操作中某一步失败会停止，之前完成的提交保留。

Magic 当前尚未初始化 Git。首次执行：

```powershell
python D:/ChemCloud/workspace.py init magic
```

在 GitHub 创建独立源码仓库后，在 Magic 目录配置真实的 `origin` 地址；随后即可用同一套批量提交和推送命令。未初始化的目录在批量 `all` 操作中明确提示并跳过，不会被悄悄当成已备份。

## 失败恢复

- 构建或测试失败：停止发布，保留源码和本地产物。
- 版本或摘要不一致：修正版本并重新构建，不覆盖云端同版本文件。
- 提交后推送失败：保留本地提交，网络恢复后执行 `python D:/ChemCloud/workspace.py push cloud`。
- 云端仓库有本地修改：先检查、提交或处理修改，再发布；脚本不会自动吞并这些更改。
- 远端已更新：通过普通 Git 合并处理分歧，再重试，不自动变基或强推。

镜像仅用于客户端获取文件；Git 提交与推送使用原仓库地址。镜像缓存可能稍后更新，发布提交中会同时包含清单与对应文件。
