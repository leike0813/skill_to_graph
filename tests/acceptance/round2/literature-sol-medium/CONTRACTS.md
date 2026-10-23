# 本轮范围

从空 DB 分别运行一次已有 round2 literature-analysis 图和一次 omp 直接执行同一份源包快照。
不重新转换或修改图。两组使用相同论文 Markdown、zh-CN、score_only=false、arXiv:1706.03762。
图主阶段和批次均使用本地 Responses 的 gpt-6.1-sol / medium；omp 主执行与批次均指定
opencodex-hub/gpt-6.1-sol / medium，禁止模型 fallback。保持 TLS 验证，不保存凭据。

验收检查复用第一轮 compare.py 的只读检查函数，以本轮 ROOT 和实际源快照替换路径常量。
检查六份产物、最终 JSON 与镜像及 DB 一致、源 schema、阶段回执与错误、同输入 hash。
语义审阅单独覆盖中文摘要/引文、关键数值与实验设置、引文解释的证据范围及批次边界。
两组输出相似或 HTTP 成功不计为保真通过；源失败与运行环境错误分别记录。

最终产物只由源 runtime 渲染，不手工填入旧结果或修改公开文件。仅发生源允许的正式修正时
记录对应失败与修正；本轮不自动重试模型错误。只运行 Python 图入口，不启动 CLI 服务。
不验证其他输入格式、score-only、搬移、生产恢复或外部副作用 exactly-once。
