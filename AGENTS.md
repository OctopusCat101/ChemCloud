# ChemCloud Agent 指令

本仓库是 Chem 项目系列的唯一云端发布与跨项目管理入口。详细开发规范见
`docs/AGENT_HANDBOOK.md`，发布流程见 `docs/RELEASING.md`。

关键边界：

- 云端目录按“设备 / 固件 / loader 或模块名”组织，加载器与模块同级。
- `index.json` 必须保留所有目标、现有模块和精确校验信息；每次只更新所选项目，
  不能抹掉未选择的旧目标或模块。
- 检查 build manifest、签名 receipt、target/firmware SHA、长度、SHA-256、
  Chem build ID、watchface ID、模块版本和版本代码。
- 二进制改变必须使用新版本；同版本不同摘要拒绝发布。不得覆盖 collaborator 更新。
- ABMF、Glaze UI 和任何付费第三方资源禁止公开。ChemClient 使用的镜像仅用于读取。
- 公开记录不得包含私钥、固件、IDA 数据库、token、cookies、个人路径或构建缓存。

常规验证与发布：

```powershell
python workspace.py status
python workspace.py check cloud
python release.py --dry-run
python release.py <projects...>
```

发布前确认 ChemCloud 在 `main`、工作区干净、已 fetch、没有未推送提交。协作者有
新提交时使用 fast-forward 或普通 merge，不 reset、不 rebase 用户提交、不 force push。
网络失败保留本地提交，使用 `workspace.py push cloud` 恢复。

`workspace.py commit` 会暂存所选仓库全部未忽略改动，调用前必须逐个检查 status。
用户未明确要求提交或发布时，只构建和验证，不执行外部写操作。
