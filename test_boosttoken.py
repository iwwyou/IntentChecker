"""
BoostToken operator_order_issue 테스트
- 버그: sendETHToTeam 함수의 amount.div(12).mul(5) 등 연산 순서 문제
- 테스트 케이스: amount=65 일 때 precision loss 탐지
"""

from Analyzer.ContractAnalyzer import ContractAnalyzer
from Analyzer.DebugUnitAnalyzer import DebugBatchManager
from Analyzer.EnhancedSolidityVisitor import EnhancedSolidityVisitor
from Utils.Helper import ParserHelpers
import json
import time

def load_json_inputs(json_path):
    """JSON 파일에서 입력 레코드 로드"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    # 1. ContractAnalyzer 초기화
    contract_analyzer = ContractAnalyzer()
    snapman = contract_analyzer.snapman
    batch_mgr = DebugBatchManager(contract_analyzer, snapman)

    # 2. JSON 입력 파일 로드 (원본 contraction 파일)
    json_path = r"C:\Users\isjeon\PycharmProjects\pythonProject\SolidityGuardian\Dataset\Numscout\contraction\operator_order_issue\BoostToken_contraction.json"
    records = load_json_inputs(json_path)

    print("=" * 60)
    print("Phase 1: 코드 입력 (test.py 방식)")
    print("=" * 60)
    print(f"Total records: {len(records)}")

    # 3. 각 레코드마다 update_code + EnhancedSolidityVisitor 호출
    for rec in records:
        code, s, e, ev = rec["code"], rec["startLine"], rec["endLine"], rec["event"]

        # update_code로 소스 코드 저장 및 context 관리
        contract_analyzer.update_code(s, e, code, ev)

        # sendETHToTeam 함수 부분만 출력 (Line 135-140)
        if 135 <= s <= 140:
            display_code = code.replace('\n', '\\n')
            print(f"Line {s}-{e}: {display_code}")

        # 일반 Solidity 코드는 EnhancedSolidityVisitor로 파싱
        stripped = code.strip()
        if stripped and not stripped.startswith("// @"):
            ctx = contract_analyzer.get_current_context_type()
            # ctx가 None이어도 파싱 시도 (컨트랙트/라이브러리 정의 등)
            try:
                tree = ParserHelpers.generate_parse_tree(code, ctx, True)
                EnhancedSolidityVisitor(contract_analyzer).visit(tree)
            except Exception as ex:
                pass  # pragma 등 파싱 실패는 무시

    print("\n" + "=" * 60)
    print("Phase 2: CFG 확인")
    print("=" * 60)

    # 디버깅: 현재 상태 확인
    print(f"\n[DEBUG] current_target_contract: {contract_analyzer.current_target_contract}")
    print(f"[DEBUG] contract_cfgs keys: {list(contract_analyzer.contract_cfgs.keys())}")

    # 각 contract의 functions 출력
    for cname, ccfg in contract_analyzer.contract_cfgs.items():
        funcs = list(ccfg.functions.keys()) if hasattr(ccfg, 'functions') else []
        print(f"[DEBUG] Contract/Library '{cname}' functions: {funcs}")

    # sendETHToTeam이 있는지 확인
    boost_cfg = contract_analyzer.contract_cfgs.get("BoostToken")
    if boost_cfg and hasattr(boost_cfg, 'functions'):
        if "sendETHToTeam" in boost_cfg.functions:
            print("[OK] sendETHToTeam 함수 등록됨!")
        else:
            print("[FAIL] sendETHToTeam 함수가 등록되지 않음")

    print("\n" + "=" * 60)
    print("Phase 3: Intent Annotation 추가 (CFG 노드에 저장)")
    print("=" * 60)

    # Intent annotation을 먼저 추가 (CFG 노드에 저장됨)
    # JSON 기준:
    # Line 141: _marketingWalletAddress.transfer(amount.div(12).mul(5));
    # Line 142: _dipWalletAddress.transfer(amount.div(9).mul(2));
    # amount=65일 때:
    #   65 / 12 = 5, 5 * 5 = 25  (의도: 65 * 5 / 12 = 27)
    #   65 / 9 = 7, 7 * 2 = 14   (의도: 65 * 2 / 9 = 14)

    intent_annotations = [
        (141, "// @During transfer.arg[0] > 27"),  # amount=65 -> 의도: 27, 실제: 25 (버그!)
        (142, "// @During transfer.arg[0] > 14"),  # amount=65 -> 의도: 14, 실제: 14 (경계)
    ]

    for line_no, annotation in intent_annotations:
        print(f"Adding intent at line {line_no}: {annotation}")
        result = contract_analyzer.add_intent_annotation(line_no, annotation)
        print(f"  Result: {result}")

    print("\n" + "=" * 60)
    print("Phase 4: Debug Annotation 추가 및 실행 (amount = 65)")
    print("=" * 60)

    # Debug annotation 적용 (Intent 검증은 해석 시점에 발생)
    batch_mgr.reset()

    # BEGIN 시그널
    print("Setting debug context via update_code...")
    contract_analyzer.update_code(140, 140, "// @Debugging BEGIN", "add")

    # LocalVar로 amount = [65, 65] 설정 (interval 형식)
    print("Adding debug: // @LocalVar amount = [65, 65]")
    batch_mgr.add_line("// @LocalVar amount = [65, 65]", 140, 140)

    # flush로 debug annotation 적용 및 해석 실행
    # 이 시점에 CFG 노드에 저장된 intent가 검증됨
    print("Running interpretation with debug values...")
    batch_mgr.flush()

    print("\n" + "=" * 60)
    print("Phase 5: 분석 완료")
    print("=" * 60)

    print("\n분석 완료!")

if __name__ == "__main__":
    start = time.time()
    main()
    end = time.time()
    print(f"\nTotal time: {end - start:.3f} sec")
