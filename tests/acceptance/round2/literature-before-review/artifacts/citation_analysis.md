## 文献综述章节引文线索

### 总体总结
源文在“1 Introduction + 2 Background”范围内按三步组织引用：先以 LSTM、门控循环网络与序列到序列等文献确立循环网络作为序列建模与转导的最先进基线，并列举注意力机制与循环网络结合的既有范式及其“少数例外”；再以端到端记忆网络说明注意力可以替代序列对齐的循环，并以自注意力在阅读理解、摘要、蕴含与句子表示上的成功说明其通用性；最后以因子分解技巧、条件计算与基于卷积的并行化模型（Extended Neural GPU、ByteNet、ConvS2S）作为缓解顺序计算但仍受距离复杂度约束的近期路线，配合梯度流分析给出的理论解释，把 Transformer 的全自注意力结构与恒定路径长度确立为对上述基线的结构性回应。整体上，引用充当的是对照与动机工具，而非被逐一评述的独立工作。


### 关键文献

- [13] Sepp Hochreiter, 1997: Long short-term memory (Baseline)

- [12] Sepp Hochreiter, 2001: Gradient flow in recurrent nets: the difficulty of learning long-term dependencies (Uncategorized)

- [27] Ankur Parikh, 2016: A decomposable attention model (Uncategorized)

- [9] Jonas Gehring, 2017: Convolutional sequence to sequence learning (Baseline)

- [18] Nal Kalchbrenner, 2017: Neural machine translation in linear time (Uncategorized)



### 范围
- 章节: 1 Introduction + 2 Background
- 行号: 25-43

### 按功能归类


#### Uncategorized

- [2] Dzmitry Bahdanau, 2014
  - 标题: Neural machine translation by jointly learning to align and translate
  - 关键词: 注意力机制, 机器翻译, 编码器-解码器, 距离无关的依赖, 既有先例
  - 总结: 源文用该文献既确立注意力在机器翻译上已成为主流组件，也用于说明这类注意力几乎总是与循环网络搭配使用，从而界定 Transformer 完全不同于此的技术定位。

- [12] Sepp Hochreiter, 2001
  - 标题: Gradient flow in recurrent nets: the difficulty of learning long-term dependencies
  - 关键词: 梯度流, 长程依赖, 循环网络, 理论支撑
  - 总结: 源文引用该文献作为循环网络梯度流问题导致长程依赖难以学习的理论依据，用以解释并行化与卷积式模型在远距离依赖上的困难，从而论证 Transformer 将路径长度降为常数的优势来源。

- [15] Rafal Jozefowicz, 2016
  - 标题: Exploring the limits of language modeling
  - 关键词: 语言建模, 循环语言模型, 规模扩展, 边界探索
  - 总结: 源文引用该文献代表在循环语言模型与编码器-解码器架构方向继续推升性能上限的后续努力，用于说明以新架构取而代之的必要性。

- [18] Nal Kalchbrenner, 2017
  - 标题: Neural machine translation in linear time
  - 关键词: ByteNet, 卷积序列模型, 对数复杂度, 并行计算, 机器翻译
  - 总结: 源文以该文献作为 ByteNet 的出处，用其对数增长的距离复杂度说明卷积式并行化仍受远距离依赖困扰，从而作为 Transformer 恒定操作数优势的直接对照。

- [21] Oleksii Kuchaiev, 2017
  - 标题: Factorization tricks for LSTM networks
  - 关键词: 因子分解技巧, LSTM, 计算效率, 顺序计算约束, 并行化
  - 总结: 源文用该引用说明循环网络内部已有的效率优化手段虽提升了计算效率，却仍无法摆脱逐时间步展开这一根本限制，从而过渡到自注意力可全并行计算的主张。

- [22] Zhouhan Lin, 2017
  - 标题: A structured self-attentive sentence embedding
  - 关键词: 自注意力, 句子表示, 句嵌入, 任务无关表示
  - 总结: 源文用该引用说明自注意力能够单独完成表示学习任务，是其将自注意力确立为独立建模原语的重要旁证。

- [24] Minh-Thang Luong, 2015
  - 标题: Effective approaches to attentionbased neural machine translation
  - 关键词: 注意力, 神经机器翻译, 编码器-解码器, 循环语言模型, 研究脉络
  - 总结: 源文把该文献归入“继续推动循环语言模型与编码器-解码器架构边界”的努力之列，用于说明 Transformer 出现之前该路线已取得的进展与饱和状态。

- [27] Ankur Parikh, 2016
  - 标题: A decomposable attention model
  - 关键词: 可分解注意力, 无循环网络, 文本蕴含, 少数例外
  - 总结: 源文以该引用标明注意力可以脱离循环网络单独使用，并展示其在文本蕴含等任务上的成功，既构成自注意力应用谱系的证据，也界定出 Transformer 结构新颖性的边界。

- [28] Romain Paulus, 2017
  - 标题: A deep reinforced model for abstractive summarization
  - 关键词: 抽象摘要, 强化学习, 自注意力应用, 生成任务
  - 总结: 源文以该引用证明自注意力已被有效用于抽象摘要这一生成式任务，支撑其关于自注意力适用面广的论述。

- [32] Noam Shazeer, 2017
  - 标题: Outrageously large neural networks: The sparsely-gated mixture-of-experts layer
  - 关键词: 条件计算, 混合专家, 稀疏门控, 计算效率, 模型容量
  - 总结: 源文用该引用说明条件计算在提升计算效率的同时还能改善性能，但这种做法仍是在顺序框架内扩展容量，未消除逐步展开的计算约束。

- [34] Sainbayar Sukhbaatar, 2015
  - 标题: End-to-end memory networks
  - 关键词: 记忆网络, 循环注意力, 问答, 语言建模, 替代循环
  - 总结: 源文用该引用说明注意力可以承担原本属于循环网络的记忆与对齐职责，并在简单问答与语言建模上验证了这一做法，是其“用自注意力替换循环”论证的直接前例。

- [38] Yonghui Wu, 2016
  - 标题: Google’s neural machine translation system: Bridging the gap between human and machine translation
  - 关键词: 神经机器翻译, 编码器-解码器架构, 循环语言模型, 后续工作举例
  - 总结: 源文把该文献作为“循环语言模型与编码器-解码器架构仍在持续演进”这一陈述的实例之一，作用是脉络性背景说明，而非对具体方法或实验结果的直接对比。



#### Component

- [4] Jianpeng Cheng, 2016
  - 标题: Long short-term memory-networks for machine reading
  - 关键词: 自注意力, 机器阅读, 阅读理解, 任务先例
  - 总结: 源文引用该文献说明自注意力机制已被成功应用于阅读理解任务，把注意力作为通用序列建模组件的论断从机器翻译扩展到其他自然语言处理任务。



#### Baseline

- [5] Kyunghyun Cho, 2014
  - 标题: Learning phrase representations using rnn encoder-decoder for statistical machine translation
  - 关键词: RNN, 编码器-解码器, 短语表示, 机器翻译, 技术先例
  - 总结: 源文引用该文献代表循环网络编码器-解码器在机器翻译方向的开创性成果，作为 RNN 类模型达到最先进水平的例证，用于界定 Transformer 需要超越的循环路线。

- [7] Junyoung Chung, 2014
  - 标题: Empirical evaluation of gated recurrent neural networks on sequence modeling
  - 关键词: 门控循环网络, 序列建模, RNN 变体, 基线模型, 状态判定
  - 总结: 源文引用该文献作为门控循环神经网络的代表工作，说明在 Transformer 出现之前 RNN 的 LSTM 与门控单元变体已确立为序列建模与转导任务的最先进方法。

- [9] Jonas Gehring, 2017
  - 标题: Convolutional sequence to sequence learning
  - 关键词: ConvS2S, 卷积神经网络, 并行计算, 序列到序列, 线性复杂度
  - 总结: 源文用该文献代表卷积式序列到序列方案：一方面借其线性距离复杂度说明这类模型难以学习远距离依赖，另一方面把它列为 Transformer 优势讨论所对照的既有转导模型，从而凸显自注意力恒定路径长度与无循环/卷积结构的新颖性。

- [13] Sepp Hochreiter, 1997
  - 标题: Long short-term memory
  - 关键词: LSTM, 循环神经网络, 长程依赖, 序列建模, 对比基线
  - 总结: 源文用该文献确立 LSTM 在序列建模与转导任务上的既成地位，作为论述起点的循环网络技术基线，说明 Transformer 是在何种既有模型之上提出替代方案。

- [16] Łukasz Kaiser, 2016
  - 标题: Can active memory replace attention?
  - 关键词: Extended Neural GPU, 卷积, 顺序计算, 并行化, 前作
  - 总结: 源文把该文献与 ByteNet、ConvS2S 一并归入以卷积并行计算、从而减少顺序计算的模型族，作为对比 Transformer 恒定操作数优势时的直接前作与复杂度参照。

- [17] Łukasz Kaiser, 2016
  - 标题: Neural GPUs learn algorithms
  - 关键词: Neural GPU, 外部记忆, 卷积, 转导模型, 对比对象
  - 总结: 源文把该文献列为 Transformer 之前转导模型路线的代表之一，用于界定“完全依赖自注意力”这一结构新颖性的边界。

- [35] Ilya Sutskever, 2014
  - 标题: Sequence to sequence learning with neural networks
  - 关键词: 序列到序列, 编码器-解码器, 神经机器翻译, 基线范式
  - 总结: 源文把该文献用作循环序列到序列方法在机器翻译上既成地位的代表之一，从而确立 Transformer 出发时的循环式转导基线水平。



#### Background

- [19] Yoon Kim, 2017
  - 标题: Structured attention networks
  - 关键词: 注意力机制, 跨距离依赖, 序列建模, 转导模型
  - 总结: 源文用该文献证明注意力机制在多种序列建模与转导任务上已取得成功并能无视位置距离建模依赖，是源文把注意力提升为通用建模原语的旁证。





### 时间线分析

#### 早期
最早的一批引用给出循环路线的起点与困难的两面：LSTM（1997）确立了用门控单元处理长程依赖的循环方案，梯度流分析（2001）则解释了这类结构为何难以学习远距离依赖；随后 2014 年前后涌现的序列到序列、RNN 编码器-解码器与注意力式神经机器翻译文献，把循环网络连同注意力一起确立为序列建模与转导任务上的最先进方法，注意力式神经机器翻译文献同时提供了“依赖关系可不受位置距离限制”的经验依据。


- [13] Sepp Hochreiter, 1997: Long short-term memory

- [12] Sepp Hochreiter, 2001: Gradient flow in recurrent nets: the difficulty of learning long-term dependencies

- [2] Dzmitry Bahdanau, 2014: Neural machine translation by jointly learning to align and translate

- [5] Kyunghyun Cho, 2014: Learning phrase representations using rnn encoder-decoder for statistical machine translation

- [7] Junyoung Chung, 2014: Empirical evaluation of gated recurrent neural networks on sequence modeling

- [35] Ilya Sutskever, 2014: Sequence to sequence learning with neural networks

- [24] Minh-Thang Luong, 2015: Effective approaches to attentionbased neural machine translation




#### 中期
随后的引用把注意力与自注意力从循环结构中部分剥离出来，并展示其任务适用面：端到端记忆网络说明注意力可以承担原本属于序列对齐循环的记忆与对齐职责，基于注意力的神经机器翻译、机器阅读与可分解注意力模型等文献分别对应注意力在转导、阅读理解与文本蕴含上的成功，可分解注意力模型还是“注意力不与循环网络结合”的少数例外；2016 年的极限语言建模与大规模神经机器翻译系统则被用来概括循环语言模型与编码器-解码器架构仍在持续演进的脉络，Extended Neural GPU 与 Neural GPU 出现在减少顺序计算的模型族列举中。


- [34] Sainbayar Sukhbaatar, 2015: End-to-end memory networks

- [4] Jianpeng Cheng, 2016: Long short-term memory-networks for machine reading

- [15] Rafal Jozefowicz, 2016: Exploring the limits of language modeling

- [16] Łukasz Kaiser, 2016: Can active memory replace attention?

- [17] Łukasz Kaiser, 2016: Neural GPUs learn algorithms

- [27] Ankur Parikh, 2016: A decomposable attention model

- [38] Yonghui Wu, 2016: Google’s neural machine translation system: Bridging the gap between human and machine translation




#### 近期
最新一批引用围绕计算效率与并行化展开：因子分解技巧与稀疏门控条件计算试图缓解循环模型的顺序瓶颈却未解除根本约束，ConvS2S（操作数随距离线性增长）与 ByteNet（对数增长）等卷积并行化模型仍受距离复杂度限制，结构化自注意力句向量与深度强化学习摘要则显示自注意力本身已具备独立的表示与生成能力，结构化注意力网络延续了注意力在跨距离依赖建模上的经验。源文以这些工作作为直接对照，凸显全自注意力把路径长度降为常数的结构性优势。


- [9] Jonas Gehring, 2017: Convolutional sequence to sequence learning

- [18] Nal Kalchbrenner, 2017: Neural machine translation in linear time

- [19] Yoon Kim, 2017: Structured attention networks

- [21] Oleksii Kuchaiev, 2017: Factorization tricks for LSTM networks

- [22] Zhouhan Lin, 2017: A structured self-attentive sentence embedding

- [28] Romain Paulus, 2017: A deep reinforced model for abstractive summarization

- [32] Noam Shazeer, 2017: Outrageously large neural networks: The sparsely-gated mixture-of-experts layer





