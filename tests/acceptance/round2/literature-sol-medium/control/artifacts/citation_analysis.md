## 文献综述章节引文线索

### 总体总结
引言先以LSTM、门控循环网络和编码器—解码器翻译建立成熟技术背景，再指出因式分解与条件计算虽改善效率，却未消除序列递推。注意力相关引文说明远距访问已经可行，并用可分解注意力标出并非所有先例都必须依附循环的例外。背景部分随后把卷积路线的并行表示与其远距路径长度相对照，以长时依赖研究支撑问题动机；又列举自注意力的多任务先例和循环注意力记忆网络，最终收束到完全去循环、去卷积的序列转换主张。引用承担的是历史基础、成熟路线、机制先例及关键对照，不应把这些背景引用一概解释为本文实验中已重新评测的基线。分析范围仅含引言与背景，不覆盖训练组件、数据集和结果章节的额外引用。


### 关键文献

- [2] D. Bahdanau, 2014: Neural Machine Translation by Jointly Learning to Align and Translate (Background)

- [9] Jonas Gehring, 2017: Convolutional Sequence to Sequence Learning (Uncategorized)

- [18] N. Kalchbrenner, 2017: Neural Machine Translation in Linear Time (Background)



### 范围
- 章节: 1 Introduction + 2 Background
- 行号: 25-44

### 按功能归类


#### Background

- [2] D. Bahdanau, 2014
  - 标题: Neural Machine Translation by Jointly Learning to Align and Translate
  - 关键词: 注意力机制, 循环网络, 机器翻译, 长距离依赖
  - 总结: 当前引用既将该工作纳入循环式机器翻译的代表性背景，也用它说明注意力已有跨距离依赖建模能力；论证重心是保留注意力而摆脱通常伴随它的循环结构。

- [5] Kyunghyun Cho, 2014
  - 标题: Learning Phrase Representations using RNN Encoder–Decoder for Statistical Machine Translation
  - 关键词: 循环网络, 序列转换, 机器翻译, 编码器—解码器
  - 总结: 片段将该工作列为循环式序列建模和机器翻译既有成就的依据，用于建立本文提出不同架构之前的研究背景；没有在该处讨论其具体训练方法或性能。

- [12] S. Hochreiter, 2001
  - 标题: Gradient Flow in Recurrent Nets: the Difficulty of Learning Long-Term Dependencies
  - 关键词: 长距离依赖, 学习困难, 计算路径, 自注意力动机
  - 总结: 虽然标题讨论循环网络中的长期依赖，当前引用的实际作用是支撑较长位置连接路径不利于学习远距离依赖这一论点；本文据此说明Transformer缩短连接路径的意义，片段未展开梯度机制细节。

- [15] R. Józefowicz, 2016
  - 标题: Exploring the Limits of Language Modeling
  - 关键词: 循环语言模型, 架构发展, 研究背景
  - 总结: 当前片段用该工作作为持续改进既有循环式路线的研究实例，而非本文采用的技术组件或具体实验基线；并列引用本身未详细说明各项改进。

- [16] Lukasz Kaiser, 2016
  - 标题: Can Active Memory Replace Attention?
  - 关键词: Extended Neural GPU, 卷积网络, 并行表示计算, 顺序计算
  - 总结: 该引用说明减少顺序计算并非本文首次提出的目标，并将Extended Neural GPU定位为卷积并行化路线的一员。后续关于路径随距离线性或对数增长的具体描述分别点名ConvS2S和ByteNet，不能据此为该引用指定同样的增长率。

- [18] N. Kalchbrenner, 2017
  - 标题: Neural Machine Translation in Linear Time
  - 关键词: ByteNet, 卷积序列模型, 并行计算, 长距离依赖, 自注意力
  - 总结: 本文借 ByteNet 说明卷积已能并行计算各位置的表示，但跨位置连接的操作数仍随距离增长；由此突出 Transformer 的常数连接路径，并将不依赖序列对齐循环或卷积的纯自注意力设计与这些先例区分。

- [19] Yoon Kim, 2017
  - 标题: Structured Attention Networks
  - 关键词: 注意力机制, 序列建模, 跨距离依赖, 循环网络
  - 总结: 该引用用于确认注意力已成为序列模型的重要组件，且能关联相距较远的位置；所在段落随后指出注意力通常仍与循环网络结合，从而铺垫本文摆脱循环结构的动机。

- [21] Oleksii Kuchaiev, 2017
  - 标题: Factorization tricks for LSTM networks
  - 关键词: 因子分解, 循环模型, 计算效率, 顺序计算瓶颈
  - 总结: 本文引用该工作说明循环模型可通过因子分解显著改善计算效率，但在当前论证中，这类改进仍无法解除训练样例内部的顺序依赖，因而不能替代对架构层面并行化的追求。

- [22] Zhouhan Lin, 2017
  - 标题: A Structured Self-attentive Sentence Embedding
  - 关键词: 自注意力, 句子表示, 任务无关表示
  - 总结: 该引用位于自注意力定义及应用列举中，作为其用于句子表示学习的已有成功案例，支持本文选择自注意力作为表示计算机制的背景论证，而非提供本文架构或实验的直接对比结果。

- [27] Ankur Parikh, 2016
  - 标题: A decomposable attention model
  - 关键词: 非循环注意力, 自注意力, 文本蕴含, 既有先例
  - 总结: 该工作在本文中承担双重作用：既作为注意力并非必然依附循环网络的明确例外，也作为自注意力已有任务应用的例证。其存在使本文的创新背景不是笼统否认非循环注意力先例，而是建立在承认这些先例之上。

- [28] Romain Paulus, 2017
  - 标题: A Deep Reinforced Model for Abstractive Summarization
  - 关键词: 自注意力, 抽象式摘要, 任务应用
  - 总结: 本文借该引用说明自注意力此前已在抽象式摘要等任务中得到成功应用；此处的论证作用是建立机制的适用背景，而不是讨论被引工作的强化学习方法或将其作为本文的摘要实验基线。

- [35] I. Sutskever, 2014
  - 标题: Sequence to Sequence Learning with Neural Networks
  - 关键词: 循环网络, 序列到序列, 机器翻译, 序列建模
  - 总结: 该引用在引言背景中用于确立循环网络在序列建模与转换任务中的成熟地位，说明本文所要改变的是已有广泛成功基础的建模路线；当前片段并未引用其具体训练方法或实验数值。

- [38] Yong-Hui Wu, 2016
  - 标题: Google's Neural Machine Translation System: Bridging the Gap between Human and Machine Translation
  - 关键词: 循环神经网络, 编码器—解码器架构, 序列建模, 机器翻译
  - 总结: 在所给片段中，[38]被用于例示持续推进循环语言模型与编码器—解码器架构的研究，与其他引文共同支撑对既有研究路线发展的概述；片段未单独讨论该文献的具体方法或结果。



#### Uncategorized

- [4] Jian-Peng Cheng, 2016
  - 标题: Long Short-Term Memory-Networks for Machine Reading
  - 关键词: 自注意力, 阅读理解, 序列表示
  - 总结: 该引用出现在自注意力应用清单中，作用是支持这一机制在既有任务中已有成功实践。片段以多篇文献共同支撑多个任务，并未逐项指定每篇文献对应的全部任务。

- [7] Junyoung Chung, 2014
  - 标题: Empirical Evaluation of Gated Recurrent Neural Networks on Sequence Modeling
  - 关键词: 门控循环网络, 序列建模, 循环架构
  - 总结: 该引用用于指认门控循环网络这一背景模型类别，与长短期记忆网络并列构成本文讨论的既有循环式路线；当前片段没有使用其具体评测数据来比较本文模型。

- [9] Jonas Gehring, 2017
  - 标题: Convolutional Sequence to Sequence Learning
  - 关键词: ConvS2S, 卷积序列转换, 并行计算, 依赖路径长度
  - 总结: 本文借ConvS2S承认卷积模型已推动并行化，再以其远距离位置连接成本的线性增长反衬Transformer的常数级连接操作数；该比较同时服务于纯自注意力架构的创新定位，而不是报告实验胜负。

- [13] S. Hochreiter, 1997
  - 标题: Long Short-Term Memory
  - 关键词: 长短期记忆网络, 循环网络, 序列建模
  - 总结: 该引用用于标识长短期记忆网络这一既有主流模型，并帮助建立本文摆脱循环计算之前的技术背景；片段没有展开其内部机制或给出与Transformer的直接实验比较。

- [17] Łukasz Kaiser, 2016
  - 标题: Neural GPUs learn algorithms
  - 关键词: 纯自注意力, 架构对照, 序列转换
  - 总结: 当前片段只把该工作列入将要比较的既有模型集合，用来衬托Transformer的纯自注意力定位；它没有给出针对该模型的具体优劣数据或展开其内部计算方式。

- [24] Thang Luong, 2015
  - 标题: Effective Approaches to Attention-based Neural Machine Translation
  - 关键词: 循环网络, 编码器—解码器, 序列转换, 研究背景
  - 总结: 本文在介绍循环网络作为序列建模主流方法后，引用该工作作为相关架构持续发展的例证；当前片段未将它用作具体性能基线，也未展开其注意力实现细节。

- [32] Noam Shazeer, 2017
  - 标题: Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer
  - 关键词: 条件计算, 计算效率, 模型性能, 顺序计算瓶颈
  - 总结: 该引用用于说明循环模型相关优化并非没有成效：条件计算能提高效率并改善性能。然而本文在同一段落中强调顺序计算约束依旧存在，以此区分局部优化收益与摆脱序列依赖这两个目标。

- [34] Sainbayar Sukhbaatar, 2015
  - 标题: End-To-End Memory Networks
  - 关键词: 端到端记忆网络, 循环注意力, 序列对齐循环, 问答, 语言建模
  - 总结: 本文引用端到端记忆网络，说明已有模型通过循环注意力而非按序列位置展开的循环来完成计算，并在简单语言问答与语言建模任务上取得良好表现；该片段支持对替代架构背景的交代，不等同于声称其完全没有循环。





### 时间线分析

#### 早期
较早的LSTM与长时依赖研究分别提供循环序列建模的历史基础和远距学习困难的机制动机。原文借此说明，成熟的记忆结构并没有自动消除逐位置递推与跨距离路径的约束。


- [13] S. Hochreiter, 1997: Long Short-Term Memory

- [12] S. Hochreiter, 2001: Gradient Flow in Recurrent Nets: the Difficulty of Learning Long-Term Dependencies

- [2] D. Bahdanau, 2014: Neural Machine Translation by Jointly Learning to Align and Translate

- [5] Kyunghyun Cho, 2014: Learning Phrase Representations using RNN Encoder–Decoder for Statistical Machine Translation

- [7] Junyoung Chung, 2014: Empirical Evaluation of Gated Recurrent Neural Networks on Sequence Modeling

- [35] I. Sutskever, 2014: Sequence to Sequence Learning with Neural Networks

- [24] Thang Luong, 2015: Effective Approaches to Attention-based Neural Machine Translation




#### 中期
随后，RNN编码器—解码器、序列到序列学习和对齐式注意力确立神经翻译主线；注意力翻译改进与端到端记忆网络拓宽了信息访问机制。它们在原文中主要承担成熟路线与机制先例的作用，而非证明纯注意力序列转换已经实现。


- [34] Sainbayar Sukhbaatar, 2015: End-To-End Memory Networks

- [4] Jian-Peng Cheng, 2016: Long Short-Term Memory-Networks for Machine Reading

- [15] R. Józefowicz, 2016: Exploring the Limits of Language Modeling

- [16] Lukasz Kaiser, 2016: Can Active Memory Replace Attention?

- [17] Łukasz Kaiser, 2016: Neural GPUs learn algorithms

- [27] Ankur Parikh, 2016: A decomposable attention model

- [38] Yong-Hui Wu, 2016: Google's Neural Machine Translation System: Bridging the Gap between Human and Machine Translation




#### 近期
接近本文的工作一方面继续改进循环模型的效率、规模和翻译系统，另一方面以卷积实现并行表示，并将自注意力用于阅读、蕴含、摘要和句子表示。原文据此区分“已有注意力或并行计算”与“输入输出表示完全不依赖循环或卷积”，把Transformer定位在这些路线的交汇处。


- [9] Jonas Gehring, 2017: Convolutional Sequence to Sequence Learning

- [18] N. Kalchbrenner, 2017: Neural Machine Translation in Linear Time

- [19] Yoon Kim, 2017: Structured Attention Networks

- [21] Oleksii Kuchaiev, 2017: Factorization tricks for LSTM networks

- [22] Zhouhan Lin, 2017: A Structured Self-attentive Sentence Embedding

- [28] Romain Paulus, 2017: A Deep Reinforced Model for Abstractive Summarization

- [32] Noam Shazeer, 2017: Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer





