# Python 객체 직렬화 방법 비교

## 1. Pickle (권장 ✅)

### 장점
- Python 표준 라이브러리 (별도 설치 불필요)
- 모든 Python 객체 자동 직렬화/역직렬화
- 빠른 속도
- 추가 직렬화 로직 불필요

### 단점
- 바이너리 파일 (사람이 읽을 수 없음)
- Python 버전 간 호환성 이슈 가능
- 보안 위험 (신뢰할 수 없는 소스에서 로드 시)

### 사용법
```python
import pickle

# 저장
with open('SafeMath.pkl', 'wb') as f:
    pickle.dump(library_cfg, f, protocol=pickle.HIGHEST_PROTOCOL)

# 로드
with open('SafeMath.pkl', 'rb') as f:
    library_cfg = pickle.load(f)
```

---

## 2. Dill

### 장점
- Pickle의 확장판
- 더 많은 타입 지원 (람다, 클래스 정의 등)
- Pickle과 동일한 API

### 단점
- 외부 라이브러리 (pip install dill)
- Pickle보다 약간 느림

### 사용법
```python
import dill

# 저장
with open('SafeMath.dill', 'wb') as f:
    dill.dump(library_cfg, f)

# 로드
with open('SafeMath.dill', 'rb') as f:
    library_cfg = dill.load(f)
```

---

## 3. JSON (현재 방식 - 실패 중 ❌)

### 장점
- 사람이 읽을 수 있음
- 버전 관리 용이
- 언어 간 호환성

### 단점
- 복잡한 객체 직렬화 실패 (현재 상태)
- 커스텀 encoder/decoder 필요
- 모든 객체 타입에 대한 직렬화 로직 구현 필요

### 문제점
- Variables, SolType, Interval 등이 `str(obj)` 형태로 저장
- 583개 객체 직렬화 실패
- 역직렬화 불가능

---

## 4. MessagePack

### 장점
- JSON보다 작고 빠름
- 바이너리 포맷
- 언어 간 호환성

### 단점
- 외부 라이브러리 (pip install msgpack)
- 복잡한 객체는 여전히 커스텀 로직 필요

---

## 5. HDF5 / Parquet

### 장점
- 대용량 데이터에 최적화
- 부분 로딩 가능
- 압축 지원

### 단점
- 외부 라이브러리 필요
- 복잡한 객체 구조에는 부적합
- 오버킬

---

## 권장: Pickle 사용

### 이유
1. **간단함**: 기존 코드 최소 수정
2. **완벽한 보존**: 모든 객체 완벽 복원
3. **빠름**: JSON보다 빠른 속도
4. **표준 라이브러리**: 별도 설치 불필요

### 예상 개선
- 직렬화 실패: 583개 → 0개
- 파일 크기: 비슷하거나 더 작음
- 로드 시간: 더 빠름
- 복잡도: 대폭 감소

---

## 구현 예시

### Before (JSON - 실패)
```python
# CFGSerializer.save_library_cfg()
serialized_data = self._serialize_library_cfg(library_cfg)
serialized_data = self._json_safe(serialized_data)  # 실패
with open(file_path, 'w') as f:
    json.dump(serialized_data, f)
```

### After (Pickle - 성공)
```python
# CFGSerializer.save_library_cfg()
with open(file_path, 'wb') as f:
    pickle.dump(library_cfg, f, protocol=pickle.HIGHEST_PROTOCOL)
```

### 추가 고려사항
- `.json` 확장자를 `.pkl` 또는 `.pickle`로 변경
- 기존 JSON 파일과 호환성 유지 필요 시 확장자로 구분
- 버전 정보 포함 가능
