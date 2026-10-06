# Awesome HTML

[English](README.md)

一个 agent skill，用来把 HTML 页面做成**一个自包含的文件**：任何浏览器都能离线打开，不需要账号，也不依赖托管服务，可以原样发给任何人。

适用场景：

- **解释页和报告**：讲清楚一个系统怎么运作、一个 bug 为什么出现、几个方案该选哪个。
- **进度看板**：从仓库里的文本文件生成的只读看板。
- **可点击原型和线框图**：多屏、真实流程，示例数据都会标明。
- **幻灯片**：固定 16:9 画布，支持键盘翻页，可以打印成 PDF。
- **图表**：手写 SVG；读者需要悬停看数值时，用内置的 Chart.js。

## 为什么做它

托管的 artifact 页面存在账号里，没法把文件交给合作方。模板渲染器能生成文件，但每个页面都长得一样。这个 skill 保留了设计上的讲究，页面可以自由编写，最后再验证这个文件能独立打开。

## 一个页面是怎么做出来的

1. **契约**：每个页面都是一个 `.html` 文件，CSS、JS、图片、字体、图解全部在文件里。不用 CDN，不用网络字体，不引用远程图片。
2. **设计**：agent 先把这个页面的配色和字体写成 `:root` 上的 token，对照页面主题检查一遍，然后从起步模板开始做：`assets/base.html`、`prototype.html` 或 `deck.html`。进度看板则由 `scripts/track.py` 从 Markdown 文件生成。
3. **内联**：`scripts/inline.py` 把页面引用的本地脚本、样式、字体和图片都写进文件里。`vendor/chart.umd.min.js` 会指向内置的 Chart.js 4.5.1。
4. **检查**：`scripts/check.py` 先扫描页面标记，找出所有要从文件外加载的东西。然后用本机 Chrome 在屏蔽 DNS 的状态下渲染页面，宽度 400px 和 1280px、浅色和深色各一次。它会报告对外请求、JS 错误、横向滚动、被裁掉的幻灯片内容，以及被 `overflow: hidden` 裁掉的内容。每次渲染都按 1200px 高度切成多张截图保存，供 agent 逐张查看。

三个脚本都只用 Python 标准库。浏览器检查需要 macOS 或 Linux，以及 Chrome、Chromium 或 Edge；用别的浏览器时，用 `AWESOME_HTML_CHROME` 指定可执行文件。条件不满足时只跑静态扫描，脚本会明确说明页面没有被渲染过。

## 安装

先把 `AWESOME_HTML_REPO` 设为本仓库的绝对路径。

### Claude Code

```bash
claude plugin validate "$AWESOME_HTML_REPO/plugins/awesome-html" --json
claude plugin marketplace add "$AWESOME_HTML_REPO"
claude plugin install awesome-html@rocky-awesome-html
```

### Codex

```bash
codex plugin marketplace add "$AWESOME_HTML_REPO"
codex plugin add awesome-html@rocky-awesome-html
```

### Kimi Code 和 zCode

- Kimi Code：用 `/plugins install` 加上 `<repo>/plugins/awesome-html` 的绝对路径，然后执行 `/reload`。
- zCode：通过它的插件市场添加本仓库，然后安装 Awesome HTML。

装完后重新加载插件，或者开一个新会话。不同宿主版本的安装语法可能不一样，有出入时以宿主自己的帮助为准。

## 使用

直接提需求，比如"做个页面讲讲我们的登录流程"、"把 docs/wip/launch.md 做成进度看板"、"给新手引导做个三屏原型"。没指定路径时，页面输出到项目下的 `html/<slug>.html`。用这个 skill 做出的样例在 [`examples/`](examples/)。

## 目录结构

```text
plugins/awesome-html/skills/awesome-html/
├── SKILL.md            契约、页型路由、工作流程
├── references/         设计、解释页、看板、原型、幻灯片、图表、交付清单
├── assets/             base.html、prototype.html、track.html、deck.html、vendor/chart.umd.min.js
└── scripts/            inline.py、check.py、track.py
```

## 开发

```bash
python3 tests/check_package.py
python3 -m unittest discover tests
```

找不到 Chrome 时会跳过浏览器测试。

## 许可

MIT，见 [LICENSE](LICENSE)。内置的 Chart.js 也是 MIT。这个 skill 借鉴了哪些来源，见 [NOTICE](NOTICE)；调研记录见 [docs/research.md](docs/research.md)。
