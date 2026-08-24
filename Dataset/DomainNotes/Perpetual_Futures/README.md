# Perpetual Futures (퍼페추얼 스왑) 개념 정리

대상 프로토콜: **Tracer Protocol** — 만기가 없는 무기한 선물(perpetual swap)을 거래하는 탈중앙화 파생상품 거래소.
관련 컨트랙트: [contracts/web3bugs_16_H_04_Balances.md](contracts/web3bugs_16_H_04_Balances.md) (`Balances` 라이브러리)

## 1. 파생상품 매매는 현물 매매와 다르다

- **현물 거래**: 실제 자산(ETH 등)의 소유권이 오간다.
- **파생상품(퍼페추얼) 거래**: 실물 자산은 전혀 오가지 않는다. "가격에 연동된 계약"을 사고파는 것이며,
  손익은 담보로 예치한 토큰(quote, 예: USDC)으로만 **현금 결제(cash-settled)** 된다.
- "매매(트레이드)"란 오더북에서 **반대 방향 주문끼리 매칭**되는 것을 의미한다. 내가 Long을 걸고 싶어도
  정확히 그만큼 Short을 건 상대가 있어야 체결된다 (제로섬 구조: 시장 전체 Long 총량 = Short 총량).
  - Tracer는 오더북 기반이라 `fillAmount(orderA, fillA, orderB, fillB)`처럼 두 주문의 잔여 수량 중
    작은 쪽만큼만 체결시킨다. (AMM/vAMM 기반 퍼페추얼은 반대편이 가상 유동성 풀인 경우도 있음 — Tracer는 아님)

## 2. Position — base / quote

거래쌍은 `BASE/QUOTE` 형태로 표기된다 (예: ETH/USD → ETH가 base, USD가 quote).

- **base**: 사용자가 베팅한 기초자산 노출량(exposure). 실제 자산 보유량이 아니라 장부상의 숫자.
  - `base > 0` → Long (가격 상승에 베팅)
  - `base < 0` → Short (가격 하락에 베팅)
  - 가격이 오르내려도 base의 부호 자체는 바뀌지 않는다 (거래를 통해 포지션을 정리하기 전까지 고정).
- **quote**: 사용자의 담보(margin/collateral) 잔고. 실제 예치된 현금성 자산.
  - 가격 변동만으로는 바뀌지 않고, **실제 거래 체결 / 입출금이 있을 때만** 갱신된다.
  - Long은 quote를 지불하고 base를 얻는 것(현물에서 자산을 사는 것과 동일한 논리) → quote 감소, base 증가
  - Short은 base를 내주고 quote를 받는 것(공매도와 동일한 논리) → quote 증가, base 감소

## 3. 담보(margin/collateral)와 레버리지

- 포지션을 열려면 먼저 quote 자산을 담보로 예치해야 한다.
- 담보 전액만큼만 포지션을 여는 게 아니라, 레버리지를 통해 담보보다 훨씬 큰 명목가치(notional value)의
  포지션을 열 수 있다. (예: 담보 $1,000, 레버리지 5배 → $5,000 어치 포지션)
- **margin (실제 자기자본, 실시간 계산값)** = `quote + base * price`
  - price가 바뀔 때마다 재계산되는 값이며 별도로 저장되지 않는다.
- **minimumMargin (요구되는 최소 기준선, 실시간 계산값)** = `notionalValue / maxLeverage + 6 * liquidationGasCost`
  - `notionalValue = |base| * price` — 현재 시세 기준 포지션 명목가치
  - "처음 낸 담보"와는 무관하며, **현재 포지션 크기 × 현재 가격**을 기준으로 매 순간 다시 계산된다.
  - `6 * liquidationGasCost`는 청산자에게 가스비를 보상하기 위한 안전 버퍼.
- **청산(liquidation)**: 매 체크 시점마다 같은 price로 `margin`과 `minimumMargin`을 동시에 재계산해서
  `margin < minimumMargin`이면 청산 대상이 된다. 진입 시점 가격은 이 비교에 다시 등장하지 않는다.

## 4. 담보 인출과 매매는 다른 동작

- **매매 체결(트레이드)**: base와 quote가 **함께** 변한다 (`applyTrade`가 담당, `Trade{price, amount, side}` 필요).
- **담보만 입출금**: base는 그대로 두고 quote만 변한다. `applyTrade`로는 표현 불가 (Trade 구조체 자체가
  실제 매매 정보를 요구하기 때문). 별도의 deposit/withdraw 로직이 담당하며, 출금 시에는 출금 후
  `marginIsValid`를 통과하는지 검증해서 청산 위험 수준까지 담보를 빼가는 것을 막는다.
  (이 데이터셋의 `Balances.sol`에는 deposit/withdraw 자체는 없고, 상위 컨트랙트에 있을 것으로 추정)

## 비유 정리

| 개념 | 비유 |
|---|---|
| 담보(quote) | 전월세 보증금 — 내가 실제로 낸 돈 |
| 포지션(base) | 보증금을 지렛대 삼아 베팅한 훨씬 큰 규모의 노출 |
| 청산 | 보증금이 손실을 감당 못 할 정도로 줄어들면 강제 정리되는 것 |
| Long 진입 | 현물에서 자산을 사는 것 (현금 내고 자산 취득) |
| Short 진입 | 공매도 (자산을 내주고 현금 취득) |
