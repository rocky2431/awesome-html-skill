# awesome-html v1（WIP）

更新：2026-10-06。本文件是进度的唯一记录；`examples/progress.html` 是由 `scripts/track.py` 从它生成的只读看板。
调研结论见 [`docs/research.md`](../research.md)。

## 目标

做一个本地 HTML skill，不依赖 claude.ai 账号。

- 交付物是能离线打开的单个文件，可以直接发给合作方。
- 质量对标内置 artifact 页面。
- 用途：解释类内容、项目进度追踪、原型制作，以及报告、幻灯片、图表页等。

## 已定决策

| 日期 | 决策 | 谁定的 |
|---|---|---|
| 2026-10-06 | 不再用 Artifact 生成或发布 HTML，因为它跟 Claude 账号绑定，没法打包发给合作方 | owner |
| 2026-10-06 | 仓库名 `awesome-html-skill`，本地 git | owner |
| 2026-10-06 | 进度只记在仓库文本文件里，HTML 看板是由它生成的只读页面 | owner |
| 2026-10-06 | v1 跑通后替换 `answer-me-with-html`，在那之前两者并存 | owner |
| 2026-10-06 | 默认输出到项目下的 `html/<slug>.html`；在项目外或 `~/.claude` 里时，输出到 `~/awesome-html/` | owner（后半句由 agent 补充） |
| 2026-10-06 | 按公开仓库准备：第三方只取有许可的部分，写 NOTICE，内置 skill 只借原则、自己重写 | owner |
| 2026-10-06 | 规范冲突的取舍：文字用由调色板推导出的近黑色；标题用句首大写；不用逐段滚动入场动画 | owner |
| 2026-10-06 | skill 名 `awesome-html`，与仓库名一致 | agent |
| 2026-10-06 | 一个 skill，按页型拆参考文档，不拆成多个 skill | agent（owner 已认可方案） |
| 2026-10-06 | v1 只内置 Chart.js；uPlot、reveal.js 等真需要时再说 | agent |
| 2026-10-06 | 检查脚本只用 Python 标准库，通过 `--remote-debugging-pipe` 驱动本机 Chrome | agent |
| 2026-10-06 | 上线四步（提交、安装、改规则、停用 answer-me-with-html）全部执行，并建远程仓库推送 | owner |
| 2026-10-06 | 远程仓库先建成私有；改公开只需 `gh repo edit --visibility public` | agent |

## 进度

### 调研与方案

- [完成] 4 路调研：解释类、设计类、打包/幻灯片、内置 artifact skill。证据：`docs/research.md`
- [完成] 方案和 6 项决策由 owner 确认。证据：见上方决策表

### 核心脚本

- [完成] `check.py`：静态扫描外部引用 + 屏蔽 DNS 后用 Chrome 渲染，400/1280 宽度 × 浅色/深色截图。证据：`tests/test_scripts.py` 浏览器测试
- [完成] `inline.py`：把本地 JS/CSS/字体/图片内联成单文件，可重复运行。证据：测试覆盖幂等和文件缺失
- [完成] Chart.js 4.5.1 锁定版本内置。证据：tarball 的 sha512 与 npm registry 一致

### Skill 内容

- [完成] SKILL.md + 7 份参考文档：设计、解释、追踪、原型、幻灯片、图表、交付清单。证据：`tests/check_package.py` 校验 SKILL.md 引用的文件都存在
- [完成] 四个模板：通用骨架、原型、进度看板、幻灯片。证据：check.py 全部通过，截图已看过

### 打包

- [完成] 4 个宿主的 manifest + Claude/Codex marketplace。证据：`tests/check_package.py` 通过
- [完成] LICENSE（MIT）和 NOTICE（第三方来源署名）。证据：仓库根目录的 LICENSE 和 NOTICE
- [完成] README（中英文）。证据：README.md、README.zh-CN.md

### 实测（v1 完成标准）

- [完成] 解释页：由独立子代理只按 skill 文档完成。证据：`examples/how-it-works.html`，check.py 通过
- [完成] 进度看板：由本文件生成。证据：`examples/progress.html`，由 track.py 生成，check.py 通过
- [完成] 可点击原型：由独立子代理只按 skill 文档完成。证据：`examples/page-library-prototype.html`，check.py 通过 9 个状态 × 4 次渲染，子代理脚本点击验证 29 项断言

### 按实测反馈修订

- [完成] check.py 截图按 1200px 分块，长页面不再被静默截断；超过 15 块时明确警告。证据：浏览器测试
- [完成] check.py 的 fragment 名转义成安全文件名；报告被 `overflow: hidden` 裁掉的内容和区块内部滚动。证据：浏览器测试
- [完成] 新增 `track.py`：按约定的 Markdown 格式生成或更新看板，不再靠猜。证据：5 个 TrackTest
- [完成] 新增原型模板：带参数的 hash 路由，每个状态都有 URL，评审条放在正常流里。证据：check.py 渲染 3 个状态通过
- [完成] 参考文档按 3 份卡壳记录修订：设计力度、中文标题、窄屏表格、图解宽度、路径隐私、焦点、动效。证据：第二轮复测中这些点没有再出现
- [完成] 第二轮复测：独立子代理按修订后的 skill 重做解释页，并新做一份幻灯片。证据：`examples/how-it-works.html`、`examples/intro-deck.html`，check.py 通过

### 第二轮修订

- [完成] 修复模板里 `.stack` 类名撞车：桌面端三列以上表格的表头会错位。证据：改名为 `table.stacked`，资源测试通过
- [完成] check.py 指出幻灯片里超出的元素和距离，区分伸进留白（!）和超出画布（✗）。证据：浏览器测试
- [完成] check.py 在同一截图目录里重跑时，标出和上次完全相同的分块，并清掉多余的旧分块。证据：浏览器测试
- [完成] 幻灯片模板：列表符号对齐页边距、中文行高、中文标题不从词中间断开。证据：中文样张在 1280 宽度渲染，截图已看过
- [完成] 文档：幻灯片用 1280 宽度检查，引用写文件加函数名而不是行号，同一系列页面沿用配色，中文字数上限。证据：仅结构检查（check_package.py），尚未复测

### 上线（owner 已授权，2026-10-06）

- [完成] 首次 git 提交。证据：提交 f98b07c
- [完成] 安装到本机的 Claude Code。证据：`claude plugin list` 显示 awesome-html@rocky-awesome-html 0.1.0，user 范围，已启用
- [完成] 把 `~/.claude/CLAUDE.md` 的 `<html_pages>` 规则改为指向 awesome-html。证据：该段已改；`~/.claude` 是公开仓库，这处改动未提交
- [完成] 停用 `answer-me-with-html`。证据：`claude plugin list` 显示 enabled=false；用 `claude plugin enable` 可恢复
- [完成] 远程仓库（私有）并推送。证据：https://github.com/rocky2431/awesome-html-skill

## 还没做

- 没有配色校验器（对比度 + 色盲区分度）。参考文档里只有文字规则。
- 浏览器检查依赖 macOS/Linux 和本机 Chrome；Windows 上只跑静态扫描。
- check.py 只渲染页面加载后的状态，不会自动点击；toast、加载中这类瞬时状态截不到。原型这次的点击验证是子代理自己写的脚本。
- 原型模板还没有经过独立子代理的复测。
- 幻灯片的键盘、点击、滑动翻页和打印成 PDF 没有自动验证。
- 注册表里的 install 数没有复核。
