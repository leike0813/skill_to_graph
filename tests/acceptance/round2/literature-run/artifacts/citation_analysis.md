## 文献综述章节引文线索

### 总体总结
源文在“1 Introduction + 2 Background”范围内把引用组织为三条线索：其一，用 LSTM [13]、门控循环网络 [7] 与序列到序列类工作 [35, 2, 5] 确立循环网络在语言建模与机器翻译等序列建模与转导问题上的最先进地位，并指出注意力机制几乎总与循环网络配合使用（例外为 [27]）；其二，用端到端记忆网络 [34] 以及自注意力在阅读理解、抽象摘要、文本蕴含与任务无关句子表示上的成功 [4, 27, 28, 22] 说明注意力可承担原属循环结构的职责且已有跨任务应用积累，并以 [38, 24, 15] 概括该路线仍在被继续推进的脉络；其三，用因子分解技巧与条件计算 [21, 32] 以及以卷积为基本构件的并行模型 Extended Neural GPU、ByteNet、ConvS2S [16, 18, 9] 构成“减少顺序计算”的对照面——这类模型关联两个位置所需操作数随距离线性或对数增长，使远距离依赖更难学习 [12]，源文据此提出完全依赖自注意力并把该操作数降为常数的结构（Transformer 优势讨论所对照的模型另含 [17]）。总体上，此处的引用主要承担基线界定、对照与动机的作用，而不是被逐一评述的独立工作。


### 关键文献

- [13] Sepp Hochreiter, 1997: Long short-term memory (Baseline)

- [12] Sepp Hochreiter, 2001: Gradient flow in recurrent nets: the difficulty of learning long-term dependencies (Uncategorized)

- [2] Dzmitry Bahdanau, 2014: Neural machine translation by jointly learning to align and translate (Uncategorized)

- [27] Ankur Parikh, 2016: A decomposable attention model (Uncategorized)

- [9] Jonas Gehring, 2017: Convolutional sequence to sequence learning (Uncategorized)



### 范围
- 章节: 1 Introduction + 2 Background
- 行号: 25-43

### 按功能归类


#### Uncategorized

- [2] Dzmitry Bahdanau, 2014
  - 标题: Neural machine translation by jointly learning to align and translate
  - 关键词: 注意力机制, 神经机器翻译, 序列建模, 转导模型, 距离无关依赖
  - 总结: 源文用该文既确立注意力在机器翻译等任务上已成为序列建模与转导模型中不可或缺的组成部分，又作为“注意力可无视输入/输出位置距离建模依赖”的代表性工作；同时它出现在源文说明注意力几乎总与循环网络搭配使用的那一段落中（该段的例外由 [27] 标出）。

- [4] Jianpeng Cheng, 2016
  - 标题: Long short-term memory-networks for machine reading
  - 关键词: 机器阅读, 长短期记忆网络, 自注意力, 阅读理解
  - 总结: 源文把该文列入自注意力已在阅读理解、抽象摘要、文本蕴含与学习任务无关句子表示等任务上成功应用的工作列表 [4, 27, 28, 22]，用以说明自注意力在序列理解类任务上已有成功应用；源文未逐项说明各引用与任务的对应关系。

- [5] Kyunghyun Cho, 2014
  - 标题: Learning phrase representations using rnn encoder-decoder for statistical machine translation
  - 关键词: RNN 编码器-解码器, 短语表示, 统计机器翻译, 序列建模
  - 总结: 源文把该文列为机器翻译方向上与 [35, 2] 并列的 RNN 编码器-解码器代表工作，用于支撑循环网络在序列建模与转导问题上已成为最先进方法的回顾性陈述；文中未评述其具体方法。

- [9] Jonas Gehring, 2017
  - 标题: Convolutional sequence to sequence learning
  - 关键词: ConvS2S, 卷积序列到序列, 并行计算, 距离复杂度, 基线对比
  - 总结: 源文用该文代表卷积式序列到序列方案：一方面借其“关联两位置所需操作数随距离线性增长”说明这类模型难以学习远距离依赖，另一方面把它列为 Transformer 优势讨论所对照的既有转导模型，凸显完全依赖自注意力的结构差异。

- [12] Sepp Hochreiter, 2001
  - 标题: Gradient flow in recurrent nets: the difficulty of learning long-term dependencies
  - 关键词: 梯度流, 长期依赖, 循环网络, 远距离依赖
  - 总结: 源文引用该文支撑“位置距离增长使远距离依赖更难学习”的判断，作为其对比路径长度的论证依据；源文在此处只给出出处，未展开该文的分析内容。

- [15] Rafal Jozefowicz, 2016
  - 标题: Exploring the limits of language modeling
  - 关键词: 语言建模, 循环语言模型, 能力边界, 后续工作
  - 总结: 源文把该文列入“继续推进循环语言模型与编码器-解码器架构边界”的并列引用 [38, 24, 15] 中，用于交代既有循环路线的持续演进；源文以集合式列举出现，未展开其具体方法或结果。

- [16] Łukasz Kaiser, 2016
  - 标题: Can active memory replace attention?
  - 关键词: Extended Neural GPU, 卷积网络, 并行计算, 顺序计算, 隐藏表示
  - 总结: 源文把该文（题名为 Can active memory replace attention?）列在“减少顺序计算”这一目标的基础性成果中，与 ByteNet、ConvS2S 共享“以卷积为基本构件、并行计算所有输入与输出位置隐藏表示”的描述，用来界定源文随后讨论操作数随位置距离增长这一问题的模型范围。

- [18] Nal Kalchbrenner, 2017
  - 标题: Neural machine translation in linear time
  - 关键词: ByteNet, 卷积序列模型, 对数复杂度, 并行计算, 机器翻译
  - 总结: 源文用该文代表 ByteNet：以卷积为基本构件并行计算各位置隐藏表示以减少顺序计算，并指出其关联两位置所需操作数随距离对数增长，仍使远距离依赖更难学习；随后又被列入 Transformer 优势讨论的对照模型 [17, 18] 和 [9]。

- [21] Oleksii Kuchaiev, 2017
  - 标题: Factorization tricks for LSTM networks
  - 关键词: 因子分解技巧, LSTM, 计算效率, 顺序计算, 并行化
  - 总结: 源文用该文说明循环模型的效率改进之一是因子分解技巧，与条件计算并列，二者显著提升了计算效率却仍未消除顺序计算的根本约束，从而过渡到源文强调自注意力可全并行计算的主张。

- [22] Zhouhan Lin, 2017
  - 标题: A structured self-attentive sentence embedding
  - 关键词: 自注意力, 句子嵌入, 表示学习, 任务无关表示
  - 总结: 源文把该文列入自注意力已成功用于阅读理解、抽象摘要、文本蕴含与学习任务无关句子表示等工作列表 [4, 27, 28, 22]，用以说明自注意力已被用于句子表示这类学习任务；源文未评述其嵌入结构。

- [24] Minh-Thang Luong, 2015
  - 标题: Effective approaches to attentionbased neural machine translation
  - 关键词: 注意力机制, 神经机器翻译, 编码器-解码器, 后续工作
  - 总结: 源文把该文作为推动循环语言模型与编码器-解码器架构边界的若干后续努力之一引用（集合式列举 [38, 24, 15]），用以说明 Transformer 之前该路线仍在被继续推进；源文在此处未给出方法细节或结果对比。

- [27] Ankur Parikh, 2016
  - 标题: A decomposable attention model
  - 关键词: 可分解注意力, 非循环注意力, 文本蕴含, 例外情况, 自注意力
  - 总结: 源文用该文标记注意力机制中少数不与循环网络结合使用的情况，并把它列入自注意力已在多种任务上成功应用的工作列表 [4, 27, 28, 22]，从而既说明注意力不必然与循环结构绑定，也提供自注意力跨任务应用的证据。

- [28] Romain Paulus, 2017
  - 标题: A deep reinforced model for abstractive summarization
  - 关键词: 抽象摘要, 深度强化学习, 自注意力, 生成式任务
  - 总结: 源文把该文列入自注意力已成功用于阅读理解、抽象摘要、文本蕴含与学习任务无关句子表示的工作列表 [4, 27, 28, 22]，用以支撑自注意力在摘要这类生成式任务上同样可用；源文未展开其模型或结果细节。

- [32] Noam Shazeer, 2017
  - 标题: Outrageously large neural networks: The sparsely-gated mixture-of-experts layer
  - 关键词: 条件计算, 稀疏门控混合专家, 计算效率, 模型性能, 顺序约束
  - 总结: 源文把该文作为条件计算方向的代表工作引用，指出其在提升计算效率的同时还改进了模型性能，但与因子分解技巧一样并未消除顺序计算的根本约束；源文未展开其具体结构。

- [35] Ilya Sutskever, 2014
  - 标题: Sequence to sequence learning with neural networks
  - 关键词: 序列到序列, 神经机器翻译, 编码器-解码器, 最先进方法, 对照基线
  - 总结: 源文用该文作为机器翻译方向的循环序列到序列代表工作之一，与 [2, 5] 一起支撑“循环网络已成为序列建模与转导问题最先进方法”的回顾性陈述；源文未在此处展开其模型细节。

- [38] Yonghui Wu, 2016
  - 标题: Google’s neural machine translation system: Bridging the gap between human and machine translation
  - 关键词: 神经机器翻译, 编码器-解码器架构, 循环语言模型, 后续工作
  - 总结: 源文把该文与另外两项并列引用，作为“循环语言模型与编码器-解码器架构仍在被继续推进”这一趋势性判断的代表性例证；引用为集合式举例，源文未展开其系统细节或实验结果。



#### Baseline

- [7] Junyoung Chung, 2014
  - 标题: Empirical evaluation of gated recurrent neural networks on sequence modeling
  - 关键词: 门控循环网络, 序列建模, 实证评估, 最先进方法
  - 总结: 源文用该文指代门控循环神经网络这一模型族，并把它与循环神经网络、LSTM 一起断言为序列建模与转导问题上的最先进方法，作为源文对照既有循环基线的一方；文中未展开其评估细节。

- [13] Sepp Hochreiter, 1997
  - 标题: Long short-term memory
  - 关键词: LSTM, 长短期记忆, 循环神经网络, 序列建模, 转导问题
  - 总结: 源文用该文指称 long short-term memory 这一模型族，并与循环神经网络、门控循环网络一起断言它们在语言建模与机器翻译等序列建模与转导问题上已成为最先进方法；该引用以模型名出处的形式出现，源文未在此处展开其机制细节。

- [17] Łukasz Kaiser, 2016
  - 标题: Neural GPUs learn algorithms
  - 关键词: Neural GPU, 转导模型, 对比模型, 自注意力首创性
  - 总结: 源文在给出“Transformer 是首个完全依赖自注意力的转导模型”这一论断后，把该文与 [18]、[9] 一并列为后续讨论 Transformer 优势时的参照模型；该引用在此处只承担对照列举的作用，源文未说明其机制细节，也未把它归入减少顺序计算的卷积模型族。



#### Background

- [19] Yoon Kim, 2017
  - 标题: Structured attention networks
  - 关键词: 注意力机制, 序列建模, 距离无关依赖, 转导模型
  - 总结: 源文引用该文与 [2] 一起佐证注意力机制已成为序列建模与转导模型中不可或缺的组成部分、能建模不受位置距离限制的依赖；引用以论点支撑的形式出现，源文未讨论其网络结构。

- [34] Sainbayar Sukhbaatar, 2015
  - 标题: End-to-end memory networks
  - 关键词: 记忆网络, 循环注意力机制, 简单语言问答, 语言建模
  - 总结: 源文引用该文指出端到端记忆网络以循环注意力机制而非与序列对齐的循环为基础，并在简单语言问答与语言建模任务上取得良好表现，作为注意力机制可行的既有实例。





### 时间线分析

#### 早期
最早的一批引用给出循环路线的起点与理论背景：LSTM（1997）与门控循环网络（2014）被源文并列为序列建模与转导问题上的最先进方法，序列到序列学习（2014）与 RNN 编码器-解码器短语表示（2014）代表机器翻译方向的循环工作；注意力式神经机器翻译（2014）支撑“注意力机制已成为不可或缺的组成部分并可建模不受位置距离限制的依赖”，基于注意力的神经机器翻译（2015）则出现在继续推进循环语言模型与编码器-解码器架构边界的并列引用中；梯度流分析（2001）支撑“位置距离增长使远距离依赖更难学习”这一判断。


- [13] Sepp Hochreiter, 1997: Long short-term memory

- [12] Sepp Hochreiter, 2001: Gradient flow in recurrent nets: the difficulty of learning long-term dependencies

- [2] Dzmitry Bahdanau, 2014: Neural machine translation by jointly learning to align and translate

- [5] Kyunghyun Cho, 2014: Learning phrase representations using rnn encoder-decoder for statistical machine translation

- [7] Junyoung Chung, 2014: Empirical evaluation of gated recurrent neural networks on sequence modeling

- [35] Ilya Sutskever, 2014: Sequence to sequence learning with neural networks

- [24] Minh-Thang Luong, 2015: Effective approaches to attentionbased neural machine translation




#### 中期
随后的一批引用把注意力的作用从循环结构中部分分离出来并显示其任务适用面：端到端记忆网络说明注意力可承担原属序列对齐循环的职责，机器阅读与可分解注意力模型出现在自注意力跨任务成功应用的语境中，可分解注意力模型同时是“注意力不与循环网络结合”的少数例外；极限语言建模探索（2016）与大规模神经机器翻译系统（2016）被用来概括循环语言模型与编码器-解码器架构仍在被继续推进的脉络；Extended Neural GPU 被列入减少顺序计算的模型族，而 Neural GPU 则出现在 Transformer 优势讨论所对照的模型 [17, 18] 和 [9] 之中。


- [34] Sainbayar Sukhbaatar, 2015: End-to-end memory networks

- [4] Jianpeng Cheng, 2016: Long short-term memory-networks for machine reading

- [15] Rafal Jozefowicz, 2016: Exploring the limits of language modeling

- [16] Łukasz Kaiser, 2016: Can active memory replace attention?

- [17] Łukasz Kaiser, 2016: Neural GPUs learn algorithms

- [27] Ankur Parikh, 2016: A decomposable attention model

- [38] Yonghui Wu, 2016: Google’s neural machine translation system: Bridging the gap between human and machine translation




#### 近期
最新一批引用围绕并行化与计算效率展开：因子分解技巧（2017）与稀疏门控条件计算（2017）试图缓解循环模型的顺序瓶颈却未解除根本约束；ConvS2S 与 ByteNet（2017）等卷积并行化模型中关联两位置所需操作数随距离线性或对数增长，仍受距离复杂度限制；结构化自注意力句子嵌入（2017）、深度强化学习抽象摘要（2017）与结构化注意力网络（2017）显示自注意力在表示、生成与跨距离依赖建模上已有成功应用。源文以这些工作作为对照，凸显全自注意力把路径长度降为常数的结构性优势。


- [9] Jonas Gehring, 2017: Convolutional sequence to sequence learning

- [18] Nal Kalchbrenner, 2017: Neural machine translation in linear time

- [19] Yoon Kim, 2017: Structured attention networks

- [21] Oleksii Kuchaiev, 2017: Factorization tricks for LSTM networks

- [22] Zhouhan Lin, 2017: A structured self-attentive sentence embedding

- [28] Romain Paulus, 2017: A deep reinforced model for abstractive summarization

- [32] Noam Shazeer, 2017: Outrageously large neural networks: The sparsely-gated mixture-of-experts layer





