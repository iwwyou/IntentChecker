#!/usr/bin/env python3
"""
현재 JSON 직렬화 상태 간단 확인
"""

import json
import pathlib
import re

def check_json_serialization():
    """SafeMath.json 파일의 직렬화 상태 확인"""

    json_file = pathlib.Path("Libraries/objectfile/SafeMath.json")

    if not json_file.exists():
        print(f"✗ {json_file} 파일을 찾을 수 없습니다")
        return

    print("=" * 60)
    print("JSON 직렬화 상태 확인")
    print("=" * 60)

    # 파일 크기
    file_size = json_file.stat().st_size
    print(f"\n파일 크기: {file_size:,} bytes ({file_size/1024:.1f} KB)")

    # JSON 로드
    with open(json_file, 'r', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)

    print(f"라이브러리 이름: {data.get('library_name', 'N/A')}")
    print(f"함수 개수: {len(data.get('functions', {}))}")

    # 객체 문자열 패턴 찾기
    pattern = r"<[\w.]+\s+object\s+at\s+0x[0-9A-Fa-f]+>"
    matches = re.findall(pattern, content)

    print(f"\n직렬화 실패한 객체: {len(matches)}개")

    if matches:
        print("\n❌ 직렬화 실패 - 객체가 문자열로 저장됨")
        print("\n샘플:")
        for match in matches[:5]:
            print(f"  {match}")
        if len(matches) > 5:
            print(f"  ... 외 {len(matches) - 5}개")
    else:
        print("\n✅ 직렬화 성공 - 모든 객체가 제대로 변환됨")

    # 함수 하나 샘플 확인
    if "functions" in data and data["functions"]:
        print("\n" + "=" * 60)
        print("샘플 함수 확인")
        print("=" * 60)

        func_name = list(data["functions"].keys())[0]
        func_data = data["functions"][func_name]

        print(f"\n함수: {func_name}")
        print(f"타입: {func_data.get('function_type', 'N/A')}")

        # return_types 확인
        if "return_types" in func_data:
            print(f"\n반환 타입:")
            for i, ret in enumerate(func_data["return_types"][:3]):
                if isinstance(ret, str) and "object at 0x" in ret:
                    print(f"  [{i}] ✗ {ret}")
                else:
                    print(f"  [{i}] ✓ {type(ret).__name__}: {ret}")

        # related_variables 확인
        if "related_variables" in func_data:
            print(f"\n관련 변수:")
            for var_name, var_data in list(func_data["related_variables"].items())[:3]:
                if isinstance(var_data, str) and "object at 0x" in var_data:
                    print(f"  {var_name}: ✗ {var_data[:50]}...")
                else:
                    print(f"  {var_name}: ✓ {type(var_data).__name__}")

    print("\n" + "=" * 60)
    print("결론")
    print("=" * 60)

    if matches:
        print("""
현재 JSON 직렬화는 실패 상태입니다:
- 복잡한 객체(Variables, SolType, Interval 등)가 문자열로 저장됨
- 역직렬화 시 실제 객체로 복원 불가능
- CFGSerializer._json_safe() 메서드가 제대로 호출되지 않음

대안:
1. Pickle 사용 (가장 간단, Python 객체 완벽 보존)
2. CFGSerializer._json_safe() 로직 수정
3. 커스텀 JSON encoder/decoder 구현
        """)
    else:
        print("✅ JSON 직렬화가 제대로 작동합니다!")

if __name__ == "__main__":
    check_json_serialization()
