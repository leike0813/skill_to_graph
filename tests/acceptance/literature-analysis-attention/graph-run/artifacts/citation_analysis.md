## 文献综述章节引文线索

### 总体总结
Within the Introduction and Background scope, the source organizes its citations as a funnel from the dominant recurrent paradigm to its own contribution: it first establishes RNNs, LSTM and gated RNNs as the state-of-the-art family for sequence modeling and transduction, then notes that further scaling of recurrent language models and encoder-decoder architectures had reached its limits while factorization tricks and conditional computation improved efficiency without removing sequential computation. Attention is then introduced as the mechanism that models dependencies independent of distance, with the observation that it is nearly always coupled to a recurrent network — the gap the source fills — supported by the small set of standalone-attention and self-attention precedents. The Background section groups the parallel-computation lineage (Extended Neural GPU, ByteNet, ConvS2S, Neural GPU) and the gradient-flow analysis as the concrete cost of distance-dependent path length, closes with memory networks as structural precedent for replacing recurrence with attention, and finally asserts the novelty claim that the Transformer is the first transduction model relying entirely on self-attention.


### 关键文献

- [2] D. Bahdanau, 2014: Neural Machine Translation by Jointly Learning to Align and Translate (Historical)

- [9] Jonas Gehring, 2017: Convolutional Sequence to Sequence Learning (Baseline)

- [12] S. Hochreiter, 2001: Gradient Flow in Recurrent Nets: the Difficulty of Learning Long-Term Dependencies (Uncategorized)

- [18] N. Kalchbrenner, 2017: Neural Machine Translation in Linear Time (Baseline)

- [27] Ankur Parikh, 2016: A decomposable attention model (Component)



### 范围
- 章节: 1 Introduction + 2 Background
- 行号: 25-43

### 按功能归类


#### Historical

- [2] D. Bahdanau, 2014
  - 标题: Neural Machine Translation by Jointly Learning to Align and Translate
  - 关键词: attention, neural machine translation, encoder-decoder, alignment, long-range dependencies
  - 总结: The cited work introduced an attention-based neural machine translation model in which the decoder attends to encoder states, so that dependencies between distant input and output positions can be modeled directly. The source uses it both as a state-of-the-art exemplar of recurrent translation models and as the reference point for the observation that attention, though widely adopted in sequence models, is nearly always tied to a recurrent network — the gap the source's self-attention-only design addresses.



#### Uncategorized

- [4] Jian-Peng Cheng, 2016
  - 标题: Long Short-Term Memory-Networks for Machine Reading
  - 关键词: self-attention, intra-attention, reading comprehension, sentence representations, LSTM
  - 总结: The cited work applies self-attention, relating different positions of a single sequence to compute a sequence representation, to machine reading and related comprehension tasks. The source cites it to establish that self-attention had already been validated across multiple task families, which grounds its claim that relying entirely on self-attention for input and output representations is a well-founded design rather than an untested one.

- [12] S. Hochreiter, 2001
  - 标题: Gradient Flow in Recurrent Nets: the Difficulty of Learning Long-Term Dependencies
  - 关键词: gradient flow, long-term dependencies, vanishing gradient, recurrent networks, path length
  - 总结: The cited work analyzes gradient propagation through recurrent networks and characterizes the difficulty of learning long-term dependencies. The source cites it to substantiate the claim that architectures whose operation count between two positions grows with their separation make distant dependencies harder to learn, converting a well-known recurrent-net training pathology into the quantitative rationale for the source's constant-number-of-operations design.

- [16] Lukasz Kaiser, 2016
  - 标题: Can Active Memory Replace Attention?
  - 关键词: Extended Neural GPU, active memory, parallel computation, attention alternative, convolutional building block
  - 总结: The cited work proposes an active-memory architecture with an extended Neural GPU, exploring whether external memory operations can substitute for attention in sequence modeling, and shares the goal of parallelizing the computation of sequence representations. The source cites it as a founding member of the family of models that reduce sequential computation by computing hidden representations in parallel, positioning it within the same efficiency lineage as ByteNet and ConvS2S.

- [21] Oleksii Kuchaiev, 2017
  - 标题: Factorization tricks for LSTM networks
  - 关键词: factorization tricks, LSTM efficiency, computational efficiency, sequential computation constraint
  - 总结: The cited factorization tricks for LSTM networks are invoked to acknowledge that recurrent models have already achieved significant computational-efficiency gains through factorization, yet these improvements do not remove the inherent sequential nature of recurrent computation. The source uses the citation to frame the Transformer as addressing a constraint that efficiency tricks alone cannot overcome.

- [22] Zhouhan Lin, 2017
  - 标题: A Structured Self-attentive Sentence Embedding
  - 关键词: self-attention, intra-attention, sentence representation, task-independent embeddings
  - 总结: The cited structured self-attentive sentence embedding work is cited as one of the tasks in which self-attention — relating different positions of a single sequence to compute a representation of that sequence — has already been applied successfully. The source uses it to show that the mechanism the Transformer relies on had prior precedent in representation-learning settings, before being scaled to full sequence transduction.

- [28] Romain Paulus, 2017
  - 标题: A Deep Reinforced Model for Abstractive Summarization
  - 关键词: self-attention, abstractive summarization, sequence model, attention application
  - 总结: The cited deep reinforced summarization model is cited as one of the successful applications of self-attention (intra-attention) across diverse tasks. The source uses the citation to demonstrate that the intra-attention mechanism underpinning the Transformer had already proven effective in conditional generation tasks such as abstractive summarization.

- [32] Noam Shazeer, 2017
  - 标题: Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer
  - 关键词: conditional computation, sparsely-gated mixture-of-experts, model capacity, computational efficiency
  - 总结: The cited sparsely-gated mixture-of-experts layer is used as the exemplar of conditional computation, which alongside factorization tricks is described as having significantly improved computational efficiency in recent work, and additionally improved model performance. The source contrasts such capacity-scaling strategies with its own approach, noting that the fundamental constraint of sequential computation remains even when efficiency is gained this way.

- [34] Sainbayar Sukhbaatar, 2015
  - 标题: End-To-End Memory Networks
  - 关键词: recurrent attention, memory networks, question answering, language modeling, non-sequence-aligned recurrence
  - 总结: The cited end-to-end memory networks are used to show that a recurrent attention mechanism can replace sequence-aligned recurrence, with reported success on simple-language question answering and language modeling. The source uses the citation as evidence that the attention-based, recurrence-free design adopted by the Transformer has structural precedent in earlier architectures.



#### Background

- [5] Kyunghyun Cho, 2014
  - 标题: Learning Phrase Representations using RNN Encoder–Decoder for Statistical Machine Translation
  - 关键词: encoder-decoder, RNN, phrase representations, statistical machine translation, sequence modeling
  - 总结: The cited work introduced an encoder-decoder recurrent network trained to score phrase pairs for statistical machine translation, an early instance of the encoder-decoder template later paired with attention. The source invokes it as part of the established evidence that recurrent, encoder-decoder models were the state of the art for sequence modeling and translation, i.e. as the baseline family whose sequential computation the source set out to remove.

- [19] Yoon Kim, 2017
  - 标题: Structured Attention Networks
  - 关键词: attention mechanism, sequence modeling, transduction, distance-independent dependencies
  - 总结: Structured Attention Networks is cited to show that attention-based modeling of dependencies independent of their distance has become a standard component of strong sequence modeling and transduction systems. The source uses this citation as general background for the benefits of attention, and immediately contrasts it with the common pattern of coupling attention to a recurrent network, a coupling that the Transformer removes.



#### Component

- [7] Junyoung Chung, 2014
  - 标题: Empirical Evaluation of Gated Recurrent Neural Networks on Sequence Modeling
  - 关键词: gated RNN, sequence modeling, recurrent neural network, state of the art, transduction
  - 总结: The cited work provides the empirical evaluation of gated recurrent units on standard sequence modeling tasks, establishing the gated RNN as a state-of-the-art sequence model. The source cites it as one of the two specific architectures (with LSTM) that had become state of the art for sequence modeling and transduction, using it to characterize the dominant recurrent modeling paradigm at the time the source was written.

- [13] S. Hochreiter, 1997
  - 标题: Long Short-Term Memory
  - 关键词: LSTM, recurrent neural network, gating, sequence modeling, state of the art
  - 总结: The cited work introduced the long short-term memory network with input, output and forget gates to mitigate vanishing gradients and preserve long-range information. The source cites it as the exemplar that made recurrent architectures state of the art for sequence modeling and transduction, using it to characterize the dominant baseline and the sequential computation that the source's architecture eliminates.

- [15] R. Józefowicz, 2016
  - 标题: Exploring the Limits of Language Modeling
  - 关键词: language modeling, recurrent network, encoder-decoder, scaling, sequence modeling
  - 总结: The cited work studies large-scale recurrent language modeling and explores the limits of such models on harder sequence modeling tasks. The source cites it as one of the efforts that pushed recurrent language models and encoder-decoder architectures to their boundaries, framing the recurrent paradigm as mature and saturated, and motivating an architecture that avoids recurrent computation entirely.

- [24] Thang Luong, 2015
  - 标题: Effective Approaches to Attention-based Neural Machine Translation
  - 关键词: attention-based NMT, encoder-decoder architecture, recurrent language model, sequence transduction
  - 总结: The cited attention-based NMT work is invoked in the opening discussion of recurrent networks as established state-of-the-art approaches to sequence modeling and transduction, and again among the numerous efforts that continued to push the boundaries of recurrent language models and encoder-decoder architectures. The source uses it as the exemplar of the attention-augmented recurrent encoder-decoder paradigm that the Transformer contrasts with and improves upon.

- [27] Ankur Parikh, 2016
  - 标题: A decomposable attention model
  - 关键词: attention without recurrence, decomposable attention, self-attention application, sequence modeling
  - 总结: The cited decomposable attention model serves a double citation role in the source. First, it is named in the statement that in all but a few cases attention mechanisms are used in conjunction with a recurrent network, making it one of the rare precedents for standalone attention-based sequence modeling that the Transformer generalizes. Second, it appears among the works where self-attention has been used successfully across tasks, evidencing the mechanism's versatility.

- [38] Yong-Hui Wu, 2016
  - 标题: Google's Neural Machine Translation System: Bridging the Gap between Human and Machine Translation
  - 关键词: recurrent neural networks, encoder-decoder, sequence transduction, machine translation, attention, state of the art
  - 总结: The source positions the cited work as a leading instance of the post-LSTM wave of large-scale recurrent encoder-decoder systems. After noting that recurrent networks, LSTMs and gated RNNs had become the state of the art for sequence modeling and transduction, the source invokes this work (with two others) as evidence that recurrent language models and encoder-decoder architectures continued to extend their boundaries, thereby motivating the source's own approach to the same family of problems.



#### Baseline

- [9] Jonas Gehring, 2017
  - 标题: Convolutional Sequence to Sequence Learning
  - 关键词: convolution, sequence-to-sequence, parallel computation, path length, baseline comparison
  - 总结: The cited work applies convolutional networks to sequence-to-sequence learning, computing all input and output positions in parallel instead of step by step. The source uses it both as the exemplar of a parallel, distance-dependent architecture — where relating two positions costs operations proportional to their distance, making distant dependencies harder to learn — and as the main non-recurrent model against which the Transformer's fully self-attention-based design and its claimed advantages are argued.

- [17] Łukasz Kaiser, 2016
  - 标题: Neural GPUs learn algorithms
  - 关键词: Neural GPU, self-attention, transduction model, parallel computation, comparison
  - 总结: The cited work shows that a GPU-style, non-sequential recurrent-free network can learn simple algorithms, positioning it as an alternative way to process sequences without step-by-step recurrence. The source cites it, alongside ByteNet and ConvS2S, as an earlier model whose advantages the Transformer claims to exceed by being the first transduction model to compute its input and output representations purely through self-attention, with no sequence-aligned recurrence or convolution.

- [18] N. Kalchbrenner, 2017
  - 标题: Neural Machine Translation in Linear Time
  - 关键词: convolutional sequence model, parallel computation, sequential computation reduction, machine translation, position-wise representations
  - 总结: The cited linear-time neural machine translation line of work is invoked to establish the convolutional approach to parallel sequence processing: like the Extended Neural GPU, ByteNet and ConvS2S, it trades recurrence for convolutions so all positions can be computed in parallel. The source uses it both as motivating background for reducing sequential computation and as a contrast case, noting that such models need a number of operations that grows linearly with the distance between positions (logarithmically for ByteNet), which makes distant dependencies harder to learn, whereas the Transformer reduces this to a constant number of operations.

- [35] I. Sutskever, 2014
  - 标题: Sequence to Sequence Learning with Neural Networks
  - 关键词: sequence-to-sequence learning, recurrent encoder-decoder, language modeling, machine translation, state-of-the-art RNN
  - 总结: The cited sequence-to-sequence work is invoked in the source's opening framing of recurrent networks, LSTM and gated recurrent units as firmly established state-of-the-art methods for sequence modeling and transduction, including machine translation. It anchors the encoder-decoder paradigm from which the Transformer departs by removing recurrence and convolution entirely.





### 时间线分析

#### 早期
Early citations establish the recurrent foundation the paper departs from: the long short-term memory network (1997) as the architecture that made recurrent sequence models state of the art, and the gradient-flow analysis of recurrent nets (2001) that explains why distant dependencies are hard to learn — the analytical basis for the source's path-length argument.


- [13] S. Hochreiter, 1997: Long Short-Term Memory

- [12] S. Hochreiter, 2001: Gradient Flow in Recurrent Nets: the Difficulty of Learning Long-Term Dependencies

- [2] D. Bahdanau, 2014: Neural Machine Translation by Jointly Learning to Align and Translate

- [5] Kyunghyun Cho, 2014: Learning Phrase Representations using RNN Encoder–Decoder for Statistical Machine Translation

- [7] Junyoung Chung, 2014: Empirical Evaluation of Gated Recurrent Neural Networks on Sequence Modeling

- [35] I. Sutskever, 2014: Sequence to Sequence Learning with Neural Networks

- [24] Thang Luong, 2015: Effective Approaches to Attention-based Neural Machine Translation




#### 中期
Middle-period citations consolidate the attention-augmented recurrent encoder-decoder paradigm that dominated the field just before the source: encoder-decoder RNNs for phrase-based and neural machine translation, attention-based NMT, gated recurrent networks, sequence-to-sequence learning, and end-to-end memory networks that already replaced sequence-aligned recurrence with recurrent attention.


- [34] Sainbayar Sukhbaatar, 2015: End-To-End Memory Networks

- [4] Jian-Peng Cheng, 2016: Long Short-Term Memory-Networks for Machine Reading

- [15] R. Józefowicz, 2016: Exploring the Limits of Language Modeling

- [16] Lukasz Kaiser, 2016: Can Active Memory Replace Attention?

- [17] Łukasz Kaiser, 2016: Neural GPUs learn algorithms

- [27] Ankur Parikh, 2016: A decomposable attention model

- [38] Yong-Hui Wu, 2016: Google's Neural Machine Translation System: Bridging the Gap between Human and Machine Translation




#### 近期
Recent citations mark the immediate competitive frontier: convolutional and linear-time sequence models that parallelize computation but pay a distance-dependent path length, plus self-attention applications in reading comprehension, summarization, entailment and sentence representation, and efficiency work on factorization tricks and conditional computation that improved speed without removing the sequential constraint.


- [9] Jonas Gehring, 2017: Convolutional Sequence to Sequence Learning

- [18] N. Kalchbrenner, 2017: Neural Machine Translation in Linear Time

- [19] Yoon Kim, 2017: Structured Attention Networks

- [21] Oleksii Kuchaiev, 2017: Factorization tricks for LSTM networks

- [22] Zhouhan Lin, 2017: A Structured Self-attentive Sentence Embedding

- [28] Romain Paulus, 2017: A Deep Reinforced Model for Abstractive Summarization

- [32] Noam Shazeer, 2017: Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer





