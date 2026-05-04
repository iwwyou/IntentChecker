# Cover Letter

Dear Editor-in-Chief,

I am writing to submit our manuscript entitled "IntentChecker: An Intent-Model-Based Debugging Assistant for Mitigating Numeric Logic Errors in Solidity" for consideration for publication in Automated Software Engineering.

Smart contracts written in Solidity mediate billions of dollars of on-chain value, yet numeric logic errors---where program behavior diverges from the developer's intended numeric relationships without raising any compile-time or runtime exception---remain particularly hard to address. Existing detectors take completed source code as their only input and check it against a fixed catalog of vulnerability patterns chosen by their designers, leaving errors outside these patterns with no practical path to early prevention.

This research addresses this gap by introducing IntentChecker, a development-time value-level intent validation tool for Solidity. Its core contribution is an intent model with @During/@Post annotations and a validation engine grounded in a formal denotational semantics, which classifies each annotation as Satisfied, Warning, or Violated against intervals produced by abstract interpretation and reports a risk score together with the violated sub-intervals. On real-world numeric logic error benchmarks, IntentChecker surfaces 20 cases as Violated judgments at a mean 3.69 s per case, and a comparison with state-of-the-art auditing-time detectors substantiates its complementary role as a development-time debugging assistant.

This work is highly appropriate for Automated Software Engineering as it: (1) proposes a new debugging methodology for smart contracts that replaces pattern-catalog matching at audit time with developer-declared intent-driven validation during editing, and (2) realizes this methodology as an automated validation technique: given developer-supplied @During/@Post annotations as input, the validation engine automatically produces a tri-valued judgment (Satisfied / Warning / Violated) grounded in a formal denotational semantics over abstract-interpretation states.

This work has not been published elsewhere nor is it under consideration by another journal. We have no conflicts of interest to declare.

Thank you for considering our manuscript. We look forward to your response.

Sincerely,

Inseong Jeon
Sundeuk Kim
Hyunwoo Kim
Hoh Peter In (Corresponding Author, hoh_in@korea.ac.kr)

Department of Computer Science
Korea University, Seoul, Republic of Korea
