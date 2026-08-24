Reviewer 3

IntentChecker is a development-time debugging tool for Solidity that explicitly expresses numeric intent via annotations. The proposal draws on interval-based abstract interpretation and classifies declared intent as Satisfied, Warning, or Violated, along with a risk score and violated regions.

Overall, I find the approach interesting and potentially useful, especially the transition from pre-defined patterns of vulnerability detection to the specification of developer intent. In addition, I like the paper's structure and the fact that the authors do not try to position their tool as a substitute for other techniques for detecting numeric logic errors. Nevertheless, I consider the empirical evidence provided in the paper insufficient to support certain claims. I thus recommend a major revision, with particular emphasis on improving the empirical approach.

Strengths
– Interesting approach
– Value-level and algorithm-level classification is useful.
– Formalization of annotations is clear and properly done.

Weaknesses
– The empirical basis of the study is insufficient for some of its conclusions.
– Performance experiments use only three executions per case.
– Correlation analysis is conducted on only 20 cases and cannot provide sufficient evidence to support the statistical assumptions underlying Pearson correlation.
– Comparison with other tools is somewhat imbalanced due to differences in their assumptions.
– Practical usability and annotation effort remain unevaluated.


My principal concern is the empirical evaluation part. The benchmark contains 89 effective cases and includes 75 cases in the end, but only 20 out of those produce the Violated judgment. On the one hand, I appreciate that the authors analyze the remaining 55 cases rather than hide them. However, it means that only 27% of the effective benchmark directly demonstrates the approach's mitigation capability. I would therefore encourage the authors to be more cautious in the claims on practicality and effectiveness.

As far as I understand, a related issue is that the annotations in the evaluation are constructed by the researchers based on their knowledge of the bugs and the corresponding buggy lines. This brings a significant retrospective advantage. The evaluation shows that the proposed tool can reveal a known bug if it is provided with the correct specification of the intent based on the knowledge of the bug. However, it still does not show that the developers can create such annotations based on their initial understanding of the code before knowing about the bug. The authors recognize this potential problem, but I consider it as an important aspect that requires a more thorough investigation. An independent annotation experiment, a few annotators, or at least an inter-rater examination, whether the developers are able to create comparable annotations without knowing the reported bug, would strengthen the paper a lot.

In the same vein, the authors conduct the experiments with only three executions per case. However, the performance results of individual executions demonstrate considerable variability. For example, there are cases with relatively wide ranges. Three repetitions are not enough to provide a reliable estimate of the runtime variance. I suggest performing much more runs for each test case and reporting median, dispersion, and ideally, confidence intervals instead of means. To operationalize my suggestion, I would recommend the authors to run power analysis to determine the correct ammount of runs to get statistical significance.

Furthermore, regarding statistics, I have similar concerns about the Pearson correlation analysis. The authors use n=20 cases in this analysis and observe relatively high correlations between runtime and several complexity metrics. However, I could not find any evidence that the assumptions behind Pearson correlation were verified. Given the small sample size, obvious outliers, a skewed distribution of runtimes, and count-based independent variables, Pearson correlation may not be the most appropriate choice. I suggest the authors to inspect the distributions and influential observations and justify the chosen statistical method. It is a very wide and common mistake in our community to oversee data distribution analysis (normality testing) and choose the wrong statistical test (parametric vs non-parametric, in this case Pearson vs Spearman). Statements such as "the analysis time scales approximately linearly" seem too strong based on only 20 observations.

Finally, regarding RQ3, IntentChecker receives developer-authored and specific to each case specifications, whereas several other approaches rely on fixed criteria for the detection of the bugs. Thus, the comparison is useful for the characterization of the approaches but not very convincing for the empirical comparison of their capabilities. Specifically, evaluating the other tools only on the 20 cases already known to be mitigated by the IntentChecker introduces selection bias. I suggest either expanding the comparison to the whole benchmark or reframing RQ3 as a design space comparison. Otherwise, there is the serious risk of “comparing apples and pears”.

On the topic of threats to validity, as a rule of thumb, if the authors employ a statistical test, they should discuss threats to the validity of the conclusion. Currently those are missing.

Although the paper’s notational semantics are well developed, I am not entirely persuaded by some of the assumptions underlying the auxiliary quantitative results. Specifically, the risk assessment function relies on an assumption of uniform distribution of the intervals and severity bands that are manually assigned. The justification for this is not yet apparent either theoretically or empirically.

In addition, the comparison semantics operates over interval conjunctions without maintaining any dependencies between variables. It would be helpful to identify which properties of Satisfied/Violated judgments could be guaranteed under such an abstraction, explain how this loss of dependencies influences Warning judgments, and separate mathematically proven facts from heuristics such as the risk score.

Finally, the paper focuses on IntentChecker as a development-time tool, yet the evaluation reproduces development activity via scripted incremental edits rather than observing actual developers using the tool. I understand that a full-fledged developer study could be future work, but some empirical evidence on the annotation effort would greatly support the paper's main message. Basic measurements such as the size of the annotations, the number of annotations per function, authoring time, or the impact of input range specification on the results will help to demonstrate the practical cost of the reported gains.

All in all, I find value in the technical approach and believe this paper can make a valuable contribution to the field. My recommendation for the major revision is mainly based on the gap between a promising technical approach and an empirical evaluation providing less evidence than some of the paper's conclusions. Improvements to the experimental and statistical methods, annotation validity testing, and comparison framing will greatly strengthen the paper.