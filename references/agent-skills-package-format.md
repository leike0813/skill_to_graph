# Agent Skill 包格式规范参考（Agent Skills / Open Agent Skills 标准）

**规范来源**：Agent Skills Specification — https://agentskills.io/specification （规范源文件 `docs/specification.mdx`）
**规范仓库**：https://github.com/agentskills/agentskills
**规范版本**：官方**未发布编号版本**（仓库无 tag、无 release，见 https://github.com/agentskills/agentskills/releases ）。本文件按以下 SHA 固定口径：`docs/specification.mdx` 最后改动提交 `217be548739f21d6008915c29aefe320ea1a90af`（2026-08-04）；仓库 HEAD `69ef37e9424c0a7ea9dd2293b559e43ec8176379`（2026-08-09）。引用规范时**不要写"规范 v1.0"**，应写"Agent Skills 规范，commit `<SHA>`"。
**采集日期**：2026-10-22

---

## 1. 规范来源与权威性

| 来源 | URL | 确立的事实 |
| --- | --- | --- |
| Agent Skills 规范页 | https://agentskills.io/specification | 目录结构、frontmatter 字段表、各字段约束、渐进式披露三层、文件引用规则 |
| 规范源文件 | https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx | 与规范页同源（仓库 `AGENTS.md` 声明："`docs/specification.mdx` is authoritative for format requirements"） |
| 仓库 AGENTS.md | https://github.com/agentskills/agentskills/blob/main/AGENTS.md | 规范只管格式；文档、示例、测试、参考实现**不新增格式要求**；`skills-ref/` 是演示件，不是生产 SDK |
| 客户端实现指南 | https://agentskills.io/client-implementation/adding-skills-support | 规范**不规定** skill 目录放在哪；`.agents/skills/` 是跨客户端惯例；frontmatter 解析与宽松校验建议 |
| Anthropic 平台文档 | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview | Claude 侧 `name`/`description` 字段要求（含保留字、XML 标签限制）；`~/.claude/skills/`、`.claude/skills/` 位置 |
| Anthropic 最佳实践 | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices | 命名风格建议、description 写法、渐进式披露模式、500 行/5k token 建议 |
| Anthropic 工程博客 | https://www.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills | 三层渐进式披露的原始叙述；2025-10-16 首发，2025-12-18 转为开放标准 |
| anthropics/skills 的 spec 指针 | https://github.com/anthropics/skills/blob/main/spec/agent-skills-spec.md | 内容仅一行："The spec is now located at https://agentskills.io/specification" —— Anthropic 自己把规范权威让渡给 agentskills.io |

> Anthropic 官方规范页与 agentskills.io 在 `name`/`description` 长度上**完全一致**（64 / 1024 字符），可互为佐证。Anthropic 侧额外多出「保留字 `anthropic`/`claude`」「不可含 XML 标签」两条 Claude 平台专属限制（见 §3.2），这些**不在**开放规范里。

---

## 2. Skill 包目录结构

规范原文（`agentskills.io/specification`）：

```
skill-name/
├── SKILL.md          # Required: metadata + instructions
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
├── assets/           # Optional: templates, resources
└── ...               # Any additional files or directories
```

### 2.1 强制项与可选项

| 路径 | 规范地位 | 规范定位 | 典型内容 | 是否进上下文 |
| --- | --- | --- | --- | --- |
| `SKILL.md` | **必需** | 元数据 + 指令正文 | YAML frontmatter + Markdown 正文 | 触发时全文进上下文 |
| `scripts/` | 可选（**推荐约定**） | 可执行代码 | `.py` / `.sh` / `.ts` 等 | **不**进上下文；执行后只有 stdout/stderr 进上下文 |
| `references/` | 可选（**推荐约定**） | 按需加载的文档 | `REFERENCE.md`、`FORMS.md`、领域文件（`finance.md`） | 被引用时进上下文 |
| `assets/` | 可选（**推荐约定**） | 静态资源 | 模板、图片、数据表 | 通常**不**进上下文，被复制/嵌入产物 |
| 其它任意文件/目录 | **允许** | "A skill directory may contain any files and directories beyond the required `SKILL.md`" | 例：`agents/openai.yaml`（Codex）、`evals/`、`LICENSE.txt` | 取决于是否被引用 |

**关键点**：`scripts/` `references/` `assets/` 三个名字在规范里是**推荐约定（recommendations）**，不是硬性要求。规范明确说 "The conventions below are recommendations for organizing common types of content."。真实官方包中三者会被改名或替换：

- `anthropics/skills/skills/mcp-builder/` 用的是 `reference/`（单数），不是 `references/`；
- `anthropics/skills/skills/pdf/` 把参考文档直接放在包根：`reference.md`、`forms.md`；
- `anthropics/skills/skills/algorithmic-art/` 用 `templates/`；
- `openai/skills/skills/.curated/pdf/` 用 `agents/openai.yaml` + `assets/pdf.png`。

→ **解析器不能按目录名硬编码语义**；能保证的只有 `SKILL.md` 存在，正文里的相对路径是唯一权威引用。

### 2.2 文件名大小写

- 规范与客户端实现指南都写 `SKILL.md`（全大写）。客户端实现指南明确："look for subdirectories containing a file named exactly `SKILL.md`"。
- 官方参考实现 `skills-ref` 额外接受小写 `skill.md` 作为回退（`skills_ref/parser.py`：`for name in ("SKILL.md", "skill.md")`）——这是**实现细节，不是规范要求**。
- OpenCode 排障指引第一条即："Verify `SKILL.md` is spelled in all caps"。

---

## 3. `SKILL.md` 的 YAML frontmatter

规范原文表（https://agentskills.io/specification）：

| 字段 | 必填 | 约束 | 含义 |
| --- | --- | --- | --- |
| `name` | 是 | 最长 64 字符。仅小写字母、数字、连字符。不能以连字符开头或结尾。 | Skill 唯一标识；**必须等于父目录名** |
| `description` | 是 | 最长 1024 字符。非空。 | 描述 skill 做什么**以及何时使用**；这是 agent 触发匹配的主要依据 |
| `license` | 否 | 许可证名，或对包内许可证文件的引用 | 建议简短 |
| `compatibility` | 否 | 最长 500 字符 | 环境要求（目标产品、系统依赖、是否需要网络等）。"Most skills do not need the `compatibility` field" |
| `metadata` | 否 | string→string 的键值映射 | 存放规范未定义的额外属性；建议 key 名足够独特以免冲突 |
| `allowed-tools` | 否 | 空格分隔的字符串 | 预授权可运行的工具。**实验性**，"Support for this field may vary between agent implementations" |

**没有其它顶层字段。** 规范 frontmatter 表只列这 6 个；客户端实现指南的宽松校验清单也是这 6 个。

### 3.1 `name`

规范（https://agentskills.io/specification#name-field）原文约束：

- Must be 1-64 characters
- May only contain unicode lowercase alphanumeric characters (`a-z`, `0-9`) and hyphens (`-`)
- Must not start or end with a hyphen (`-`)
- Must not contain consecutive hyphens (`--`)
- **Must match the parent directory name**

规范给出的合法/非法样例：

```yaml
# 合法
name: pdf-processing
name: data-analysis
name: code-review

# 非法
name: PDF-Processing  # uppercase not allowed
name: -pdf            # cannot start with hyphen
name: pdf--processing # consecutive hyphens not allowed
```

### 3.2 Anthropic/Claude 追加的限制（不属于开放规范）

Anthropic 平台文档（https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview#skill-structure）：

- `name`：最长 64 字符；只含小写字母、数字、连字符；**不能含 XML 标签**；**不能含保留字 `"anthropic"`、`"claude"`**。
- `description`：非空；最长 1,024 字符；**不能含 XML 标签**。

Anthropic 官方校验脚本 `skills/skill-creator/scripts/quick_validate.py` 实现了描述中的尖括号检查：出现 `<` 或 `>` 直接判失败。OpenAI 官方 `openai/skills/skills/.system/skill-creator/scripts/quick_validate.py` 也检查尖括号，但**不**检查保留字。

### 3.3 `description`

规范约束：1–1024 字符；应同时说明「做什么」与「何时用」；应包含帮助 agent 匹配任务的关键词。

规范的正反例：

```yaml
# Good
description: Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction.

# Poor
description: Helps with PDFs.
```

写法要求（Anthropic 最佳实践，https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices）：

- **第三人称写**（描述被注入 system prompt，人称不一致会导致发现异常）：`"Processes Excel files and generates reports"`，不要 `"I can help you..."`。
- 具体、带触发词；把主要用例放最前。
- 避免空洞：`"Helps with documents"` / `"Processes data"` / `"Does stuff with files"`。

1024 上限的**来源**（三处一手）：

1. 规范 frontmatter 表与 `#description-field` 小节：https://agentskills.io/specification#description-field
2. Anthropic 平台文档：https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview#skill-structure
3. 两家官方校验器硬编码 `1024`（`anthropics/skills` 的 `quick_validate.py`、`openai/skills` 的 `quick_validate.py`）

优化 description 的官方方法论（触发率评测、train/validation 切分、约 5 轮迭代）：https://agentskills.io/skill-creation/optimizing-descriptions

### 3.4 `license` / `compatibility` / `metadata` / `allowed-tools`

```yaml
license: Apache-2.0
# 或
license: Proprietary. LICENSE.txt has complete terms

compatibility: Requires git, docker, jq, and access to the internet
compatibility: Requires Python 3.14+ and uv

metadata:
  author: example-org
  version: "1.0"

allowed-tools: Bash(git:*) Bash(jq:*) Read
```

- `metadata` 规范定义为 **string→string**。OpenCode 明确说："The Agent Skills spec defines `metadata` values as strings, so quoted values are the portable form."（OpenCode 额外接受 YAML bool，如 `opencode/slash: true`）
- `allowed-tools` 规范标为**实验性**。Claude Code 侧实现更宽：接受空格或逗号分隔字符串，也接受 YAML list；授权**只在调用该 skill 的那一轮**有效，下一条消息即清除。Claude Code 侧还有规范里没有的 `disallowed-tools`（反向移除工具池）。
- Claude Code 侧的 `metadata`：自由 YAML map，Claude Code 不解释其内容，但**若不是 map 会丢弃**；且不得复用 `paths` 这类 frontmatter 字段名做 key。

### 3.5 正文中额外字段的落地后果

Claude Code 区分两类分发路径（https://code.claude.com/docs/en/skills#using-skill-frontmatter-outside-claude-code）：

| 分发路径 | 可用 frontmatter 字段 |
| --- | --- |
| Claude Code skill（任意层级，含 plugin skill） | 上表全部字段（含 `argument-hint`、`context`、`agent`、`model`、`paths`、`hooks`、`when_to_use` 等扩展） |
| claude.ai 上传、Skills API、`package_skill.py` 打包 | 仅 `name`、`description`、`license`、`compatibility`、`metadata`、`allowed-tools` |

超出规范字段会**硬失败**，不是忽略：

```
Unexpected key(s) in SKILL.md frontmatter: argument-hint. Allowed properties are: allowed-tools, compatibility, description, license, metadata, name
```

→ **要跨客户端通用的 skill，frontmatter 只能用规范的 6 个字段。**

---

## 4. `name` 与目录名的关系

| 来源 | 约束强度 | 表述 |
| --- | --- | --- |
| 开放规范 | **硬约束** | "Must match the parent directory name"（https://agentskills.io/specification#name-field） |
| `skills-ref` 参考实现 | **硬错误** | `Directory name '{dir}' must match skill name '{name}'`（`skills_ref/validator.py`） |
| 客户端实现指南 | **建议宽松** | "Name doesn't match the parent directory name → warn, load anyway"（https://agentskills.io/client-implementation/adding-skills-support） |
| OpenCode | 硬约束 | `name` "Match the directory name that contains `SKILL.md`"，并给出等价正则 `^[a-z0-9]+(-[a-z0-9]+)*$` |
| VS Code / Copilot | 硬约束 | "Must match the parent directory name. Maximum 64 characters. Names with invalid characters cause the skill to silently fail to load." |
| Gemini CLI | 建议 | "A unique identifier for the skill. This **should** match the directory name." |
| Claude Code | **不一致 / 可省略** | frontmatter 表里 `name` 是 **No（选填）**，"Defaults to the directory name" |

Claude Code 的命令名来源（https://code.claude.com/docs/en/skills#how-a-skill-gets-its-command-name）：

| Skill 位置 | 命令名来源 |
| --- | --- |
| `~/.claude/skills/` 或 `.claude/skills/` 下的目录 | frontmatter `name`，**或**目录名 |
| 嵌套 `.claude/skills/`（目录名冲突时） | 相对工作目录的子目录路径 + 目录名，形如 `/apps/web:deploy` |
| `.claude/commands/` 下的文件 | 文件名（无扩展名） |
| plugin 的 `skills/` 子目录 | frontmatter `name` 或目录名，带 plugin 前缀 `/my-plugin:review` |
| plugin 根部的 `SKILL.md` | frontmatter `name`（无目录可取），缺失时回落 plugin 目录名 |

**给转换器的结论**：包目录名 == frontmatter `name` 是规范要求，但 Claude Code 允许二者不同且以 frontmatter 为准。转换时若发现不一致，**不要静默改写**；按目标 harness 的规则决定采用哪个（Claude Code 用 frontmatter；OpenCode/VS Code 判「不匹配」；规范参考实现报错）。

---

## 5. 渐进式披露与 `references/`

### 5.1 三层模型

规范（https://agentskills.io/specification#progressive-disclosure）：

| 层 | 加载内容 | 加载时机 | 预算 |
| --- | --- | --- | --- |
| 1. Metadata | `name` + `description` | **启动时**对所有 skill 加载 | ~100 tokens / skill |
| 2. Instructions | `SKILL.md` 正文 | skill 被激活时 | **< 5000 tokens（建议）** |
| 3. Resources | `scripts/`、`references/`、`assets/` 中的文件 | 被需要时 | 不限 |

配套硬建议：**"Keep your main `SKILL.md` under 500 lines. Move detailed reference material to separate files."**（Anthropic 最佳实践给出同样 500 行/5k token 口径。）

Anthropic 侧的 token 成本表（https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview#how-skills-work）：Level 1 ~100 tokens/skill（始终加载）、Level 2 <5k tokens（触发时）、Level 3 访问前 0 token。

客户端实现指南给出同一模型的略不同预算（~50–100 tokens/skill）：https://agentskills.io/client-implementation/adding-skills-support

### 5.2 引用写法

规范原文（https://agentskills.io/specification#file-references）：

```markdown
See [the reference guide](references/REFERENCE.md) for details.

Run the extraction script:
scripts/extract.py
```

规则：

- 用**相对 skill 根目录**的路径（skill 根 = `SKILL.md` 的父目录）。
- **只保持一层深**："Keep file references one level deep from `SKILL.md`. Avoid deeply nested reference chains." 原因（Anthropic 最佳实践）：嵌套引用时 Claude 可能只 `head -100` 预览，读不全。
- 显式写"什么时候读"比写"详见 references/"更有用：`"Read references/api-errors.md if the API returns a non-200 status code"`。
- 长参考文件（>100 行）顶部加目录（Table of Contents），便于部分读取时仍能看到全貌。
- 路径用正斜杠（Anthropic 最佳实践："Use forward slashes (`reference/guide.md`), not backslashes"）。

其他 harness 的路径约定差异：

- VS Code：`[test template](./test-template.js)` 或 `#file:./test-template.js`，相对 `SKILL.md` 文件；用 Unix 风格 `/` 保证跨平台。
- Claude Code：可用 `${CLAUDE_SKILL_DIR}` 拿 skill 绝对目录（`${CLAUDE_PROJECT_DIR}` 拿项目根），在 `allowed-tools` 的 Bash 规则里也会替换。
- 客户端实现指南建议：给模型注入 `location`（绝对路径）+ 一句"resolve relative paths against the skill's directory"；或者用专用激活工具返回带标签的 `<skill_content>` + `<skill_resources>` 包裹。

### 5.3 `references/` 的规范定位

- 规范列举的典型文件：`REFERENCE.md`（详细技术参考）、`FORMS.md`（表单模板/结构化数据格式）、领域文件（`finance.md`、`legal.md`）。
- "Keep individual reference files focused. Agents load these on demand, so smaller files mean less use of context."
- 规范**未规定** `references/` 的文件大小上限、深度上限、命名格式；只有"引用保持一层深"这条书写规则。
- 客户端实现指南的额外建议：激活工具列出捆绑资源时**不要预读**；大目录要给列表设上限并声明可能不完整；权限系统应**白名单化 skill 目录**，否则每次引用 `scripts/`/`references/` 都会弹权限框。

### 5.4 各 harness 的披露预算差异

| Harness | 行为 | 来源 |
| --- | --- | --- |
| Codex | 初始 skill 列表含每个 skill 的文件路径；默认最多占模型上下文窗口 **2%**，上下文未知时 **8,000 字符**；skill 多时先缩短 description，再省略部分 skill 并警告。可用 `skills.max_context_tokens` 调，最高 10,000 tokens。**该预算只作用于初始列表**，选中后仍读完整 `SKILL.md` | https://learn.chatgpt.com/docs/build-skills |
| Claude Code | skill 列表中 `description` 与 `when_to_use` 合并后**截断在 1,536 字符** | https://code.claude.com/docs/en/skills#frontmatter-reference |
| Claude Code 生命周期 | skill 内容作为**单条消息**进入对话并跨轮留存，不会在后续轮次重读；压缩后每个 skill 保留前 5,000 tokens，合计预算 25,000 tokens | https://code.claude.com/docs/en/skills#skill-content-lifecycle |
| Gemini CLI | 启动时把 name+description 注入 system prompt；激活时把 `SKILL.md` 正文与整个目录结构加入对话历史，并把 skill 目录加入允许读写的路径 | https://geminicli.com/docs/cli/skills/ |

---

## 6. `scripts/` 的执行约定

### 6.1 规范定位

规范（https://agentskills.io/specification#scripts）：

- "Contains executable code that agents can run."
- 脚本应当：自包含或清楚声明依赖；给出有用的错误信息；优雅处理边界情况。
- "Supported languages depend on the agent implementation. Common options include Python, Bash, and JavaScript."

### 6.2 调用方式

规范 + 官方脚本指南（https://agentskills.io/skill-creation/using-scripts）：

- **用相对 skill 目录根的路径**；"The agent resolves these paths automatically — no absolute paths needed."
- 脚本执行路径（代码块里的）相对于 **skill 目录根**，因为 agent 在那里执行命令。
- 典型写法：

```markdown
## Available scripts

- **`scripts/validate.sh`** — Validates configuration files
- **`scripts/process.py`** — Processes input data

## Workflow

1. Run the validation script:
   ```bash
   bash scripts/validate.sh "$INPUT_FILE"
   ```

2. Process the results:
   ```bash
   python3 scripts/process.py --input results.json
   ```
```

- 解释器由**调用命令显式声明**（`bash scripts/validate.sh`、`python3 scripts/process.py`、`uv run scripts/extract.py`、`deno run scripts/extract.ts`、`bun run scripts/extract.ts`）。规范**不要求** shebang。
- shebang 只在「直接执行型」运行时示例里出现：Deno `#!/usr/bin/env -S deno run`、Bun `#!/usr/bin/env bun`。Python 用 [PEP 723](https://peps.python.org/pep-0723/) 内联依赖块（`# /// script` … `# ///`），`uv run` / `pipx run` 识别。
- Ruby 用 `bundler/inline`；`npm`/`npx`/`uvx`/`pipx`/`go run` 一类**不需要 `scripts/` 目录**，直接在 SKILL.md 里引用即可，且应**锁定版本**。

### 6.3 面向 agent 设计的脚本要求

官方脚本指南明确列出的硬性/建议项：

- **禁止交互式提示**（硬性）：agent 在非交互 shell 里跑，交互会永久挂起。输入只走 flag / 环境变量 / stdin。
- **必须有 `--help`**：这是 agent 学会脚本接口的主要途径。
- **错误信息要有用**：`Error: --format must be one of: json, csv, table. Received: "xml"`。
- **结构化输出优先**：JSON/CSV/TSV 而非自由文本；stdout 走数据，stderr 走诊断。
- **幂等**：agent 可能重试；"create if not exists" 优于 "create and fail on duplicate"。
- **dry-run** 支持；**有意义的 exit code**（区分 not found / invalid args / auth failure，并在 `--help` 里说明）；**可预测的输出大小**（harness 常在 10–30K 字符处截断工具输出）。

### 6.4 权限与信任约定

规范本身不写权限模型；相关约定分布在各 harness：

| 约定 | 内容 | 来源 |
| --- | --- | --- |
| 技能来源信任 | 只用可信来源的 skill；恶意 skill 可以引导 agent 调用工具/跑代码做与声明目的不符的事 | Anthropic 平台文档 "Security considerations"、工程博客 "Security considerations when using Skills" |
| 预授权工具 | `allowed-tools` 让 agent 在该轮免确认调用指定工具；**授权下一条消息即失效** | https://code.claude.com/docs/en/skills#pre-approve-tools-for-a-skill |
| 仓库信任不拦截 | Claude Code 对**未信任**项目目录里的 skill 同样应用 `allowed-tools`；组织可用 `allowManagedPermissionRulesOnly` 关闭 | 同上 + "#when-only-managed-permission-rules-apply" |
| 目录白名单 | 客户端实现指南：把 skill 目录加进文件访问白名单，避免每次读资源都弹框 | https://agentskills.io/client-implementation/adding-skills-support |
| 激活需同意 | Gemini CLI 每次激活 skill 都要用户确认，并授予该目录访问权；安装远程 skill 也要确认来源 | https://geminicli.com/docs/cli/using-agent-skills |
| 细粒度授权 | OpenCode 用 `permission.skill` 模式串（`"*": allow` / `internal-*: deny` / `experimental-*: ask`） | https://opencode.ai/docs/skills/ |
| 项目级 skill 不可信 | 客户端实现指南：project 级 skill 来自被操作的仓库，可能不可信；应做信任门控 | https://agentskills.io/client-implementation/adding-skills-support |
| 打包 | Anthropic `package_skill.py` 把 skill 目录打成 `<name>.skill`（zip，根目录保留 skill 文件夹名），排除 `__pycache__`、`node_modules`、`*.pyc`、`.DS_Store`、根级 `evals/` | https://github.com/anthropics/skills/blob/main/skills/skill-creator/scripts/package_skill.py |

---

## 7. `assets/` 的规范定位

规范（https://agentskills.io/specification#assets）：

- "Contains static resources:"
  - Templates（document templates, configuration templates）
  - Images（diagrams, examples）
  - Data files（lookup tables, schemas）

配套写法建议：输出格式模板短的可以内联在 `SKILL.md`，长的、需要时才用的放 `assets/` 并从 `SKILL.md` 引用。

OpenAI 官方 skill-creator 脚手架给出的**三分类判据**（最有操作性的版本，https://github.com/openai/skills/blob/main/skills/.system/skill-creator/scripts/init_skill.py）：

| 目录 | 定义 | 例子 |
| --- | --- | --- |
| `scripts/` | 可直接执行的代码 | `fill_fillable_fields.py`、`extract_form_field_info.py`、`document.py` |
| `references/` | **要载入上下文**以支撑模型推理的文档 | API 参考、数据库 schema、完整指南、公司政策 |
| `assets/` | **不载入上下文**，而是进入模型产出的文件 | `.pptx` 模板、logo、字体 `.ttf`、前端脚手架目录 |

Anthropic 侧对应表述（Claude 平台文档 Level 3）：Instructions = additional markdown files（`FORMS.md`、`REFERENCE.md`）；Code = executable scripts（跑，只有输出进上下文）；Resources = reference materials（数据库 schema、API 文档、模板、示例）。

---

## 8. 各家 harness 的差异

> **前提**：开放规范**不规定** skill 目录放在哪 —— 客户端实现指南原文："the Agent Skills specification does not mandate where skill directories live (it only defines what goes inside them)"。下表的路径全部来自各 harness 自己的官方文档。

### 8.1 发现位置

| Harness | 项目级 | 用户级 | 其它 |
| --- | --- | --- | --- |
| Claude Code | `.claude/skills/<name>/SKILL.md`；嵌套 `<subdir>/.claude/skills/`；`--add-dir` 目录下的 `.claude/skills/` | `~/.claude/skills/` | Enterprise：managed settings 目录下的 `.claude/skills/`（Linux 如 `/etc/claude-code/.claude/skills/`）；Plugin：`<plugin>/skills/`；claude.ai 账号同步：下载到 `~/.claude/skills/synced/`。**不读 `~/.claude/skills/` 的场景**：Cowork / cloud sessions / cloud 定时任务 |
| Codex（ChatGPT/Codex CLI/IDE） | `$CWD/.agents/skills`、`$CWD/../.agents/skills`、`$REPO_ROOT/.agents/skills`（从 CWD 向上扫到仓库根） | `$HOME/.agents/skills` | ADMIN：`/etc/codex/skills`；SYSTEM：Codex 内置。**`~/.codex/skills` 不在当前文档列出的发现位置中**（旧文档/旧博客里出现过，属遗留口径）；`~/.codex/config.toml` 仍是配置位置 |
| OpenCode | `.opencode/skills/`、`.claude/skills/`、`.agents/skills/` | `~/.config/opencode/skills/`、`~/.claude/skills/`、`~/.agents/skills/` | 项目级路径从 CWD 向上走到 git worktree 根 |
| Gemini CLI | `.gemini/skills/` 或 `.agents/skills/` | `~/.gemini/skills/` 或 `~/.agents/skills/` | 另有 built-in skills 与 extension skills 两层 |
| VS Code / GitHub Copilot | `.github/skills/`、`.claude/skills/`、`.agents/skills/` | `~/.copilot/skills/`、`~/.claude/skills/`、`~/.agents/skills/` | VS Code 的实验性 Codex 集成会先发现 `.github/skills/`；Codex 原生发现 `.agents/skills/` |
| 通用惯例 | `.agents/skills/` —— 客户端实现指南称其"emerged as a widely-adopted convention for cross-client skill sharing" | `~/.agents/skills/` | 部分实现也扫 `.claude/skills/` 做务实兼容 |

### 8.2 frontmatter 字段支持差异

| Harness | 规范 6 字段 | 额外支持的字段 | 差异说明 |
| --- | --- | --- | --- |
| 开放规范 | `name`、`description`、`license`、`compatibility`、`metadata`、`allowed-tools` | — | `allowed-tools` 标为实验性 |
| Claude Code | 全部 6 个（`license`/`compatibility` 接受但**不解释**） | `when_to_use`、`argument-hint`、`arguments`、`disable-model-invocation`、`user-invocable`、`allowed-tools`（语义更宽：空格/逗号/列表）、`disallowed-tools`、`model`、`effort`、`context`、`agent`、`background`、`hooks`、`paths`、`shell` | 字段名用小写连字符（`when_to_use` 例外用下划线）；**未识别的字段被静默忽略，不报错**；布尔值接受 `yes/no/on/off/1/0/true/false` |
| Claude Code（claude.ai / Skills API / `package_skill.py`） | 仅 6 个 | 无 | 出现规范外字段 → **硬错误**（见 §3.5） |
| Codex | 要求 `name` + `description` | 通过**独立的 `agents/openai.yaml`** 承载 UI/策略/依赖，不塞进 frontmatter：`interface.display_name`、`interface.short_description`、`interface.icon_small/large`、`interface.brand_color`、`interface.default_prompt`、`policy.allow_implicit_invocation`、`dependencies.tools[]` | 规范里 `license`/`compatibility` 在 Codex 文档中未出现（`metadata` 在 openai 官方 skill-creator 的 SKILL.md 里确有使用：`metadata: short-description: ...`） |
| OpenCode | `name`（必填）、`description`（必填）、`license`、`compatibility`、`metadata` | 无额外顶层字段；客户端专有键塞进 `metadata`：`opencode/slash`、`opencode/autoinvoke` | 文档**未列出** `allowed-tools` |
| Gemini CLI | 文档只详述 `name` + `description` | — | `name` "should match the directory name"；激活需用户同意 |
| VS Code / Copilot | `name`（必填）、`description`（必填） | `argument-hint`、`user-invocable`、`disable-model-invocation`、`context`（`fork`） | `name` 明确禁止斜杠/冒号/点/命名空间前缀（否则静默加载失败）；`description` 上限同为 1024 |

**未能从一手来源证实**：各 harness 对 `license` / `compatibility` / `metadata` 的**具体运行时行为**（是否校验、是否注入上下文、是否做长度限制）——除 Claude Code 明确写了「接受但不解释」外，其余 harness 官方文档均未说明。规范层面 `compatibility` ≤500 字符、`metadata` 为 string→string 映射是硬要求。

### 8.3 其它行为差异

- **`name` 缺失时**：Claude Code 回落目录名（`name` 选填）；OpenCode / VS Code / Codex / 规范均要求 `name` 存在。OpenCode 排障第 2 条即 "Check that frontmatter includes `name` and `description`"。
- **重名冲突**：规范实现指南给出通用约定 **project 级覆盖 user 级**；Codex 不合并同名 skill，两个都出现在选择器里；Gemini CLI 按层优先级取高者，同层内 `.agents/skills/` 优先于 `.gemini/skills/`；Claude Code 的优先级是 enterprise > personal > project。
- **`description` 缺失时**：Claude Code 回落为"markdown 内容的首个非空行"。
- **目录扫描边界**：客户端实现指南建议设上界（如最大深度 4–6 层、最多 2000 个目录），跳过 `.git/`、`node_modules/`，可尊重 `.gitignore`。

---

## 9. 官方示例对照

### 9.1 Anthropic 官方 `pdf` skill（完整三层结构）

来源：https://github.com/anthropics/skills/tree/main/skills/pdf

```
skills/pdf/
├── SKILL.md              (8072 bytes)   # 必需
├── reference.md          (16692 bytes)  # 参考文档（放在包根，非 references/）
├── forms.md              (11854 bytes)  # 表单指南（同上）
├── scripts/                            # 8 个脚本
│   ├── check_bounding_boxes.py
│   ├── check_fillable_fields.py
│   ├── convert_pdf_to_images.py
│   ├── create_validation_image.py
│   ├── extract_form_field_info.py
│   ├── extract_form_structure.py
│   ├── fill_fillable_fields.py
│   └── fill_pdf_form_with_annotations.py
└── LICENSE.txt           (1467 bytes)
```

`SKILL.md` frontmatter 原文（逐字抄录）：

```yaml
---
name: pdf
description: Use this skill whenever the user wants to do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging multiple PDFs into one, splitting PDFs apart, rotating pages, adding watermarks, creating new PDFs, filling PDF forms, encrypting/decrypting PDFs, extracting images, and OCR on scanned PDFs to make them searchable. If the user mentions a .pdf file or asks to produce one, use this skill.
license: Proprietary. LICENSE.txt has complete terms
---
```

正文里的引用写法（原文）：

> For advanced features, JavaScript libraries, and detailed examples, see REFERENCE.md. If you need to fill out a PDF form, read FORMS.md and follow its instructions.

注意：这里用的是**文件名散文引用**（`REFERENCE.md`），且实际文件名是小写 `reference.md` —— 大小写在真实包里并不严格一致。

### 9.2 Anthropic 官方 `mcp-builder` skill（`reference/` 单数 + 相对路径链接）

来源：https://github.com/anthropics/skills/tree/main/skills/mcp-builder

```
skills/mcp-builder/
├── SKILL.md              (9092 bytes)
├── reference/
│   ├── evaluation.md          (21663 bytes)
│   ├── mcp_best_practices.md  (7330 bytes)
│   ├── node_mcp_server.md     (28550 bytes)
│   └── python_mcp_server.md   (25099 bytes)
├── scripts/
└── LICENSE.txt
```

frontmatter 原文：

```yaml
---
name: mcp-builder
description: Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services, whether in Python (FastMCP) or Node/TypeScript (MCP SDK).
license: Complete terms in LICENSE.txt
---
```

正文引用原文（体现 `./reference/xxx.md` 的相对路径写法，与 §5.2 规范示例一致）：

```markdown
- [📋 View Best Practices](./reference/mcp_best_practices.md) - Core guidelines
- [⚡ TypeScript Guide](./reference/node_mcp_server.md) - TypeScript patterns and examples
- [🐍 Python Guide](./reference/python_mcp_server.md) - Python patterns and examples
```

### 9.3 OpenAI 官方 `pdf` skill（带 `agents/openai.yaml` + `assets/`）

来源：https://github.com/openai/skills/tree/main/skills/.curated/pdf

```
skills/.curated/pdf/
├── SKILL.md                 (2517 bytes)
├── agents/
│   └── openai.yaml          (219 bytes)
├── assets/
│   └── pdf.png              (1312 bytes)
└── LICENSE.txt
```

`SKILL.md` frontmatter 原文（注意值带引号）：

```yaml
---
name: "pdf"
description: "Use when tasks involve reading, creating, or reviewing PDF files where rendering and layout matter; prefer visual checks by rendering pages (Poppler) and use Python tools such as `reportlab`, `pdfplumber`, and `pypdf` for generation and extraction."
---
```

`agents/openai.yaml` 原文（**不是** frontmatter 字段）：

```yaml
interface:
  display_name: "PDF Skill"
  short_description: "Create, edit, and review PDFs"
  icon_large: "./assets/pdf.png"
  default_prompt: "Create, edit, or review this PDF and summarize the key output or changes."
```

### 9.4 Anthropic 官方最小模板

来源：https://github.com/anthropics/skills/blob/main/template/SKILL.md

```markdown
---
name: template-skill
description: Replace with description of the skill and when Claude should use it.
---

# Insert instructions below
```

### 9.5 官方 skill-creator（`scripts/` + `references/` + `assets/` + `agents/` 并存）

来源：https://github.com/anthropics/skills/tree/main/skills/skill-creator

```
skills/skill-creator/
├── SKILL.md                (33168 bytes)
├── agents/                 # 评分用子代理说明
│   ├── analyzer.md
│   ├── comparator.md
│   └── grader.md
├── assets/
│   └── eval_review.html
├── eval-viewer/
│   ├── generate_review.py
│   └── viewer.html
├── references/
│   └── schemas.md
├── scripts/
│   ├── aggregate_benchmark.py
│   ├── generate_report.py
│   ├── improve_description.py
│   ├── package_skill.py
│   ├── quick_validate.py
│   ├── run_eval.py
│   ├── run_loop.py
│   └── utils.py
└── LICENSE.txt
```

其 `SKILL.md` 内部对资源语义的定义（原文）：

```
├── scripts/    - Executable code for deterministic/repetitive tasks
├── references/ - Docs loaded into context as needed
└── assets/     - Files used in output (templates, icons, fonts)
```

OpenAI 对应版本：https://github.com/openai/skills/tree/main/skills/.system/skill-creator （`agents/` + `references/openai_yaml.md` + `scripts/{init_skill.py,quick_validate.py,generate_openai_yaml.py}`），其 `SKILL.md` frontmatter 用了 `metadata`：

```yaml
---
name: skill-creator
description: Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Codex's capabilities with specialized knowledge, workflows, or tool integrations.
metadata:
  short-description: Create or update a skill
---
```

---

## 10. 校验器与可执行口径

三个一手实现给出的**实际**校验规则（可直接当作合规检查表）：

| 校验器 | 来源 | 允许字段 | 规则 |
| --- | --- | --- | --- |
| `skills-ref validate <dir>` | https://github.com/agentskills/agentskills/tree/main/skills-ref | `name`、`description`、`license`、`allowed-tools`、`metadata`、`compatibility` | `name` 必填、≤64、NFKC 归一化、必须小写、不能首尾连字符、不能 `--`、字符须为 alnum 或 `-`、**目录名必须等于 name**；`description` 必填非空、≤1024；`compatibility` 若存在必须是字符串且 ≤500；**出现任何规范外顶层字段即报错** |
| Anthropic `quick_validate.py` | https://github.com/anthropics/skills/blob/main/skills/skill-creator/scripts/quick_validate.py | 同上 6 个 | 额外：frontmatter 必须以 `---` 开头且能被 `yaml.safe_load` 解析成 dict；`name` 匹配 `^[a-z0-9-]+$`；`description` **不能含 `<` 或 `>`** |
| OpenAI `quick_validate.py` | https://github.com/openai/skills/blob/main/skills/.system/skill-creator/scripts/quick_validate.py | `name`、`description`、`license`、`allowed-tools`、`metadata`（**无 `compatibility`**） | 同样检查 kebab-case、连字符规则、≤64、description ≤1024 且不含尖括号 |

**注意 `skills-ref` 的两个实现细节**（非规范）：`name` 允许 Unicode 字母数字（`c.isalnum()`），与 OpenCode 的 ASCII 正则 `^[a-z0-9]+(-[a-z0-9]+)*$` 不同；它也接受小写 `skill.md` 文件名。参考实现 README 明确写 "This library is intended for demonstration purposes only. It is not meant to be used in production."

---

## 11. 冲突与不确定

1. **`name` 字符集**：规范文字自相矛盾（"unicode lowercase alphanumeric characters (`a-z`, `0-9`)" —— 说是 unicode 却只列 ASCII 范围）。`skills-ref` 接受 Unicode 字母（`isalnum()`），OpenCode 只接受 ASCII，VS Code 表述为"小写字母、数字、连字符"。**结论：以 ASCII `^[a-z0-9]+(-[a-z0-9]+)*$` 为安全子集。**
2. **`name` 是否必填**：规范必填；Claude Code 选填（回落目录名）。这是真实的跨客户端不一致。
3. **`name` 与目录名必须一致**：规范是硬约束，但客户端实现指南明确建议"warn, load anyway"；Claude Code 则两者都接受且以 frontmatter 为准。
4. **规范外顶层字段**：规范只列 6 个；Claude Code 接受更多并静默忽略；但 claude.ai/Skills API 打包路径对规范外字段**硬报错**。OpenAI 官方校验器的允许集**不含 `compatibility`**，与规范不符（疑似遗漏）。
5. **规范无版本号**：仓库无 tag、无 release、无 changelog。引用时须用 commit SHA。
6. **规范对 `references/` 的大小/深度没有硬限制**，只有"引用保持一层深"这条书写建议。`SKILL.md` 的 500 行 / 5000 token 是**建议**而非硬校验（`skills-ref` 不检查）。
7. **`allowed-tools` 是实验性**，各 harness 支持差异大（OpenCode 文档未列；Claude Code 语义更宽并扩展出 `disallowed-tools`）。
8. **`description` 里的 XML 标签限制**只来自 Anthropic 平台侧校验脚本，开放规范未提。
9. **`.codex/skills` 不是当前 Codex 文档列出的发现位置**（当前是 `.agents/skills`），但旧博客与旧仓库文档仍在使用它 —— 新建 skill 不要依赖该路径。
10. **未能从一手来源证实**：各 harness 对 `license` / `compatibility` / `metadata` 的运行时行为；`references/`/`assets/` 在多数 harness 侧的具体加载时机（只有规范与 Anthropic 文档给出了通用模型）。

---

## 12. 来源

- Agent Skills 规范：https://agentskills.io/specification （源文件 https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx ，commit `217be548739f21d6008915c29aefe320ea1a90af`）
- 规范仓库与权威性声明：https://github.com/agentskills/agentskills/blob/main/AGENTS.md
- 客户端实现指南：https://agentskills.io/client-implementation/adding-skills-support
- 官方脚本指南：https://agentskills.io/skill-creation/using-scripts
- 官方 description 优化指南：https://agentskills.io/skill-creation/optimizing-descriptions
- 官方最佳实践：https://agentskills.io/skill-creation/best-practices
- 官方 quickstart：https://agentskills.io/skill-creation/quickstart
- 规范文档索引（用于发现全部页面）：https://agentskills.io/llms.txt
- `skills-ref` 参考实现（validator/parser）：https://github.com/agentskills/agentskills/tree/main/skills-ref
- Anthropic 平台：Agent Skills 总览 https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- Anthropic 平台：最佳实践 https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- Anthropic 平台：Skills API 指南 https://platform.claude.com/docs/en/build-with-claude/skills-guide
- Anthropic 工程博客（三层渐进式披露原始叙述）：https://www.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills
- Claude Code：Skills 文档（frontmatter 全表、位置表、命令名来源）https://code.claude.com/docs/en/skills
- Anthropic 官方示例库：https://github.com/anthropics/skills （`template/SKILL.md`、`skills/pdf`、`skills/mcp-builder`、`skills/skill-creator`）
- OpenAI：Build skills（Codex 发现位置、`agents/openai.yaml`）https://learn.chatgpt.com/docs/build-skills
- OpenAI：Plugins 概念页 https://developers.openai.com/plugins/concepts/skills
- OpenAI：Skills 打包/挂载（Responses API）https://developers.openai.com/api/docs/guides/tools-skills
- OpenAI 官方示例库：https://github.com/openai/skills （`skills/.curated/pdf`、`skills/.system/skill-creator`）
- OpenCode：Agent Skills https://opencode.ai/docs/skills/
- Gemini CLI：Agent Skills https://geminicli.com/docs/cli/skills/ ；Creating Agent Skills https://geminicli.com/docs/cli/creating-skills ；Using Agent Skills https://geminicli.com/docs/cli/using-agent-skills
- VS Code / GitHub Copilot：https://code.visualstudio.com/docs/agent-customization/agent-skills ；https://docs.github.com/en/copilot/concepts/customizations/agent-skills
