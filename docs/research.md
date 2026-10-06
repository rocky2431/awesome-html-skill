# 调研结论：本地 HTML skill 的现有方案

调研日期：2026-10-06。由 4 个子代理完成，数据来自 `gh api`、`npm view`、jsdelivr，以及本机插件缓存。
许可证和 star 数已经抽查复核；install 数直接取自 `npx skills find` 注册表，没有复核。
各来源具体借鉴了什么、用在哪里，见仓库根目录的 `NOTICE`。

## 采用或借鉴

| 来源 | Stars | 许可 | 离线 | 借什么 |
|---|---|---|---|---|
| anthropics/skills `frontend-design` | 179,853（仓库） | Apache-2.0 | 纯文字 | **设计主干**。71 行，不绑定框架。借"先定 4–6 个颜色"、AI 默认审美的反例清单、"结构即信息"。 |
| vercel-labs/web-interface-guidelines | 942 | MIT | 清单 | **交付前清单**。191 行。去掉 React 专属条目，锁定版本后内置。原版每次运行都从远程拉取，我们不这样做。 |
| warpdotdev/common-skills `readout` | 604 | MIT | 是 | **离线契约和检查**。规则是不引用任何外部 URL、只用系统字体；交付前用 `html.parser` 扫描，外部引用必须为 0。 |
| nicobailon/visual-explainer | 10,270 | MIT | 否（用了 Google Fonts） | **内容规则**。一张图只讲一个论点、画机制而不是只写名字、每条箭头标动词。要求 390px 和 1280px 宽度下都不溢出。`history.replaceState` 在 `file://` 下会抛错，要包 try/catch。 |
| plannotator/effective-html | 3,544 | MIT | 是（字体用 data URI 内联） | **按页型拆分**：html-prototype、html-wireframe、html-plan、html-diagram。**原创性检查**："把主题换成相邻话题，这套视觉还成立吗？" |
| tt-a1i/archify | 78,378 | MIT | 是（字体用 base64 内联） | **机械检查 + 诚实回执**："没做过的视觉检查不许声称做过"。它的代码有几百 KB，不搬。 |
| zarazhangrui/frontend-slides | 30,202 | MIT | 否（要求 web 字体） | **幻灯片的固定 1920×1080 画布，整体缩放到屏幕**。只用 `scrollHeight` 检查发现不了面板互相遮挡。给 3 个风格预览，而不是直接问用户的审美偏好。 |
| pbakaus/impeccable | 77,291 | Apache-2.0 | — | 只借 `craft-floor.md` 和 `mode-read.md` 的思路，例如阅读栏宽 60–75 字符。 |
| 内置 `artifact-design` / `artifact-diagramming` / `dataviz` | — | 没有许可文件 | 大部分可移植 | 只借原则，用自己的话重写。`dataviz` 的配色校验器要用公开算法（OKLab、Machado 2009 色盲模拟、WCAG 对比度）自己写，阈值自己定。 |

## 不采用

- `answer-me-with-html`（MIT）：组件固定，没有真正的图表，主题也固定。它的页面本来就能离线。新 skill 跑通之前先保留。
- `web-artifacts-builder`：目前是坏的。issue #1362 是 pnpm ≥10.1 下直接中止；#1893 是依赖没锁版本导致 React 报错。另外 `html-inline` 不处理 CSS 里的 `url()`，字体不会被内联。
- `lavish`：发遥测，README 没说明；指令运行时从没锁版本的 npm 包拉取。
- `impeccable` 的程序部分：首次运行会下载二进制，默认开遥测，还会往 `.claude/settings.local.json` 写 hook。
- `taste-skill`：默认 React 加 Tailwind，引用远程图片，内容自相矛盾。
- `ui-ux-pro-max`：配色数据正好是别家禁止的那类默认配色，还带 Google Fonts 链接。
- `plannotator-visual-explainer`：让 agent 自己去装别的 skill。
- `superdesign`：云端 SaaS，需要登录。
- `theme-factory`：只有 Linux 字体，没有深色模式。
- `canvas-design`：输出 PNG/PDF，文中还编造了一句用户原话。
- `baoyu-*`：页面依赖网络。
- `hyperframes`：做视频的，超出范围。

## 图表库内联的体积

数字来自 jsdelivr，是本地文件的原始大小，没有 gzip。

| 方案 | 体积 | 用途 |
|---|---|---|
| 手写 SVG | 0 | 少量静态图 |
| uPlot 1.6.32 | 51 KB | 时间序列、大数据量 |
| Chart.js 4.5.1 | 209 KB | 通用图表，自带 tooltip 和图例 |
| ECharts 6.1.0 | 500 KB–1.1 MB | 只用于地图、桑基图这类 |
| Mermaid 12.1.0 | 5.5 MB | **不内联**，改成手画 SVG |

已经验证：把 Chart.js 和 uPlot 内联进一个 262 KB 的文件，用无头 Chrome 以 `file://` 打开，同时屏蔽 DNS，两个图表都能正常绘制。
