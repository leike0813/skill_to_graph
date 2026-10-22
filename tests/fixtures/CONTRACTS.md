# 受控源样本契约与可观察预期

本文件记录 `tests/fixtures/skills/` 下两个受控源样本的源契约与可观察预期，供转换验收使用。
预期来自源包 `SKILL.md` 的规定，不是从生成图的行为倒推得到；生成图与本文件冲突时以源契约为准。

两个样本都是合成的验收素材，不代表真实业务记录或真实观察结果。

## 覆盖范围

| 样本 | 流程类型 | 覆盖的验收风险 |
| --- | --- | --- |
| `fixed-file` | 固定流程 | 资源读取、包内脚本、校验失败停止、人工确认分支、文件副作用、已有文件冲突、写入失败不重试 |
| `mixed-retrieval` | 混合流程 | 自主键选择、语义充分性循环、证据引用、人工确认分支、文件副作用、工具故障停止 |

覆盖的验收矩阵行：固定流程与分支循环、人工确认与恢复、文件及脚本副作用、失败与外部依赖。
未覆盖：Python 与 CLI 双入口差异、并行写入、迁移远端依赖、真实外部服务接入。

## fixed-file

### 源契约

- 输入：`source_csv`（UTF-8 CSV，首次调用时由调用方给出）、`output_dir`（首次调用时由调用方给出）、
  `approved`（第 3 步确认后由用户回复得到，不要求提前提供）。
- 流程次序固定：校验 CSV → 计算并生成计划 → 请求确认 → 按回复处理。
- CSV 必需列 `name` 与 `count`；`count` 必须是非负整数；空白行忽略。
- 计算由包内 `scripts/render.py` 完成：只读 CSV 与 `templates/summary.txt`（格式 `Total: {total}`），
  向 stdout 打印 JSON 计划，不写文件。
- `rows` 为数据行数（不含表头），`total` 为所有数据行 `count` 之和。
- 写入由执行者用真实写入能力完成，脚本不承担写入。
- 目标文件为 `<output_dir>/summary.txt`；`output_dir` 不存在则创建；目标已存在则失败且不覆盖。
- 失败策略：校验失败、脚本失败、写入出错均停止且不重试。

### 可观察预期

成功写入时返回 `status`=`ok`、`rows`、`total`、`path`；未批准时返回 `status`=`cancelled` 且 `path` 不出现；
失败时返回 `status`=`error` 并带结构化错误（错误码、位置、原因）。
状态字符串不代替实际文件，文件是否存在由写入方确认。

### 场景与样例

| 场景 | 输入 | 预期 |
| --- | --- | --- |
| valid | `data/example.csv`（`a,2` 与 `b,3`），用户回复 `true` | `rows`=2、`total`=5；写入 `<output_dir>/summary.txt`，内容为 `Total: 5\n`（模板渲染结果） |
| invalid CSV | 表头缺 `count`，或某行 `count` 为 `-1` / `2.5` / 空值 | 校验失败即停止，返回结构化错误，不写任何文件；不重试 |
| refusal | 用户回复 `false`（或其它非 `true` 内容） | 返回 `cancelled`，不写任何文件，`output_dir` 不被创建 |
| existing file | `<output_dir>/summary.txt` 已存在，用户回复 `true` | 失败并返回结构化错误，已有文件内容不变；不覆盖、不重试 |
| 写入错误 | `output_dir` 不可写 | 停止并返回结构化错误，不重试、不换路径重试 |

`scripts/render.py` 的可观察行为：成功退出码 0，stdout 为含 `rows`、`total`、`content` 的 JSON；
失败退出码非 0，stdout 为含 `error`（`code`、`path`、`detail`）的 JSON；任何情况下都不创建文件。

### 样例数据的确定性

`data/example.csv` 固定为两行数据，渲染结果固定为 `Total: 5\n`，与当前时钟、路径和环境无关。

## mixed-retrieval

### 源契约

- 输入：`question`（非空，首次调用时由调用方给出）、`catalog`（UTF-8 JSON 对象，首次调用时由调用方给出）、
  `output_dir`（写入前确定）。
- 流程次序固定：校验输入 → 检索并判断充分性 → 报告提案与确认 → 按回复处理。
- 检索只能通过 `lookup(key)` 工具读取 catalog 中某个键的证据文本；不使用外部搜索或网络检索。
- 键的选择和证据是否足以回答问题由模型按语义判断；证据不足时继续 `lookup`，
  catalog 中没有能支持答案的证据时返回 `insufficient`。
- 停止条件是语义上的证据充分或证据不可得，不是检索次数，也不是报告字数。
- `lookup` 调用故障时停止，返回 `failed`，不重试。
- 报告提案需标注所依据的证据键；确认后写入 `<output_dir>/report.md`，目标已存在则失败且不覆盖。
- 写入由执行者用真实写入能力完成；校验失败、证据不足、工具故障、用户未确认时都不写文件。

### 可观察预期

检索阶段的模型输出固定为 `status`（`sufficient` 或 `insufficient`）、`report`、`used_keys` 三个字段。
业务结果为 `status`（`ok` / `cancelled` / `insufficient` / `failed` / `error`）、适用时的 `report` 与 `path`、
`used_keys`，以及失败时的结构化 `error`。

### 场景与样例

| 场景 | 输入 | 预期 |
| --- | --- | --- |
| valid | `question` 可由 `examples/catalog.json` 的 `alpha` 或 `beta` 支撑，用户回复 `true` | 模型自行选键并据语义判断充分后返回 `status`=`sufficient`、`used_keys` 含所用键；确认后写入 `<output_dir>/report.md`，内容含结论与证据键引用 |
| insufficient | `question` 只能由 `empty`（`No relevant material`）或 catalog 中不存在的键支撑 | 返回 `status`=`insufficient`，不写任何文件；不以检索次数或字数作为判据 |
| sufficiency 循环 | 初始检索到的键不足以回答，需再取一个键 | 模型先取键、判为不足、再取下一个键，直到语义上充分；轮次由模型决定，流程不按次数截断 |
| lookup 故障 | `lookup` 调用失败 | 停止并返回 `status`=`failed` 与错误信息，不重试、不写文件 |
| invalid 输入 | `question` 为空、`catalog` 不存在或不是可解析的 JSON 对象 | 校验失败即停止，不调用 `lookup`，不写任何文件，返回 `status`=`error` 与结构化错误 |
| refusal | 用户回复 `false` | 返回 `status`=`cancelled`，不写任何文件，`output_dir` 不被创建 |
| existing file | `<output_dir>/report.md` 已存在，用户回复 `true` | 失败并返回结构化错误，已有文件内容不变；不覆盖、不重试 |

### 样例数据的确定性

`examples/catalog.json` 固定为三个键：`alpha`、`beta`、`empty`。键与文本固定，与时钟、路径和环境无关。

### 运行前提

`lookup(key)` 是环境提供的本地文件工具，读 catalog 文件并返回该键的证据文本，不需要网络访问。
充分性判断与键选择需要真实模型；没有模型时该样本的相关验收记为环境受阻，不计通过。

## 说明

- 本文件不记录具体措辞快照，也不要求生成图与源包逐字一致；只核对上表列出的可观察行为。
- 上表未列出的行为属于源契约未规定范围，不作判定依据。
- 完整样本包随转换产物一并快照，生成图应能在脱离原包路径后读取包内资源。
