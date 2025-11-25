#!/usr/bin/env python3
"""
다양한 직렬화 방법 테스트 스크립트
SafeMath 라이브러리를 여러 방식으로 저장/로드하여 비교
"""

import sys
import pathlib
import pickle
import json
import time
from typing import Any

sys.path.append(str(pathlib.Path(__file__).parent))

from Analyzer.ContractAnalyzer import ContractAnalyzer
from Analyzer.CFGSerializer import CFGSerializer


class SerializationTester:
    """다양한 직렬화 방법을 테스트하는 클래스"""

    def __init__(self):
        self.test_dir = pathlib.Path(__file__).parent / "serialization_test"
        self.test_dir.mkdir(exist_ok=True)

        # SafeMath 라이브러리 로드
        self.library_name = "SafeMath"
        self.analyzer = ContractAnalyzer()

    def load_original_library(self):
        """원본 라이브러리 CFG 로드"""
        print("=== 원본 라이브러리 로드 ===")

        # Libraries/objectfile/SafeMath.json에서 로드 시도
        serializer = CFGSerializer()
        library_file = pathlib.Path(__file__).parent / "Libraries" / "objectfile" / f"{self.library_name}.json"

        if library_file.exists():
            print(f"✓ {library_file} 발견")
            library_cfg = serializer.load_library_cfg(self.library_name, str(library_file))
            return library_cfg
        else:
            print(f"✗ {library_file} 없음")
            return None

    def test_pickle_serialization(self, library_cfg):
        """Pickle 방식 테스트"""
        print("\n=== Pickle 직렬화 테스트 ===")

        pickle_file = self.test_dir / f"{self.library_name}.pkl"

        try:
            # 저장
            start = time.time()
            with open(pickle_file, 'wb') as f:
                pickle.dump(library_cfg, f, protocol=pickle.HIGHEST_PROTOCOL)
            save_time = time.time() - start
            file_size = pickle_file.stat().st_size

            print(f"✓ 저장 완료: {file_size:,} bytes ({save_time:.3f}s)")

            # 로드
            start = time.time()
            with open(pickle_file, 'rb') as f:
                loaded_cfg = pickle.load(f)
            load_time = time.time() - start

            print(f"✓ 로드 완료 ({load_time:.3f}s)")

            # 검증
            self._verify_library_cfg(loaded_cfg, "Pickle")

            return {
                "method": "pickle",
                "save_time": save_time,
                "load_time": load_time,
                "file_size": file_size,
                "success": True
            }

        except Exception as e:
            print(f"✗ Pickle 실패: {e}")
            import traceback
            traceback.print_exc()
            return {"method": "pickle", "success": False, "error": str(e)}

    def test_json_current_serialization(self, library_cfg):
        """현재 JSON 방식 테스트 (CFGSerializer 사용)"""
        print("\n=== 현재 JSON 직렬화 테스트 ===")

        json_file = self.test_dir / f"{self.library_name}_current.json"

        try:
            # 저장
            serializer = CFGSerializer()
            start = time.time()
            serializer.save_library_cfg(library_cfg, self.library_name, str(json_file))
            save_time = time.time() - start
            file_size = json_file.stat().st_size

            print(f"✓ 저장 완료: {file_size:,} bytes ({save_time:.3f}s)")

            # 로드
            start = time.time()
            loaded_cfg = serializer.load_library_cfg(self.library_name, str(json_file))
            load_time = time.time() - start

            print(f"✓ 로드 완료 ({load_time:.3f}s)")

            # 검증
            self._verify_library_cfg(loaded_cfg, "JSON (Current)")

            # JSON 내용 샘플 확인
            self._check_json_content(json_file)

            return {
                "method": "json_current",
                "save_time": save_time,
                "load_time": load_time,
                "file_size": file_size,
                "success": True
            }

        except Exception as e:
            print(f"✗ JSON 실패: {e}")
            import traceback
            traceback.print_exc()
            return {"method": "json_current", "success": False, "error": str(e)}

    def test_dill_serialization(self, library_cfg):
        """Dill 방식 테스트 (pickle 확장)"""
        print("\n=== Dill 직렬화 테스트 ===")

        try:
            import dill
        except ImportError:
            print("✗ dill 미설치 (pip install dill)")
            return {"method": "dill", "success": False, "error": "not installed"}

        dill_file = self.test_dir / f"{self.library_name}.dill"

        try:
            # 저장
            start = time.time()
            with open(dill_file, 'wb') as f:
                dill.dump(library_cfg, f)
            save_time = time.time() - start
            file_size = dill_file.stat().st_size

            print(f"✓ 저장 완료: {file_size:,} bytes ({save_time:.3f}s)")

            # 로드
            start = time.time()
            with open(dill_file, 'rb') as f:
                loaded_cfg = dill.load(f)
            load_time = time.time() - start

            print(f"✓ 로드 완료 ({load_time:.3f}s)")

            # 검증
            self._verify_library_cfg(loaded_cfg, "Dill")

            return {
                "method": "dill",
                "save_time": save_time,
                "load_time": load_time,
                "file_size": file_size,
                "success": True
            }

        except Exception as e:
            print(f"✗ Dill 실패: {e}")
            import traceback
            traceback.print_exc()
            return {"method": "dill", "success": False, "error": str(e)}

    def _verify_library_cfg(self, loaded_cfg, method_name: str):
        """로드된 라이브러리 CFG 검증"""
        print(f"\n  [{method_name}] CFG 검증:")

        if loaded_cfg is None:
            print("    ✗ CFG가 None입니다")
            return False

        # 기본 속성 확인
        library_name = getattr(loaded_cfg, 'library_name',
                              getattr(loaded_cfg, 'contract_name', None))
        print(f"    - 라이브러리 이름: {library_name}")

        # 함수들 확인
        if hasattr(loaded_cfg, 'functions'):
            functions = loaded_cfg.functions
            print(f"    - 함수 개수: {len(functions)}")

            if functions:
                # 첫 번째 함수 상세 검증
                first_func_name = list(functions.keys())[0]
                first_func = functions[first_func_name]

                print(f"    - 샘플 함수: {first_func_name}")

                # 파라미터 타입 확인
                if hasattr(first_func, 'parameters'):
                    params = first_func.parameters
                    print(f"      • 파라미터: {len(params)}개")
                    for param in params[:2]:  # 처음 2개만
                        param_type = type(param).__name__
                        print(f"        - {param_type}: {param}")

                # Return 타입 확인
                if hasattr(first_func, 'return_types'):
                    returns = first_func.return_types
                    print(f"      • 반환 타입: {len(returns)}개")
                    for ret in returns[:2]:
                        ret_type = type(ret).__name__
                        # 객체 문자열인지 확인
                        if isinstance(ret, str) and "object at 0x" in ret:
                            print(f"        ✗ 직렬화 실패: {ret}")
                        else:
                            print(f"        ✓ {ret_type}")

                # Variables 확인
                if hasattr(first_func, 'related_variables'):
                    vars_dict = first_func.related_variables
                    print(f"      • 관련 변수: {len(vars_dict)}개")
                    for var_name, var_obj in list(vars_dict.items())[:2]:
                        var_type = type(var_obj).__name__
                        # 객체 문자열인지 확인
                        if isinstance(var_obj, str) and "object at 0x" in var_obj:
                            print(f"        ✗ {var_name}: 직렬화 실패")
                        else:
                            print(f"        ✓ {var_name}: {var_type}")
                            # 변수 값 확인
                            if hasattr(var_obj, 'value'):
                                value = var_obj.value
                                value_type = type(value).__name__
                                print(f"          값: {value_type}")

        return True

    def _check_json_content(self, json_file: pathlib.Path):
        """JSON 파일 내용 샘플 확인"""
        print("\n  JSON 내용 샘플:")

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 첫 번째 함수의 첫 번째 return_type 확인
        if "functions" in data:
            first_func = list(data["functions"].values())[0]
            if "return_types" in first_func and first_func["return_types"]:
                sample_return = first_func["return_types"][0]
                if isinstance(sample_return, str) and "object at 0x" in sample_return:
                    print(f"    ✗ 객체가 문자열로 저장됨: {sample_return}")
                else:
                    print(f"    ✓ 제대로 직렬화됨: {sample_return}")

    def run_all_tests(self):
        """모든 직렬화 방법 테스트"""
        print("=" * 60)
        print("직렬화 방법 비교 테스트")
        print("=" * 60)

        # 원본 라이브러리 로드
        library_cfg = self.load_original_library()

        if library_cfg is None:
            print("\n✗ 원본 라이브러리를 로드할 수 없습니다.")
            print("Libraries/main.py를 먼저 실행하여 SafeMath 라이브러리를 분석하세요.")
            return

        results = []

        # 각 방법 테스트
        results.append(self.test_pickle_serialization(library_cfg))
        results.append(self.test_json_current_serialization(library_cfg))
        results.append(self.test_dill_serialization(library_cfg))

        # 결과 요약
        print("\n" + "=" * 60)
        print("테스트 결과 요약")
        print("=" * 60)

        for result in results:
            if result["success"]:
                print(f"\n{result['method'].upper()}:")
                print(f"  저장 시간: {result['save_time']:.3f}s")
                print(f"  로드 시간: {result['load_time']:.3f}s")
                print(f"  파일 크기: {result['file_size']:,} bytes ({result['file_size']/1024:.1f} KB)")
            else:
                print(f"\n{result['method'].upper()}: 실패")
                if "error" in result:
                    print(f"  오류: {result['error']}")

        print("\n" + "=" * 60)
        print("권장사항:")
        print("=" * 60)
        print("1. Pickle: 가장 간단하고 빠름, Python 객체 완벽 보존")
        print("2. Dill: Pickle의 확장, 더 많은 타입 지원")
        print("3. JSON: 현재 방식은 객체 직렬화 실패 (수정 필요)")


def main():
    tester = SerializationTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
