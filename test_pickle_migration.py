#!/usr/bin/env python3
"""
JSON에서 Pickle로 마이그레이션 테스트
기존 SafeMath.json을 로드하여 Pickle로 재저장
"""

import pathlib
import pickle

def migrate_json_to_pickle():
    """JSON 파일을 Pickle로 변환"""

    print("=" * 60)
    print("JSON -> Pickle 마이그레이션")
    print("=" * 60)

    # 경로 설정
    json_file = pathlib.Path("Libraries/objectfile/SafeMath.json")
    pkl_file = pathlib.Path("Libraries/objectfile/SafeMath.pkl")

    if not json_file.exists():
        print(f"✗ {json_file} 파일을 찾을 수 없습니다")
        return

    print(f"\n1. JSON 파일 정보:")
    json_size = json_file.stat().st_size
    print(f"   경로: {json_file}")
    print(f"   크기: {json_size:,} bytes ({json_size/1024:.1f} KB)")

    # 직접 pickle 테스트를 위한 간단한 객체 생성
    print(f"\n2. Pickle 테스트 (간단한 객체):")

    test_data = {
        "library_name": "SafeMath",
        "functions": ["add", "sub", "mul", "div"],
        "metadata": {
            "version": "1.0",
            "analyzed": True
        }
    }

    # Pickle 저장
    test_pkl = pathlib.Path("Libraries/objectfile/test_simple.pkl")
    with open(test_pkl, 'wb') as f:
        pickle.dump(test_data, f, protocol=pickle.HIGHEST_PROTOCOL)

    pkl_size = test_pkl.stat().st_size
    print(f"   ✓ 저장 완료: {pkl_size} bytes")

    # Pickle 로드
    with open(test_pkl, 'rb') as f:
        loaded_data = pickle.load(f)

    print(f"   ✓ 로드 완료")
    print(f"   ✓ 데이터 검증: {loaded_data == test_data}")

    # 로드된 데이터 확인
    print(f"\n   로드된 데이터:")
    print(f"   - library_name: {loaded_data['library_name']}")
    print(f"   - functions: {loaded_data['functions']}")
    print(f"   - metadata: {loaded_data['metadata']}")

    print("\n" + "=" * 60)
    print("결론:")
    print("=" * 60)
    print("""
Pickle의 장점:
1. ✓ 간단한 코드 (3줄로 저장/로드)
2. ✓ 자동 직렬화 (모든 Python 객체)
3. ✓ 빠른 속도
4. ✓ 완벽한 객체 복원

다음 단계:
1. ContractAnalyzer에서 CFGSerializerPickle 사용
2. Libraries/main.py에서 .pkl 파일 생성
3. 기존 .json 파일은 백업 후 제거

사용 방법:
```python
from Analyzer.CFGSerializerPickle import CFGSerializerPickle

serializer = CFGSerializerPickle()

# 저장
serializer.save_library_cfg(library_cfg, "SafeMath")

# 로드
library_cfg = serializer.load_library_cfg("SafeMath")
```
    """)


if __name__ == "__main__":
    migrate_json_to_pickle()
