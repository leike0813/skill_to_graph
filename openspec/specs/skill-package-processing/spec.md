# skill-package-processing Specification

## Purpose

使转换器从一个合法 Agent Skill 包路径开始工作，取得可核对的源包信息并完整携带资源，同时保留源包及已有文件，避免把运行环境缺口变成额外的源材料要求。

## Requirements

### Requirement: Source package is the sole required conversion input
转换器 MUST 以合法源包路径为唯一必需转换输入；输出位置可选。源运行环境配置、执行记录及模型凭据 SHALL NOT 成为开始转换的普遍前提。

#### Scenario: Start with a self-contained package
- **WHEN** 用户只提供合法且自足的源包路径
- **THEN** 转换器取得包内指令与资源开展转换，不要求用户先提供运行记录或服务凭据

### Requirement: Deterministic package inspection
包处理工具 MUST 检查包根的 `SKILL.md` 及适用的 Agent Skills 元数据约束，并提供元数据和文件清单。包中任意目录的资源 MUST 纳入盘点，检查失败 MUST 给出可定位的问题。

#### Scenario: Inventory a nonstandard resource directory
- **WHEN** 合法源包包含正文引用的 `templates/` 等非约定目录
- **THEN** 文件清单包含这些资源，不因目录不叫 `references`、`scripts` 或 `assets` 而遗漏

#### Scenario: Report invalid source metadata
- **WHEN** 必需的核心指令文件缺失或其元数据不符合适用规范
- **THEN** 工具报告对应路径和结构化问题，不将该源包报告为检查通过

### Requirement: Complete source snapshot
转换器 MUST 完整携带源包的文件和相对目录结构，保留资源内容及脚本执行所需属性，并与新生成代码分放。文件复制 SHALL NOT 改写原源包。

#### Scenario: Preserve dynamically selected resources
- **WHEN** 源脚本在运行时选择包内资源文件
- **THEN** 复制后的源包仍包含该文件及其原有相对布局，不按静态引用裁剪源包

### Requirement: Non-overlapping fresh output destination
未指定输出位置时，转换器 SHALL 使用任务工作目录下的 `<skill-name>-graph/`。目标已存在或与源包重叠时 MUST 报告冲突并请求另选位置，SHALL NOT 自动覆盖源包或已有文件。

#### Scenario: Destination already exists
- **WHEN** 默认或显式目标目录已存在
- **THEN** 转换器报告冲突，不覆盖该目录中的已有内容

#### Scenario: Destination overlaps source
- **WHEN** 路径解析后目标与源包相同、包含源包或位于源包内部
- **THEN** 转换器拒绝该写入位置并说明冲突，不产生递归复制

### Requirement: Stable helper command results
辅助命令 MUST 提供帮助信息、明确退出码及成功和失败均可机器读取的稳定结果结构。结果 MUST 区分实际检查数据与问题，无法读取或复制的内容不得作为成功处理。

#### Scenario: Recover from an invalid invocation
- **WHEN** 调用参数无效、路径不可读或复制失败
- **THEN** 命令返回非成功退出码及结构化问题，调用方无需解析完整错误文案才能识别失败
