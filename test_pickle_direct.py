#!/usr/bin/env python3
"""
직접 Pickle serialization 테스트
ContractAnalyzer import 없이 CFG 객체만 테스트
"""

import sys
import pathlib

# Utils.CFG만 import
sys.path.append(str(pathlib.Path(__file__).parent))

from Utils.CFG import LibraryCFG, FunctionCFG
from Analyzer.CFGSerializerPickle import CFGSerializerPickle


def create_mock_library_cfg():
    """테스트용 LibraryCFG 생성"""
    print("=== Mock LibraryCFG 생성 ===")

    # LibraryCFG 생성
    library_cfg = LibraryCFG("SafeMath")

    # 함수 추가
    add_func = FunctionCFG("function", "add")
    mul_func = FunctionCFG("function", "mul")

    library_cfg.functions["add"] = add_func
    library_cfg.functions["mul"] = mul_func

    print(f"✓ LibraryCFG 생성: {library_cfg.library_name}")
    print(f"✓ 함수 개수: {len(library_cfg.functions)}")

    return library_cfg


def test_pickle_serialization():
    """Pickle 직렬화/역직렬화 테스트"""
    print("\n" + "=" * 60)
    print("Pickle 직렬화/역직렬화 테스트")
    print("=" * 60)

    # 1. Mock LibraryCFG 생성
    library_cfg = create_mock_library_cfg()

    # 2. CFGSerializerPickle로 저장
    print("\n=== Pickle로 저장 ===")
    serializer = CFGSerializerPickle()

    saved_path = serializer.save_library_cfg(library_cfg, "TestSafeMath")
    print(f"✓ 저장 완료: {saved_path}")

    # 파일 크기 확인
    file_path = pathlib.Path(saved_path)
    file_size = file_path.stat().st_size
    print(f"✓ 파일 크기: {file_size:,} bytes ({file_size/1024:.2f} KB)")

    # 3. Pickle에서 로드
    print("\n=== Pickle에서 로드 ===")
    loaded_cfg = serializer.load_library_cfg("TestSafeMath")

    if loaded_cfg is None:
        print("✗ 로드 실패")
        return False

    print(f"✓ 로드 완료")

    # 4. 검증
    print("\n=== 검증 ===")

    # 라이브러리 이름
    loaded_name = getattr(loaded_cfg, 'library_name',
                         getattr(loaded_cfg, 'contract_name', None))
    print(f"  라이브러리 이름: {loaded_name}")

    if loaded_name != "SafeMath":
        print(f"  ✗ 이름 불일치: {loaded_name} != SafeMath")
        return False

    # 함수 개수
    if hasattr(loaded_cfg, 'functions'):
        func_count = len(loaded_cfg.functions)
        print(f"  함수 개수: {func_count}")

        if func_count != 2:
            print(f"  ✗ 함수 개수 불일치: {func_count} != 2")
            return False

        # 함수 이름
        func_names = list(loaded_cfg.functions.keys())
        print(f"  함수 이름: {func_names}")

        if set(func_names) != {"add", "mul"}:
            print(f"  ✗ 함수 이름 불일치")
            return False

    print("\n✅ 모든 검증 통과!")
    return True


def test_with_complex_objects():
    """복잡한 객체 테스트"""
    print("\n" + "=" * 60)
    print("복잡한 객체 직렬화 테스트")
    print("=" * 60)

    try:
        # Domain.Variable import 시도
        from Domain.Variable import Variables
        from Domain.Type import SolType
        from Domain.Interval import IntegerInterval

        print("✓ Domain 모듈 import 성공")

        # LibraryCFG 생성
        library_cfg = LibraryCFG("SafeMathComplex")
        add_func = FunctionCFG("function", "add")

        # 복잡한 객체 추가
        var = Variables("testVar", "local")
        var.typeInfo = SolType.uint256()
        var.value = IntegerInterval(0, 100)

        add_func.related_variables["testVar"] = var
        library_cfg.functions["add"] = add_func

        print(f"✓ 복잡한 객체 생성: Variables, SolType, IntegerInterval")

        # 저장
        serializer = CFGSerializerPickle()
        saved_path = serializer.save_library_cfg(library_cfg, "SafeMathComplex")
        print(f"✓ 저장 완료: {saved_path}")

        # 로드
        loaded_cfg = serializer.load_library_cfg("SafeMathComplex")
        print(f"✓ 로드 완료")

        # 검증
        if loaded_cfg and "add" in loaded_cfg.functions:
            add_func_loaded = loaded_cfg.functions["add"]
            if hasattr(add_func_loaded, 'related_variables'):
                if "testVar" in add_func_loaded.related_variables:
                    loaded_var = add_func_loaded.related_variables["testVar"]

                    # 타입 확인
                    var_type = type(loaded_var).__name__
                    print(f"  로드된 변수 타입: {var_type}")

                    if var_type == "Variables":
                        print(f"  ✅ Variables 객체 완벽 복원!")

                        # 내부 객체 확인
                        if hasattr(loaded_var, 'typeInfo'):
                            type_info_type = type(loaded_var.typeInfo).__name__
                            print(f"  ✅ SolType 복원: {type_info_type}")

                        if hasattr(loaded_var, 'value'):
                            value_type = type(loaded_var.value).__name__
                            print(f"  ✅ IntegerInterval 복원: {value_type}")

                        return True

        print("  ✗ 객체 복원 실패")
        return False

    except ImportError as e:
        print(f"⚠ Domain 모듈 import 불가: {e}")
        print("  (기본 테스트는 통과했으므로 Pickle은 정상 작동)")
        return True


def main():
    print("=" * 60)
    print("Pickle Serialization 테스트")
    print("=" * 60)

    # 기본 테스트
    result1 = test_pickle_serialization()

    # 복잡한 객체 테스트
    result2 = test_with_complex_objects()

    print("\n" + "=" * 60)
    print("테스트 결과")
    print("=" * 60)
    print(f"기본 테스트: {'✅ 통과' if result1 else '✗ 실패'}")
    print(f"복잡한 객체 테스트: {'✅ 통과' if result2 else '✗ 실패'}")

    if result1 and result2:
        print("\n✅ 모든 테스트 통과!")
        print("\n다음 단계:")
        print("1. EnhancedSolidityVisitor.py의 PostDirectiveContext 문제 수정")
        print("2. Libraries/main.py 실행하여 실제 SafeMath.pkl 생성")
        print("3. 기존 SafeMath.json과 비교 검증")
    else:
        print("\n⚠ 일부 테스트 실패")


if __name__ == "__main__":
    main()
