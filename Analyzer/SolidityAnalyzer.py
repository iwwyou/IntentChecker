# Analyzer/SolidityAnalyzer.py
"""
Solidity 소스 코드의 최상위 분석기.

소스 코드 저장(full_code_lines, full_code, line_info)을 담당하고,
file-level 구조(struct, type alias)를 처리한다.
Contract-level 분석은 ContractAnalyzer에 위임한다.
"""
from Domain.Type import SolType


class SolidityAnalyzer:

    def __init__(self):
        # ── Source storage ──────────────────────────────────────
        self.full_code = None
        self.full_code_lines = {}   # line_no -> code string
        self.line_info = {}         # line_no -> {"open": int, "close": int, "cfg_nodes": []}

        # ── File-level definitions ─────────────────────────────
        self.file_level_structs = {}    # {"StructName": {field_name: SolType, ...}}
        self.type_aliases = {}          # {"TypeName": "underlyingElementaryType"}

        # ── File-level context tracking ────────────────────────
        self._current_file_struct = None  # 현재 열린 file-level struct 이름

        # ── ContractAnalyzer 생성 (self 참조 전달) ──────────────
        from Analyzer.ContractAnalyzer import ContractAnalyzer
        self.contract_analyzer = ContractAnalyzer(solidity_analyzer=self)

    # ── Main entry point ────────────────────────────────────────
    def update_code(self, start_line: int, end_line: int, new_code: str,
                    event: str, close_before: bool = False):
        """소스 코드 업데이트의 진입점.
        file-level 구조는 자체 context 설정, contract-level은 ContractAnalyzer에 위임."""
        # 항상 ContractAnalyzer에 위임 (소스 관리 + context 분석)
        self.contract_analyzer.update_code(start_line, end_line, new_code,
                                           event, close_before)

    # ── File-level process 메서드 ──────────────────────────────
    def process_file_level_struct_definition(self, struct_name: str):
        """file-level struct 정의 시작"""
        self._current_file_struct = struct_name
        self.file_level_structs[struct_name] = {}

    def process_file_level_struct_member(self, var_name: str, type_obj: SolType):
        """file-level struct member 추가"""
        if self._current_file_struct:
            self.file_level_structs[self._current_file_struct][var_name] = type_obj

    def end_file_level_struct(self):
        """file-level struct 정의 종료"""
        self._current_file_struct = None

    def process_type_alias(self, alias_name: str, underlying_type: str):
        """user-defined value type alias 등록 (e.g., type Fixed18 is int256)"""
        self.type_aliases[alias_name] = underlying_type

    # ── File-level 조회 API (ContractAnalyzer/Visitor에서 호출) ──
    def get_file_level_struct(self, name: str) -> dict | None:
        """file-level struct 정의 조회"""
        return self.file_level_structs.get(name)

    def resolve_type(self, type_name: str) -> str | None:
        """user-defined type alias를 underlying type으로 resolve.
        alias가 없으면 None 반환."""
        return self.type_aliases.get(type_name)
