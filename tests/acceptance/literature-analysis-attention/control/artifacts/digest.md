## TL;DR

论文针对序列转导模型长期依赖循环与卷积、无法在样本内并行、且长距离依赖路径过长的问题，提出只依赖注意力机制的 Transformer 架构，完全去掉循环与卷积。

Transformer 保留编码器-解码器结构：编码器由 N=6 层相同的 multi-head self-attention 与逐位置前馈网络堆叠而成，解码器在此基础上增加一层对编码器输出的 multi-head attention，并用掩码阻止解码位置看到未来位置。

核心算子是 Scaled Dot-Product Attention：把 query 与 key 的点积除以 sqrt(d_k) 后再 softmax，从而避免大维度下点积过大把 softmax 推入极小梯度区域。

Multi-Head Attention 用 h=8 组不同的线性投影并行做注意力（d_k=d_v=d_model/h=64）再拼接输出，使模型能同时关注不同表示子空间与不同位置；单头时平均效应会抑制这种能力。

由于模型不含循环与卷积，作者用正弦-余弦位置编码注入序列顺序信息，并称其有望外推到比训练时更长的序列。

训练使用 Adam，学习率按 d_model^-0.5 与 warmup（warmup_steps=4000）结合的公式变化；正则化包括残差 dropout（P_drop=0.1）和标签平滑（epsilon_ls=0.1）。

实验在 WMT 2014 英德与英法翻译任务上进行：big 模型取得 28.4 BLEU（英德）与 41.0 BLEU（英法），英德任务超过此前最好结果与集成模型 2 BLEU 以上，而训练成本更低。

消融显示单头注意力比最佳设置低 0.9 BLEU，减小 d_k 伤害质量，模型越大越好，dropout 有明显帮助；正弦位置编码与可学习位置嵌入结果几乎相同。

泛化实验在 WSJ Penn Treebank 组句分析上得到 91.3 F1，仅次于循环神经语法模型，说明架构可迁移到文本以外的序列任务。

作者明确指出注意力平均带来的有效分辨率下降是需要付出的代价，并指出当序列长度超过表示维度时自注意力的复杂度优势会减小，因此提出限制局部注意力等未来方向。

复现线索：论文给出训练数据规模、词表大小、批量 token 数、GPU 型号与训练步数、推理超参（beam size=4、长度惩罚 alpha=0.6、检查点平均），并公开代码仓库 https://github.com/tensorflow/tensor2tensor。


## 研究问题与贡献

- 研究问题：能否在保持甚至提升翻译质量的前提下，用完全基于注意力的架构取代循环与卷积，从而消除序列建模中的顺序计算瓶颈并大幅提升训练并行度？


- 提出 Transformer：首个完全基于自注意力、不使用序列对齐 RNN 或卷积的转导模型

- 提出 Scaled Dot-Product Attention，用 1/sqrt(d_k) 缩放点积以稳定 softmax 梯度

- 提出 Multi-Head Attention，在多个表示子空间并行做注意力

- 给出基于正弦-余弦函数的位置编码，使无循环模型仍能利用序列顺序并有望外推更长序列

- 在 WMT 2014 英德、英法翻译上以更低训练成本刷新 BLEU 纪录（28.4 / 41.0）

- 在架构变体实验与英语组句分析任务上验证组件有效性与任务可迁移性


## 方法要点

- 编码器：N=6 层，每层含 multi-head self-attention 与逐位置全连接前馈网络两个子层，子层外包裹残差连接并接 layer normalization

- 解码器：同为 N=6 层，额外插入一层以编码器输出为 memory 的 multi-head attention，并对自注意力子层做掩码以保证自回归性

- Scaled Dot-Product Attention：Attention(Q,K,V)=softmax(QK^T/sqrt(d_k))V

- 与加性注意力对比：点积注意力理论复杂度相近但实现更快更省空间，未缩放的点积注意力在 d_k 较大时劣于加性注意力

- Multi-Head Attention：用 h 组不同的学习到的线性投影分别处理 query/key/value，并行注意力后拼接再投影，h=8、d_k=d_v=64

- 三种注意力用法：编码器-解码器注意力、编码器自注意力、带掩码的解码器自注意力（掩码通过把 softmax 输入置为 −∞ 实现）

- 逐位置前馈网络 FFN(x)=max(0,xW1+b1)W2+b2，d_model=512、d_ff=2048，相当于两个卷积核为 1 的卷积

- Embedding 与 softmax 共享同一权重矩阵，embedding 权重按 sqrt(d_model) 缩放

- 位置编码采用不同频率的正弦与余弦函数，波长构成 2π 到 10000·2π 的几何级数

- 优化器 Adam（beta1=0.9, beta2=0.98, eps=1e-9），学习率按 d_model^-0.5 * min(step^-0.5, step*warmup_steps^-1.5) 变化

- 正则化：子层输出残差 dropout 与 embedding+位置编码求和处的 dropout（P_drop=0.1），以及标签平滑 epsilon_ls=0.1


## 关键结果

- WMT 2014 英德翻译：big 模型 BLEU 28.4，比此前最好结果（含集成）高 2 BLEU 以上，训练 3.5 天、8 块 P100

- WMT 2014 英法翻译：big 模型 BLEU 41.0，超过此前所有单模型，训练成本不到此前最好模型的 1/4

- base 模型训练 100,000 步（约 12 小时，8×P100，每步约 0.4 秒），仍超过此前已发表的所有模型与集成

- Table 1 复杂度对比：self-attention 每层 O(n²·d)、顺序操作 O(1)、最大路径长度 O(1)；recurrent 为 O(n·d²)/O(n)/O(n)；convolutional 为 O(k·n·d²)/O(1)/O(log_k(n))

- 消融：单头注意力比最佳设置低 0.9 BLEU，头数过多时质量同样下降；减小 d_k 损害模型质量

- 消融：更大模型效果更好，dropout 对抑制过拟合有明显帮助（rows C、D）

- 位置编码变体：正弦位置编码与可学习位置嵌入（row E）结果几乎一致

- 英语组句分析（WSJ Section 23）：4 层 Transformer F1 91.3，仅次于循环神经语法模型的 91.7；半监督设置下同为 91.3，低于 McClosky 等的 92.1

- 推理设置：beam size=4、长度惩罚 alpha=0.6，base 平均最后 5 个检查点、big 平均最后 20 个检查点


## 局限与可复现性线索

- 注意力是加权平均，作者承认会降低有效分辨率（reduced effective resolution）

- 自注意力复杂度为 O(n²·d)，序列长度大于表示维度时不再比循环层更快，长序列需靠限制局部注意力

- 论文中若干正文与表格被截断（如 Table 2/3/4 与部分段落以省略号结束），部分超参细节需依赖完整版论文

- 解析任务仅做少量超参选择实验，且只在 Section 22 调参，未做任务特定调优

- 复现线索：训练/评估代码已开源于 https://github.com/tensorflow/tensor2tensor；文中给出数据规模、词表大小、批量规模、GPU 型号、训练步数与推理超参，但未列出完整软件依赖版本


## 分章节总结

### Abstract

- 指出当时最好的序列转导模型基于复杂循环或卷积网络，编码器与解码器之间再由注意力连接

- 提出完全基于注意力机制的新架构 Transformer，彻底去掉循环与卷积

- 在两个机器翻译任务上质量更优、并行度更高、训练时间显著更短

- 摘要给出英德任务 28.4 BLEU，超过含集成在内的既有最好结果 2 BLEU 以上



### 1 Introduction

- 回顾 LSTM [13]、门控循环网络 [7] 在序列建模与机器翻译 [35, 2, 5] 中的统治地位，以及后续对循环语言模型与编码器-解码器架构的改进 [38, 24, 15]

- 指出循环模型沿符号位置分解计算、逐时间步生成隐状态，样本内无法并行，长序列时受内存限制难以批处理

- 承认因子分解技巧 [21] 与条件计算 [32] 提升了计算效率，但顺序计算的根本约束仍在

- 指出注意力机制已成为序列建模的组成部分 [2, 19]，但除少数工作 [27] 外仍与循环网络配合使用

- 提出 Transformer 仅靠注意力建立全局依赖，显著提升并行度，在 8 块 P100 上训练 12 小时即可达到新的翻译质量水平



### 2 Background

- 介绍以卷积为基本单元、并行计算所有位置表示的 Extended Neural GPU [16]、ByteNet [18]、ConvS2S [9]

- 指出这些模型中关联两个位置所需的操作数随距离增长（ConvS2S 线性、ByteNet 对数），使远距离依赖更难学习 [12]

- 说明 Transformer 将该操作数降为常数，代价是注意力加权平均导致有效分辨率下降

- 回顾 self-attention（intra-attention）在阅读理解、抽象摘要、文本蕴含、任务无关句表示等任务上的成功应用 [4, 27, 28, 22]

- 说明端到端记忆网络基于循环注意力机制，在简单问答与语言建模上表现良好 [34]

- 声明 Transformer 是首个完全依靠 self-attention、不使用序列对齐 RNN 或卷积的转导模型，并将与 [17, 18]、[9] 比较



### 3 Model Architecture

- 沿用主流编码器-解码器结构 [5, 2, 35]：编码器把输入符号序列映射为连续表示，解码器自回归地逐个生成输出符号，每步消费已生成符号 [10]

- 给出模型整体架构图（Figure 1），左半为编码器、右半为解码器

- 编码器与解码器均由堆叠的自注意力层和逐位置全连接层构成



### 3.1 Encoder and Decoder Stacks

- 编码器为 N=6 层相同结构，每层含 multi-head self-attention 与逐位置前馈网络两个子层

- 每个子层使用残差连接 [11] 并接 layer normalization [1]，输出为 LayerNorm(x + Sublayer(x))

- 所有子层与 embedding 层输出维度 d_model=512

- 解码器同为 N=6 层，额外插入一层对编码器堆叠输出做 multi-head attention 的子层

- 解码器自注意力子层加入掩码阻止关注后续位置，配合输出 embedding 偏移一位，保证位置 i 的预测只依赖 i 之前已知输出



### 3.2 Attention

- 把注意力函数定义为 query 与一组 key-value 对到输出的映射，输出是 value 的加权和，权重由 query 与对应 key 的兼容函数给出

- 给出注意力机制示意图（Figure 2：左为 Scaled Dot-Product Attention，右为 Multi-Head Attention）



### 3.2.1 Scaled Dot-Product Attention

- 输入为维度 d_k 的 query 与 key、维度 d_v 的 value，先算 query 与所有 key 的点积、除以 sqrt(d_k)，再 softmax 得到权重

- 批量形式：Attention(Q,K,V)=softmax(QK^T/sqrt(d_k))V

- 对比两类常用注意力：加性注意力 [2] 用单隐层前馈网络算兼容函数；点积注意力与本文算法相同，仅少一个 1/sqrt(d_k) 缩放因子

- 两者理论复杂度相近，但点积注意力实现更快更省空间，可借助高度优化的矩阵乘法

- d_k 较小时两者表现相近，d_k 较大时未缩放的点积注意力劣于加性注意力 [3]

- 推测原因是点积数值过大会把 softmax 推入极小梯度区域，因此用 1/sqrt(d_k) 缩放来抵消



### 3.2.2 Multi-Head Attention

- 不用单一全维注意力，而是用 h 组不同的学习到的线性投影把 query、key、value 投影到 d_k、d_k、d_v 维

- 在各投影版本上并行计算注意力，得到 d_v 维输出后拼接并再次投影（Figure 2）

- 多头的价值在于让模型能同时关注不同位置的不同表示子空间；单头时平均会抑制这种能力

- 本文取 h=8、d_k=d_v=d_model/h=64；因每个头维度下降，总计算量与全维单头注意力相当



### 3.2.3 Applications of Attention in our Model

- encoder-decoder attention：query 来自解码器上一层，memory 的 key/value 来自编码器输出，使解码器每个位置可关注输入序列所有位置，模仿 [38, 2, 9] 的注意力机制

- 编码器自注意力：key、value、query 同源于编码器上一层输出，每个位置可关注上一层所有位置

- 解码器自注意力：每个位置可关注解码器中截至该位置的所有位置，通过把 softmax 输入中的非法连接置为 −∞ 实现掩码（见 Figure 2）



### 3.3 Position-wise Feed-Forward Networks

- 每层除注意力子层外还含一个对每个位置独立且相同地施加的全连接前馈网络，由两次线性变换与中间 ReLU 构成

- FFN(x)=max(0,xW1+b1)W2+b2；等价于两个卷积核为 1 的卷积

- 输入输出维度 d_model=512，内层维度 d_ff=2048；不同位置共享同一线性变换，但各层参数不同



### 3.4 Embeddings and Softmax

- 使用学习到的 embedding 把输入与输出 token 转为 d_model 维向量，并用学习到的线性变换加 softmax 得到下一个 token 的概率

- 输入 embedding 层、输出 embedding 层与 softmax 前线性变换共享同一权重矩阵，类似于 [30]

- 在 embedding 层把权重乘以 sqrt(d_model)



### 3.5 Positional Encoding

- 由于模型不含循环与卷积，必须注入位置信息，因此在编码器与解码器堆叠底部把位置编码加到输入 embedding 上

- 位置编码维度与 embedding 相同因而可直接相加；可选方案包括学习式与固定式 [9]

- 本文采用不同频率的正弦与余弦函数：PE(pos,2i)=sin(pos/10000^{2i/d_model})，PE(pos,2i+1)=cos(pos/10000^{2i/d_model})

- 波长构成 2π 到 10000·2π 的几何级数；选择该函数是因为希望模型能轻松学会按相对位置注意，对任意固定偏移 k，PE(pos+k) 可表示为 PE(pos) 的线性函数

- 作者也实验了可学习位置嵌入 [9]，结果几乎相同（Table 3 row E），最终选正弦版本因为它可能外推到比训练时更长的序列



### 4 Why Self-Attention

- 从三方面比较 self-attention 与循环层、卷积层：每层总计算复杂度、可并行化的计算量（最少顺序操作数）、以及长距离依赖的路径长度

- 指出学习长距离依赖是序列转导任务的关键挑战，路径越短越易学习 [12]

- 依据 Table 1：自注意力层以常数个顺序操作连接所有位置，而循环层需要 O(n) 个顺序操作

- 当序列长度 n 小于表示维度 d（句级表示的常见情形）时自注意力更快，句表示常用 word-piece [38] 与 byte-pair [31]

- 对超长序列可将自注意力限制在以输出位置为中心的 r 大小邻域

- 单个卷积层（核宽 k<n）无法连接所有位置，需要 O(n/k) 层连续卷积或 O(log_k(n)) 层空洞卷积 [18]，会拉长最长路径；可分离卷积 [6] 可降低复杂度

- 附加好处是可解释性：检查注意力分布可发现不同注意力头学到不同任务，许多头表现出与句法语义结构相关的行为



### 5 Training

- 本节介绍训练设置：数据与批处理、硬件与训练时长、优化器与学习率调度、正则化



### 5.1 Training Data and Batching

- 英德任务使用标准 WMT 2014 English-German 数据集，约 450 万句对，用 byte-pair 编码 [3]，共享源目标词表约 37000 token

- 英法任务使用更大的 WMT 2014 English-French 数据集，3600 万句，切分为 32000 词表大小的 word-piece [38]

- 按近似序列长度把句对分批，每批约含 25000 个源 token 与 25000 个目标 token



### 5.2 Hardware and Schedule

- 训练在一台机器上使用 8 块 NVIDIA P100 GPU

- base 模型每步约 0.4 秒，共训练 100,000 步即 12 小时

- big 模型每步 1.0 秒，共训练 300,000 步即 3.5 天



### 5.3 Optimizer

- 使用 Adam 优化器 [20]，beta1=0.9、beta2=0.98、eps=1e-9

- 学习率公式：rate = d_model^-0.5 * min(step_num^-0.5, step_num * warmup_steps^-1.5)

- 即前 warmup_steps 步线性升高学习率，之后按步数的平方根倒数衰减；本文 warmup_steps=4000



### 5.4 Regularization

- 使用三种正则化手段（正文展开其中两种）

- Residual dropout：对每个子层输出在其加回子层输入并归一化之前施加 dropout [33]，同时对编码器与解码器中 embedding 与位置编码求和处施加 dropout；base 模型 P_drop=0.1

- Label smoothing：训练中采用 epsilon_ls=0.1 [36]；虽损害困惑度（模型变得更不确定），但提升准确率与 BLEU



### 6 Results

- 结果部分给出机器翻译主结果、架构变体消融，以及英语组句分析上的跨任务泛化实验



### 6.1 Machine Translation

- 英德任务：big 模型（Transformer (big)，Table 2）比此前最好的已报道模型（含集成）高 2 BLEU 以上，创下 28.4 BLEU 的新纪录；训练耗时 3.5 天、8 块 P100

- 即便 base 模型也超过所有此前发表的模型与集成，且训练成本只占竞争模型的一小部分

- 英法任务：big 模型取得 41.0 BLEU，优于此前所有单模型，训练成本不到此前最好模型的 1/4；该配置的 dropout 率为 0.1 而非 0.3

- base 模型用最后 5 个检查点（每 10 分钟写一次）平均，big 模型平均最后 20 个检查点

- 推理用 beam search，beam size=4、长度惩罚 alpha=0.6 [38]，超参在开发集上实验选定；最大输出长度为输入长度 + 50，可提前终止 [38]

- 训练 FLOPs 用训练时间、GPU 数量与单 GPU 单精度持续算力估计相乘得到



### 6.2 Model Variations

- 在英德开发集 newstest2013 上改变 base 模型各组件以评估其重要性，使用 beam search 但不做检查点平均，结果见 Table 3

- rows (A)：固定计算量改变注意力头数与 d_k、d_v，单头注意力比最佳设置低 0.9 BLEU，头数过多时质量也下降

- rows (B)：减小注意力 key 尺寸 d_k 会损害模型质量，说明判定兼容性并不容易，比点积更复杂的兼容函数可能有帮助

- rows (C)、(D)：更大的模型更好，dropout 对避免过拟合非常有帮助

- row (E)：用可学习位置嵌入 [9] 替换正弦位置编码，结果与 base 模型几乎一致



### 6.3 English Constituency Parsing

- 为检验可迁移性，在英语组句分析上实验；该任务输出受强结构约束且明显长于输入，小数据场景下 RNN seq2seq 未能达到最好结果 [37]

- 训练 4 层、d_model=1024 的 Transformer：WSJ-only 使用 Penn Treebank [25] 约 4 万训练句、16K 词表；半监督设置使用高置信度与 BerkleyParser 语料约 1700 万句、32K 词表

- 仅在 Section 22 开发集上做了 dropout（残差与注意力）、学习率与 beam size 的少量实验，其余参数沿用英德 base 模型；推理时最大输出长度为输入长度 + 300，beam size=21、alpha=0.3

- Table 4（WSJ Section 23）结果：Transformer 4 层 WSJ-only 达 91.3 F1，仅次于循环神经语法模型 [8] 的 91.7，超过 Petrov 等 [29] 的 Berkeley Parser

- 半监督设置下 Transformer 为 91.3，低于 McClosky 等 [26] 的 92.1，与 Huang & Harper [14] 持平

- 结论是尽管缺少任务特定调优，模型表现仍相当突出，且在仅用 4 万句 WSJ 训练集时也超过基于 RNN 的解析器



### 7 Conclusion

- 总结提出 Transformer：首个完全基于注意力的序列转导模型，用多头自注意力取代编码器-解码器架构中最常用的循环层

- 翻译任务上训练显著快于基于循环或卷积的架构，在 WMT 2014 英德与英法任务上均取得新最好结果，英德任务上甚至超过所有已报道的集成模型

- 未来方向：把 Transformer 扩展到文本之外的输入输出模态，研究局部受限注意力以高效处理图像、音频、视频等大输入输出，减少生成的顺序性

- 训练与评估代码开源于 https://github.com/tensorflow/tensor2tensor；作者感谢 Nal Kalchbrenner 与 Stephan Gouws 的意见与启发



### Attention Visualizations

- 附录给出编码器第 5 层（6 层中的第 5 层）自注意力的可视化示例

- Figure 3：注意力机制跟随长距离依赖的示例，许多注意力头关注动词 'making' 的远处依赖，补全 'making...more difficult' 短语

- Figure 4：两个注意力头似乎参与指代消解，展示 head 5 的完整注意力与 head 5、6 仅针对 'its' 的注意力，'its' 的注意力非常尖锐

- Figure 5：许多注意力头表现出与句子结构相关的行为，图中给出同一层两个不同注意力头的示例
