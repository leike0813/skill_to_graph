# LangChain / LangGraph CLI 与部署运行形态

> **版本声明**：本文基于 2026-10-22 抓取的一手来源（官方文档站 `docs.langchain.com`、官方仓库 `langchain-ai/langgraph`、`langchain-ai/langchain`、官方 API 参考 `reference.langchain.com`、PyPI 包元数据）撰写。对应版本：`langgraph-cli` 0.4.37、`langgraph` 1.2.16、`langchain` 1.x（`langchain-ai/langchain` master 分支 `libs/langchain_v1/pyproject.toml` 声明 `version = "1.4.7"`）、`langgraph-api` 0.16.4、`langchain-cli` 0.0.37（最新稳定版，2025-08-30）与 `1.0.0a1`（2025-10-02）。
> 版本来源：https://pypi.org/project/langgraph-cli/ ｜ https://pypi.org/project/langgraph/ ｜ https://pypi.org/project/langgraph-api/ ｜ https://pypi.org/project/langchain-cli/
> CLI 参考总入口：https://docs.langchain.com/langsmith/cli ｜ `langgraph.json` JSON Schema：https://raw.githubusercontent.com/langchain-ai/langgraph/refs/heads/main/libs/cli/schemas/schema.json

## 0. 先看结论

1. **现行的 CLI 是 `langgraph`（发行包 `langgraph-cli`），不是 `langchain`。** 官方文档站 LangChain 1.x 索引里没有任何 "LangChain CLI" 页面；CLI 文档全在 `/langsmith/cli`（标题 “LangGraph CLI”）。
2. **`langchain new` / `langchain build` / `langchain dev` / `langchain prompt` 在现行官方 CLI 中都不存在。** `langchain-cli` 的真实命令树是 `langchain app new|add|remove|serve`、`langchain template ...`、`langchain integration ...`、`langchain migrate ...`、`langchain serve`（源码 `libs/cli/langchain_cli/cli.py`，tag `langchain-cli==1.0.0a1`）。该 CLI 已被官方从主仓库删除（commit `4e9a1eb` “chore: delete CLI (#34855)”，2026-01-23，代码保留在 `langchain-cli` 分支）。
3. **`langchain app new` 创建的是 LangServe 应用（模板脚手架），不是 LangGraph 图**；`langchain` v1 包（`libs/langchain_v1/pyproject.toml`）**没有 `[project.scripts]`**，即 1.x 的 `langchain` 包不提供 `langchain` 命令。
4. **“build 产物是目录”在 LangGraph 侧不成立**：`langgraph build` 的产物是 **Docker 镜像**；可发布的**目录**是 `langgraph new` 脚手架或自维护的应用目录，约定为 `langgraph.json` + 依赖声明文件 + 图代码（按需 `.env`）。
5. 本项目产物须以同一套构图逻辑支持两种运行形态：① 纯 Python `graph.invoke(...)`；② CLI/平台形态（被 `langgraph.json` 的 `graphs` 发现、由 `langgraph dev` / `up` / `deploy` 拉起）。按实际配置选择一个入口导出即可，不要求同时导出 compiled graph 与工厂函数。第 9 节给出差异表，第 10 节给出落地要求。

---

## 1. `langchain` CLI（发行包 `langchain-cli`）——已下线，仅供识别

命令树来自 tag `langchain-cli==1.0.0a1` 源码 `libs/cli/langchain_cli/cli.py`（`app.add_typer(..., name="template"/"app"/"integration")` + `app.command(name="migrate")` + 顶层 `serve`）与 `libs/cli/langchain_cli/namespaces/app.py`：

| 命令 | 参数 | docstring 原文 |
| - | - | - |
| `langchain app new` | `name`、`--package`（可重复）、`--pip/--no-pip`、`--non-interactive/--interactive` | “Create a new LangServe application.” |
| `langchain app add` | `dependencies`（可重复）、`--api-path`、`--project-dir`、`--repo`、`--branch`、`--pip/--no-pip` | “Add the specified template to the current LangServe app.” |
| `langchain app remove` | `api_paths` | “Remove the specified package from the current LangServe app.” |
| `langchain app serve` | `--port`、`--host`、`--app`（默认 `app.server:app`） | “Start the LangServe app.”（内部 `uvicorn.run(..., reload=True)`，默认 host `127.0.0.1`、port `8000`） |
| `langchain serve` | `--port`、`--host` | “Start the LangServe app, whether it's a template or an app.” |

约束：

- 依赖 `langserve[all]>=0.0.51`，属 **LangServe + LangChain Templates** 生态，与 LangGraph 图、Agent Server、`langgraph.json` 无关。
- `langchain app new` 的实现是从包内 `project_template` 目录 `shutil.copytree` 到目标目录并替换 `__app_name__`，随后生成 `add_routes(app, <chain>, path=...)`。**它产出的不是可被 `langgraph dev` 发现的图。**
- `langchain prompt` **不存在**。提示词/上下文版本化是 LangSmith 平台侧能力（`/langsmith/prompt-context-hub`、`/langsmith/manage-prompts`），走 API/SDK。
- PyPI 元数据里的 `[CLI Docs](.../libs/cli/DOCS.md)` 已 404（目录随 commit `4e9a1eb` 删除）。

---

## 2. `langgraph` CLI（发行包 `langgraph-cli`）——现行 CLI

### 安装

```bash
# Python >= 3.11 is required.
pip install -U "langgraph-cli[inmem]"      # 开发模式（内存 + 本地落盘）
pip install langgraph-cli                  # build / up / deploy
```

来源：https://docs.langchain.com/oss/python/langgraph/local-server.md ｜ https://docs.langchain.com/langsmith/cli

### 子命令总览（官方 “Quick commands” 表，逐字）

| Command | What it does |
| - | - |
| `langgraph dev` | Starts a lightweight local dev server (no Docker required), ideal for rapid testing. |
| `langgraph build` | Builds a Docker image of your LangGraph API server for deployment. |
| `langgraph deploy` | Builds and deploys a LangGraph image directly to LangSmith Deployments in a single step. |
| `langgraph dockerfile` | Emits a Dockerfile derived from your config for custom builds. |
| `langgraph up` | Starts the LangGraph API server locally in Docker. Requires Docker running; LangSmith API key for local dev; license for production. |

另有 `langgraph new`（脚手架）与 `langgraph validate`（校验配置），API 参考签名：`new(path: str | None, template: str | None)`、`validate(config: pathlib.Path)`（https://reference.langchain.com/python/langgraph-cli/cli/new ｜ .../cli/validate）。

### `langgraph new`

```bash
langgraph new path/to/your/app --template new-langgraph-project-python   # Python
npx @langchain/langgraph-cli new path/to/your/app --template new-langgraph-project-js  # JS
```

不指定 `--template` 时进入交互式模板选择菜单。模板仓库：`github.com/langchain-ai/new-langgraph-project`、`github.com/langchain-ai/new-langgraphjs-project`。

### `langgraph dev`

```bash
pip install -U "langgraph-cli[inmem]"
langgraph dev
langgraph dev --host 0.0.0.0 --port 2024 --no-reload --tunnel --no-browser
langgraph dev --config ./langgraph.json
```

| Option | Default | Description |
| - | - | - |
| `-c, --config FILE` | `langgraph.json` | Path to configuration file declaring dependencies, graphs and environment variables |
| `--host TEXT` | `127.0.0.1` | Host to bind the server to |
| `--port INTEGER` | `2024` | Port to bind the server to |
| `--no-reload` | | Disable auto-reload |
| `--n-jobs-per-worker INTEGER` | `1` | Maximum number of concurrent jobs per worker |
| `--debug-port INTEGER` | | Port for debugger to listen at |
| `--wait-for-client` | `False` | Wait for a debugger client to connect to the debug port before starting the server |
| `--no-browser` | | Skip automatically opening the browser when the server starts |
| `--studio-url TEXT` | | URL of the Studio instance to connect to. Defaults to https://smith.langchain.com |
| `--allow-blocking` | `False` | Do not raise errors for synchronous I/O blocking operations in your code (added in `0.2.6`) |
| `--tunnel` | `False` | Expose the local server via a public tunnel (Cloudflare) for remote frontend access. |

约束：`Currently, the CLI only supports Python 3.11 or later`；`dev` 模式状态持久化到本地目录（in-memory + pickled）。启动输出（官方逐字）：

```
- 🚀 API: http://127.0.0.1:2024
- 🎨 Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
- 📚 API Docs: http://127.0.0.1:2024/docs

This in-memory server is designed for development and testing.
For production use, please use LangSmith Deployment.
```

### `langgraph build`

```bash
langgraph build -t my-image
langgraph build --platform linux/amd64,linux/arm64 -t my-image --no-pull
```

| Option | Default | Description |
| - | - | - |
| `--platform TEXT` | | Target platform(s) to build the Docker image for. Example: `langgraph build --platform linux/amd64,linux/arm64` |
| `-t, --tag TEXT` | | **Required**. Tag for the Docker image. Example: `langgraph build -t my-image` |
| `--pull / --no-pull` | `--pull` | Build with latest remote Docker image. Use `--no-pull` for running the LangSmith API server with locally built images. |
| `-c, --config FILE` | `langgraph.json` | Path to configuration file declaring dependencies, graphs and environment variables. |
| `--build-command TEXT`* | | Build command to run. Runs from the directory where your `langgraph.json` file lives. |
| `--install-command TEXT`* | | Install command to run. Runs from the directory where you call `langgraph build` from. |

\* 官方标注 “Only supported for JS deployments, will have no impact on Python deployments.”

### `langgraph up`

```bash
langgraph up --port 8123 --wait --watch --verbose
langgraph up --image my-image:dev --no-pull --recreate
```

常用选项（逐字节选，完整表见官方 CLI 文档）：`-c/--config`（默认 `langgraph.json`）、`-p/--port`（默认 `8123`）、`--wait`（“Wait for services to start before returning. Implies --detach”）、`--base-image`（默认 `langchain/langgraph-api`）、`--image`（“If specified, skips building and uses this image directly.”）、`--postgres-uri`（默认 Local database）、`--watch`、`--verbose`、`-d/--docker-compose`、`--pull/--no-pull`、`--recreate/--no-recreate`、`--debugger-base-url`、`--debugger-port`。

### `langgraph deploy`（部署到 LangSmith Deployment）

```bash
LANGSMITH_API_KEY=lsv2_... langgraph deploy
langgraph deploy --name my-agent --deployment-type dedicated
langgraph deploy --deployment-id abc123
langgraph deploy --push-to 123456789.dkr.ecr.us-east-1.amazonaws.com/agents/my-agent --tag v1.2.0
langgraph deploy --image-uri 123456789.dkr.ecr.us-east-1.amazonaws.com/agents/my-agent@sha256:1a2b3c4d...
```

关键选项：`--api-key`、`--name`（默认当前目录名）、`--deployment-id`、`--deployment-type`（`serverless` 默认；`dedicated`；旧名 `dev`/`prod` 仍接受）、`--remote/--no-remote`、`--push-to`、`--image`、`-t/--tag`、`--image-uri`（必须带 digest）、`--listener-id`、`--k8s-namespace`、`--image-pull-secret`、`--no-wait`、`--verbose`。API key 可来自 `LANGGRAPH_HOST_API_KEY` / `LANGSMITH_API_KEY` / `LANGCHAIN_API_KEY` 或项目 `.env`。该命令官方标注为 **beta**；在 LangSmith Cloud 上本地构建需 `langgraph-cli` ≥ 0.4.35。

### `langgraph dockerfile`

```bash
langgraph dockerfile -c langgraph.json Dockerfile
```

生成片段（官方文档逐字）：

```dockerfile
FROM langchain/langgraph-api:3.11
...
ADD ./graphs /deps/__outer_graphs/src
...
ENV LANGSERVE_GRAPHS='{"agent": "/deps/__outer_graphs/src/agent.py:graph", "storm": "/deps/__outer_graphs/src/storm.py:graph"}'
```

官方提醒：改 `langgraph.json` 后必须重新执行该命令，否则改动不会进入镜像。

---

## 3. `langgraph.json`——配置文件全字段

### 最小可用示例

```json
{
  "$schema": "https://langgra.ph/schema.json",
  "dependencies": ["."],
  "graphs": { "agent": "./my_agent/agent.py:agent" },
  "env": ".env"
}
```

CLI 默认读取当前目录下的 `langgraph.json`（“The LangGraph CLI defaults to using the configuration file named **langgraph.json** in the current directory.”）。JSON Schema：`https://langgra.ph/schema.json`（源文件 `libs/cli/schemas/schema.json`）。

### `graphs`：键名与 `path` 语法

- **键名 = graph ID**。“Mapping from graph ID to path where the compiled graph or a function that makes a graph is defined.” 该 ID 会成为 API 里的 assistant/graph 名字：`assistant_id` 可直接填 graph ID（OpenAPI：“The assistant ID or graph name to run. If using graph name, will default to first assistant created from that graph.”）。
- **字符串形式** `./your_package/your_file.py:variable`：
  - `variable` 是 `langgraph.graph.state.CompiledStateGraph` 实例（官方推荐：“The server loads it once at container startup and reuses it for every run—no compilation overhead per request.”）；
  - 或 `make_graph` 工厂函数：接收 config 字典（`langchain_core.runnables.RunnableConfig`），返回 `StateGraph` / `CompiledStateGraph`。官方提醒工厂函数“run on every invocation”，只在需要 per-run 定制时用。
- **对象形式**（Schema `GraphDef`）：`{"path": "./my_agent/agent.py:agent", "description": "..."}`，`description` 会出现在 API 里。
- 官方补充：graphs 可以是 `StateGraph`、`@entrypoint` 或任何 Pregel 对象，也可指向 “(async) context managers that accept a single configuration argument (of type RunnableConfig) and return a pregel object”。

服务工厂按完整签名分类，额外的 keyword-only 参数也计数。当前验收服务 `langgraph-api 0.16.4` 拒绝含 `config`、`checkpointer`、`store` 三个参数的工厂；Python 可保留该装配函数，另以 `def cli_graph(config): return make_graph(config)` 对接 CLI，让服务注入存储。此处是一份装配逻辑的两种调用适配，不要求没有此需要的图增加两个入口。

### 全字段表（Python；逐字来自官方 CLI 文档 configuration file 表）

| Key | Description（原文） |
| - | - |
| `dependencies` | **Required** unless `source` is set. Array of dependencies for LangSmith API server. 可为 `"."`（本地 Python 包）、含 `pyproject.toml`/`setup.py`/`requirements.txt` 的目录路径（如 `"./"`、`"./local_package"`，**不要写 `"requirements.txt"` 本身**）、或一个 PyPI 包名。 |
| `graphs` | **Required**. Mapping from graph ID to path where the compiled graph or a function that makes a graph is defined. |
| `auth` | Authentication and authorization configuration：`path`（必填，指向 `langgraph_sdk.Auth` 实例，如 `./your_package/auth.py:auth`）、`disable_studio_auth`（默认 `false`）、`allow_langsmith_api_keys`（Agent Server v0.14.0rc2+，默认 `false`）、`openapi`（写入 OpenAPI 的 security schemes）。 |
| `base_image` | Optional. Defaults to `langchain/langgraph-api` or `langchain/langgraphjs-api`. |
| `image_distro` | Optional. Must be one of `"debian"`, `"wolfi"`, `"bookworm"`, or `"bullseye"`. If omitted, defaults to `"debian"`.（`langgraph-cli>=0.2.11`；Wolfi 为官方推荐） |
| `env` | Path to `.env` file or a mapping from environment variable to its value.（Schema：给字符串时“must be a path to a file containing lines in KEY=VALUE format”） |
| `store` | BaseStore 的语义检索 / TTL：`index`（`embed`、`dims`、可选 `fields`）、`ttl`（`refresh_on_read` 默认 `true`、`default_ttl`（分钟）、`sweep_interval_minutes`）。 |
| `ui` | Optional. Named definitions of UI components emitted by the agent, each pointing to a JS/TS file.（`langgraph-cli==0.1.84`） |
| `python_version` | `3.11`, `3.12`, or `3.13`. Defaults to `3.11`. |
| `node_version` | Specify `node_version: 20` to use LangGraph.js. |
| `pip_config_file` | Path to `pip` config file. |
| `pip_installer` | （v0.3+）`"auto"` / `"pip"` / `"uv"`；0.3 起默认走 `uv pip`。 |
| `source` | （`langgraph-cli>=0.4.20`）`{"kind": "uv", "root": "...", "package": "..."}`，从 `uv.lock` 安装（`uv export --frozen`）。**Requires `python_version`**；与 `dependencies` 互斥。 |
| `keep_pkg_tools` | （v0.3.4+）`true` / `false` / `["pip","setuptools","wheel"]`，默认全部卸载。 |
| `dockerfile_lines` | Array of additional lines to add to Dockerfile following the import from parent image. |
| `checkpointer` | `backend`（`"default"`=PostgreSQL / `"mongo"` / `"custom"`）、`path`、`ttl`（`strategy`、`sweep_interval_minutes`、`default_ttl`、`sweep_limit`）、`serde`（`allowed_json_modules`、`pickle_fallback`）。 |
| `http` | `app`（自定义 Starlette/FastAPI）、`cors`、`configurable_headers`、`logging_headers`、`middleware_order`（`auth_first` / `middleware_first`）、`enable_custom_route_auth`、`mount_prefix`，及路由开关 `disable_meta` / `disable_assistants` / `disable_runs` / `disable_threads` / `disable_store` / `disable_ui` / `disable_mcp` / `disable_a2a` / `disable_webhooks`。 |
| `webhooks` | （v0.5.36+）`env_prefix`（默认 `LG_WEBHOOK_`）、`headers`（支持 `${{ env.VAR }}` 模板）、`url`（`allowed_domains`、`allowed_ports`、`require_https`、`disable_loopback`、`max_url_length`）。 |
| `api_version` | （v0.3.7+）固定 Agent Server 语义化版本，如 `"0.2"`，默认 latest。 |
| `encryption` | （Schema）自定义静态加密逻辑 `path`。 |

### 带认证的示例

```json
{
  "$schema": "https://langgra.ph/schema.json",
  "dependencies": ["."],
  "graphs": { "chat": "chat.graph:graph" },
  "env": ".env",
  "auth": {
    "path": "./auth.py:auth",
    "openapi": {
      "securitySchemes": { "apiKeyAuth": { "type": "apiKey", "in": "header", "name": "X-API-Key" } },
      "security": [{ "apiKeyAuth": [] }]
    },
    "disable_studio_auth": false,
    "allow_langsmith_api_keys": false
  }
}
```

### 目录结构约定（官方 application structure）

```plaintext
my-app/
├── my_agent/            # 图代码（__init__.py / agent.py …）
├── .env                 # 环境变量
├── requirements.txt     # 或 pyproject.toml
└── langgraph.json       # CLI 默认读取的配置文件
```

---

## 4. `langgraph dev` / `langgraph up`：本地 server 形态

### dev vs up（官方 “Local development & testing” 对比表，逐字）

| Feature | `langgraph dev` | `langgraph up` |
| - | - | - |
| **Docker required** | No | Yes |
| **Installation** | `pip install langgraph-cli[inmem]` | `pip install langgraph-cli` |
| **Primary use case** | Rapid development & testing | Production-like validation |
| **State persistence** | In-memory & pickled to local directory | PostgreSQL |
| **Hot reloading** | Yes (default) | Optional (`--watch` flag) |
| **Default port** | `2024` | `8123` |
| **Resource usage** | Lightweight | Heavier (build and run separate docker containers for the server, PostgreSQL, and Redis) |
| **IDE Debugging** | Built-in DAP support | Regular container debugging |
| **Custom auth** | Yes | Yes (with license key) |

### `langgraph-api` 与 `langgraph-cli` 的关系

- `langgraph-api` 是**服务端运行时包**。PyPI 描述：“This package implements the LangGraph API for rapid development and testing… The server is backed by a predominently in-memory data store that is persisted to local disk when the server is restarted.”
- 它**不是单独安装**的：`pip install -U "langgraph-cli[inmem]"` 即安装；其 README 明确 “Install the `langgraph-cli` package with the `inmem` extra. Your CLI version must be no lower than `0.1.55`.”
- `langgraph dev` 启动的就是这个 in-memory 模式的 Agent Server（输出横幅来自 `langgraph_api.cli`：`INFO:langgraph_api.cli:`）。生产形态用基础镜像 `langchain/langgraph-api`（`up`/`build`/`deploy` 都基于它）。

### `langgraph dev` 暴露什么

- API 根地址 `http://127.0.0.1:2024`，OpenAPI UI 在 `/docs`。
- CLI 文档原文：“The resulting server exposes all API endpoints for runs, threads, assistants, etc., and includes supporting services such as a managed database for checkpointing and storage.”
- 端点组（Agent Server OpenAPI 的 tags）：`Assistants`、`Threads`、`Thread Runs`、`Stateless Runs`、`Crons`、`Store`、`A2A`、`MCP`、`System`、`Streaming`。
- Studio UI 通过 `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024` 连接；Safari 无法访问 localhost 时用 `--tunnel`。

---

## 5. 图如何被打包成可运行 artifact

**artifact = Docker 镜像**（不是目录）。链路：`langgraph.json` →（`langgraph dockerfile` 生成 Dockerfile / `langgraph build` 直接构建）→ 基于 `langchain/langgraph-api` 的镜像 → 容器内通过 `ENV LANGSERVE_GRAPHS='{"<graph_id>": "<path>:<symbol>"}'` 告诉服务端加载哪些图。

```bash
langgraph new ./my-app --template new-langgraph-project-python  # 1) 可发布目录
langgraph dev -c langgraph.json                                  # 2) 本地验证
langgraph dockerfile -c langgraph.json Dockerfile                # 3) 生成 Dockerfile
langgraph build -t my-agent:latest                                # 4) 构建镜像
langgraph up --image my-agent:latest --port 8123                  # 5) 生产形态本地跑
langgraph deploy -t my-agent:latest --name my-agent               # 6) 上云
```

要点：

- **依赖声明**：`dependencies`（PyPI 包名 / 本地目录）或 `source.kind=uv`（锁文件）；系统级依赖用 `dockerfile_lines`。
- **启动命令**：不需要自己写——基础镜像自带 server 入口，图位置由 `LANGSERVE_GRAPHS` 注入。
- **上云**：GitHub UI 路径（LangSmith UI → Deployments → Import from GitHub，授权 `hosted-langserve` app，指定 `langgraph.json` 完整路径）或 CLI 路径（`langgraph deploy`，本地 build+push）。云端环境变量在 UI 或 `langgraph.json` 的 `env` 配置。
- `base_image` 可钉版本；`image_distro: "wolfi"` 为官方推荐（更小更安全）；`api_version: "0.2"` 可钉服务端语义版本。
- `build` / `up` / `dockerfile` / `deploy` 是可选分发路径；首版验收不默认要求 Docker 构建或托管部署，除非声明的验收范围包含它们。

---

## 6. 运行期契约：thread / checkpoint / 幂等并发 / durability / recursion_limit

### thread 与 checkpoint

- Thread 是**持久化会话容器**：“A thread is a persistent conversation container that maintains state across multiple runs.” 唯一 `thread_id`；每次 run 后状态写回 thread。
- OSS 侧：checkpoint 以 `thread_id` 为主键；**用了 checkpointer 就必须传 `thread_id`**：`{"configurable": {"thread_id": "1"}}`。每个 **super-step** 边界产生一个 checkpoint；节点级写入另存 `checkpoint_writes`（pending writes），可用于恢复已持久化的工作。这些记录不提供外部副作用的 exactly-once 保证：恢复可能重跑当前节点，外部调用仍可能重复。`checkpoint_ns`：空串 = 根图，`"node_name:uuid"` = 子图。
- 服务端 thread 端点：`POST /threads`（可带 `supersteps` 预置初始状态）、`GET /threads/{id}`、`GET /threads/{id}/state`、`GET /threads/{id}/history`、`POST /threads/{id}/state`、`POST /threads/{id}/copy`、`GET /threads/{id}/storage`。
- Run 状态机：`pending | running | error | success | timeout | interrupted`；`Run` 对象带 `run_id`、`thread_id`、`assistant_id`、`multitask_strategy`、`cancel_reason` 等。

### 幂等与并发

- **同一 thread 同时只执行 1 个 run**：“The queue enforces that at most 1 run can be executed for a given thread at one time.”
- 并发策略字段 `multitask_strategy`（枚举 `reject` / `rollback` / `interrupt` / `enqueue`，**默认 `enqueue`**），官方 “Double texting” 页语义：
  - `enqueue`（默认）：当前 run 跑完后再依次处理新输入；
  - `reject`：有 run 在跑时拒绝新 run；
  - `interrupt`：中止当前执行、保留已推进状态，新输入插入后续跑；
  - `rollback`：中止当前执行并回滚（含初始输入），新输入作为全新 run。
- `if_not_exists`：`create` / `reject`（默认 `reject`）——thread 不存在时创建还是报错。
- `on_disconnect`（仅流式 run）：`cancel` / `continue`（默认 `continue`）——客户端断开是否取消运行。
- `checkpoint`：指定恢复点，实现“从某个检查点重放”。
- **官方文档未定义请求级幂等键**；重复 POST `/runs` 会创建新 run（[INFERENCE]：需调用方自行用 `metadata`/外部记录去重）。

### durability

- OSS 侧参数 `durability="sync|async|exit"`（官方 checkpointers 文档逐字）：
  - `"exit"`：只在执行退出时（成功、报错或被 interrupt）持久化，性能最好但中间状态不落盘，进程崩溃无法恢复；
  - `"async"`：下一步执行的同时异步持久化（默认），崩溃时可能丢最近 checkpoint；
  - `"sync"`：每步开始前同步落盘，最耐久但有性能开销。
- 服务端 run 请求字段 `durability` 枚举相同，**默认 `async`**；旧字段 `checkpoint_during` 已 `deprecated`，官方提示 “Use `durability` instead to control checkpoint persistence behavior during the run.” Agent Server 侧：`async` 每步后写、`exit` 只存最终状态。

### recursion_limit

- 放在 **config 顶层**（不在 `configurable` 里）：`graph.invoke({...}, {"recursion_limit": 1000})`；run 请求体对应 `config.recursion_limit`（OpenAPI `Config`：`tags`、`recursion_limit`、`configurable`）。
- 超限抛 `GraphRecursionError`：“Raised when the graph has exhausted the maximum number of steps… run your graph with a config specifying a higher `recursion_limit`.”

---

## 7. 流式接口

### `POST /threads/{thread_id}/runs/stream`

请求体（OpenAPI `RunCreateStreamingStateful` = `RunCreateStateful` + `on_disconnect`）关键字段：

| 字段 | 类型/枚举 | 说明（原文节选） |
| - | - | - |
| `assistant_id` | uuid 或 graph 名 | **required**。`The assistant ID or graph name to run. If using graph name, will default to first assistant created from that graph.` |
| `input` | object/array/string/number/bool/null | The input to the graph. |
| `command` | Command | 另一种输入形式（恢复 / 跳转）。 |
| `stream_mode` | 枚举或枚举数组，默认 `["values"]` | `values`、`messages`、`messages-tuple`、`tasks`、`checkpoints`、`updates`、`events`、`debug`、`custom` |
| `stream_subgraphs` | bool，默认 `false` | Whether to stream output from subgraphs. |
| `stream_resumable` | bool，默认 `false` | Whether to persist the stream chunks in order to resume the stream later. |
| `durability` | `sync`/`async`/`exit`，默认 `async` | Durability level for the run. |
| `multitask_strategy` | `reject`/`rollback`/`interrupt`/`enqueue`，默认 `enqueue` | Strategy to handle concurrent runs on the same thread. |
| `if_not_exists` | `create`/`reject`，默认 `reject` | How to handle missing thread. |
| `on_disconnect` | `cancel`/`continue`，默认 `continue` | The disconnect mode to use. |
| `config` | `{tags, recursion_limit, configurable}` | The configuration for the assistant. |
| 其它 | `metadata` / `context` / `webhook` / `feedback_keys` / `after_seconds` / `interrupt_before` / `interrupt_after` / `checkpoint` | 运行元数据、静态上下文、完成后回调、反馈键、延迟启动、中断节点、恢复点。 |

SSE 响应帧形状（OpenAPI 描述逐字）：

```
id: 1

event: message

data: {}
```

响应头带 `Content-Location`：“The URL of the run that was created. Can be used to later join the stream.”

```bash
curl --request POST \
--url <DEPLOYMENT_URL>/threads/<THREAD_ID>/runs/stream \
--header 'Content-Type: application/json' \
--data '{"assistant_id": "agent", "input": {"topic": "ice cream"}, "stream_mode": "updates"}'
```

SDK 侧读到 `chunk.event` + `chunk.data`；`stream_mode="messages-tuple"` 时 `chunk.event == "messages"`，`chunk.data` 是 `(message_chunk, metadata)` 元组；多模式时传数组，输出为 `(mode, chunk)` 元组。

### 其它流式端点

| 端点 | 用途 | 关键点 |
| - | - | - |
| `POST /runs/stream` | 无状态流式 run | `thread_id` 传 `None`；不落盘。 |
| `GET /threads/{thread_id}/stream` | 订阅整个 thread 的所有 run 输出 | 查询参数 `stream_modes`（`lifecycle` / `run_modes`（默认） / `state_update`）；支持 `Last-Event-ID` 断线续传（传 `-` 从头）。 |
| `GET /threads/{thread_id}/runs/{run_id}/stream` | join 已有后台 run | 官方警告：**不缓冲**，join 之前的输出收不到。 |
| `POST /threads/{thread_id}/stream/events` | Protocol v2 事件流 | 体 `ProtocolEventStreamRequest`（`channels`、`namespaces`、`depth`、`since`）；每帧 `event:` = 事件 `method`，`data:` = JSON 编码的 `ProtocolEvent`，`id:` = `seq`。示例：`id: 42` / `event: messages` / `data: {"type":"event","event_id":"42","seq":42,"method":"messages","params":{"namespace":[],"timestamp":1700000000000,"data":{...}}}`。 |

（Protocol v2 规范：https://langchain-ai.github.io/agent-protocol/streaming/ ）

---

## 8. 认证，以及本地 CLI 与托管平台的边界

### 认证模型

- **LangSmith（云）**：默认用 LangSmith API key，请求头 `x-api-key`（server-api-ref：“Pass the `X-Api-Key` header with each request to the Agent Server.”）。
- **自托管**：**No default authentication**（“Complete flexibility to implement your security model”）。
- **自定义认证**：`langgraph.json` 的 `auth.path` 指向 `langgraph_sdk.Auth` 实例；`@auth.authenticate` 做身份识别（返回 `identity` 等），`@auth.on` / `@auth.on.threads.create` 等做按资源授权（返回过滤字典限制可见资源）。认证信息通过 `config["configuration"]["langgraph_auth_user"]` 暴露给图代码。
- `auth.disable_studio_auth=true` → Studio 不再回退用 LangSmith 凭据；`auth.allow_langsmith_api_keys=true`（Agent Server v0.14.0rc2+）→ 自定义 auth 与 LangSmith API key 并行。

### 只在托管平台（或需要平台设施）可用的能力

| 能力 | 本地 `langgraph dev` | 备注 |
| - | - | - |
| assistants / threads / runs / store / crons 全套 REST API | ✅ | dev 起的就是完整 Agent Server。 |
| **Double texting（`multitask_strategy`）** | ✅ 字段存在 | 官方标注：“Double texting is a feature of LangSmith Deployment. It is not available in the LangGraph open source framework.” |
| 生产级持久化 | ❌（in-memory + 本地落盘） | `langgraph up` 才有 PostgreSQL/Redis；生产需 license key。 |
| 自动扩缩容、Serverless 缩容到 0、Dedicated 独占数据库与高可用 | ❌ | Cloud 专属；部署类型创建后不可改。 |
| 数据区域（US/EU）、静态出口 IP、25 MB 请求体上限 | ❌ | Cloud 专属（超限返回 `413 Payload Too Large`）。 |
| 托管 Postgres 免运维 | ❌ | “There is no direct access to the database. All access to the database occurs through the Agent Server.” |
| GitHub 自动构建/自动更新部署、预览构建、修订版本 | ❌（本地只能 `langgraph deploy` 一次） | 走 UI 的 `hosted-langserve` app。 |
| `N_JOBS_PER_WORKER` 并发调优 | 默认固定 | Cloud/自托管可用环境变量调。 |

### 配置层面的本地 vs 云差异

- 本地：`langgraph.json` 的 `env` 指向 `.env`；生产则“在部署环境里配环境变量”（application-structure 原话）。
- 本地 `langgraph up` 支持 `--postgres-uri` 指定数据库；云端由平台自动建库。
- `base_image` / `api_version` / `image_distro` 只在构建镜像时生效；`langgraph dev` 不构建镜像。
- 云端 `langgraph deploy` 需要 LangSmith API key + Plus 计划及以上；本地 `langgraph dev` 只需一个能连 Studio 的 API key（Studio 用 `baseUrl` 指向本地 server）。

---

## 9. 差异表：本地纯 Python 执行 vs CLI/平台服务执行

| 维度 | 纯 Python（`graph.invoke`） | CLI/平台服务（Agent Server） |
| - | - | - |
| 入口 | `from my_pkg import graph; graph.invoke(input, config)` | `POST /threads/{id}/runs/stream`、`client.runs.stream(...)` |
| 输入 | 直接传 Python 对象 | JSON（`input` 支持 object/array/string/number/bool/null） |
| 输出 | Python 原生对象 / 生成器 | JSON / SSE 帧 |
| checkpointer | 自己 `graph.compile(checkpointer=...)`；`InMemorySaver` 进程重启即丢 | **服务端自动注入**（“the server automatically injects the checkpointer and memory store configured for that deployment at runtime. **Do not configure these in your graph code**”） |
| store | 自己传 `store=` | 同上，自动注入 |
| `thread_id` | `config={"configurable": {"thread_id": "1"}}` | 路径参数 `thread_id`（或 `null` 走无状态 run） |
| `recursion_limit` | config 顶层键 | 请求体 `config.recursion_limit` |
| `durability` | 调用参数 `durability="sync\|async\|exit"` | 请求体 `durability`（默认 `async`） |
| 并发控制 | 自己管（进程内无服务端队列） | `multitask_strategy` + 服务端队列保证同 thread 串行 |
| 流式 | `graph.stream(..., stream_mode=...)`；取值 `values/updates/messages/messages-tuple/custom/debug/events` | 请求体 `stream_mode`，服务端还多 `tasks`、`checkpoints`；另有 `stream_subgraphs`、`stream_resumable` |
| 认证 | 无（进程内） | `x-api-key` 或 `@auth.authenticate` |
| 打包 | 无需 | 必须有 `langgraph.json` + `dependencies`/`source` |
| 图对象 | 任意 Python callable | 必须是 compiled Pregel 对象，或接受 `RunnableConfig` 并返回 Pregel 的工厂函数 |
| 错误 | Python 异常 | HTTP 状态码 + `{"detail": ...}` |

**同一份图代码要同时满足两边**：(a) 导出可被 `langgraph.json` 指向的 compiled graph **或**工厂函数，二选一即可；(b) 不在图代码里硬编码 checkpointer/store（否则服务端会替换你的实现）；(c) 不依赖服务端注入的 `langgraph_auth_user` 等配置才能跑通纯 Python 路径。

---

## 10. 本项目产物的落地要求（把图注册成 CLI 可发现的图）

```plaintext
my-skill-graph/
├── source/
│   └── original-skill/     # 完整源 Skill 包，保留原目录名和结构
│       ├── SKILL.md
│       └── ...             # 原包的其他目录与文件
├── skill_graph/            # 新生成代码使用固定、合法的 Python 包名
│   ├── __init__.py
│   └── graph.py            # 选出 compiled graph 或 make_graph(config) 之一
├── langgraph.json
├── pyproject.toml          # 依赖声明（或 requirements.txt）
└── README.md               # 输入输出映射、依赖、配置和验证边界
```

源名含连字符等字符时保留在 `source/` 目录及目标允许的 graph ID 中；Python 模块和变量使用合法标识符，映射记录在 `README.md`。源包内脚本留在 `source/original-skill/` 下；转换 Skill 自身脚本与生成应用分开，不复制到应用根目录。

```json
{
  "$schema": "https://langgra.ph/schema.json",
  "dependencies": ["."],
  "graphs": { "my_skill": "./skill_graph/graph.py:graph" },
  "python_version": "3.11"
}
```

```python
# skill_graph/graph.py
from langgraph.graph import StateGraph, START, END

def build_graph():
    builder = StateGraph(SkillState)
    builder.add_node("run_skill", run_skill)
    builder.add_edge(START, "run_skill")
    builder.add_edge("run_skill", END)
    return builder.compile()          # 不传 checkpointer / store

graph = build_graph()
```

需要 per-run 定制时，可让配置指向工厂函数 `make_graph(config)`；普通路径只导出 `graph`，不要求两个符号并存。`.env` 仅在确有配置需要时创建。

自检清单（Python 与 CLI 两条调用路径检查同一入口）：

1. `python -c "from skill_graph.graph import graph; print(graph.invoke({...}))"` 可用；
2. `langgraph dev -c langgraph.json` 启动后，`POST /threads/{id}/runs/stream` 带 `assistant_id="my_skill"` 能跑通；
3. 输入输出契约与源 Skill 一致（键名、类型、可选字段），不要为适配平台改语义；
4. 外部工具、服务或凭据缺失时，仍生成真实调用与依赖声明；加载或运行未完成时记为环境受阻或未验证，不能计作通过。
5. Docker 构建、`langgraph up` 和托管部署仅在验收范围明确包含时检查，不作为默认必验项。

---

## 来源

**官方文档站（docs.langchain.com）**

- LangGraph CLI（子命令、选项表、`langgraph.json` 全字段、deploy/dockerfile/up）：https://docs.langchain.com/langsmith/cli
- Application structure（目录结构、依赖、graphs、env）：https://docs.langchain.com/oss/python/langgraph/application-structure
- Run a local server（`langgraph dev` 流程与输出）：https://docs.langchain.com/oss/python/langgraph/local-server.md
- Local development & testing（dev vs up 对比表）：https://docs.langchain.com/langsmith/local-dev-testing.md
- Agent Server（运行时架构、持久化、任务队列、run 生命周期）：https://docs.langchain.com/langsmith/agent-server.md ｜ overview：https://docs.langchain.com/langsmith/agent-server-overview.md
- Use threads（thread 语义与端点）：https://docs.langchain.com/langsmith/use-threads.md ｜ Runs：https://docs.langchain.com/langsmith/runs.md
- Streaming API（stream_mode 表、thread streaming、`Last-Event-ID`）：https://docs.langchain.com/langsmith/streaming.md
- Double texting（multitask 四种语义、平台限定）：https://docs.langchain.com/langsmith/double-texting.md
- Authentication & access control（`@auth.authenticate` / `@auth.on`、默认安全模型）：https://docs.langchain.com/langsmith/auth.md
- 部署：https://docs.langchain.com/langsmith/deploy-to-cloud-overview.md ｜ https://docs.langchain.com/langsmith/deploy-to-cloud.md ｜ Cloud platform features（部署类型、扩缩容、25 MB 上限、数据区域）：https://docs.langchain.com/langsmith/cloud-platform-features.md
- API reference 入口与认证说明：https://docs.langchain.com/langsmith/server-api-ref.md ｜ OpenAPI 原文（端点、SSE 帧形状、`RunCreate*` 字段）：https://docs.langchain.com/langsmith/agent-server-openapi.json
- Checkpointers（durability 三档、checkpoint/thread/checkpoint_ns、pending writes）：https://docs.langchain.com/oss/python/langgraph/checkpointers.md ｜ Persistence：https://docs.langchain.com/oss/python/langgraph/persistence.md ｜ GRAPH_RECURSION_LIMIT：https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT.md

**官方 API 参考（reference.langchain.com）**

- `langgraph_cli` 命令函数（`new(path, template)`、`validate(config)` 等）：https://reference.langchain.com/python/langgraph-cli/ ｜ https://reference.langchain.com/python/langgraph-cli/cli/new ｜ https://reference.langchain.com/python/langgraph-cli/cli/validate
- `GraphRecursionError`（`recursion_limit` 位置与语义）：https://reference.langchain.com/python/langgraph/errors/GraphRecursionError

**官方仓库源码 / README / JSON Schema / 包元数据**

- `langgraph.json` JSON Schema（字段类型、枚举、`GraphDef`、`AuthConfig`、`HttpConfig`、`StoreConfig`、`CheckpointerConfig`、`UvSource`、`WebhooksConfig`）：https://raw.githubusercontent.com/langchain-ai/langgraph/refs/heads/main/libs/cli/schemas/schema.json
- LangGraph CLI README（`new/dev/up/build/dockerfile` 速查、示例 `langgraph.json`）：https://raw.githubusercontent.com/langchain-ai/langgraph/main/libs/cli/README.md
- `langchain` CLI 命令树与 `app` 命名空间源码（tag `langchain-cli==1.0.0a1`）：https://raw.githubusercontent.com/langchain-ai/langchain/langchain-cli%3D%3D1.0.0a1/libs/cli/langchain_cli/cli.py ｜ https://raw.githubusercontent.com/langchain-ai/langchain/langchain-cli%3D%3D1.0.0a1/libs/cli/langchain_cli/namespaces/app.py
- `langchain` CLI 被删除的 commit（`chore: delete CLI (#34855)`，2026-01-23）：https://github.com/langchain-ai/langchain/commit/4e9a1eb2834695d637742c3ff232d55ba5db7e57 ｜ `langchain` v1 包无 CLI 入口：https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/langchain_v1/pyproject.toml
- 包元数据（版本、依赖、`langgraph-api` 与 `langgraph-cli[inmem]` 的关系、in-memory + 本地落盘语义）：https://pypi.org/project/langgraph-api/ ｜ https://pypi.org/project/langchain-cli/ ｜ https://pypi.org/project/langgraph-cli/ ｜ https://pypi.org/project/langgraph/
- Agent Protocol 流式规范（Protocol v2 帧、channel/namespace/since 语义）：https://langchain-ai.github.io/agent-protocol/streaming/

**本文中的推断（未由一手来源逐字确认）**

- `langgraph.json` 中 `graphs` 的相对路径按 `langgraph.json` 所在目录解析——文档未逐字说明，依据是 `langgraph build --build-command` 的 “Runs from the directory where your `langgraph.json` file lives”。
- 服务端缺少请求级幂等键，因此重复提交 run 需调用方自行去重——文档只提供 `multitask_strategy` / `if_not_exists` / `checkpoint`，未定义幂等键。
- “`langchain` CLI 已下线”的依据是官方删除 commit + 官方文档索引中无对应页面，而非官方公告中的 “deprecated” 字样。
