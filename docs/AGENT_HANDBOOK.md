# Chem 项目系列 Agent 开发手册

本文件是整个 Chem 项目系列的权威 Agent 开发规范。所有源码仓库根目录的
`AGENTS.md` 都指向本文件，并补充该仓库的最小上下文。若工具无法读取兄弟仓库，
应继续遵循所在仓库的 `AGENTS.md`、`README.md`、`docs/BUILD.md` 和发布文档。

## 1. 指令优先级与工作方式

发生冲突时按以下顺序判断：

1. 用户在当前任务中的明确要求。
2. 当前仓库更近的 `AGENTS.md`。
3. 本手册。
4. 当前 `README.md`、`docs/BUILD.md`、接口文档和发布文档。
5. 带日期的进度记录、事故记录和逆向证据。
6. 历史提交与旧说明。

当前代码、测试、配置和实测结果优先于过时文字。带日期的历史文档用于追溯原因，
不能自动视为当前行为；不得因为旧文档写着某个版本已通过，就跳过重新验证。

Agent 应先理解现有实现，再修改代码：

- 查看 `git status --short --branch` 和最近提交。
- 阅读仓库入口、构建文件、相关协议/ABI、测试和最近一次目标记录。
- 查找是否已有相同逻辑、同类修复或废弃分支，优先复用已有边界。
- 明确本次要改变的行为、受影响的设备/固件和验证层级。
- 保持修改范围小而完整，避免格式化整个文件、无关改名和顺手重构。
- 工作区已有的新增、删除和修改默认属于用户。不得用 `git reset --hard`、
  `git checkout --`、`git clean` 或批量覆盖来清理。
- 任务需要外部写操作时，仅在用户明确要求“提交”“发布”“推送”等动作后执行。

完成任务前必须回查用户目标，确认正常入口可用、错误路径有处理、旧数据仍能读取、
产物与源码一致，并准确说明哪些检查通过、哪些仍需真机验证。

## 2. 项目系列与职责边界

各仓库保持独立 Git 历史，不以内嵌 Git 仓库或复制源码的方式混在一起。

| 项目 | 权威职责 | 不应承担 |
| --- | --- | --- |
| `Chem` | Supervisor、原生管理器、SDK、目标 ABI、ELF 加载器、安装表盘模板、签包工具 | 播放器业务、资源包内容、跨项目发布脚本 |
| `ChemClient` | AstroBox 插件、设备发现、协议客户端、模块安装/管理、NoirMusic/Magic 内容上传器 | 固件加载器实现、模块业务 UI |
| `NoirMusic` | 蓝牙音频业务、播放器状态、原生音乐 UI、音乐导入协议 | 通用模块管理、云端发布 |
| `Magic` | 原生资源包管理、图标/字体/日历/背景替换、资源格式与包工具 | Chem 通用管理器、付费资源公开发布 |
| `ChemCloud` | 云端清单、已构建产物、统一构建/发布、跨仓库状态与提交工具 | 承载各项目的日常源码或私有构建缓存 |

跨仓库路径由 `ChemCloud/projects.toml` 管理。新机器可通过被忽略的
`projects.local.toml` 覆盖路径。源码和默认构建不得写入维护者的绝对路径，
也不得自动搜索下载目录、桌面、旧参考工程或外部应用的源码。

ChemCloud 是发布目录和跨仓库工具的家。上传工具、云清单同步和跨项目管理应留在
ChemCloud；业务项目只保留自己的构建、测试和打包入口。

## 3. 产品身份和兼容标识

面向用户的名称固定为：

- `Chem`：框架、安装器和模块管理器。
- `ChemClient`：桌面/手机客户端插件。
- `NoirMusic`：音乐模块。
- `Magic`：资源包管理模块。

产品 UI、文档、版本名、文件名和发布描述必须使用这些名称。不得在 Chem 项目中
加入旧参考项目的显示文本、文件名后缀、配置模板或安装链路。

以下标识是兼容 ABI 或已存在的数据身份，必须保留：

- `chem_*` C/Rust ABI、`chem-*` Cargo 包、`/dev/chem`、`/dev/chem_audio`。
- `/chem/install`、`/data/chem`、`com.chem.*`、`.chem` 包格式和 CMI1/CMO1 魔数。
- 模块 ID `bluetooth_audio`、`com.chem.magic`、`com.chem.music`。
- 现有签名 key ID、key role、公钥路径和已安装用户数据路径。

这些兼容标识不是产品展示名。修改它们必须同时提供迁移、兼容读取、回滚和
设备端验证方案。第三方许可、NOTICE 和逆向证据可以保留必要的上游归属。

## 4. 当前精确目标

一个 target ID 只对应一个固件。构建成功、静态分析、模拟器通过和真机证明是
四个不同层级。

| 目标 | 设备身份 | 固件 | 固件 SHA-256 | 显示与 UI |
| --- | --- | --- | --- | --- |
| `xiaomi-band-9-3.1.35` | `M2346B1`、`miwear.watch.n66tc`、`n66tc`、`N66TC`、`xiaomi.watch.n66`、`M2345B1` | 3.1.35 | `03e838857f68a98688173053c19990571c44a561cbb90d92a7fa798c85a32522` | 192×490，LVGL v8 |
| `xiaomi-band-10-nfc-3.1.28` | `o66nfc`、`O66NFC`、`miwear.watch.o66nfc`、`xiaomi.watch.o66nfc`、`M2456B1`、`M2457B1` | 3.1.28 | `fb726472416e99ba11d1c20ce8f0d4f0831a6e9a673d63bb5918e2c3921d8845` | 212×520，LVGL v9 |

`M2456B1` 与 `M2457B1` 共用上述 NFC 固件，可以共享精确目标身份和产物。
“小米手环 10”普通版、NFC、Pro 和其他固件不能因为名称相似而混用。

Band 9 与 Band 10 NFC 的图片头、颜色格式、页面 ABI、Launcher 布局、服务槽、
资源尺寸和回调生命周期不同。不得交叉复制地址、对象偏移、资源 BIN 或 UI 常量。

新增或升级固件时必须创建独立 target pack。旧 target 只能提供定位线索，所有地址、
类型、所有权、线程上下文和回调必须在新固件独立恢复。

## 5. 工具链与环境

常规环境：

- Python 3.11+，在 Windows 优先使用 Python 3.12。
- Rust stable 与所需的 nightly 工具链。
- Clang/LLD、`llvm-ar`、OpenSSL、Git Bash。
- ARM 目标：`thumbv8m.main-none-eabi`。
- ChemClient：`wasm32-wasip2`、`wit-bindgen 0.60.0`、兼容 Wasmtime 48 的
  `wasm-component-ld >= 0.5.27`。
- AstroBox 2.2.6，API 4 / WASI 2，使用新版 Queue 和 Watchface 接口。
- 固件仿真需要 Python `unicorn`、`lupa`、`pyelftools` 等显式测试依赖。

本机工具路径放在被忽略的 `build.local.toml`、`projects.local.toml` 或环境变量中。
不要把个人绝对路径、密钥、日志、固件、IDA 数据库和测试运行时提交到源码仓库。

Windows 上遇到路径、换行或工具找不到时，先确认是调用环境问题。不要通过大规模
换行转换、重写脚本或复制项目来规避。

## 6. 构建产物与目录卫生

- 原始源码、手写后端、schema、测试和必要文档进入 Git。
- 中间对象、日志、缓存、固件、IDA 数据库和临时下载进入被忽略的 `out/`。
- Chem/NoirMusic/Magic 的最终 `.face`、`.chem`、`.magic` 通常进入被忽略的
  `dist/`，由 ChemCloud 发布副本。
- ChemClient 的 `dist/manifest.json`、`dist/chemclient.wasm`、`dist/icon.png`
  和声明的资源是插件发布内容，需要与源码同版本提交；`.abp` 用于本地安装。
- 不把生成目录作为下一次构建的源码输入。
- 清理时必须验证解析后的目标位于当前项目，不使用项目根、用户目录、磁盘根或
  未解析通配符做递归删除。

## 7. Chem 架构和安全不变量

Chem 至少包含三个独立边界：

1. 主机工具：分析、目标生成、构建、验证、签名和打包。
2. 设备控制面：Supervisor、原生管理器、存储、生命周期和恢复。
3. 模块运行时：目标后端、资源追踪、callback 防护和实际业务代码。

关键规则：

- 默认拒绝未知固件、未知重定位、未批准地址、错误目标和损坏签名。
- 签名通过后仍必须检查 exact target、固件摘要、能力、生命周期和 anti-rollback。
- `/dev/chem` 与 Supervisor 在同一地址空间，不是安全沙箱。
- 安装后的模块默认禁用；启用、停用、删除和更新都按 next-boot intent 处理。
- 已加载的常驻模块不能在本次运行中热卸载。更新后重启，再手动运行新版安装器。
- 每个失败事务必须保持旧 registry 或旧 generation 可用。
- `safe mode` 只允许查询、诊断、next-boot 修改、回退和移除；禁止安装、启用或激活代码。
- safe mode 恢复先持久化，再重启生效。未完成的试启动再次失败必须回到 safe mode。
- `loader init returned` 不等于模块 READY。必须完成 identity、launcher、app 和 UI 注册。
- 资源释放、缓存退休和对象删除必须等固件不再引用；无法证明时 fail-closed。

ABI 2、UI2 公共接口和 14 组通用服务表存在，不等于每个设备后端都已完整或
实机验证。LOG、FS、TIME、MEM、NOTIFY、HOOK、SYSTEM、BLUETOOTH、KV、
HAPTICS、DISPLAY、BUS、CONNECT、LAUNCHER 必须按 target capability 检查；
不得用其他目标或模拟器通过替代当前设备证据。包格式、线协议和客户端链路尚未
完全统一的部分，要保持现有可工作的闭环，不能在只补枚举或头文件后宣称完成迁移。

当前启动策略是手动运行 Chem 安装器。新安装器会清理旧自启动启动脚本，同时保留
模块、配置、曲库和资源包。不得重新加入自动修改固件启动区、自动自启动入口或无提示
重启。若设备上仍是旧版自启动，先关闭它，再重启并运行新版安装器。

## 8. 协议、安装器和连接链路

### 8.1 模块包

`.chem` 是已签名模块包。设备侧和客户端都必须验证：

- 包路径规范，无绝对路径、`..`、NUL、重复 entry 或链接。
- module ID、target ID、firmware SHA-256、version、ELF 长度与摘要。
- Ed25519 receipt、资源长度和资源 SHA-256。
- 文件大小、文件数量、写入偏移和 CRC。

模块安装不经过表盘。ChemClient 验证后会直接走 `com.chem.manager` 原生导入链路。

### 8.2 批量传输

- 文件 bulk 写入使用 16 KiB 分片。
- CPC2 控制 payload 保持 512 字节上限。
- 12 字节 ID/op 轮询获取缓存应答；退避约 25/50/100 ms，控制等待可到 250 ms。
- 一秒内没有结果可重发完整请求，但必须保留 request ID 和重复抑制。
- request ID 持久分段预留；进度 UI 约 400 ms 节流一次。
- 超时按照最后有效进展刷新，不按整个任务起点硬切。
- BLE callback、UI owner 或 receive callback 中不得执行长时间文件 I/O、编码或解包。

### 8.3 连接发现

插件启动后自动检查宿主连接的设备并读取精确设备身份，再探测 Chem 服务。连接不应
依赖当前显示的是哪个表盘。连接成功后隐藏连接面板，直接展示模块列表。

一次只保留一个刷新入口。刷新期间禁用依赖旧状态的模块操作，避免缓存列表可点击。
本地 `.chem` 导入在云端清单不可用时应继续可用；身份未知时仍必须 fail-closed。

连接探测不能在忙碌门之前无条件执行。单次设备列表为空、宿主查询超时或手机切后台
不能立即当成物理断开。任务进行中应以最后一次有效进展计算超时，并保留有限宽限、
多次确认和 epoch 校验。压缩、下载、文件选择等长任务期间，宿主状态查询失败应
短暂重试，不得因此取消任务或删除已经下载完成的文件。

### 8.4 Chem 安装器

Chem 安装器是 `.face`，通过用户点击安装按钮触发，不在启动时自动安装：

1. 查询精确目标对应的云端清单和已安装表盘。
2. 已安装相同 face ID 时直接切换，不重复上传。
3. 未安装时下载、校验长度和 SHA-256，再交给 AstroBox Queue。
4. Queue 成功后切换表盘；失败时保留明确错误和重试入口。
5. 用户在手环点击「启动」，客户端等待 Chem 服务真实响应。

Chem 二进制变化时必须使用新的 build ID 和 watchface ID。不同目标可以复用相同
watchface ID 内容时也必须经过发布器验证，不手动覆盖云端同版本。

## 9. UI 和交互规范

整体保持黑底的 Material Design 3 视觉：

- ChemClient：黑底、浅薄荷绿主色、中性灰文字层级。
- NoirMusic：黑底、浅薄荷绿、圆形控制面。
- Magic：紫色主题、圆形图标、原生列表与详情。
- Chem 手环管理器：深色、简洁列表、固定几何和清晰错误。

模块主页只显示模块名和必要控件。不得恢复设备页、多步骤连接向导、常驻大面板、
重复刷新按钮或展开式管理区域。

模块行固定边界：

- 点击名称进入该模块独立的上传器或详情，不把其他功能混在列表行。
- 右侧依次为开关、删除和更新等纯图标控件。
- 图标保持固定尺寸，使用静态 SVG/原生图片；禁止悬浮时动画、缩放、闪烁、旋转或位置漂移。
- 开关是主控制。删除和更新与开关同排，空间不足时才可整体换行。
- 更新按钮始终占位；无更新时禁用，避免刷新后其他控件移动。
- 所有图标必须有 `aria-label` 和可见文本 tooltip/状态。

安装器更新卡片：

- 标题保持单行；「安装」按钮固定约 80 px。
- 窄屏允许按钮换到下一行，进度条始终在标题和按钮之后。
- 进度只在自己的卡片或模块下方显示，不汇聚成全局进度条。

状态和布局：

- 异步提示使用 `State::notice(NoticeOwner, message)`，任务开始时确定归属。
- 原生节点 key 使用页面作用域和业务 ID；禁止使用列表索引、可重复显示名或裸事件名。
- 切页、重连、换任务必须更新 page generation/epoch，旧页事件不得影响新页。
- 条件区块、进度条和列表重排不得复用其他卡片节点或改变控件身份。
- 新增布局包装函数若依赖调用位置，使用 `#[track_caller]`。
- 窄屏使用明确 flex 换行、`min-width: 0` 和固定控件尺寸，避免标题挤成竖排。
- 不显示内部 stage、检查版本文件、无意义诊断或会让文案乱飞的重复错误。
- 面向用户使用简洁中文；原始错误码保留在可诊断位置，不把不同层级的同值错误混淆。

ChemClient UI 应至少检查 240、320、390 和 768 CSS 像素宽度。使用
`CHEM_UI_FIXTURES` 导出节点树，再用 Playwright 检查单行标题、按钮宽度、重叠、
越界、进度位置和页面切换。浏览器预览不替代 Astro 手机 WebView 与蓝牙实机测试。

## 10. NoirMusic 领域规则

NoirMusic 维持 6 秒目标预缓冲，但所有分配必须有界，并能按设备可用内存退让。
预缓冲时间不是解决“开播前几秒无声”和“界面刷新后变流畅”的通用修复。处理音频
问题时必须区分：

- 歌曲从第 0 秒开始，只是耳机延迟出声。
- 歌曲音频样本已被跳过。
- 解码/送流在起播时欠载。
- UI 页面刷新触发了新的 allocator/owner warm-up。

不得只增加缓存、修改预缓冲时间或加固定 sleep 来掩盖根因。修复要落在音频时钟、
首帧提交、owner 调度、解码/送流水位或电源状态的真实问题处。

导入协议：

- 手机到模块为 protobuf type20/id8，模块回复 id9。
- 原生应答使用 CMI1/CMO1；当前 ABI 和魔数不能随意改名。
- 音乐与附件使用 begin/chunk/commit、顺序 offset、CRC 和耐久 ACK。
- 接受 MP3 和 NSB1 固定帧 SBC；未实现 Opus/CELT、AMZ1 或通用 Ogg。
- 封面是 NCV1，必须为 160×160 BGRA8888 并携带主题色；歌词 UTF-8 LRC
  或网易云 JSON，最大 96 KiB。
- 旧 MP3 曲库和已有歌曲必须继续可读取。

播放与生命周期：

- `/dev/chem_audio` 一次只允许一个 writer。
- START 返回表示请求已接受；进入 PLAYING 必须查询状态。
- 蓝牙 callback 不承担长时间解码、文件读取、压缩或 UI 工作。
- Audio producer、文件 worker、播放器状态和 UI owner 必须串行且有界。
- 暂停保留输入；停止、关闭和换歌释放不需要的解码器和 PCM 缓冲。
- 不通过强制常亮、篡改系统 PM、跨 owner UI 同步等待或全局资源劫持保活。

导入 UI：

- 任务进度和错误始终显示在对应歌曲或对应模块卡片的父容器下。
- 下载、压缩、上传和提交阶段使用同一业务 ID；任务完成不能跳到其他页面。
- NetEase 下载必须有独立进度和明确超时，不能只显示“正在下载”。
- 不完整验证时不得承诺网易云服务端限制、速度或账号可用性。

## 11. Magic 领域规则

`.chem` 安装 Magic 模块，`.magic` 导入资源包，两者职责不同。

资源包约束：

- MGP1 包单文件不超过 16 MiB、最多 256 个文件、最多保存 16 个包。
- 每条映射使用精确源路径和目标路径；目录映射及 `@system` 必须经过验证。
- 导入、路径检查、CRC、重传、解包和最终配置必须支持失败回退。
- 一次只启用一个资源包；关闭后恢复系统资源。
- 列表点击进入详情，详情保留紫色开关和删除确认；不恢复外侧多按钮面板。
- 删除当前包先关闭。失败保留资源包与详情；成功后返回列表。
- 已加载的字体/图片可能仍被固件引用，删除文件延迟到下次重启回收。
- 切换或删除资源包不能重置独立背景设置。

资源格式：

- Band 9 使用 LVGL v8 图片头、RGB565、192×490 原生资源与对应页面 ABI。
- Band 10 NFC 使用 LVGL v9 图片头、RGB565/需要的 RGB888 设备路径、212×520
  和对应 0x80 页面/0x40 app 布局。
- 不能通过只改版本号或图片头把 Band 9 资源转成 NFC。
- 融合控制中心与小组件是不同入口。应用列表入口要使用真实注册路径，例如米家
  `mijia/mijia1.bin` 与融合入口 `share/share.bin`。

背景模糊：

- 使用单次静态采样，不逐帧截图，不使用全屏强刷。
- 模糊图固定在屏幕坐标；绘制区域取屏幕、面板可见区域和刷新区域交集。
- 应用列表、通知菜单、控制中心和小组件各自独立开关。
- 快速拉出和收回都要覆盖边缘 clip、局部刷新、不透明子节点和共享边界行。
- 背景修复必须沿用原生截图、GPU fence、缓存同步和对象删除保护。
- 不得把整张背景直接贴到滚动组件，导致内容移动或黑边。

第三方资源：

- ABMF 与 Glaze UI 是付费资源，只能保留在本地/私有开发环境。
- 它们不得进入公开 ChemCloud、公开 release、公开示例或插件下载列表。
- 自有 `VioletCalendar.magic` 可以作为公开最小示例。

## 12. 固件逆向和目标适配

用户明确指定使用 IDA MCP 时，直接通过 MCP 的只读接口分析，不切换到 CLI。
所有结论必须绑定：

- 固件文件与 SHA-256。
- 对应 IDA 数据库身份。
- firmware version/build string。
- 设备型号、UI/LVGL 版本和 loader/capability。
- 函数 even entry、Thumb callable odd bit、原型、上下文和所有权。
- evidence ID、静态证据、主机测试、设备探针和最终批准状态。

证据状态至少区分：

`CANDIDATE`、`STATIC_RECOVERED`、`STATIC_CONFIRMED`、`HOST_TESTED`、
`DEVICE_PROBED`、`DEVICE_PROVEN`、`RESTRICTED`、`FORBIDDEN`、`WITHDRAWN`。

只允许由 schema、验证任务和独立审核提升状态。LLM 输出只能生成假设或带证据候选。

旧地址扫描只能用于寻找新候选。必须检查：

- 函数边界和指令集状态。
- callers/callees、xrefs、字符串和结构访问。
- 参数宽度、返回值、调用上下文、锁和阻塞行为。
- 参数、返回值、callback 和全局对象的所有权。
- 同一函数是否被 inline、拆分、删除或更换 dispatcher。

Band 9 AP 的常见加载基址是 `0x0C100000`，只读别名常见于 `0x2C100000`；
这只能帮助查找 literal pointer，不能免除逐 target 重新验证。Thumb 函数必须
保存 even entry 与 odd callable，不能在手写业务代码里随手补 `+1`。

禁止：

- 复制相邻固件地址或固定 offset。
- 把字节特征命中直接变成 callable。
- 在设备运行时扫描最相似函数并跳转。
- 自动 patch binary、修改权威 IDB 或写入设备内存。
- 找不到原型时为“先编译通过”猜测签名。

手工业务代码只能引用 generated constants/wrapper。generated 文件不得直接编辑；
应修改 symbol/type/evidence records 后重新生成并做逐字节稳定检查。

## 13. 并发、缓存和性能规则

- 每个异步操作绑定 device address、connection epoch、task ID 和 owner。
- 重连、切页、取消或换目标后到达的结果必须丢弃并清理临时文件。
- 同一 transport 只能有一个写入 owner；不得让控制轮询与 upload 同时推进 offset。
- 缓存必须有明确所有权、容量、失效条件和释放点。
- 不保留永久 timer、subscription、WASI future 或跨 epoch waiter。
- 处理大文件时使用流式读写和 bounded window，避免整文件分配。
- 网络/蓝牙超时应基于最后进展时间，并允许短写入、重试和取消。
- 性能问题先测量阶段耗时，再优化。禁止用固定 UI 延迟、隐藏进度或降低安全门禁掩盖慢链路。
- 视觉滚动/模糊优化必须保持像素输出，不增加每帧全屏复制或重复 snapshot。

## 14. 错误处理与诊断

- 错误必须说明动作、真实结果和用户下一步，不把“已入队”写成“已安装”。
- 错误码按协议层解释。不能把 service、Supervisor、registry 和 Flash 的同值错误混用。
- 本地可重试问题提供单一刷新/重试入口；安全或身份不匹配继续 fail-closed。
- 临时失败保留可恢复状态。不得在超时、假断连或验证失败时删除已完成下载。
- 用户取消和真实设备断开要分开；取消必须可达终态，不永久卡在 busy。
- 日志不得包含 cookies、token、密钥、完整 URL query、私钥内容或账号凭据。

## 15. 构建与测试矩阵

### 15.1 Chem

```powershell
cargo build -p chem-cli --locked
.\build.ps1 check
.\build.ps1 payload -Target xiaomi-band-9-3.1.35
.\build.ps1 -Target xiaomi-band-9-3.1.35
python tools/build/build.py --project . --target xiaomi-band-10-nfc-3.1.28 face
cargo test --workspace
python scripts/check-repository.py
```

相关原生、Lua、ARM、FACE 和固件检查优先使用仓库已有脚本。当前 worktree 若正在
退役自启动，发布器中的旧 boot 测试项目应同步改为现行测试，不保留失效引用。

### 15.2 ChemClient

```powershell
cargo test --locked --target x86_64-pc-windows-msvc -- --test-threads=1
python build.py --abp
python tests/check_network_runtime.py --wasmtime <WASMTIME_48>
```

必须覆盖页面树身份、重复刷新、旧页事件、后台任务归属、窄屏布局和离线导入。

### 15.3 NoirMusic

```powershell
python scripts/configure.py --chem-root <Chem>
cargo test -p noirmusic-bluetooth -p noirmusic-player
python tests/check-stream-scheduling.py
.\build.ps1 check
.\build.ps1 -Target xiaomi-band-9-3.1.35
python scripts/check-repository.py
```

固件仿真通过 `NOIRMUSIC_TEST_FIRMWARE` 显式提供精确固件。

### 15.4 Magic

```powershell
python build.py
python build.py test
python build.py package --target xiaomi-band-9-3.1.35
python build.py package --target xiaomi-band-10-nfc-3.1.28
python tests/firmware_font_band9.py
python tests/firmware_calendar_band9.py
python tests/firmware_blur_band9.py
```

固件执行测试只模拟指定硬件叶子，不能写成 GPU、显示或实机已通过。

### 15.5 ChemCloud

```powershell
python workspace.py status
python workspace.py check cloud
python release.py --dry-run
```

测试和发布失败必须停止，保留源码与本地产物；不得自动 rollback、强推或覆盖同版本文件。

## 16. 提交规范

开始提交前：

1. 确认目标仓库、分支和 `origin`。
2. 查看 `git status`，区分本次修改与用户已有修改。
3. 查看 diff，运行 `git diff --check`。
4. 只暂存本次涉及的路径。若用户明确要求提交全部改动，仍需先检查是否混入私钥、
   固件、临时测试文件或无关工程。
5. 检查构建产物与源码版本一致。

提交信息使用动词开头，必要时带精确范围：

```text
Fix Chem installer card layout in narrow windows
Restore Chem installer delivery
fix(band10-nfc): register module launcher transactionally
docs: define project-series agent workflow
```

一个提交保持一个主要意图。不要提交纯换行、缓存或生成时间噪声。不要改写其他维护者
已推送的历史。

## 17. 同步、合并和推送

用户要求发布或推送前：

```powershell
git fetch origin
git status --short --branch
git rev-list --left-right --count HEAD...origin/main
```

若远端有更新：

- 无本地提交时可 fast-forward。
- 有本地提交时先检查双方 diff，使用普通 merge 保留协作历史。
- 不因冲突或网络失败执行 reset、force push 或删除本地提交。
- 推送后使用 `ls-remote` 或远端页面确认 `main` 指向新提交。

网络不稳定时，ChemCloud 的 `network_git()` 使用系统代理、HTTP/1.1、低速度超时和
自动重试。不要在脚本中打印认证 token。请求被代理重置时保留本地提交并重试。

批量工具允许：

```powershell
python workspace.py commit chem client -m "Improve connection handling"
python workspace.py push chem client
```

批量 `commit` 会暂存所选仓库全部未忽略修改，执行前必须逐个检查状态。

## 18. 版本和云端发布

- Chem 二进制改变时递增 build ID 和 watchface ID。
- 模块改变时递增 `Chem.toml` 的语义版本和 `build.toml` 的 version code。
- ChemClient 改变时同时更新 `Cargo.toml`、`Cargo.lock`、根 `manifest.json`、
  `dist/manifest.json` 和重新构建的 WASM。
- 同版本不同 SHA-256 一律拒绝。不得覆盖云端同版本文件。
- 先添加 loader，再发布模块；`chem-loader` 与 `NoirMusic`、`Magic` 在固件层级下同级。
- 每次只保留当前发布文件，清单必须包含 all existing targets 和未选择但已发布的旧模块。
- 发布前校验 build manifest、签名 receipt、精确 target、firmware hash、文件大小和摘要。

发布流程：

```powershell
python release.py <project...> --dry-run
python release.py <project...>
```

省略项目时使用现有已验证产物。`--skip-build` 只同步现有产物；`--no-push` 保留本地
发布提交。是否构建、提交和推送由用户要求决定，脚本不能自行扩大范围。

ChemClient 云端读取使用：

`https://gh-proxy.com/https://raw.githubusercontent.com/OctopusCat101/ChemCloud/main`

镜像仅用于客户端获取；Git fetch/push 使用原仓库 URL。镜像缓存可能延迟。

## 19. 私有数据与公开边界

严禁公开：

- 正式签名私钥及额外副本。
- 设备完整固件、`app.bin`、`vela_ap.bin`、OTA、IDA 数据库和崩溃转储。
- 测试账号、cookies、token、设备地址和个人路径。
- ABMF、Glaze UI 和其他付费第三方资源包。
- 含付费素材的预览、生成 BIN、构建中间目录或临时研究下载。

公开前检查 Git 历史和当前 tree。若敏感文件曾进入提交，不能只删除工作区文件；
需要报告并采用用户批准的清理方案。

## 20. 文档和证据写法

- 当前事实写进 README、BUILD、接口文档；日期记录只记录当时状态。
- 区分“已实现”“构建通过”“模拟通过”“用户确认”“真机逐项验证”。
- 记录精确固件、版本号、提交、文件长度、SHA-256 和验证范围。
- 新能力更新对应 CHANGELOG、target/capability evidence 和发布说明。
- 不把多个目标的项目状态合并成一句“全部完成”。
- 不以“预计”“应该可以”作为通过结论。

## 21. 完成检查

交付前逐项确认：

- 用户要求的正常入口已经调用新逻辑。
- 错误、取消、重试、重连和离线路径有明确终态。
- 旧数据、旧包和已安装模块的读取兼容性没有被无意破坏。
- 新增常量来自目标记录，不来自旧固件复制。
- UI 窄屏、刷新、切页和后台进度没有节点串页或控件漂移。
- 测试覆盖最可能回归的行为，不只是重复实现细节。
- 构建产物与 manifest/版本/摘要一致。
- `git diff --check` 通过，未提交无关文件、私密文件或付费资源。
- 最终说明中列出实际运行过的检查和仍待真机验证的部分。

任何未完成项必须明确写出。不得因为上下文压缩、时间、构建耗时或远端等待而把
未验证状态描述为完成。
