# SoK: Decentralized Finance (DeFi) Attacks - Reference Summary

이 문서는 "SoK: Decentralized Finance (DeFi) Attacks" 논문에서 언급된 취약점/에러 유형별 참조 논문을 정리한 것입니다.

---

## Absence of coding logic or sanity check
참조 번호: 10, 13, 72, 77, 78, 82, 84, 86, 121

| # | 논문 제목 | 저자/출처 | 연도 |
|---|---------|----------|------|
| 10 | Security analysis methods on ethereum smart contract vulnerabilities: a survey | Praitheeshan et al. | 2019 |
| 13 | A survey on ethereum systems security: Vulnerabilities, attacks, and defenses | Chen et al., ACM Computing Surveys | 2020 |
| 72 | TXSPECTOR: Uncovering attacks in ethereum from transactions | Zhang et al., USENIX Security | 2020 |
| 77 | Smartpulse: Automated checking of temporal properties in smart contracts | Stephens et al., IEEE S&P | 2021 |
| 78 | Verx: Safety verification of smart contracts | Permenev et al., IEEE S&P | 2020 |
| 82 | Securify: Practical security analysis of smart contracts | Tsankov et al., ACM CCS | 2018 |
| 84 | Soda: A generic online detection framework for smart contracts | Chen et al., NDSS | 2020 |
| 86 | Zeus: Analyzing safety of smart contracts | Kalra et al., NDSS | 2018 |
| 121 | Smart contract security: a practitioners' perspective | Wan et al., IEEE/ACM ICSE | 2021 |

---

## Arithmetic mistakes
참조 번호: 71, 76, 78, 79

| # | 논문 제목 | 저자/출처 | 연도 |
|---|---------|----------|------|
| 71 | Smartest: Effectively hunting vulnerable transaction sequences in smart contracts through language model-guided symbolic execution | So et al., USENIX Security | 2021 |
| 76 | Sguard: Smart contracts made vulnerability-free | Nguyen et al., IEEE S&P | 2021 |
| 78 | Verx: Safety verification of smart contracts | Permenev et al., IEEE S&P | 2020 |
| 79 | Verismart: A highly precise safety verifier for ethereum smart contracts | So et al., IEEE S&P | 2020 |

---

## Liquidity (borrow, purchase, mint, deposit)
참조 번호: 8, 14

| # | 논문 제목 | 저자/출처 | 연도 |
|---|---------|----------|------|
| 8 | Attacking the defi ecosystem with flash loans for fun and profit | Qin et al., FC (Financial Cryptography) | 2021 |
| 14 | Sok: Decentralized finance (defi) | Werner et al. | 2021 |

---

## Other coding mistake
참조 번호: 10, 72, 75, 79

| # | 논문 제목 | 저자/출처 | 연도 |
|---|---------|----------|------|
| 10 | Security analysis methods on ethereum smart contract vulnerabilities: a survey | Praitheeshan et al. | 2019 |
| 72 | TXSPECTOR: Uncovering attacks in ethereum from transactions | Zhang et al., USENIX Security | 2020 |
| 75 | Sailfish: Vetting smart contract state-inconsistency bugs in seconds | Bose et al., IEEE S&P | 2022 |
| 79 | Verismart: A highly precise safety verifier for ethereum smart contracts | So et al., IEEE S&P | 2020 |

---

## Unfair slippage protection
참조 번호: 8, 9, 97

| # | 논문 제목 | 저자/출처 | 연도 |
|---|---------|----------|------|
| 8 | Attacking the defi ecosystem with flash loans for fun and profit | Qin et al., FC (Financial Cryptography) | 2021 |
| 9 | On the just-in-time discovery of profit-generating transactions in defi protocols | Zhou et al. (DeFiPoser), IEEE S&P | 2021 |
| 97 | Defiranger: Detecting price manipulation attacks on defi applications | Wu et al. | 2021 |

---

## Unfair liquidity providing
참조 번호: 없음 (x)

해당 취약점 유형에 대해 명시적으로 다루는 학술 논문이 표에 표시되어 있지 않음.

---

## Unsafe or infinite token approval
참조 번호: 없음 (x)

해당 취약점 유형에 대해 명시적으로 다루는 학술 논문이 표에 표시되어 있지 않음.

---

## Other unfair or unsafe interaction
참조 번호: 9

| # | 논문 제목 | 저자/출처 | 연도 |
|---|---------|----------|------|
| 9 | On the just-in-time discovery of profit-generating transactions in defi protocols | Zhou et al. (DeFiPoser), IEEE S&P | 2021 |

---

## 참고 사항

- 이 논문(SoK: DeFi Attacks)은 2023 IEEE Symposium on Security and Privacy (S&P)에 발표됨
- 저자: Liyi Zhou, Xihan Xiong, Jens Ernstberger, Stefanos Chaliasos, Zhipeng Wang, Ye Wang, Kaihua Qin, Roger Wattenhofer, Dawn Song, Arthur Gervais
- 분석 대상: 77개 학술 논문, 30개 감사 보고서, 181개 실제 사건

### 주요 발견
- **Absence of coding logic or sanity check**: 전체 사건의 24%를 차지 (44건)
- **Arithmetic mistakes**: 전체 사건의 1%를 차지 (2건)
- **Unfair slippage protection**: 전체 사건의 2%를 차지 (3건)
- **Liquidity related**: 전체 사건의 5%를 차지 (9건)

### TABLE III 분류 체계
논문에서는 DeFi 사건을 다음 5개 레이어로 분류:
1. **Network Layer (NET)** - 네트워크 관련 취약점
2. **Consensus Layer (CON)** - 합의 메커니즘 관련
3. **Smart Contract Layer (SC)** - 스마트 컨트랙트 코딩 오류
4. **Protocol Layer (PRO)** - DeFi 프로토콜 설계 결함
5. **Auxiliary Services (AUX)** - 보조 서비스 취약점
