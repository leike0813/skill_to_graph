## 文献综述章节引文线索

### 总体总结
原文在引言与背景两节中按“既有主流 → 局部缓解 → 直接对照 → 自注意力先例”的顺序组织引用。先以 LSTM [13]、门控循环网络 [7]、RNN encoder–decoder [5]、seq2seq [35] 与注意力式 NMT [24] 确立循环序列模型在序列建模与机器翻译中的既有地位，再指出其沿符号位置分解计算带来的顺序约束无法通过因子分解技巧 [21] 或条件计算 [32] 根本解除。随后引用注意力式 NMT [24] 与结构化注意力网络 [19] 说明注意力已成为主流组件，却几乎总是与循环网络搭配使用，只有可分解注意力模型 [27] 等少数例外；再以端到端记忆网络 [34]、神经 GPU [17] 承认以注意力替代序列对齐递归的先例及其“仍是循环注意力、任务简单”的局限；最后以 ConvS2S [9]、ByteNet [18] 提供位置距离开销可量化的并行化对照，并以自注意力在阅读理解、摘要、文本蕴含与句表示上的既有应用支撑其作为通用序列建模组件的可行性，从而为提出完全依赖 self-attention 的 Transformer 划出清晰边界。


### 关键文献

- [9] Jonas Gehring, 2017: Convolutional Sequence to Sequence Learning (Baseline)

- [13] S. Hochreiter, 1997: Long Short-Term Memory (Background)

- [17] Łukasz Kaiser, 2016: Neural GPUs learn algorithms (Baseline)

- [18] N. Kalchbrenner, 2017: Neural Machine Translation in Linear Time (Baseline)

- [27] Ankur Parikh, 2016: A decomposable attention model (Contrast)



### 范围
- 章节: 1 Introduction + 2 Background
- 行号: 25-43

### 按功能归类


#### Uncategorized

- [2] D. Bahdanau, 2014
  - 标题: Neural Machine Translation by Jointly Learning to Align and Translate
  - 关键词: attention, seq2seq, NMT, encoder-decoder, soft alignment
  - 总结: 在本节语境中，该引用承担双重论证职能：一方面它为“注意力机制已成为 compelling sequence modeling 与 transduction 模型不可分割的组成部分”提供原始出处，界定了本文所推进的注意力技术谱系；另一方面它也是“注意力几乎都与循环网络联合使用”这一论断的典型样本，源文借此把当时的主流范式概括为 RNN + attention 的组合，从而为“Transformer 是第一个完全依赖 self-attention、既不用序列对齐的 RNN 也不用卷积的 transduction 模型”这一新颖性主张划出清晰的边界。源文并未在该处引用其具体对齐算法或实验结果，仅将其作为范式层面的支点。



#### Component

- [4] Jian-Peng Cheng, 2016
  - 标题: Long Short-Term Memory-Networks for Machine Reading
  - 关键词: self-attention, reading comprehension, LSTM, sentence representation
  - 总结: 在本节语境中，该引用只是 self-attention 任务覆盖面清单中的一个实例：它说明“把注意力用于序列内部不同位置之间的关联”这一做法，已被用于机器阅读这类需要跨位置推理的任务，从而佐证 self-attention 并非 Transformer 才引入的新机制。源文在此不涉及其具体网络结构或注意力层的实现细节，其功能是历史与覆盖面意义上的背景铺垫，而不是对比或论证依据。



#### Baseline

- [5] Kyunghyun Cho, 2014
  - 标题: Learning Phrase Representations using RNN Encoder–Decoder for Statistical Machine Translation
  - 关键词: seq2seq, encoder-decoder, RNN, phrase representation, SMT
  - 总结: 在本节语境中，该引用的作用是把“encoder-decoder 架构”与“循环网络”牢牢绑定为一个既有范式：它示范了以 RNN 编码输入句子、解码生成目标短语的端到端翻译框架，并证明该框架在机器翻译上取得强结果。源文以此支撑“RNN 已被 firmly established as state of the art”这一前提性判断，进而说明其沿时间步的顺序计算为何成为必须绕开的瓶颈；引用本身不承担对比或方法继承的功能，也不涉及其内部结构细节。

- [9] Jonas Gehring, 2017
  - 标题: Convolutional Sequence to Sequence Learning
  - 关键词: ConvS2S, CNN, seq2seq, parallel computation, contrast baseline
  - 总结: 在本节语境中，该引用是论文并行化论证中最具体、最可量化的对照物：源文借它指出卷积模型虽然以并行方式计算所有位置的隐藏表示，但关联任意两个输入/输出位置所需的操作数会随位置距离增长——对 ConvS2S 是线性增长（对 ByteNet 是对数增长），因而更难学习远距离依赖；而 Transformer 把该操作数降为常数，仅以注意力加权平均带来的有效分辨率下降为代价。源文还在结尾把它明确列入“将要讨论优势”的对照名单，使它成为全文比较框架中的正式基线。

- [16] Lukasz Kaiser, 2016
  - 标题: Can Active Memory Replace Attention?
  - 关键词: Extended Neural GPU, CNN, parallel computation, active memory, sequence modeling
  - 总结: 在本节语境中，该引用承担“减少顺序计算”这一动机链条上的路线起点：它与 ByteNet、ConvS2S 一同说明，把循环计算替换为可并行的卷积操作是当时已被充分探索的替代思路，因而 Transformer 的差异化只能落在“以 self-attention 而非卷积操作来关联位置”这一点上。该工作本身探讨的是以主动记忆操作替代注意力计算，与源文关注点相邻但方向不同，源文在此仅借用其卷积化并行这一属性作为对照坐标，不涉及其内部机制或实验结论。

- [17] Łukasz Kaiser, 2016
  - 标题: Neural GPUs learn algorithms
  - 关键词: Neural GPU, algorithm learning, contrast baseline, convolution
  - 总结: 在本节语境中，该引用只以点名方式出现，功能是为源文的新颖性主张划定对照谱系：论文宣称 Transformer 是首个完全依赖 self-attention 计算输入与输出表示、且不使用序列对齐 RNN 或卷积的 transduction 模型，这一界线正是以 Neural GPU、ByteNet、ConvS2S 这一组既有模型为参照划出的；源文在此不展开其技术细节，仅把它列入后续章节将展开优势论证的对照名单，因此其角色是命名式对比基线而非论据来源。

- [18] N. Kalchbrenner, 2017
  - 标题: Neural Machine Translation in Linear Time
  - 关键词: Extended Neural GPU, 卷积序列模型, 并行计算, NMT, 顺序计算
  - 总结: 论文借该文说明减少顺序计算在卷积路线上的实现方式是用 CNN 一次性算出所有位置的隐藏表示，但关联两个任意位置所需的操作数会随距离增长（ConvS2S 线性、ByteNet 对数），因而难以学习远距离依赖；Transformer 用自注意力把该操作数降为常数。两处提及都把该文放在与自注意力路线对立的卷积模型一侧。

- [35] I. Sutskever, 2014
  - 标题: Sequence to Sequence Learning with Neural Networks
  - 关键词: seq2seq, encoder-decoder, NMT, RNN, state of the art
  - 总结: 论文借该文确立循环式 encoder–decoder 在机器翻译上的 state-of-the-art 与主流地位，作为随后"顺序计算阻碍样本内并行"这一批评所针对的对象，并由此把 Transformer 定位为对这一主流架构族的替换方案。

- [38] Yong-Hui Wu, 2016
  - 标题: Google's Neural Machine Translation System: Bridging the Gap between Human and Machine Translation
  - 关键词: NMT, encoder-decoder, LSTM, attention, GNMT
  - 总结: 在该综述语境中，这一引用的具体作用是为“循环模型是当时 state of the art 且仍在被不断推进”这一判断提供代表性证据：它把 LSTM encoder-decoder 加 attention 的循环式 NMT 体系推进到工业可用的深度与翻译质量，因而成为该段列举既有路线时的典型样本。源文在此并未把它当作需要与 Transformer 逐一比较的具体方法，而只是作为背景性的路线代表出现；这一铺垫同时为后文关于顺序计算限制训练并行度的批评、以及 Transformer 以 self-attention 取代循环结构的动机提供了参照系。



#### Background

- [7] Junyoung Chung, 2014
  - 标题: Empirical Evaluation of Gated Recurrent Neural Networks on Sequence Modeling
  - 关键词: gated RNN, GRU, sequence modeling, RNN
  - 总结: 在本节语境中，该引用为“gated recurrent neural networks 已成为序列建模的 state of the art”提供实验层面的依据：它通过大规模实证评测确立了带门控单元的循环网络在长序列建模上的优势，是源文用以界定被替代对象范围的另一半（另一半为 LSTM）。源文只借用它作为该架构家族的代表性成果标签，不引用其评测结论或具体门控设计，其价值在于说明循环路线当时的成熟度，从而支撑源文随后以“减少顺序计算”为切入点的动机论证。

- [12] S. Hochreiter, 2001
  - 标题: Gradient Flow in Recurrent Nets: the Difficulty of Learning Long-Term Dependencies
  - 关键词: vanishing gradient, long-term dependency, RNN, gradient flow
  - 总结: 在本节语境中，该引用承担的是“已知事实的出处”角色：它确立了循环网络中长期依赖难以学习的经典梯度流分析，源文据此把卷积模型随位置距离增长的操作数开销转化为实际的建模难度问题，从而支撑“远距离依赖更难学习”这一论断，也为 Transformer 恒定路径长度的主张提供学理上的落点。源文并未复述其推导过程或误差分析细节，引用仅用于标示该困难的公认来源。

- [13] S. Hochreiter, 1997
  - 标题: Long Short-Term Memory
  - 关键词: LSTM, RNN, sequence modeling, gating, cell state
  - 总结: 在本节语境中，该引用是整篇论文动机链条的前提：正因为 LSTM 这类循环网络已经成为语言建模与机器翻译等任务的 state of the art，其必须沿时间步逐个计算的顺序性才构成需要被消除的真正瓶颈，源文由此把“减少顺序计算”确立为整篇工作的出发点。引用在此处承担的是范式标定功能——它回答“被替代的对象是谁”，而非提供任何可直接迁移到 Transformer 的组件或实验结论。

- [15] R. Józefowicz, 2016
  - 标题: Exploring the Limits of Language Modeling
  - 关键词: language modeling, LSTM, large-scale, encoder-decoder
  - 总结: 在本节语境中，该引用的功能是把“循环路线仍在被持续推进”这件事交代清楚：它代表了在大规模语料上把循环语言模型与 encoder-decoder 架构推向极限的一类后续工作，与该句中的另两项引用并列。源文以此说明，围绕循环模型的改进已相当充分，从而让完全转向 self-attention 显得是一条此前未被尝试的替代方向；源文不涉及其具体模型规模、采样方法或评测设置，引用仅承担路线史层面的背景铺垫。

- [19] Yoon Kim, 2017
  - 标题: Structured Attention Networks
  - 关键词: attention, structured attention, 序列建模, 依赖建模
  - 总结: 该文把注意力机制系统地组织进序列建模框架，代表注意力在多个序列任务中被广泛采用的状况；论文引用它来确立"注意力已是主流组件"这一前提，随后以"除少数情况外注意力仍与循环网络搭配使用"把讨论引向让自注意力独立承担序列表示。

- [21] Oleksii Kuchaiev, 2017
  - 标题: Factorization tricks for LSTM networks
  - 关键词: LSTM, factorization tricks, 计算效率, 顺序计算
  - 总结: 在 Background 中它不是待采用的组件，而是"部分缓解顺序计算限制的既有努力"之一；论文紧接着指出根本约束依然存在，用以论证只有改变计算结构本身（改用自注意力）才能真正获得样本内并行性。

- [22] Zhouhan Lin, 2017
  - 标题: A Structured Self-attentive Sentence Embedding
  - 关键词: self-attention, sentence embedding, structured attention, 序列表示
  - 总结: 该文用结构化自注意力聚合序列位置信息来学习句子级表示，论文借此说明自注意力在表示学习类任务上已经验证有效；但其目标是表示而非转换建模，因此并未覆盖 Transformer 所主张的转换模型场景。

- [24] Thang Luong, 2015
  - 标题: Effective Approaches to Attention-based Neural Machine Translation
  - 关键词: attention-based NMT, encoder-decoder, recurrent language model, Luong attention
  - 总结: 论文用该文说明循环语言模型与 encoder-decoder 架构虽不断被改进、注意力也已被成功引入其中，但这类模型仍沿序列位置逐步计算、无法在样本内并行；它因此构成"继续在原架构内做局部优化不足以突破瓶颈"的论据。

- [28] Romain Paulus, 2017
  - 标题: A Deep Reinforced Model for Abstractive Summarization
  - 关键词: abstractive summarization, self-attention, reinforcement learning, sequence generation
  - 总结: 该文在摘要生成中引入基于自注意力的注意力机制并用强化学习训练，论文引用它来说明自注意力在阅读理解、摘要、蕴含等任务上均已取得成功，从而为把自注意力提升为转换模型的核心机制提供经验铺垫。

- [32] Noam Shazeer, 2017
  - 标题: Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer
  - 关键词: sparsely-gated MoE, conditional computation, 模型容量, 计算效率, scaling
  - 总结: 论文用该文代表通过稀疏专家与条件计算扩大模型容量、提升效率的方向，并将其与分解技巧并列作为"局部缓解"的证据；由于这类方案在序列维度上仍逐步计算，它们无法提供 Transformer 所追求的样本内全并行。



#### Contrast

- [27] Ankur Parikh, 2016
  - 标题: A decomposable attention model
  - 关键词: decomposable attention, self-attention, textual entailment, 非循环注意力, 例外
  - 总结: 该文以纯前馈的注意力结构完成文本蕴含而无需循环网络，因此论文在陈述"首个完全依赖自注意力的转换模型"时必须为它留出余地：它既证明了无循环注意力的可行性，也构成对 Transformer 新颖性主张的直接限定。

- [34] Sainbayar Sukhbaatar, 2015
  - 标题: End-To-End Memory Networks
  - 关键词: end-to-end memory networks, recurrent attention, external memory, 语言建模, 问答
  - 总结: 它说明在 Transformer 之前已存在把注意力而非序列对齐循环当作序列处理主机制的模型，并在简单问答与语言建模上有效；论文把它置于新颖性主张之前，既承认这一先例，也以"仅是循环注意力、且任务简单"界定其与自注意力转换模型的差别。





### 时间线分析

#### 早期
早期引用集中奠定了循环序列建模的骨架：LSTM [13] 与门控循环网络评测 [7] 确立了长序列建模的 state of the art，RNN encoder–decoder [5] 与 seq2seq [35] 把循环网络推入机器翻译的主流，注意力式 NMT [24] 给出了注意力融入该体系的代表方案，而梯度流分析 [12] 则提供了远距离依赖难以学习的经典依据。


- [13] S. Hochreiter, 1997: Long Short-Term Memory

- [12] S. Hochreiter, 2001: Gradient Flow in Recurrent Nets: the Difficulty of Learning Long-Term Dependencies

- [2] D. Bahdanau, 2014: Neural Machine Translation by Jointly Learning to Align and Translate

- [5] Kyunghyun Cho, 2014: Learning Phrase Representations using RNN Encoder–Decoder for Statistical Machine Translation

- [7] Junyoung Chung, 2014: Empirical Evaluation of Gated Recurrent Neural Networks on Sequence Modeling

- [35] I. Sutskever, 2014: Sequence to Sequence Learning with Neural Networks

- [24] Thang Luong, 2015: Effective Approaches to Attention-based Neural Machine Translation




#### 中期
中期引用把讨论从循环架构扩展到注意力本身：端到端记忆网络 [34] 与神经 GPU [17] 用循环注意力替代序列对齐递归，构成最接近的先例；可分解注意力模型 [27] 则是论文自己点名的少数不依赖循环的例外；自注意力在阅读理解 [4]、语言建模上限 [15]、任务无关句子表示 [22] 与注意力式 NMT [24] 上的成功，说明注意力已成为可独立承担序列建模的通用组件。


- [34] Sainbayar Sukhbaatar, 2015: End-To-End Memory Networks

- [4] Jian-Peng Cheng, 2016: Long Short-Term Memory-Networks for Machine Reading

- [15] R. Józefowicz, 2016: Exploring the Limits of Language Modeling

- [16] Lukasz Kaiser, 2016: Can Active Memory Replace Attention?

- [17] Łukasz Kaiser, 2016: Neural GPUs learn algorithms

- [27] Ankur Parikh, 2016: A decomposable attention model

- [38] Yong-Hui Wu, 2016: Google's Neural Machine Translation System: Bridging the Gap between Human and Machine Translation




#### 近期
近期引用与本文方法直接相邻：ConvS2S [9] 与 ByteNet [18] 代表卷积并行化路线，其位置距离开销随距离增长、难以学习远距离依赖；因子分解技巧 [21] 与稀疏门控混合专家层 [32] 说明既有缓解手段只做局部改良、无法解除顺序计算约束；结构化注意力网络 [19]、强化学习摘要 [28] 与结构化句表示 [22] 则显示自注意力在生成式与表示式任务上已可独立工作。


- [9] Jonas Gehring, 2017: Convolutional Sequence to Sequence Learning

- [18] N. Kalchbrenner, 2017: Neural Machine Translation in Linear Time

- [19] Yoon Kim, 2017: Structured Attention Networks

- [21] Oleksii Kuchaiev, 2017: Factorization tricks for LSTM networks

- [22] Zhouhan Lin, 2017: A Structured Self-attentive Sentence Embedding

- [28] Romain Paulus, 2017: A Deep Reinforced Model for Abstractive Summarization

- [32] Noam Shazeer, 2017: Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer





