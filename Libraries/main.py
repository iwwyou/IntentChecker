#!/usr/bin/env python3
"""
라이브러리 관리 시스템 메인 스크립트

이 스크립트는 다음 기능들을 수행합니다:
1. libraries/solfile/*.sol 파일들을 스캔
2. SolidityGuardian을 통해 라이브러리들을 분석
3. 분석 결과를 libraries/objectfile/*.json에 저장
4. using directive 사용 시 objectfile에서 로드하는 시스템 테스트
"""

import os
import sys
import pathlib
from typing import Dict, List

# 상위 디렉토리를 sys.path에 추가하여 SolidityGuardian 모듈 사용
sys.path.append(str(pathlib.Path(__file__).parent.parent))

from Analyzer.ContractAnalyzer import ContractAnalyzer

class LibraryManager:
    """라이브러리 관리 클래스"""
    
    def __init__(self):
        self.current_dir = pathlib.Path(__file__).parent
        self.solfile_dir = self.current_dir / "solfile"
        self.objectfile_dir = self.current_dir / "objectfile"
        self.analyzer = ContractAnalyzer()
        
        # 디렉토리 생성 확인
        self.solfile_dir.mkdir(exist_ok=True)
        self.objectfile_dir.mkdir(exist_ok=True)
    
    def scan_sol_files(self) -> List[pathlib.Path]:
        """solfile 디렉토리의 .sol 파일들을 스캔"""
        sol_files = list(self.solfile_dir.glob("*.sol"))
        print(f"발견된 .sol 파일: {len(sol_files)}개")
        for sol_file in sol_files:
            print(f"  - {sol_file.name}")
        return sol_files
    
    def analyze_library_file(self, sol_file_path: pathlib.Path) -> str:
        """
        .sol 파일을 분석하여 objectfile에 저장
        
        Args:
            sol_file_path: 분석할 .sol 파일 경로
            
        Returns:
            라이브러리 이름
        """
        print(f"\n=== {sol_file_path.name} 분석 시작 ===")
        
        # 1. 소스 파일 읽기
        try:
            library_source = sol_file_path.read_text(encoding='utf-8')
            print(f"✓ 소스 파일 읽기 성공 ({len(library_source)} 문자)")
        except Exception as e:
            print(f"✗ 소스 파일 읽기 실패: {e}")
            raise
        
        # 2. 라이브러리 분석 및 저장
        try:
            library_name = self.analyzer.analyze_and_save_library(library_source)
            print(f"✓ 라이브러리 '{library_name}' 분석 완료")
            
            # 3. 분석된 CFG를 objectfile 디렉토리로 이동
            self._move_to_objectfile(library_name)
            
            return library_name
            
        except Exception as e:
            print(f"✗ 라이브러리 분석 실패: {e}")
            raise
    
    def _move_to_objectfile(self, library_name: str):
        """분석된 라이브러리 CFG를 objectfile 디렉토리로 이동"""
        # 기본 Libraries 디렉토리에서 objectfile로 이동
        default_library_path = pathlib.Path(__file__).parent.parent / "Libraries" / f"{library_name}.json"
        target_path = self.objectfile_dir / f"{library_name}.json"
        
        if default_library_path.exists():
            # 파일 이동
            import shutil
            shutil.move(str(default_library_path), str(target_path))
            print(f"✓ {library_name}.json을 objectfile 디렉토리로 이동")
        else:
            print(f"⚠ {library_name}.json 파일을 찾을 수 없습니다")
    
    def analyze_all_libraries(self) -> Dict[str, str]:
        """solfile의 모든 .sol 파일들을 분석"""
        print("=== 전체 라이브러리 분석 시작 ===")
        
        sol_files = self.scan_sol_files()
        analyzed_libraries = {}
        
        for sol_file in sol_files:
            try:
                library_name = self.analyze_library_file(sol_file)
                analyzed_libraries[sol_file.name] = library_name
                print(f"✓ {sol_file.name} → {library_name}")
            except Exception as e:
                print(f"✗ {sol_file.name} 분석 실패: {e}")
                continue
        
        print(f"\n=== 분석 완료: {len(analyzed_libraries)}/{len(sol_files)}개 성공 ===")
        return analyzed_libraries
    
    def list_object_files(self):
        """objectfile 디렉토리의 파일들 목록"""
        print("\n=== Object Files ===")
        object_files = list(self.objectfile_dir.glob("*.json"))
        
        if object_files:
            print(f"저장된 라이브러리 객체: {len(object_files)}개")
            for obj_file in object_files:
                print(f"  - {obj_file.name}")
                # 파일 크기도 표시
                size_kb = obj_file.stat().st_size / 1024
                print(f"    크기: {size_kb:.1f} KB")
        else:
            print("저장된 객체 파일이 없습니다.")
    
    def test_library_loading(self, library_name: str):
        """라이브러리 로딩 테스트"""
        print(f"\n=== {library_name} 로딩 테스트 ===")
        
        # ContractAnalyzer의 라이브러리 경로를 objectfile로 변경
        original_lib_dir = None
        if hasattr(self.analyzer, 'libraries_dir'):
            original_lib_dir = self.analyzer.libraries_dir
        
        # 임시로 objectfile 디렉토리로 변경
        self.analyzer.libraries_dir = self.objectfile_dir
        
        try:
            loaded_library = self.analyzer.load_library_cfg(library_name)
            if loaded_library:
                print("✓ 라이브러리 로드 성공")
                print(f"  - 라이브러리 이름: {loaded_library.contract_name}")
                if hasattr(loaded_library, 'functions'):
                    print(f"  - 함수 개수: {len(loaded_library.functions)}")
                    print(f"  - 함수 목록: {list(loaded_library.functions.keys())}")
            else:
                print("✗ 라이브러리 로드 실패")
        except Exception as e:
            print(f"✗ 라이브러리 로드 중 오류: {e}")
        finally:
            # 원래 경로로 복원
            if original_lib_dir:
                self.analyzer.libraries_dir = original_lib_dir
    
    def test_using_directive_simulation(self):
        """using directive 시뮬레이션 테스트"""
        print("\n=== Using Directive 시뮬레이션 ===")
        
        # 테스트용 컨트랙트 생성
        test_contract_source = """
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
        
        try:
            # 컨트랙트 분석
            from Analyzer.ContractParser import ContractParser
            parser = ContractParser()
            chunks = parser.parse_contract(test_contract_source)
            
            print(f"✓ 테스트 컨트랙트 파싱 완료 ({len(chunks)}개 청크)")
            
            # using directive 찾기
            using_directives = [chunk for chunk in chunks if chunk.chunk_type == "using_directive"]
            print(f"✓ using directive 발견: {len(using_directives)}개")
            
            for directive in using_directives:
                if directive.context_info:
                    lib_name = directive.context_info.get("library_name")
                    target_type = directive.context_info.get("target_type")
                    print(f"  - using {lib_name} for {target_type}")
                    
                    # 해당 라이브러리 로딩 테스트
                    self.test_library_loading(lib_name)
            
        except Exception as e:
            print(f"✗ using directive 시뮬레이션 실패: {e}")

def main():
    """메인 함수"""
    print("라이브러리 관리 시스템 시작\n")
    
    manager = LibraryManager()
    
    # 1. 모든 라이브러리 분석
    analyzed_libs = manager.analyze_all_libraries()
    
    # 2. 저장된 객체 파일들 확인
    manager.list_object_files()
    
    # 3. 각 라이브러리 로딩 테스트
    for sol_file, lib_name in analyzed_libs.items():
        manager.test_library_loading(lib_name)
    
    # 4. using directive 시뮬레이션
    manager.test_using_directive_simulation()
    
    print("\n라이브러리 관리 시스템 테스트 완료")

if __name__ == "__main__":
    main()