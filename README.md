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

发布仓库为 https://github.com/OctopusCat101/ChemCloud 。`repository.json` 和 ChemClient 的 `cloud.json` 已配置镜像根地址 `https://gh-proxy.com/https://raw.githubusercontent.com/OctopusCat101/ChemCloud/main`，目录和安装文件均经此镜像下载并校验 SHA-256。

当前发布：Chem 构建号 `0x26111301`、安装器 ID `913211301`、NoirMusic `0.4.58 / code90`，ABI 2.0。ChemClient 当前本地构建为 `1.7.20`，客户端插件需单独分发。

自动启动由固件 `rcS` 末尾触发，后台 worker 等待 8 秒并检查系统就绪。撤回亮屏自动注册：仅在完全熄屏时由后台 owner 推进管理器注册和模块恢复；亮屏、AOD 或异常屏幕状态暂停，最后观察到非熄屏后至少等待 3 秒再继续。用户报告此前亮屏注入与切表盘、渲染并发时可能重启，因此采用熄屏策略。

保留固件精确匹配、Flash 整块摘要与写后回读、低电量拒绝、Lua 引用清理校验、连续失败熔断、模块安全模式和启动后 60 秒加亮灭屏稳定观察。ARM 启动/Flash 回放 16 项和 Lua/启动资源测试 6 项通过；当前修订仍待实机验证，阶段前屏幕检查并非对整个固件渲染系统的全局互斥，首次 LVGL 引导的既有风险也未消除。

从旧版升级后，需在手环手动运行新版安装器以更新驻留资源，再将自动启动关闭后重新开启，迁移到较晚的启动入口。仅下载或更换安装器不会自动改写启动设置；已有失败记录和安全模式不会被升级静默清除。

发布流程：先构建 Chem 安装器和 NoirMusic 模块，再运行 `D:/Chem/scripts/publish-cloud.py`。脚本校验并同步本地安装器、模块与云端索引，不执行提交或推送。客户端每次连接检查或手动刷新均从云端获取清单，不再内置发布清单。每次发布新版加载器必须同时更新原生构建号和九位表盘 ID，避免把旧安装器认作最新。

连接后客户端先检查驻留服务，服务可用时直接显示模块列表。需要安装或更新安装器时显示安装按钮，仅在用户点击后加入 Astro 上传队列，检测实际安装完成后切换，等待用户在手环运行。Astro API 4 仅开放添加上传队列，没有开始上传和上传完成接口；如宿主没有自动开始，需在宿主队列开始上传。普通 `.chem` 模块不使用表盘上传队列。

ChemClient 1.7.1 修复设备识别：按标准 DeviceInfo 的固件字段 2、型号字段 4 匹配，不要求不存在的产品字段 5；索引补充 `miwear.watch.n66tc`。

ChemClient 1.7.2 与云端目录补齐 `M2346B1 / 3.1.35`。当前固件的设备信息初始化函数在 `factory.board.id=TC` 时返回该型号，不能将内部板号直接当作协议返回型号。


## 手动发布（PowerShell）

新版 Chem 发布前，先递增 `D:/Chem/manager/target/lvgl_v8/chem_manager_target_lvgl_v8.c` 中的构建号，以及 `D:/Chem/build.toml` 中的九位 `watchface_id`，然后构建、验证。只有 NoirMusic 代码发生变化时，才需要重新构建其模块。

```powershell
# 1. 构建并测试 Chem；已经完成且测试通过时可跳过
D:/python312/python.exe -X utf8 D:/Chem/tools/build/build.py --project D:/Chem face
D:/python312/python.exe -X utf8 D:/Chem/tests/tooling/test_boot_flash.py
D:/python312/python.exe -X utf8 D:/Chem/tests/tooling/test_boot_persistence.py

# 2. 先同步远端；有未提交修改时先处理，避免混入其他工作
Set-Location D:/ChemCloud
git status --short
git pull --ff-only origin main

# 3. 同步已验证的安装器、模块、大小和 SHA-256 到此仓库
D:/python312/python.exe -X utf8 D:/Chem/scripts/publish-cloud.py

# 4. 更新本 README 的当前版本和说明，检查清单差异
git diff -- index.json README.md
git diff --stat

# 5. 将安装文件与清单放在同一个提交中，再推送
git add -- index.json README.md xiaomi-band-9/3.1.35/chem-loader/Chem-Band9-3.1.35.face xiaomi-band-9/3.1.35/NoirMusic/NoirMusic-Band9-3.1.35.chem
git commit -m "Publish Chem build <构建号>"
git push origin main
```

此脚本当前针对手环 9 / 3.1.35，生成包含 Chem 加载器和 NoirMusic 的索引。不要在脚本仍为单目标结构时手工增加其他目标后直接覆盖发布。签名密钥、固件镜像、构建中间文件不上传；发布只需索引、对应安装文件及说明。镜像可能有缓存，推送后在客户端刷新并确认版本；无需因单独更新 Chem 而重建客户端插件。
