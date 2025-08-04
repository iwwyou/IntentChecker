
#!/usr/bin/env python3
"""
라이브러리 관리 기능 테스트 스크립트

이 스크립트는 다음 기능들을 테스트합니다:
1. 라이브러리 소스 분석 및 저장
2. using directive 처리 시 라이브러리 로드
3. 라이브러리 함수 호출 처리
"""

from Analyzer.ContractAnalyzer import ContractAnalyzer

def test_library_management():
    """라이브러리 관리 기능 테스트"""
    
    # 1. ContractAnalyzer 인스턴스 생성
    analyzer = ContractAnalyzer()
    
    # 2. 테스트용 라이브러리 소스 코드
    math_library_source = """
library SafeMath {
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        uint256 c = a + b;
        require(c >= a, "SafeMath: addition overflow");
        return c;
    }
    
    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b <= a, "SafeMath: subtraction overflow");
        return a - b;
    }
    
    function mul(uint256 a, uint256 b) internal pure returns (uint256) {
        if (a == 0) {
            return 0;
        }
        uint256 c = a * b;
        require(c / a == b, "SafeMath: multiplication overflow");
        return c;
    }
}
"""

    # 3. 라이브러리 분석 및 저장
    print("=== 라이브러리 분석 및 저장 ===")
    try:
        library_name = analyzer.analyze_and_save_library(math_library_source)
        print(f"✓ 라이브러리 '{library_name}' 분석 및 저장 완료")
    except Exception as e:
        print(f"✗ 라이브러리 분석 실패: {e}")
        return

    # 4. 테스트용 컨트랙트 소스 코드 (using directive 포함)
    contract_source = """
contract TestContract {
    using SafeMath for uint256;
    
    uint256 public value;
    
    function addValues(uint256 a, uint256 b) public returns (uint256) {
        return a.add(b);
    }
    
    function multiplyValues(uint256 a, uint256 b) public returns (uint256) {
        return a.mul(b);
    }
}
"""

    # 5. 컨트랙트 분석 (using directive 처리 포함)
    print("\n=== 컨트랙트 분석 (using directive 처리) ===")
    try:
        # 컨트랙트 소스를 청크로 나누어 분석
        from Analyzer.ContractParser import ContractParser
        parser = ContractParser()
        chunks = parser.parse_contract(contract_source)
        
        for chunk in chunks:
            code = chunk.code
            start_line = chunk.start_line
            end_line = chunk.end_line
            event = chunk.event
            
            if code.strip() == "" or code.strip() == "\n":
                continue
                
            analyzer.update_code(start_line, end_line, code, event)
            
        print("✓ 컨트랙트 분석 완료")
        
    except Exception as e:
        print(f"✗ 컨트랙트 분석 실패: {e}")
        return

    # 6. 라이브러리 로드 테스트
    print("\n=== 라이브러리 로드 테스트 ===")
    try:
        loaded_library = analyzer.load_library_cfg("SafeMath")
        if loaded_library:
            print("✓ 라이브러리 로드 성공")
            print(f"  - 라이브러리 이름: {loaded_library.contract_name}")
            print(f"  - 함수 개수: {len(loaded_library.functions)}")
            print(f"  - 함수 목록: {list(loaded_library.functions.keys())}")
        else:
            print("✗ 라이브러리 로드 실패")
    except Exception as e:
        print(f"✗ 라이브러리 로드 중 오류: {e}")

    # 7. 저장된 파일 확인
    print("\n=== 저장된 파일 확인 ===")
    import pathlib
    libraries_dir = pathlib.Path(__file__).parent / "Libraries"
    if libraries_dir.exists():
        library_files = list(libraries_dir.glob("*.json"))
        print(f"저장된 라이브러리 파일: {len(library_files)}개")
        for file_path in library_files:
            print(f"  - {file_path.name}")
    else:
        print("Libraries 디렉토리가 존재하지 않습니다.")

def test_using_directive_processing():
    """using directive 처리 테스트"""
    print("\n=== using directive 처리 테스트 ===")
    
    analyzer = ContractAnalyzer()
    
    # 먼저 컨트랙트 생성
    analyzer.make_contract_cfg("TestContract")
    
    try:
        # using directive 처리
        analyzer.process_using_directive("SafeMath", "uint256")
        print("✓ using directive 처리 성공")
        
        # 현재 컨트랙트에서 라이브러리 확인
        contract_cfg = analyzer.contract_cfgs.get("TestContract")
        if hasattr(contract_cfg, 'using_libraries'):
            print(f"✓ 연결된 라이브러리: {len(contract_cfg.using_libraries)}개")
        
    except Exception as e:
        print(f"✗ using directive 처리 실패: {e}")

if __name__ == "__main__":
    print("라이브러리 관리 기능 테스트 시작\n")
    
    test_library_management()
    test_using_directive_processing()
    
    print("\n테스트 완료")