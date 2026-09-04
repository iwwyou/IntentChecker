# RQ1/RQ2/RQ3 데이터 파이프라인 체크리스트

작성 배경: 이번 세션에서 엔진(interval-domain 분석기)과 일부 케이스 JSON annotation을 여러 건 수정했음
(`First Revision/engine_run_triage.md` / `engine_code_changes.md` 참고). 그 결과 `evaluation/RQ1/`,
`evaluation/RQ2/`, `evaluation/RQ3/`에 이미 있는 CSV/analysis.md 수치 중 일부는 더 이상 현재 코드베이스
상태를 반영하지 못할 수 있음. 또한 RQ1 자체가 "몇 개 탐지했는가"가 아니라 **Expressibility(RQ1-A) →
Validation(RQ1-B) → Amenability(RQ1-C)** 3단 논리로 재구성됨. 아래 체크리스트는 이 두 가지를 모두
반영한 것.

## 실행 상태 (2026-09-04 기준)

- [x] §2-A phase_reviews 34 eligible 추출 (25 expressible + 9 inexpressible) — 서브에이전트 4개 병렬,
  완료. `evaluation/RQ2/extracted/*.json`.
  - 추출 중 발견/수정: `web3bugs_16_H_04`는 원래 "9개 미해결" 목록에 잘못 들어가 있었음 — 실제로는
    Expressible=Yes이나 case JSON이 아직 빌드된 적 없음(`case_built=No`로 별도 표시). RQ2-A 구조
    통계(46-case set)에는 포함, RQ1-B/latency(45-case set)에서는 제외하도록 처리.
  - `web3bugs_44_H_02`는 정상적으로 finding-level Expressible=No(Member A만 Yes, Member B
    alpha_and_beta로 No — completeness rule)로 이미 잘 분류돼 있었음, 재확인만 하고 그대로 둠.
- [x] §2-B old-L4 track 20개 추출/재확인 — 서브에이전트 2개 병렬, 완료.
- [x] §3 RQ3 case_mapping.csv — 이미 75행 전부 존재하던 걸 확인(제가 원래 20행만 있다고 착각했었음),
  신규 25개 `status`만 `not_detectable → annotated`로 수정 완료. 로컬에서 도구 3종 실행 준비 끝남.
- [x] §2-C Excel 골격 스크립트(`evaluation/RQ2/build_excel.py`) 작성 및 74개 전체로 검증 완료.
- [~] §2-E RQ1-B validation_outcome + RQ2-B latency (`evaluation/RQ2/collect_rq2b.py`) — **1차 실행은
  추출 서브에이전트들과 병렬로 돌아가서 앞부분(특히 baseline 다수)이 CPU 경합으로 오염 의심** →
  백업(`rq2b_latency.csv.contaminated_backup` 등) 후 **아무 병렬 작업 없이 2차(클린) 재실행 중**.
- [ ] 클린 latency 재실행 완료 → `build_excel.py` 최종 재실행 → 결과 검토/보고

순서/방법론은 이 문서 §0~§4 그대로 확정된 상태로 진행 중.

---

## 0. 공통 전제

### 0.1 전체 케이스 구성 (74개 = 20 + 34 + 20, +1 excluded, 직접 대조로 확정)

- 20개 **baseline** — 이미 `Violated`. (`evaluation/RQ1/rq1_results.csv`)
- **35개 phase_reviews 디렉토리 중 34개가 eligible, 1개는 제외.**
  - **제외 1개**: `web3bugs_101_H_02` (`33_web3bugs_101_H_02/analysis.md`). Final disposition:
    "Excluded — source already fixed (`excluded_fixed_code`)". 리비전 중 duplicate 이슈(`#55`)를
    추가로 대조한 결과, 이 벤치마크 소스(`target_contracts_original/web3bugs_101_H_02.sol` L389)가
    이미 리포트가 지적한 수정(`_notBorrowedInShares` 기반 계산)을 반영하고 있음을 확인 — 즉 이
    소스에는 해당 버그가 없음. **어느 그룹에도 속하지 않음 — Expressibility 판정도, RQ2-A도,
    Value/Algorithm·Usable/Unusable 분류도 대상이 아니고, 원래의 14개 excluded 케이스와 같은
    지위로 별도 트래킹만.** 이 하나 때문에 eligible denominator가 75→74, 구 L5 pool이 14→13으로
    줄어듦(analysis.md 자신이 명시).
  - **34개 eligible**, 그중:
    - **25개**: Expressible=Yes, `evaluation/RQ1/cases/`에 case JSON 빌드됨("phase_reviews 유래
      25개"). RQ1-A+RQ1-B+RQ2-A+RQ2-B 전체 대상.
    - **9개**: Expressible=No 또는 미해결 — `web3bugs_16_H_04`, `71_H_11`, `34_H_01`, `70_H_03`,
      `45_H_02`, `5_H_15`, `8_H_03`, `44_H_02`, `70_H_09`(101_H_02 제외 후 9개로 확정). RQ1-A
      (Expressible=No + blocker 태그) + §5(Value/Algorithm, Usable/Unusable) 대상, RQ2-A/RQ2-B는
      대상 아님.
- 20개 **old-L4 track** — phase_reviews와 전혀 안 겹침(직접 대조 확인). 논문 `main.tex`
  1397–1488행(구 RQ2 섹션)의 원출처. `l4_l5_classification.csv`(34행 = L4 20 + L5 14, 이 중 L5
  14행은 phase_reviews로 대체되고 101_H_02 제외분 1개도 포함되어 있어 실질적으로 L5 13행만 유효) +
  `l4_l5_case_review_(kor).md`가 소스. **old-L4 track으로는 L4 20행만 사용** (L5 14행은 안 씀 —
  phase_reviews가 대체).
- **검증**: 20(baseline) + 34(phase_reviews eligible: 25+9) + 20(old-L4) = **74**. phase_reviews
  디렉토리 자체는 35개(34 eligible + 1 excluded)로 물리적으로 그대로 있음.

### 0.2 자료 출처 정책 (3-way, 그룹별로 다름)

**baseline 20 (참고 허용, 배경정보로만)**: `rq1_results.csv`, `dataset.csv`,
`annotation_plans.md`/`(kor).md`. 이 문서들엔 Value/Algorithm·Usable/Unusable·relation form 분류가
없음(직접 확인) → 전부 새로 판정.

**phase_reviews 34 eligible (25 + 9) — 아래 자료 참조 절대 금지**: `rq1_results.csv`, `dataset.csv`,
`annotation_plans.md`/`(kor).md`, `l4_l5_classification.csv`/`.py`,
`l4_l5_case_review.md`/`(kor).md`. **오직 `First Revision/phase_reviews/` 디렉토리만 사용**
(README.md + 각 `analysis.md` + 그 안에서 인용하는 1차 소스: Web3Bugs 리포트 원본,
`target_contracts_original/*.sol`, 현재 case JSON).

**old-L4 track 20 (예외 — 여기서만 위 forbidden 문서가 정당한 소스)**: `l4_l5_classification.csv`의
`bug_category`(value/algorithm)+`proxy_type`(A=Usable/B=Unusable)+`final_class`+
`l4_l5_case_review_(kor).md`. README §1 triage 규칙 적용(재확인만, 전면 재작성 아님) — 상세는 §2-B.

**제외 1개(`web3bugs_101_H_02`)**: 어떤 분류 정책도 적용 안 함 — "excluded, reason=excluded_fixed_code"
로만 기록.

### 0.3 향후 검토 사항 (미확정, 지금 실행 안 함)

사용자가 "annotation_plans.md / phase_reviews / l4_l5_classification 원본을 추출 후 별도 보관하고
Excel + case JSON만 남길지"를 고민 중 — 아직 미결정, 지금 단계에서 어떤 문서도 이동/삭제 안 함.

### 0.4 case JSON 기준 전수 재검증 + 레거시 파일 배제

- [ ] baseline 20 + phase_reviews-expressible 25 = 45개는 모든 구조/카운트 지표를 현재 case JSON +
  현재 엔진 기준으로 재산출.
- [ ] 이번 세션에 case JSON을 직접 수정한 9개(특히 주의): baseline `45_H_01`/`47_H_02`/`62_H_08`/
  `70_H_10`, phase_reviews `70_H_04`/`70_H_05`/`3_H_04`/`5_H_12`/`62_H_03`.
- [ ] `evaluation/RQ1/cases/` 레거시 루트 중복 JSON 배제, 서브폴더 canonical 경로만 참조.
- [ ] 케이스 경로 목록은 디렉토리 스캔으로.

### 0.5 Annotation 텍스트 출처 정책 (case JSON 우선, 전 케이스 적용)

- [ ] **case JSON이 존재하는 45개(baseline 20 + phase_reviews_expressible 25) 전부**: 실제
  `@During`/`@Post` annotation 텍스트, `relation_form`, `during_or_post`는 **반드시 현재
  `evaluation/RQ1/cases/<case>/<case>.json`에서 직접 읽어서 판정** — `analysis.md`나
  `annotation_plans.md`의 R1-6 prose를 그대로 옮기지 않음(작성 시점 이후 annotation이 바뀐 케이스가
  이미 5개 확인됨, §0.4 — 이 규칙을 9개가 아니라 45개 전체에 일반화).
  `analysis.md`/`annotation_plans.md`는 R1-1 배경 서술, Value/Algorithm·Usable 판단 근거,
  RQ2-A statement/value backward-slice 설명(이건 코드만 봐서 재구성하기보다 서술을 참고하는 게
  안전)에만 사용.
- [ ] case JSON이 없는 29개(phase_reviews-inexpressible 9 + old-L4 20)는 애초에 실행되는 annotation
  자체가 없으므로 이 규칙 대상 아님 — 기존 정책(§0.2)대로 analysis.md/l4_l5_classification.csv가
  유일한 소스.

---

## 1. RQ1 — Expressibility(RQ1-A) + Validation(RQ1-B) + Amenability(RQ1-C)

새 RQ1 프레이밍: "몇 개 탐지했는가"가 아니라 "reported numeric intent가 (1) 표현 가능한가, (2) 실제
분석기로 검증 가능한가"를 단계적으로 보임. 좋은 소식은 지금까지 설계한 §2(RQ2-A/§5) 파이프라인이 이
데이터의 상당 부분을 이미 커버한다는 것 — 다만 몇 개 필드는 명시적으로 추가해야 함.

### 1-A. RQ1-A(Expressibility)용 — 기존 계획에 이미 있는 것

- Expressible Yes/No — §2-A(phase_reviews)/§2-B(old-L4)/§2-D(baseline)에서 이미 수집 예정
- Value/Algorithm, Usable/Unusable — 동일
- Inexpressible blocker 태그(alpha/beta/gamma/delta) — §2-A(phase_reviews 9개)/§2-B(old-L4 20개)에서
  이미 수집 대상으로 잡혀 있었음 → **명시적 Excel 컬럼으로 승격 필요** (아래 1-C)

### 1-B. RQ1-A용 — 새로 추가해야 하는 것

- [ ] **`relation_form` 컬럼** (R1-5 bookkeeping: exact_equality / inequality_bound / entry_exit /
  before_after / changed_unchanged / return_value / call_argument / implication / feasibility) —
  각 analysis.md의 R1-5 섹션에 이미 서술돼 있지만 지금까지 Excel 컬럼으로 계획하지 않았음. 25개
  expressible + baseline 20 전부에 대해 추가.
- [ ] **`during_or_post` 컬럼** (attachment scope, R1-4) — 마찬가지로 이미 analysis.md에 있으나 컬럼
  누락 상태였음.
- [ ] **`finding_level_note`** — multi-annotation-set 케이스(예: `70_H_04`, `29_H_11`, `44_H_02`)는
  각 member가 어떤 reported mechanism을 커버하는지 1줄로 기록 (README §10 요구사항).
- [ ] Excluded 케이스(`101_H_02`) 처리 — Excel에 별도 status 행(`excluded`)으로만 기록, 위 컬럼들
  전부 N/A.

### 1-C. RQ1-B(Validation)용 — 신규 섹션, 데이터 요구사항 재정의

기존 계획의 `rq1_verdict`(Violated/Warning/Unsupported) 필드로는 부족함 — RQ1-B가 요구하는 결과
taxonomy를 명시적으로 갖춰야 함.

- [ ] **`validation_outcome` 컬럼**을 다음 값으로 표준화: `Violated` / `Warning` / `Unsupported` /
  `Satisfied`. baseline 20 + phase_reviews-expressible 25 (총 45개) 대상 — RQ1-B는 "Expressible로
  판정된 case만" 대상이므로 이 45개와 정확히 일치(=§2-E RQ2-B latency 대상 집합과도 동일).
- [ ] **`validation_note` 컬럼** (질적 서술, Warning/Unsupported/Satisfied에서 특히 중요):
  - Warning: interval precision loss(widening/fixpoint) / external·opaque value(TOP 전파) /
    loop-body observation 한계 / 기타 engine-specific 원인 중 어디에 해당하는지
  - Unsupported: 어떤 observation point/engine 한계 때문인지 (예: delta 케이스라면 loop-body @During
    이 애초에 평가 안 됨). **확인된 실사례**: `numscout_EthereumGod` Member B(`newBalance`)가
    `Unsupported`(unmodeled external-call state transition) — `swapTokensForEth()`의 external
    router call이 일으키는 `address(this).balance` 변화를 analyzer가 모델링 안 해서 `fromSwap`이
    항상 0으로 강제되고, 그 결과 관계식이 vacuous하게 평가됨. R1-7의 세 조건(값 참조 가능/relation
    표현 가능/observation point 지원) 중 어느 것도 실패하지 않으므로 Expressible=Yes는 유지, 이건
    순수하게 RQ1-B 실패임 — 상세 도출은 `29_numscout_EthereumGod/analysis.md`의 "Resolved issue"
    섹션. **이 사례로 "Satisfied/Unsupported는 안 나와야 한다"는 이전 가정이 정정됨**: Unsupported는
    R1-7이 커버 안 하는 "discriminating scenario 구성 가능성" 문제에서 legitimate하게 발생 가능.
  - Satisfied(있다면): scenario가 defect를 노출 못 시킨 것인지 / relation이 non-discriminating이었는지
    / precision 문제인지 구분해서 기록. **주의**: 엔진이 raw로 `[INTENT SUCCESS]`를 출력해도 그게
    반드시 진짜 Satisfied라는 뜻은 아님 — `numscout_EthereumGod` Member B처럼 vacuous(구성 불가능한
    시나리오)로 인한 위양성일 수 있으므로, raw 출력을 그대로 옮기지 말고 케이스별 R1-6 시나리오가
    실제로 구성 가능했는지 먼저 확인 후 validation_outcome을 정함(raw `SUCCESS` → 실제로는
    `Unsupported`로 정정한 사례가 이미 하나 있음).
- [ ] **multi-annotation-set 케이스의 per-member outcome**: 케이스 레벨 하나의 verdict로 뭉개지 말고,
  member별 validation_outcome을 별도로 기록(README §10 "judge each member independently and report
  per-member"). Excel에서는 `raw_profile`의 case당-1행 구조에 `member_outcomes`라는 자유 텍스트
  컬럼(예: "A: Violated; B: Warning")으로 처리하거나, 필요시 member당 별도 행으로 분리 — 실제 개수
  보고 결정.
- [ ] 이 컬럼들은 이미 §2-E(RQ2-B latency)에서 case를 실제로 재실행하는 pass와 자연히 겹침 — latency
  10-run 실행 결과에서 verdict/risk 값도 같이 기록되므로 별도 실행 없이 동일 pass에서 채울 수 있음.

### 1-D. RQ1-C(Amenability)용 — 분석 축 정리 (신규 데이터 수집은 없음, 기존 필드의 cross-tab만)

RQ1-C는 새 데이터가 필요한 게 아니라 1-A/1-B/§2(RQ2-A)에서 이미 모은 필드들의 교차분석임 —
`aggregates`/`by_outcome` 시트 설계에 반영:

- [ ] `value_or_algorithm` × `validation_outcome` 교차표
- [ ] `relation_form` × `validation_outcome` 교차표
- [ ] `context_breadth`(RQ2-A) × `validation_outcome` 교차표
- [ ] blocker 태그(alpha/beta/gamma/delta) 분포 — Inexpressible 34개 전체(phase_reviews 9 +
  old-L4 20) 대상
- [ ] annotation_multiplicity(single/multi) × validation_outcome
- [ ] 대표 예시 후보 선정(논문 서술용, 데이터 확정 후 수작업): simple equality/bound 케이스,
  multi-annotation 케이스, alpha/delta 대표 blocker 케이스, 대표 Warning/Unsupported 실패 사례
  1~2개씩

### 1-E. RQ1 구조 지표(참고 데이터, baseline 20 한정 — 기존 §1 내용)

- [ ] `collect_metrics.py`를 §2-F RQ2-B 스크립트로 흡수/확장해 재산출.
- [ ] 재산출 후 `rq1_results.csv`(VIOLATED 여부) 20/20 유지 재확인.
- 이 구조 지표(lines/calls/branches/debug 개수)는 RQ1-A/B/C 서술의 핵심이 아니라 부가 정보 —
  1-A~1-D가 실제 RQ1 논리의 본체.

---

## 2. RQ2 — Specification Profile(RQ2-A) + Value/Algorithm·Usable/Unusable + Latency(RQ2-B)

### 순서 (확정)
1. phase_reviews 34 eligible(25 + 9) 추출 — phase_reviews 디렉토리만 사용, `101_H_02`는 별도 excluded
   행으로만 기록
2. old-L4 track 20개 추출/재확인 — l4_l5_classification.csv + case_review만 사용
3. Excel 골격(4-group + excluded 1행) 확정
4. baseline 20개 경량 RQ2-A + §1-B/§1-C용 필드 채우기
5. (병행 가능) RQ2-B latency + RQ1-B validation_outcome 동시 재측정 — 45개, 10-run

### 2-A. phase_reviews 34 eligible 추출

**25개 (Expressible=Yes, RQ1-A+RQ1-B+RQ2-A 전체 대상)**
- [ ] `## RQ2-A — Specification Requirements profile` + 직전 `## §5 — Value/Algorithm and
  Usable/Unusable` + R1-4(during/post)/R1-5(relation form) 섹션 추출.
- [ ] 각 케이스의 `## Summary` 블록을 최종 확정치의 1차 소스로 사용(Review Notes/Second Review Pass로
  사후 수정된 케이스 있음 — `62_H_03` 확인됨, 35개 전체 grep으로 재확인).
- [ ] 5개(`70_H_04`/`70_H_05`/`3_H_04`/`5_H_12`/`62_H_03`)는 현재 case JSON과 문자열 대조.
- [ ] 추출 필드: 기존(relevant_statements, unique_values, additional_functions_n,
  additional_contracts_n, context_breadth, external_spec, value_or_algorithm, usable,
  annotation_multiplicity, case_notes) + 신규(relation_form, during_or_post, finding_level_note,
  blocker_tags — 해당 없으면 공란)

**9개 (Expressible=No/미해결, RQ1-A §5+blocker만 대상)**
- [ ] `web3bugs_16_H_04`, `71_H_11`, `34_H_01`, `70_H_03`, `45_H_02`, `5_H_15`, `8_H_03`, `44_H_02`,
  `70_H_09`의 각 analysis.md에서 §5 + Expressible verdict + alpha/beta/gamma/delta 태그 추출.
  RQ2-A/RQ1-B 필드는 전부 N/A.
- [ ] `45_H_02`/`71_H_11`은 README §0에 "disputed" 이력 — 최종 verdict 확정 상태인지 재확인 후 추출.

**excluded 1개**
- [ ] `web3bugs_101_H_02` — Excel에 status=`excluded`, reason=`excluded_fixed_code`, 근거는
  `33_web3bugs_101_H_02/analysis.md`의 "Final disposition" 섹션 그대로 인용. 다른 컬럼 전부 N/A.

### 2-B. old-L4 track 20개 추출/재확인

- [ ] `l4_l5_classification.csv`에서 `final_class`가 L4로 시작하는 20행만 추출: `bug_category`,
  `proxy_type`, `final_class`, `reclass_reason`, `notes`.
- [ ] README §1 triage 규칙 적용: `proxy_type=B`+`reclass_reason` 없음 ~9개 carry-forward,
  `l4a_axis=alpha` 케이스 rescue 재확인, `reclass_reason` 있는 ~10개 alpha/beta/gamma/delta 어휘로
  재표현(verification pass), `35_H_10`/`36_H_02`(proxy_type=A) carry-forward.
- [ ] `l4_l5_case_review_(kor).md` 대조.
- [ ] Excel 컬럼: `value_or_algorithm`(←bug_category), `usable`(←proxy_type A/B),
  `blocker_tags`(←재표현 결과), `final_class`, `triage_status`(carry_forward/rechecked/
  re_expressed). RQ2-A/RQ1-B 필드는 N/A(대부분 Inexpressible).

### 2-C. Excel 골격 (4-group + excluded 1행)

- [ ] 파일: `evaluation/RQ2/rq2a_specification_profile.xlsx`
- [ ] 시트 `raw_profile` — `group`: `baseline20` / `phase_reviews_expressible25` /
  `phase_reviews_inexpressible9` / `old_l4_track20` / `excluded1`. 공통 컬럼: `case_id, source,
  expressible, value_or_algorithm, usable, blocker_tags, relation_form, during_or_post,
  finding_level_note, validation_outcome, validation_note, case_notes, source_file`. RQ2-A 전용
  컬럼은 `phase_reviews_expressible25`+`baseline20`만, `validation_outcome`/`validation_note`도
  이 45개만(=RQ1-B 대상과 동일).
- [ ] 시트 `aggregates` — RQ2-A 수치(45개 한정) + RQ1-C 교차표(§1-D: value/algorithm×outcome,
  relation_form×outcome, breadth×outcome, blocker 분포, multiplicity×outcome).
- [ ] 시트 `by_outcome` — Violated vs Warning/Unsupported/Satisfied 비교(45개, RQ1-B/RQ2-A 공통).
- [ ] 시트 `value_usable_matrix` — **74개 eligible 전체**(excluded 1개 제외) 대상 Value/Algorithm ×
  Usable/Unusable 2×2(구 논문 Table 1470–1483행의 74-케이스 확장판) + 그룹별 분해.

### 2-D. baseline 20개 경량 채우기

- [ ] 기존 annotation(case JSON)을 given으로, README §6 Step 1→Step 2 순서로 RQ2-A 적용.
- [ ] relation_form/during_or_post도 함께 판정(annotation 문법에서 직접 읽어낼 수 있음).
- [ ] `annotation_plans.md`/`dataset.csv`/`rq1_results.csv`는 배경정보로만, 분류 근거로 인용 금지.
- [ ] R1-1 서술/§7 표/negation check 생략.
- [ ] Value/Algorithm, Usable/Unusable, annotation_multiplicity, relation_form까지 20개 전부.
- [ ] 최소 1회 self-check.

### 2-E. RQ1-B validation_outcome + RQ2-B Latency (같은 재실행 pass)

- [ ] 케이스: baseline 20 + phase_reviews_expressible25 = 45개(§0.4 디렉토리 스캔).
- [ ] 스크립트 확장 — 케이스당 10회 실행, `run_1..run_10, mean, median, std, q1, q3, iqr, min, max` +
  **`validation_outcome`(Violated/Warning/Unsupported/Satisfied) + risk 값도 같은 실행에서 기록**
  (§1-C 요구사항).
- [ ] multi-annotation-set 케이스는 member별 outcome 별도 기록(§1-C).
- [ ] cumulative median stability(1/3/6/10회) 별도 컬럼/시트.
- [ ] case-median들의 median/IQR + all-runs pooled median/IQR 둘 다 보존, mean/SD는 보조.
- [ ] 엔진 수정 마무리 후 baseline 20 포함 전량 재측정.

---

## 3. RQ3 — 다른 도구 비교, 25개 신규 케이스로 확장

(실행은 사용자가 로컬에서 직접 함 — 아래는 준비/방법론 체크리스트만)

- [ ] `evaluation/RQ3/case_mapping.csv`에 phase_reviews_expressible25 행 추가(기존 20개와 동일
  스키마). `target_sol_file`/`project_root`/`solc_version`은 `target_contracts_original/` 또는 각
  analysis.md Case metadata에서만.
- [ ] `rq3_comparison_table.csv` 스키마 유지, 3-run 컨벤션 유지.
- [ ] 이번 세션 수정 5개는 IC 쪽 결과 기존 실행분 있어도 무효 — 현재 case JSON 기준 재실행.
- [ ] 실행 순서: (1) case_mapping.csv 25행 추가 → (2) 도구 3종 3회씩 실행 → (3) 비교 테이블 재생성.
- [ ] old-L4 track 20개 + excluded 1개는 IntentChecker annotation이 없거나 대상 자체가 아니므로 RQ3
  비교 대상에서 제외.

---

## 4. 전체 작업 순서 요약

1. §0 공통 전제 확인 (74개 구성 확정, excluded 1개 별도 트래킹, 3-way 자료 출처 정책, 레거시 JSON 배제)
2. §2-A phase_reviews 34 eligible 추출(25 RQ1-A+B+RQ2-A full + 9 §5/blocker-only) + excluded 1개
   기록 — phase_reviews 디렉토리만 사용
3. §2-B old-L4 track 20개 추출/재확인 — l4_l5_classification.csv + case_review만 사용
4. §2-C Excel 골격 확정(4-group + excluded)
5. §2-D baseline 20개 경량 채우기(RQ2-A + relation_form/during_or_post 포함)
6. §1-E + §2-E: RQ1 구조 지표 + RQ1-B validation_outcome + RQ2-B latency 45개 동시 재산출
7. §3 RQ3: case_mapping.csv 25행 추가(내가 준비 가능) → 사용자가 로컬에서 도구 3종 3회 실행 →
   비교 테이블 재생성

## 5. 최종 검토 메모

- **정정 이력**: (a) 이전 버전에서 "evaluation/ 전체에 Value/Algorithm·Usable/Unusable 분류가 없다"고
  잘못 판단 — 실제로는 구 L4(20)+L5(14)가 `l4_l5_classification.csv`의 `bug_category`/`proxy_type`
  컬럼으로 존재, `main.tex` 1470–1483행 구 Table의 원출처. (b) 75→**74**로 정정 — phase_reviews
  리비전 중 `web3bugs_101_H_02`가 duplicate 이슈 대조로 "이미 패치된 소스"임이 밝혀져 eligible pool
  에서 제외됨(analysis.md 자신이 74/13 산술을 명시).
- **RQ1 재구성 반영**: RQ1이 "탐지 개수"가 아니라 Expressibility(RQ1-A)→Validation(RQ1-B)→
  Amenability(RQ1-C) 3단 논리로 바뀜에 따라, 기존 §2(RQ2-A) 파이프라인이 RQ1-A 데이터의 상당 부분을
  이미 커버하고 있었음을 확인 — 신규로 추가한 것은 `relation_form`/`during_or_post`/
  `finding_level_note`/`blocker_tags` 명시적 컬럼화, `validation_outcome`+`validation_note`의
  표준 taxonomy(Violated/Warning/Unsupported/Satisfied), multi-annotation-set의 member별 outcome
  기록. RQ1-C는 신규 데이터가 아니라 기존 필드들의 cross-tab(aggregates 시트로 흡수).
- 75개 전체 구성(현 74) 검증: phase_reviews 디렉토리 35개(34 eligible+1 excluded),
  `l4_l5_classification.csv` 34행(L4 20+L5 14, L5 중 1개가 phase_reviews 쪽 excluded와 동일 케이스),
  expressible-25 목록을 교차 검증해 정확히 들어맞음.
- Value/Algorithm × Usable/Unusable 2×2는 74개 eligible 전체에서 집계(excluded 1개만 제외).
  RQ2-A/RQ1-B는 45개(baseline20+phase_reviews_expressible25) 한정.
- 작업량이 가장 큰 지점은 여전히 §2-A(34건, 특히 25건은 RQ1-A+B+RQ2-A 풀로) + §2-D(baseline 20건
  경량) — §2-B(old-L4 20건)는 재확인 위주라 상대적으로 가벼움. 원본 문서 별도 보관 여부는 §0.3 참고,
  미확정.
