## 文献综述章节引文线索

### 总体总结
引言与背景的引用围绕 Transformer 的架构动机组织，而不是逐篇介绍被引论文。源文先以 LSTM、门控循环网络及循环编码器—解码器工作确立既有序列建模范式，再承认效率优化和注意力机制的进展，指出循环模型的样本内顺序计算约束仍未消除。背景随后以 Extended Neural GPU、ByteNet 和 ConvS2S 说明并行卷积路线，并通过远距离位置关联所需操作数的比较引出自注意力的动机；同时承认注意力加权平均可能降低有效分辨率，并提出以多头注意力应对。自注意力的已有任务应用、非循环注意力例外及采用循环注意力的记忆网络共同约束创新主张：源文仅以“据我们所知”声称 Transformer 是首个完全依靠自注意力计算输入输出表示、无需序列对齐循环网络或卷积的转导模型，而非声称首次提出注意力或自注意力。所选范围中的引用主要承担背景、动机和架构对照作用，未给出被引工作的逐项实验比较。


### 关键文献

- [2] D. Bahdanau, 2014: Neural Machine Translation by Jointly Learning to Align and Translate (Background)

- [9] Jonas Gehring, 2017: Convolutional Sequence to Sequence Learning (Uncategorized)

- [18] N. Kalchbrenner, 2017: Neural Machine Translation in Linear Time (Baseline)

- [27] Ankur Parikh, 2016: A decomposable attention model (Uncategorized)



### 范围
- 章节: 1 Introduction + 2 Background
- 行号: 25-44

### 按功能归类


#### Background

- [2] D. Bahdanau, 2014
  - 标题: Neural Machine Translation by Jointly Learning to Align and Translate
  - 关键词: 机器翻译, 循环神经网络, 注意力机制, 序列转导
  - 总结: 该引用既支持循环网络在序列转导领域既有地位的概述，也为注意力机制的作用提供先例，帮助引出 Transformer 不再依赖循环网络的区别。

- [4] Jian-Peng Cheng, 2016
  - 标题: Long Short-Term Memory-Networks for Machine Reading
  - 关键词: 自注意力, 序列表示, 阅读理解
  - 总结: 该引用支持自注意力已有成功任务应用的论述，为进一步采用自注意力构建序列转导模型提供背景，而非充当此处的实验基线。

- [5] Kyunghyun Cho, 2014
  - 标题: Learning Phrase Representations using RNN Encoder–Decoder for Statistical Machine Translation
  - 关键词: 循环神经网络, 编码器—解码器, 机器翻译, 序列转导
  - 总结: 源文以该工作交代循环网络在机器翻译等任务中的成熟应用，建立提出非循环 Transformer 架构之前的技术背景。

- [7] Junyoung Chung, 2014
  - 标题: Empirical Evaluation of Gated Recurrent Neural Networks on Sequence Modeling
  - 关键词: 门控循环网络, 循环神经网络, 序列建模
  - 总结: 该引用标明门控循环网络这一重要循环模型类别，服务于源文关于循环网络在序列建模和转导任务中确立地位的论述；此处未讨论具体评估结果。

- [12] S. Hochreiter, 2001
  - 标题: Gradient Flow in Recurrent Nets: the Difficulty of Learning Long-Term Dependencies
  - 关键词: 长距离依赖, 计算路径长度, 依赖学习, 自注意力
  - 总结: 该引用连接跨位置操作数增长与远距离依赖学习困难两项论述，为 Transformer 缩短位置间关联路径的动机提供支持；此处没有展开被引工作的具体梯度分析。

- [13] S. Hochreiter, 1997
  - 标题: Long Short-Term Memory
  - 关键词: 长短期记忆网络, LSTM, 循环神经网络, 序列建模
  - 总结: 该引用交代 LSTM 这一重要循环网络形式，支撑循环架构在语言建模和机器翻译等任务中确立地位的背景陈述，为后续介绍非循环架构作铺垫。

- [15] R. Józefowicz, 2016
  - 标题: Exploring the Limits of Language Modeling
  - 关键词: 语言建模, 循环语言模型, 架构发展
  - 总结: 该引用说明在循环模型确立主流地位后，仍有研究继续拓展其能力边界。此处仅将其作为研究进展的例证，未引用具体方法或实验指标。

- [19] Yoon Kim, 2017
  - 标题: Structured Attention Networks
  - 关键词: 注意力机制, 序列建模, 序列转导, 跨距离依赖
  - 总结: 源文用该引用支持注意力机制的重要性与跨距离依赖建模能力。它位于多数注意力模型仍与循环网络结合的背景讨论中，并非此处的具体实验比较。

- [21] Oleksii Kuchaiev, 2017
  - 标题: Factorization tricks for LSTM networks
  - 关键词: 循环网络, 因子分解, 计算效率, 顺序计算, 训练并行化
  - 总结: 源文用该工作区分效率优化与根本的并行化障碍：即使计算效率已有改进，循环模型仍依赖前一位置的隐藏状态，样本内部的顺序计算约束依然存在。

- [24] Thang Luong, 2015
  - 标题: Effective Approaches to Attention-based Neural Machine Translation
  - 关键词: 神经机器翻译, 注意力机制, 循环网络, 编码器—解码器
  - 总结: 源文将该工作作为继续推进循环语言模型与编码器—解码器架构的实例。此处未讨论其具体注意力方案或实验结果，主要用于铺垫 Transformer 所处的研究背景。

- [32] Noam Shazeer, 2017
  - 标题: Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer
  - 关键词: 条件计算, 计算效率, 模型性能, 循环模型, 顺序计算
  - 总结: 源文引用该工作承认条件计算的效率与性能进展，同时强调这些进展没有解除循环模型在单个训练样本内部难以并行化的根本约束。

- [34] Sainbayar Sukhbaatar, 2015
  - 标题: End-To-End Memory Networks
  - 关键词: 端到端记忆网络, 循环注意力, 序列对齐循环, 问答, 语言建模
  - 总结: 源文以该引用说明不同于传统序列对齐循环的架构已有先例，并支持端到端记忆网络在简单语言问答与语言建模上表现良好的说法；它没有将该模型描述为完全没有循环。

- [35] I. Sutskever, 2014
  - 标题: Sequence to Sequence Learning with Neural Networks
  - 关键词: 序列到序列学习, 循环神经网络, 机器翻译, 序列转导
  - 总结: 源文将该工作与其他文献并列，交代 Transformer 提出前的主流技术背景；所给片段并未进行具体方法或指标比较。



#### Uncategorized

- [9] Jonas Gehring, 2017
  - 标题: Convolutional Sequence to Sequence Learning
  - 关键词: ConvS2S, 卷积序列模型, 并行计算, 长距离依赖, 自注意力
  - 总结: 源文认可 ConvS2S 的位置级并行计算，同时指出其跨位置关联路径随距离线性增长，以突出 Transformer 用自注意力将位置间关联所需操作数降为常数、且不依赖卷积的架构差异。

- [16] Lukasz Kaiser, 2016
  - 标题: Can Active Memory Replace Attention?
  - 关键词: Extended Neural GPU, 卷积神经网络, 并行计算, 顺序计算
  - 总结: 源文以 Extended Neural GPU 交代通过卷积减少顺序计算的先行路线。此处没有单独给出该模型的跨位置路径复杂度，不能将针对 ConvS2S 或 ByteNet 的具体复杂度结论归于它。

- [17] Łukasz Kaiser, 2016
  - 标题: Neural GPUs learn algorithms
  - 关键词: Neural GPU, 序列转导, 自注意力, 架构比较
  - 总结: 该引用为 Transformer 完全依靠自注意力、无需序列对齐循环网络或卷积的架构定位提供参照；此处未展开该模型的具体机制、性能或比较结果。

- [22] Zhouhan Lin, 2017
  - 标题: A Structured Self-attentive Sentence Embedding
  - 关键词: 自注意力, 句子表示, 任务无关表示, 序列表示
  - 总结: 该引用出现在自注意力定义及成功应用的概述中，用于建立其在任务无关句子表示学习中的实践基础，而非提供 Transformer 的实验基线。

- [27] Ankur Parikh, 2016
  - 标题: A decomposable attention model
  - 关键词: 注意力机制, 非循环架构, 自注意力, 文本蕴含
  - 总结: 该工作首次用于说明并非所有注意力模型都依赖循环网络，避免将常见组合说成普遍规律；第二次出现在包含文本蕴含等任务的自注意力应用概述中。两处引用表明 Transformer 之前已有非循环注意力及自注意力应用基础。

- [28] Romain Paulus, 2017
  - 标题: A Deep Reinforced Model for Abstractive Summarization
  - 关键词: 自注意力, 抽象式摘要, 序列表示
  - 总结: 源文在解释自注意力如何关联同一序列不同位置之后，将该工作列为成功应用实例。此处未展开其强化学习方法或性能细节。

- [38] Yong-Hui Wu, 2016
  - 标题: Google's Neural Machine Translation System: Bridging the Gap between Human and Machine Translation
  - 关键词: 循环神经网络, 循环语言模型, 编码器—解码器, 机器翻译, 序列建模
  - 总结: 该引用是源文背景介绍中持续推进既有序列建模路线的研究实例之一；此处没有具体讨论其系统设计、实验结果或性能指标。



#### Baseline

- [18] N. Kalchbrenner, 2017
  - 标题: Neural Machine Translation in Linear Time
  - 关键词: ByteNet, 卷积序列模型, 并行计算, 长距离依赖, 依赖路径
  - 总结: 源文以 ByteNet 说明卷积模型可并行计算各位置隐藏表示，但关联远距离位置所需操作数仍随距离对数增长，据此对比 Transformer 的常数操作路径。源文同时承认注意力加权平均可能降低有效分辨率，并提出以多头注意力应对；ByteNet 也被列为后续讨论的比较对象。





### 时间线分析

#### 早期
较早的文献承担两类基础论证作用：以 LSTM 交代循环序列模型的重要形式，并以长距离依赖学习困难的研究支持缩短位置间信息交互路径的动机。源文将这些基础分别用于说明既有范式与架构设计问题，并未据此展开完整的技术演进史。


- [13] S. Hochreiter, 1997: Long Short-Term Memory

- [12] S. Hochreiter, 2001: Gradient Flow in Recurrent Nets: the Difficulty of Learning Long-Term Dependencies

- [2] D. Bahdanau, 2014: Neural Machine Translation by Jointly Learning to Align and Translate

- [5] Kyunghyun Cho, 2014: Learning Phrase Representations using RNN Encoder–Decoder for Statistical Machine Translation

- [7] Junyoung Chung, 2014: Empirical Evaluation of Gated Recurrent Neural Networks on Sequence Modeling

- [35] I. Sutskever, 2014: Sequence to Sequence Learning with Neural Networks

- [24] Thang Luong, 2015: Effective Approaches to Attention-based Neural Machine Translation




#### 中期
随后引用的研究使背景从循环序列转导扩展到注意力及替代架构：循环编码器—解码器与机器翻译工作说明主流路线及其持续进展，自注意力应用、非循环注意力例外和端到端记忆网络则展示既有探索的多样性。它们共同限定了 Transformer 的创新边界，不能把其主张概括成首次使用注意力或首次去除序列对齐循环。


- [34] Sainbayar Sukhbaatar, 2015: End-To-End Memory Networks

- [4] Jian-Peng Cheng, 2016: Long Short-Term Memory-Networks for Machine Reading

- [15] R. Józefowicz, 2016: Exploring the Limits of Language Modeling

- [16] Lukasz Kaiser, 2016: Can Active Memory Replace Attention?

- [17] Łukasz Kaiser, 2016: Neural GPUs learn algorithms

- [27] Ankur Parikh, 2016: A decomposable attention model

- [38] Yong-Hui Wu, 2016: Google's Neural Machine Translation System: Bridging the Gap between Human and Machine Translation




#### 近期
近期文献将论证集中到效率、并行化与自注意力的可行性：因子分解和条件计算虽带来效率改进，源文仍指出循环计算的顺序约束；ByteNet 与 ConvS2S 提供并行卷积路线及跨位置关联成本的直接对照，注意力与句子表示、摘要等应用进一步提供背景支持。源文据此突出纯自注意力转导架构，同时保留注意力加权平均降低有效分辨率这一代价。


- [9] Jonas Gehring, 2017: Convolutional Sequence to Sequence Learning

- [18] N. Kalchbrenner, 2017: Neural Machine Translation in Linear Time

- [19] Yoon Kim, 2017: Structured Attention Networks

- [21] Oleksii Kuchaiev, 2017: Factorization tricks for LSTM networks

- [22] Zhouhan Lin, 2017: A Structured Self-attentive Sentence Embedding

- [28] Romain Paulus, 2017: A Deep Reinforced Model for Abstractive Summarization

- [32] Noam Shazeer, 2017: Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer





