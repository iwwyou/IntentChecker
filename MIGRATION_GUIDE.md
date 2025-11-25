# JSON → Pickle 마이그레이션 가이드

## 현재 문제

**JSON 직렬화 실패 상태**
- 583개 객체가 `<Domain.Variable.Variables object at 0x...>` 형태로 저장
- 역직렬화 불가능
- 파일 크기: 126.7 KB (불필요하게 큼)

## 해결책: Pickle 사용

**테스트 결과**
- ✅ 간단한 객체 저장/로드 성공
- ✅ 125 bytes (작은 테스트 데이터)
- ✅ 완벽한 데이터 복원

---

## 적용 방법

### 옵션 1: 기존 코드 최소 수정 (권장)

ContractAnalyzer에서 CFGSerializer 대신 CFGSerializerPickle 사용:

**1. ContractAnalyzer.py 수정**

```python
# Before
from Analyzer.CFGSerializer import CFGSerializer

class ContractAnalyzer:
    def __init__(self):
        self.cfg_serializer = CFGSerializer()

# After
from Analyzer.CFGSerializerPickle import CFGSerializerPickle

class ContractAnalyzer:
    def __init__(self):
        self.cfg_serializer = CFGSerializerPickle()
```

**2. Libraries/main.py 수정 (선택사항)**

이미 ContractAnalyzer가 CFGSerializerPickle을 사용하므로 수정 불필요.
단, 명시적으로 사용하려면:

```python
# Before
from Analyzer.CFGSerializer import CFGSerializer
serializer = CFGSerializer()

# After
from Analyzer.CFGSerializerPickle import CFGSerializerPickle
serializer = CFGSerializerPickle()
```

**3. 파일 확장자**
- 기존: `SafeMath.json` → 새로운: `SafeMath.pkl`
- CFGSerializerPickle이 자동으로 `.pkl` 확장자 사용
- 기존 `.json` 파일이 있으면 자동 fallback (하위 호환성)

---

### 옵션 2: 하이브리드 (JSON과 Pickle 모두 지원)

기존 CFGSerializer를 수정하여 포맷 선택 가능하게:

```python
class CFGSerializer:
    def __init__(self, format='pickle'):  # 'pickle' or 'json'
        self.format = format

    def save_library_cfg(self, library_cfg, library_name, file_path=None):
        if self.format == 'pickle':
            # Use pickle
            with open(file_path, 'wb') as f:
                pickle.dump(library_cfg, f)
        else:
            # Use JSON (existing logic)
            ...
```

---

## 마이그레이션 절차

### 1단계: 새 Serializer로 재생성

```bash
# Libraries/main.py 실행하여 새로운 .pkl 파일 생성
cd Libraries
python main.py
```

**결과:**
- `Libraries/objectfile/SafeMath.pkl` 생성
- 기존 `SafeMath.json`은 그대로 유지 (백업용)

### 2단계: 검증

```python
from Analyzer.CFGSerializerPickle import CFGSerializerPickle

serializer = CFGSerializerPickle()
library_cfg = serializer.load_library_cfg("SafeMath")

# 검증
print(f"Library: {library_cfg.library_name}")
print(f"Functions: {len(library_cfg.functions)}")

# 함수 하나 확인
func = list(library_cfg.functions.values())[0]
print(f"Sample function: {func.function_name}")
print(f"Parameters: {func.parameters}")
print(f"Return types: {func.return_types}")

# ✅ 모든 객체가 제대로 복원되었는지 확인
for var_name, var_obj in func.related_variables.items():
    print(f"  {var_name}: {type(var_obj).__name__}")  # Variables, not str!
```

### 3단계: 기존 JSON 파일 정리 (선택사항)

```bash
# 백업
mv Libraries/objectfile/SafeMath.json Libraries/objectfile/SafeMath.json.bak

# 또는 삭제
rm Libraries/objectfile/SafeMath.json
```

---

## 예상 효과

| 항목 | JSON (현재) | Pickle (개선) |
|------|-------------|---------------|
| 파일 크기 | 126.7 KB | 비슷하거나 작음 |
| 직렬화 실패 | 583개 | 0개 ✅ |
| 코드 복잡도 | 높음 (558줄) | 낮음 (300줄) |
| 로드 속도 | 느림 | 빠름 |
| 객체 복원 | 실패 ❌ | 성공 ✅ |

---

## 주의사항

### Pickle의 한계
1. **보안**: 신뢰할 수 없는 소스에서 pickle 파일 로드 금지
2. **버전 호환성**: Python 버전이 크게 바뀌면 호환성 문제 가능
3. **가독성**: 바이너리 파일이므로 사람이 읽을 수 없음

### 대응 방안
- 라이브러리 파일은 프로젝트 내부에서만 사용 (외부 입력 X)
- Python 버전 고정 (예: Python 3.8+)
- 필요 시 디버깅용 JSON 내보내기 기능 추가

---

## 롤백 방법

문제 발생 시 기존 JSON 방식으로 복귀:

```python
# ContractAnalyzer.py
from Analyzer.CFGSerializer import CFGSerializer  # 원래대로
```

CFGSerializerPickle은 `.json` 파일 fallback을 지원하므로 즉시 롤백 가능.

---

## 요약

**현재 상태**
- ❌ JSON 직렬화 실패 (583개 객체)
- ❌ 역직렬화 불가능
- ❌ 복잡한 직렬화 로직

**Pickle 적용 후**
- ✅ 모든 객체 완벽 보존
- ✅ 3줄로 저장/로드
- ✅ 빠른 속도
- ✅ 간단한 코드

**다음 단계**
1. ContractAnalyzer.py에서 import 변경
2. Libraries/main.py 실행하여 .pkl 파일 생성
3. 검증 스크립트 실행
4. 기존 .json 파일 백업 또는 삭제
