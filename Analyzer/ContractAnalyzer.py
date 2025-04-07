# SolidityGuardian/Analyzers/ContractAnalyzer.py
from Utils.Interval import *
from Utils.cfg import *
from Utils.util import *
from solcx import compile_source, install_solc
from collections import deque
import solcx
import re
import copy


class ContractAnalyzer:
    def __init__(self):
        self.full_code = None
        self.full_code_lines = {} # 라인별 코드를 저장하는 딕셔너리
        self.brace_count = {} # 각 라인에서 `{`와 `}`의 개수를 저장하는 딕셔너리

        self.current_start_line = None
        self.current_end_line = None

        self.current_context_type = None
        self.current_target_contract = None
        self.current_target_function = None
        self.current_target_function_cfg = None
        self.current_target_struct = None

        # for Multiple Contract
        self.contract_cfgs = {} # name -> CFG

        self.analysis_results = None

    """
    Prev analysis part
    """

    def update_code(self, start_line, end_line, new_code):
        """
        1) 기존 로직 그대로 유지: 라인들을 self.full_code_lines에 삽입/갱신
        2) 만약 new_code가 "@during-execution" 주석이라면, 기존 라인을 수정 (append) 하여 코드가 '밀리지' 않도록 처리
        """

        self.current_start_line = start_line
        self.current_end_line = end_line

        lines = new_code.split('\n')

        # STEP A) 먼저, 'lines'가 딱 한 줄이고, 해당 줄이 '@during-execution' 주석인지 검사
        #        (여러 줄 주석이 들어오면 아래 별도 처리 필요)
        is_single_line = (len(lines) == 1)
        stripped_line = lines[0].strip() if is_single_line else None

        # 체크: 이 라인이 '@during-execution'인지
        # (혹은 startswith("// @during-execution")로 더 정확히 해도 됨)
        is_during_execution_comment = False
        if is_single_line and stripped_line.startswith('// @during-execution'):
            is_during_execution_comment = True

        if is_during_execution_comment:
            # --- STEP B) 인라인 주석을 기존 line 끝에 추가 ---

            # 1) 기존 라인 가져오기
            #    만약 기존에 해당 line이 없으면? (ex: new code appended at end) -> fallback?
            if start_line in self.full_code_lines:
                original = self.full_code_lines[start_line]

                # 2) 혹시 이미 세미콜론 등 공백이 있는지 확인 후
                #    (원하는 대로 spacing/줄바꿈을 조정)
                updated_line = original.rstrip() + " " + new_code.lstrip()
                # -> 이렇게 하면 "int256 _magCorrection = toInt256(...);" 뒤에
                #    "// @during-execution ..."을 이어붙임

                self.full_code_lines[start_line] = updated_line
                # brace_count 갱신
                self.update_brace_count(start_line, updated_line)

            # 3) full_code 다시 합치기
            self.full_code = '\n'.join(
                [self.full_code_lines[line_no] for line_no in sorted(self.full_code_lines.keys())]
            )

        # --- STEP C) 그 외의 경우(기존 로직) ---
        # 새 라인들 삽입/밀기 등
        if not self.full_code_lines:  # initialize
            for i, line_no in enumerate(range(start_line, end_line + 1)):
                self.full_code_lines[line_no] = lines[i]
                self.update_brace_count(line_no, lines[i])
        else:
            offset = end_line - start_line + 1

            # 1. 기존 라인 뒤로 밀기
            keys_to_shift = sorted(
                [line_no for line_no in self.full_code_lines.keys() if line_no >= start_line],
                reverse=True
            )
            for old_line_no in keys_to_shift:
                self.full_code_lines[old_line_no + offset] = self.full_code_lines.pop(old_line_no)
                self.update_brace_count(old_line_no + offset, self.full_code_lines[old_line_no + offset])

            # 2. 새로운 코드 라인 삽입
            for i, line_no in enumerate(range(start_line, end_line + 1)):
                self.full_code_lines[line_no] = lines[i]
                self.update_brace_count(line_no, lines[i])

        # 3. full_code 재구성
        self.full_code = '\n'.join(
            [self.full_code_lines[line_no] for line_no in sorted(self.full_code_lines.keys())]
        )

        # 4. analyze_context
        if new_code != "\n":
            self.analyze_context(start_line, new_code)

        self.compile_check()

    def compile_check(self):
        try:
            install_solc('0.8.0')  # 필요한 Solidity 컴파일러 버전을 설치합니다.
            compile_source(self.full_code)
        except solcx.exceptions.SolcError as e:
            print("Solidity 컴파일 오류: ", e)
        except Exception as e:
            print("예상치 못한 오류: ", e)

    def update_brace_count(self, line_number, code):
        open_braces = code.count('{')
        close_braces = code.count('}')

        # brace_count 업데이트
        self.brace_count[line_number] = {
            'open': open_braces,
            'close': close_braces,
            'cfg_node': None
        }

    def analyze_context(self, start_line, new_code):
        stripped_code = new_code.strip()

        # (1) 만약 이 라인이 "@pre-execution-global", "@pre-execution-state", 등 Intent가 들어간 주석인지 확인
        if stripped_code.startswith('// @'):
            self.current_context_type = "intentUnit"
            self.current_target_contract = self.find_contract_context(start_line)
            if 'pre-execution-global' in stripped_code :
                return
            self.current_target_function = self.find_function_context(start_line)
            return  # 이 함수 종료

        # 매 분석마다 초기화
        self.current_context_type = None
        self.current_target_contract = None
        self.current_target_function = None
        self.current_target_struct = None

        # 새로 추가된 코드 블록의 컨텍스트를 분석
        if stripped_code.endswith(';'):
            if 'while' in stripped_code :
                self.current_context_type = "doWhileWhile"
                pass

            parent_context = self.find_parent_context(start_line)
            if parent_context == "contract" : # 시작 규칙 : interactiveSourceUnit
                self.current_context_type = "stateVariableDeclaration"
                self.current_target_contract = self.find_contract_context(start_line)
            elif parent_context == "struct" : # 시작 규칙 : interactiveStructUnit
                self.current_context_type = "structMember"
                self.current_target_contract = self.find_contract_context(start_line)
                self.current_target_struct = self.find_struct_context(start_line)
            else : # constructor, function, --- # 시작 규칙 : interactiveBlockUnit
                self.current_context_type = "simpleStatement"
                self.current_target_contract = self.find_contract_context(start_line)
                self.current_target_function = self.find_function_context(start_line)

        elif ',' in stripped_code:
            # 함수 정의인지 확인 (괄호 열고 닫힌 경우는 함수 파라미터로 가정)
            if '(' in stripped_code and ')' in stripped_code:
                self.current_context_type = "functionDefinition"
                self.current_target_contract = self.find_contract_context(start_line)
                self.current_target_function = self.find_function_context(start_line)

            # enum인지 확인
            else:
                parent_context = self.find_parent_context(start_line)
                if parent_context == "enum":
                    self.current_context_type = "enumMember"
                    self.current_target_contract = self.find_contract_context(start_line)

        elif '{' in stripped_code: # definition 및 block 관련
            self.current_context_type = self.determine_top_level_context(new_code)

            if self.current_context_type == "contract" :
                return

            # 수정 필요할수도 있음
            self.current_target_contract = self.find_contract_context(start_line)
            self.current_target_function = self.find_function_context(start_line)

        # 최종적으로 context가 제대로 파악되지 않은 경우 기본값 처리
        if not self.current_target_contract:
            raise ValueError(f"Contract context not found for line {start_line}")
        if self.current_context_type == "simpleStatement" and not self.current_target_function:
            raise ValueError(f"Function context not found for simple statement at line {start_line}")

    def find_parent_context(self, line_number):
        close_brace_count = 0

        # 위로 거슬러 올라가면서 `{`와 `}`의 짝을 찾기
        for line in range(line_number - 1, 0, -1):
            brace_info = self.brace_count.get(line, {'open': 0, 'close': 0, 'cfg_node': None})
            open_braces = brace_info['open']
            close_braces = brace_info['close']

            if close_brace_count > 0:
                close_brace_count -= open_braces
                if close_brace_count <= 0:
                    close_brace_count = 0
            else:
                if open_braces > 0:
                    return self.determine_top_level_context(self.full_code_lines[line])
                close_brace_count += close_braces

        return "unknown"

    def find_contract_context(self, line_number):
        # 위로 거슬러 올라가면서 해당 라인이 속한 컨트랙트를 찾습니다.
        for line in range(line_number, 0, -1):
            brace_info = self.brace_count.get(line, {'open': 0, 'close': 0, 'cfg_node': None})
            if brace_info['open'] > 0 and brace_info['cfg_node']:
                context_type = self.determine_top_level_context(self.full_code_lines[line])
                if context_type == "contract":
                    return self.full_code_lines[line].split()[1]  # contract 이름 반환
        return None

    def find_function_context(self, line_number):
        # 위로 거슬러 올라가면서 해당 라인이 속한 함수를 찾습니다.
        for line in range(line_number, 0, -1):
            brace_info = self.brace_count.get(line, {'open': 0, 'close': 0, 'cfg_node': None})
            if brace_info['open'] > 0 and brace_info['cfg_node']:
                context_type = self.determine_top_level_context(self.full_code_lines[line])
                if context_type == "function":
                    # 함수 이름 뒤에 붙은 '('를 기준으로 함수 이름만 추출
                    function_declaration = self.full_code_lines[line]
                    function_name = function_declaration.split()[1]  # 첫 번째는 함수 선언, 두 번째는 함수 이름 포함
                    function_name = function_name.split('(')[0]  # 함수 이름만 추출
                    return function_name
        return None

    def find_struct_context(self, line_number):
        # 위로 거슬러 올라가면서 해당 라인이 속한 함수를 찾습니다.
        for line in range(line_number, 0, -1):
            brace_info = self.brace_count.get(line, {'open': 0, 'close': 0, 'cfg_node': None})
            if brace_info['open'] > 0 and brace_info['cfg_node']:
                context_type = self.determine_top_level_context(self.full_code_lines[line])
                if context_type == "struct":
                    return self.full_code_lines[line].split()[1]

    def determine_top_level_context(self, code_line):
        try:
            # 코드 라인의 내용에 따라 최상위 컨텍스트를 결정
            stripped_code = code_line.strip()

            if stripped_code.startswith("contract"):
                return "contract"
            elif stripped_code.startswith("interface"):
                return "interface"
            elif stripped_code.startswith("library"):
                return "library"
            elif stripped_code.startswith("function"):
                return "function"
            elif stripped_code.startswith("constructor"):
                return "constructor"
            elif stripped_code.startswith("fallback"):
                return "fallback"
            elif stripped_code.startswith("receive"):
                return "receive"
            elif stripped_code.startswith("modifier"):
                return "modifier"
            elif stripped_code.startswith("struct"):
                return "struct"
            elif stripped_code.startswith("enum"):
                return "enum"
            elif stripped_code.startswith("event"):
                return "event"
            elif stripped_code.startswith("if"):
                return "if"
            elif stripped_code.startswith("else if"):
                return "else_if"
            elif stripped_code.startswith("else"):
                return "else"
            elif stripped_code.startswith("for"):
                return "for"
            elif stripped_code.startswith("while"):
                return "while"
            elif stripped_code.startswith("do"):
                return "do_while"
            elif stripped_code.startswith("try"):
                return "try"
            elif stripped_code.startswith("catch"):
                return "catch"
            elif stripped_code.startswith("assembly"):
                return "assembly"
            else:
                raise ValueError(f"Unknown context type for line: {code_line}")

        except ValueError as e:
            print(f"Error: {e}")
            return "unknown"

    def get_full_code(self):
        return self.full_code

    def get_current_context_type(self):
        return self.current_context_type

    """
    cfg part    
    """

    def make_contract_cfg(self, contract_name):
        if contract_name not in self.contract_cfgs:
            # 새로운 ContractCFG 생성
            self.contract_cfgs[contract_name] = ContractCFG(contract_name)
            # CFG 노드를 brace_count에 저장 (cfg_node만 업데이트)
            self.brace_count[self.current_start_line]['cfg_node'] = self.contract_cfgs[contract_name]

    def get_contract_cfg(self, contract_name):
        return self.contract_cfgs.get(contract_name)

    # for interactiveEnumDefinition in Solidity.g4
    def process_enum_definition(self, enum_name):
        contract_cfg = self.contract_cfgs.get(self.current_target_contract)

        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # 새로운 EnumDefinition 객체 생성
        enum_def = EnumDefinition(enum_name)
        contract_cfg.define_enum(enum_name, enum_def)

        # brace_count 업데이트
        self.brace_count[self.current_start_line]['cfg_node'] = enum_def

    def process_enum_item(self, items):
        # 현재 타겟 컨트랙트의 CFG 가져오기
        contract_cfg = self.contract_cfgs.get(self.current_target_contract)

        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # brace_count에서 가장 최근의 enum 정의를 찾습니다.
        enum_def = None
        for line in reversed(range(self.current_start_line + 1)):
            context = self.brace_count.get(line)
            if context and 'cfg_node' in context and isinstance(context['cfg_node'], EnumDefinition):
                enum_def = context['cfg_node']
                break

        if enum_def is not None:
            # EnumDefinition에 아이템 추가
            for item in items:
                enum_def.add_member(item)
        else:
            raise ValueError(f"Unable to find EnumDefinition context for line {self.current_start_line}")

    # for interactiveStructDefinition in Solidity.g4
    def process_struct_definition(self, struct_name):
        contract_cfg = self.contract_cfgs[self.current_target_contract]

        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        struct_def = StructDefinition(struct_name=struct_name)

        contract_cfg.define_struct(struct_def)

        # 10. contract_cfg를 contract_cfgs에 반영
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        # brace_count 업데이트
        self.brace_count[self.current_start_line]['structs'] = contract_cfg.structs

    def process_struct_member(self, var_name, type_obj):
        # 1. 현재 타겟 컨트랙트의 CFG를 가져옴
        contract_cfg = self.contract_cfgs[self.current_target_contract]
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # 2. 현재 타겟 구조체를 확인하고 멤버 추가
        if not self.current_target_struct:
            raise ValueError("No target struct to add members to.")

        contract_cfg.add_struct_member(self.current_target_struct, var_name, type_obj)

        # 10. contract_cfg를 contract_cfgs에 반영
        self.contract_cfgs[self.current_target_contract] = contract_cfg

    def process_state_variable(self, variable_obj, init_expr=None):
        # 1. 현재 타겟 컨트랙트의 CFG 가져오기
        contract_cfg = self.contract_cfgs[self.current_target_contract]

        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # 2. abstract interpretation 수행
        interval_result = None

        # 우변 표현식을 저장하기 위해 init_expr를 확인
        if init_expr is None: # 초기화가 없으면
            if isinstance(variable_obj, ArrayVariable) :
                if variable_obj.typeInfo.arrayBaseType.startswith("int") :
                    variable_obj.initialize_elements(IntegerInterval.bottom())
                elif variable_obj.typeInfo.arrayBaseType.startswith("uint") :
                    variable_obj.initialize_elements(UnsignedIntegerInterval.bottom())
                elif variable_obj.typeInfo.arrayBaseType.startswith("bool") :
                    variable_obj.initialize_elements(BoolInterval.bottom())
                elif variable_obj.typeInfo.arrayBaseType in ["address", "address payable", "string", "bytes", "Byte", "Fixed", "Ufixed"] :
                    variable_obj.initialize_elements_of_not_abstracted_type(variable_obj.identifier)
            elif isinstance(variable_obj, StructVariable) :
                if variable_obj.struct_type in contract_cfg.structDefs.keys() :
                    struct_def = contract_cfg.structDefs[variable_obj.struct_type]
                    variable_obj.initialize_struct(struct_def)
                else :
                    ValueError(f"This struct def {variable_obj.struct_type} is undefined")
            elif isinstance(variable_obj, MappingVariable) :
                pass
            elif isinstance(variable_obj,EnumVariable) :
                pass
            elif variable_obj.typeCategory == "elementary" :
                if variable_obj.elementaryTypeName.startswith("int", "uint", "bool") :
                    variable_obj.value = self.calculate_default_interval(variable_obj.elementaryTypeName)
                elif variable_obj.elementaryTypeName in ["address", "address payable", "string", "bytes", "Byte", "Fixed", "Ufixed"] :
                    variable_obj.value = str('symbol' + variable_obj.identifier)
        else : # 초기화 식이 있으면
            if isinstance(variable_obj, ArrayVariable) :
                inlineArrayValues = self.evaluate_expression(init_expr, contract_cfg.state_variable_node.variables, None)

                for value in inlineArrayValues :
                    variable_obj.elements.append(value)
            elif isinstance(variable_obj, StructVariable) : # 관련된 경우 없을듯
                pass
            elif isinstance(variable_obj, MappingVariable) : # 관련된 경우 없을 듯
                pass
            elif variable_obj.typeCategory == "elementary" :
                variable_obj.value = self.evaluate_expression(init_expr, contract_cfg.state_variable_node.variables, None)

        # 4. 상태 변수를 ContractCFG에 추가
        contract_cfg.add_state_variable(variable_obj, expr=init_expr)

        # 5. ContractCFG에 있는 모든 FunctionCFG에 상태 변수 추가
        for function_cfg in contract_cfg.functions.values():
            function_cfg.add_related_variable(variable_obj.identifier, variable_obj)

        # 6. contract_cfg를 contract_cfgs에 반영
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        # 7. brace_count 업데이트
        self.brace_count[self.current_start_line]['cfg_node'] = contract_cfg.state_variable_node

    def process_constant_variable(self, variable_obj, init_expr):
        # 1. 현재 타겟 컨트랙트의 CFG 가져오기
        contract_cfg = self.contract_cfgs[self.current_target_contract]

        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # 2. abstract interpretation 수행 (상수이므로 반드시 초기화 식이 있어야 함)
        if init_expr:
            interval_result = self.evaluate_expression(init_expr)
            if interval_result is not None:
                variable_obj.value = interval_result
            else:
                raise ValueError(f"Unable to evaluate constant expression for {variable_obj.identifier}")
        else:
            raise ValueError(f"Constant variable {variable_obj.identifier} must have an initializer.")

        # 4. 상수임을 표시
        variable_obj.isConstant = True

        # 3. 상태 변수를 ContractCFG에 추가
        contract_cfg.add_state_variable(variable_obj.identifier, variable_obj)

        # 5. brace_count 업데이트
        self.brace_count[self.current_start_line]['cfg_node'] = contract_cfg.state_variable_node

    def process_modifier_definition(self, modifier_name, parameters):
        # 현재 컨텍스트에서 타겟 컨트랙트를 가져옴
        contract_cfg = self.contract_cfgs[self.current_target_contract]

        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # Modifier에 대한 FunctionCFG 생성
        modifier_cfg = FunctionCFG(function_type='modifier', function_name=modifier_name)

        # 파라미터가 있을 경우, 이를 FunctionCFG에 추가
        for var_name, var_type_info in parameters.items():
            modifier_cfg.add_related_variable(var_name, var_type_info)

        # 현재 state_variable_node에서 상태 변수를 가져와 related_variables에 추가
        if contract_cfg.state_variable_node:
            for var_name, var_info in contract_cfg.state_variable_node.variables.items():
                modifier_cfg.add_related_variable(var_name, var_info)

        # Modifier CFG를 ContractCFG에 추가
        contract_cfg.add_function_cfg(modifier_cfg)

        # 10. contract_cfg를 contract_cfgs에 반영
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        # brace_count 업데이트 (필요시)
        self.brace_count[self.current_start_line]['cfg_node'] = modifier_cfg.get_entry_node()

    def process_modifier_invocation(self, function_cfg, modifier_name):
        # 현재 타겟 컨트랙트의 CFG를 가져옴
        contract_cfg = self.contract_cfgs[self.current_target_contract]

        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # ContractCFG에서 modifier CFG를 가져옴
        modifier_cfg = contract_cfg.get_modifier_cfg(modifier_name)

        if not modifier_cfg:
            raise ValueError(f"Modifier {modifier_name} not found in contract {self.current_target_contract}")

        # Modifier를 function CFG에 통합 (entry와 exit 노드 연결)
        function_cfg.integrate_modifier(modifier_cfg)

        # function_cfg에 modifier 이름 추가
        function_cfg.modifiers[modifier_name] = modifier_cfg

        # 9. function_cfg 결과를 contract_cfg에 반영
        contract_cfg.functions[self.current_target_function] = function_cfg

        # 10. contract_cfg를 contract_cfgs에 반영
        self.contract_cfgs[self.current_target_contract] = contract_cfg

    def process_constructor_definition(self, constructor_name, parameters, modifiers):
        # 현재 컨텍스트에서 타겟 컨트랙트를 가져옴
        contract_cfg = self.contract_cfgs[self.current_target_contract]

        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # Constructor에 대한 FunctionCFG 생성
        constructor_cfg = FunctionCFG(function_type='constructor', function_name=constructor_name)

        # 파라미터가 있을 경우, 이를 FunctionCFG에 추가
        for variable in parameters:
            constructor_cfg.add_related_variable(variable)

        # Modifier가 있을 경우 이를 FunctionCFG에 추가
        for modifier_name in modifiers:
            self.process_modifier_invocation(constructor_cfg, modifier_name)

        # Constructor CFG를 ContractCFG에 추가
        contract_cfg.add_constructor_to_cfg(constructor_cfg)

        # 10. contract_cfg를 contract_cfgs에 반영
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        # 현재 state_variable_node에서 상태 변수를 가져와 related_variables에 추가
        if contract_cfg.state_variable_node:
            for var_name, var_info in contract_cfg.state_variable_node.variables.items():
                constructor_cfg.add_related_variable(var_name, var_info)

        self.brace_count[self.current_start_line]['cfg_node'] = constructor_cfg.get_entry_node()

    def process_function_definition(self, function_name, parameters, modifiers, returns):
        # 1. 현재 타겟 컨트랙트의 CFG를 가져옴
        contract_cfg = self.contract_cfgs[self.current_target_contract]
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # 2. 함수에 대한 FunctionCFG 생성
        function_cfg = FunctionCFG(function_type='function', function_name=function_name)

        # 3. 파라미터 처리
        for type_obj, var_name in parameters:
            variable_obj = None

            # 타입에 따라 적절한 변수 클래스를 생성
            if type_obj.typeCategory == 'array':
                # 배열 타입인 경우 ArrayVariable 생성
                variable_obj = ArrayVariable(
                    identifier=var_name,
                    base_type=type_obj.arrayBaseType,
                    array_length=type_obj.arrayLength,
                    scope="local"
                )

                baseType = type_obj.arrayBaseType

                # 배열 요소 초기화
                if baseType.startswith('int') :
                    length = int(baseType[3:]) if baseType != "int" else 256
                    variable_obj.initialize_elements(IntegerInterval.bottom(length))  # 기본 interval 설정
                elif baseType.startswith('uint') :
                    length = int(baseType[4:]) if baseType != "int" else 256
                    variable_obj.initialize_elements(UnsignedIntegerInterval.bottom(length))  # 기본 interval 설정
                elif baseType == 'bool' :
                    variable_obj.initialize_elements(BoolInterval.bottom())
                elif baseType in ["address", "address payable", "string", "bytes", "Byte", "Fixed", "Ufixed"] :
                    variable_obj.initialize_elements_of_not_abstracted_type(var_name)

            elif type_obj.typeCategory == 'struct':
                if type_obj.structTypeName in contract_cfg.structDefs :
                    struct_def = contract_cfg.structDefs[type_obj.structTypeName]

                    variable_obj = StructVariable(
                        identifier = var_name,
                        struct_type = type_obj.structTypeName,
                        socpe="local" # 이거 나중에 storage인지 memory인지 보고 고쳐야됨
                    )

                    variable_obj.initialize_struct(struct_def)

                else :
                    raise ValueError (f"This struct definition {type_obj.structTypeName} is not defined")
            elif type_obj.typeCategory == "elementary":
                # 기본 타입인 경우 Variables 객체 생성
                variable_obj = Variables(identifier=var_name, scope="local")
                variable_obj.typeInfo = type_obj  # SolType 객체를 typeInfo로 설정

                if type_obj.elementaryTypeName.startswith('int', 'uint', 'bool') :
                    variable_obj.value = self.calculate_default_interval(type_obj.elementaryTypeName)
                elif type_obj.elementaryTypeName in ["address", "address payable", "string", "bytes", "Byte", "Fixed", "Ufixed"] :
                    variable_obj.value = str("symbol" + var_name)

        # 4. Modifier 처리 및 CFG 통합
        for modifier_name in modifiers:
            self.process_modifier_invocation(function_cfg, modifier_name)

        # 5. 반환 타입 처리 (있다면)
        if returns:
            for variable in returns:
                function_cfg.add_related_variable(variable)

        # 현재 state_variable_node에서 상태 변수를 가져와 related_variables에 추가
        if contract_cfg.state_variable_node:
            for var_name, variable in contract_cfg.state_variable_node.variables.items():
                function_cfg.add_related_variable(variable)

        # 9. function_cfg 결과를 contract_cfg에 반영
        contract_cfg.functions[function_name] = function_cfg

        # 10. contract_cfg를 contract_cfgs에 반영
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        # 7. brace_count에 CFG 노드 정보 업데이트 (함수의 시작 라인 정보 사용)
        self.brace_count[self.current_start_line]['cfg_node'] = function_cfg.get_entry_node()

    def process_variable_declaration(self, variable_obj, init_expr=None):
        # 1. 현재 타겟 컨트랙트의 CFG 가져오기
        contract_cfg = self.contract_cfgs[self.current_target_contract]
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # 2. 현재 타겟 함수의 CFG 가져오기
        self.current_target_function_cfg = contract_cfg.get_function_cfg(self.current_target_function)
        if not self.current_target_function_cfg:
            raise ValueError("No active function to add variables to.")

        # 3. 현재 블록의 CFG 노드 가져오기
        current_block = self.get_current_block()

        # 4. 변수 선언 시 초기화 값이 없는 경우 처리
        if init_expr is None:
            # 초기화 값이 없는 경우 기본 Interval 설정
            interval = self.calculate_default_interval(variable_obj.typeInfo.elementaryTypeName)
            variable_obj.value = interval  # 기본 interval 설정

            # 우변 표현식 생성 (리터럴 값)
            expr = Expression(literal=interval)
            # Statement에 우변 표현식과 평가된 Interval 값을 함께 저장
            current_block.add_assign_statement(variable_obj, expr)

        else:
            if init_expr.context == 'FunctionCallContext':
                return_var = self.function_abstract_interpretation(init_expr)

        # 11. current_block을 function CFG에 반영
        self.current_target_function_cfg.update_block(current_block)  # 변경된 블록을 반영

        # 12. function_cfg 결과를 contract_cfg에 반영
        contract_cfg.functions[self.current_target_function] = self.current_target_function_cfg

        # 13. contract_cfg를 contract_cfgs에 반영
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        # 14. brace_count에 CFG 노드 정보 업데이트 (함수의 시작 라인 정보 사용)
        self.brace_count[self.current_start_line]['cfg_node'] = current_block

        self.current_target_function_cfg = None

    def process_compound_assignment(self, left_interval, right_interval, operator):
        if operator == '+=':
            return left_interval.add(right_interval)
        elif operator == '-=':
            return left_interval.subtract(right_interval)
        elif operator == '*=':
            return left_interval.multiply(right_interval)
        elif operator == '/=':
            return left_interval.divide(right_interval)
        elif operator == '%=':
            return left_interval.modulo(right_interval)
        elif operator == '|=':
            return left_interval.bitwise_or(right_interval)
        elif operator == '^=':
            return left_interval.bitwise_xor(right_interval)
        elif operator == '&=':
            return left_interval.bitwise_and(right_interval)
        elif operator in ['<<=', '>>=', '>>>=']:
            # '<<=', '>>=' 등에서 '=' 제거 후 처리
            return left_interval.shift(right_interval, operator[:-1])
        else:
            raise ValueError(f"Unsupported operator '{operator}' in compound assignment")

    def process_assignment_expression(self, expr):
        # 1. 현재 타겟 컨트랙트의 CFG 가져오기
        contract_cfg = self.contract_cfgs[self.current_target_contract]
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # 2. 현재 타겟 함수의 CFG 가져오기
        self.current_target_function_cfg = contract_cfg.get_function_cfg(self.current_target_function)
        if not self.current_target_function_cfg:
            raise ValueError("No active function to add variables to.")

        # 3. 현재 블록의 CFG 노드 가져오기
        current_block = self.get_current_block()

        # 4. 좌변 변수 정보 가져오기
        variable_obj, var_name, element_var, key_or_index = self.get_variable_from_expression(expr.left,
                                                                                              current_block.variables)
        if not variable_obj:
            raise ValueError(f"Variable '{var_name}' not found in current CFG node.")

        # 5. 우변 표현식 평가 (좌변 변수의 타입과 우변 context에 따른 분기)
        right_expr = expr.right  # 미리 선언하여 모든 분기에서 참조 가능하도록 함

        if right_expr.context == 'FunctionCallContext':
            return_var = self.function_abstract_interpretation(right_expr)

        # 6. 좌변 변수의 타입에 따른 처리
        if isinstance(variable_obj, MappingVariable):
            # 좌변이 매핑 변수인 경우
            mapping_var = variable_obj
            if key_or_index is not None:
                key_str = str(key_or_index)

                right_value = self.evaluate_expression(right_expr, current_block.variables)  # 우변 표현식
                # 복합 할당 연산자 처리
                if expr.operator != '=':
                    new_value = self.process_compound_assignment(element_var.value, right_value, expr.operator)
                    variable_obj.mapping[key_or_index] = new_value
                else:
                    variable_obj.mapping[key_or_index] = right_value

                # Statement에 우변 표현식과 평가된 값 저장
                current_block.add_mapping_assign_statement(mapping_var, expr.left, right_expr, operator=expr.operator)
            else:
                raise ValueError(f"Cannot assign value directly to mapping variable '{variable_obj.identifier}'")

        elif isinstance(variable_obj, ArrayVariable):
            # 좌변이 배열인 경우
            if right_expr.context == 'InlineArrayExpressionContext':
                # 우변이 배열 초기화 표현식인 경우
                intervals = self.evaluate_array_expression(right_expr, variables=current_block.variables)
                variable_obj.elements = []
                for idx, interval in enumerate(intervals):
                    elem_identifier = f"{variable_obj.identifier}[{idx}]"
                    elem_var = Variables(
                        identifier=elem_identifier,
                        value=interval,
                        isConstant=False,
                        scope=variable_obj.scope
                    )
                    elem_var.typeInfo = variable_obj.typeInfo.arrayBaseType
                    variable_obj.elements.append(elem_var)
                # Statement에 우변 표현식과 평가된 값 저장
                current_block.add_array_assign_statement(variable_obj, right_expr)
            elif right_expr.context == 'IndexAccessContext':
                # 우변이 배열의 인덱스 접근인 경우
                result = self.evaluate_array_expression(right_expr, variables=current_block.variables)
                right_interval = result if not isinstance(result, list) else result[0]

                # 복합 할당 연산자 처리
                if expr.operator != '=':
                    new_elements = []
                    for elem in variable_obj.elements:
                        new_interval = self.process_compound_assignment(elem.value, right_interval, expr.operator)
                        elem.value = new_interval
                        new_elements.append(elem)
                    # Statement에 우변 표현식과 평가된 값 저장
                    current_block.add_array_assign_statement(variable_obj, right_expr)
                else:
                    for elem in variable_obj.elements:
                        elem.value = right_interval
                    # Statement에 우변 표현식과 평가된 값 저장
                    current_block.add_array_assign_statement(variable_obj, right_expr)
            elif right_expr.context == 'MemberAccessContext':
                # 우변이 MemberAccess인 경우 (배열의 length 등)
                result = self.evaluate_array_expression(right_expr, variables=current_block.variables)
                right_interval = result

                # 복합 할당 연산자 처리
                if expr.operator != '=':
                    new_elements = []
                    for elem in variable_obj.elements:
                        new_interval = self.process_compound_assignment(elem.value, right_interval, expr.operator)
                        elem.value = new_interval
                        new_elements.append(elem)
                    current_block.add_array_assign_statement(variable_obj, right_expr)
                else:
                    for elem in variable_obj.elements:
                        elem.value = right_interval
                    current_block.add_array_assign_statement(variable_obj, right_expr)
            else:
                # 일반 배열 처리
                intervals = self.evaluate_array_expression(right_expr, variables=current_block.variables)
                variable_obj.elements = []
                for idx, interval in enumerate(intervals):
                    elem_identifier = f"{variable_obj.identifier}[{idx}]"
                    elem_var = Variables(
                        identifier=elem_identifier,
                        value=interval,
                        isConstant=False,
                        scope=variable_obj.scope
                    )
                    elem_var.typeInfo = variable_obj.typeInfo.arrayBaseType
                    variable_obj.elements.append(elem_var)
                current_block.add_array_assign_statement(variable_obj, right_expr)

        elif isinstance(variable_obj, EnumVariable):
            # 좌변이 EnumVariable인 경우
            # 우변 표현식을 평가하여 Enum 값 설정
            right_interval = self.evaluate_enum_expression(right_expr, variables=current_block.variables)
            if isinstance(right_interval, IntegerInterval):
                enum_value = right_interval.min_value
                # EnumDefinition에서 해당 값의 멤버를 찾습니다.
                enum_def = self.contract_cfgs[self.current_target_contract].enums.get(
                    variable_obj.typeInfo.enumTypeName)
                if enum_def:
                    if 0 <= enum_value < len(enum_def.members):
                        member_name = enum_def.members[enum_value]
                        variable_obj.set_member_value(member_name)
                        variable_obj.value = enum_value
                        # Statement에 우변 표현식과 평가된 값 저장
                        current_block.add_assign_statement(variable_obj, right_expr)
                    else:
                        raise ValueError(
                            f"Enum value '{enum_value}' is out of range for enum '{variable_obj.typeInfo.enumTypeName}'.")
                else:
                    raise ValueError(f"Enum '{variable_obj.typeInfo.enumTypeName}' is not defined.")
            else:
                raise ValueError("Assigned value to EnumVariable must be an integer interval.")

        elif isinstance(variable_obj, StructVariable):
            # 좌변이 구조체인 경우
            if right_expr.context == 'MemberAccessContext':
                # 우변이 구조체 멤버 접근인 경우
                right_member_intervals = self.evaluate_struct_expression(right_expr, variables=current_block.variables)
                # 복합 할당 연산자 처리
                if expr.operator != '=':
                    new_members = {}
                    for member_name, right_interval in right_member_intervals.items():
                        if member_name in variable_obj.members:
                            member_var = variable_obj.members[member_name]
                            new_interval = self.process_compound_assignment(member_var.value, right_interval,
                                                                            expr.operator)
                            member_var.value = new_interval
                            new_members[member_name] = member_var
                        else:
                            raise ValueError(f"Struct member '{member_name}' not found in '{variable_obj.identifier}'")
                    current_block.add_struct_assign_statement(variable_obj, right_expr)
                else:
                    for member_name, right_interval in right_member_intervals.items():
                        if member_name in variable_obj.members:
                            member_var = variable_obj.members[member_name]
                            member_var.value = right_interval
                    current_block.add_struct_assign_statement(variable_obj, right_expr)
            else:
                # 일반 구조체 처리
                right_member_intervals = self.evaluate_struct_expression(right_expr, variables=current_block.variables)
                variable_obj.members = {}
                for member_name, interval in right_member_intervals.items():
                    member_identifier = f"{variable_obj.identifier}.{member_name}"
                    member_var = Variables(
                        identifier=member_identifier,
                        value=interval,
                        isConstant=False,
                        scope=variable_obj.scope
                    )
                    member_var.typeInfo = variable_obj.typeInfo.structType.members[member_name]
                    variable_obj.members[member_name] = member_var
                current_block.add_struct_assign_statement(variable_obj, right_expr)

        else:
            # 좌변이 일반 변수인 경우
            if right_expr.context == 'IndexAccessContext':
                # 우변이 배열 인덱스 접근인 경우
                right_interval = self.evaluate_array_expression(right_expr, variables=current_block.variables)
                # 복합 할당 연산자 처리
                if expr.operator != '=':
                    new_interval = self.process_compound_assignment(variable_obj.value, right_interval, expr.operator)
                    variable_obj.value = new_interval
                    current_block.add_assign_statement(variable_obj, right_expr)
                else:
                    variable_obj.value = right_interval
                    current_block.add_assign_statement(variable_obj, right_expr)
            elif right_expr.context == 'MemberAccessContext':
                # 우변이 MemberAccessContext인 경우
                base_identifier = right_expr.base.identifier
                base_variable = current_block.get_variable(base_identifier)
                if not base_variable:
                    base_variable = self.current_target_function_cfg.get_related_variable(base_identifier)
                if isinstance(base_variable, ArrayVariable):
                    # 배열의 멤버 접근 처리 (예: array.length)
                    right_interval = self.evaluate_array_expression(right_expr, variables=current_block.variables)
                    # 복합 할당 연산자 처리
                    if expr.operator != '=':
                        new_interval = self.process_compound_assignment(variable_obj.value, right_interval,
                                                                        expr.operator)
                        variable_obj.value = new_interval
                        current_block.add_assign_statement(variable_obj, right_expr)
                    else:
                        variable_obj.value = right_interval
                        current_block.add_assign_statement(variable_obj, right_expr)
                elif isinstance(base_variable, StructVariable):
                    # 구조체 멤버 접근 처리
                    right_interval = self.evaluate_struct_expression(right_expr, variables=current_block.variables)
                    # 복합 할당 연산자 처리
                    if expr.operator != '=':
                        new_interval = self.process_compound_assignment(variable_obj.value, right_interval,
                                                                        expr.operator)
                        variable_obj.value = new_interval
                        current_block.add_assign_statement(variable_obj, right_expr)
                    else:
                        variable_obj.value = right_interval
                        current_block.add_assign_statement(variable_obj, right_expr)
                else:
                    raise ValueError(f"Unsupported base type for MemberAccess: {type(base_variable)}")
            else:
                # 기본 표현식 처리
                right_interval = self.evaluate_expression(right_expr, variables=current_block.variables)
                # 복합 할당 연산자 처리
                if expr.operator != '=':
                    new_interval = self.process_compound_assignment(variable_obj.value, right_interval, expr.operator)
                    variable_obj.value = new_interval
                    current_block.add_assign_statement(variable_obj, right_expr)
                else:
                    variable_obj.value = right_interval
                    current_block.add_assign_statement(variable_obj, right_expr)

        # 6. 관련 변수 정보 추출 및 분석 결과 저장
        related_vars = self.extract_related_variables(right_expr, current_block, self.current_target_function_cfg)

        intervals_info = {
            "left": {
                "variable": var_name,
                "assigned_interval": [variable_obj.value.min_value,
                                      variable_obj.value.max_value] if variable_obj.value else None,
            },
            "right": []
        }

        for related_var in related_vars:
            if related_var.identifier not in current_block.variables:
                current_block.variables[related_var.identifier] = related_var

            intervals_info["right"].append({
                "variable": related_var.identifier,
                "interval": [related_var.value.min_value, related_var.value.max_value]
            })

        if current_block.is_while_body:
            vars = self.fixpoint(current_block)
            self.update_while_body(vars, current_block)

        # 8. 분석 결과 저장
        result = {
            "line": self.current_start_line,
            "variables_info": intervals_info
        }

        self.analysis_results = result

        # 9. current_block을 function CFG에 반영
        self.current_target_function_cfg.update_block(current_block)  # 변경된 블록을 반영

        # 10. function_cfg 결과를 contract_cfg에 반영
        contract_cfg.functions[self.current_target_function] = self.current_target_function_cfg

        # 11. contract_cfg를 contract_cfgs에 반영
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        # 12. brace_count에 CFG 노드 정보 업데이트 (함수의 시작 라인 정보 사용)
        self.brace_count[self.current_start_line]['cfg_node'] = current_block

        self.current_target_function_cfg = None

    def process_assignment_function_call(self, expr):
        # 1. 좌변 변수 이름 추출
        if expr.left.identifier:
            var_name = expr.left.identifier
        else:
            # 좌변이 복잡한 표현식인 경우 추가적인 처리가 필요함
            var_name = self.extract_variable_name(expr.left)

        # 2. 함수 호출 표현식 추출
        function_call_expr = expr.right

        # 3. 함수 이름과 인자 추출
        function_name = self.get_function_name(function_call_expr)
        function_args = function_call_expr.arguments if hasattr(function_call_expr, 'arguments') else []

        # 4. 함수의 리턴 타입과 Interval 추론
        return_interval = self.analyze_function_call(function_name, function_args)

        # 5. 변수의 타입 정보 설정 (함수의 리턴 타입 사용)
        var_type = return_interval.var_type if hasattr(return_interval, 'var_type') else 'int256'
        type_length = return_interval.type_length if hasattr(return_interval, 'type_length') else 256

        # 6. 현재 CFG 노드 가져오기
        current_block = self.get_current_block()

        # 7. CFG 노드에 할당문 추가
        current_block.add_assign_statement(var_name, var_type, return_interval)

        # 9. 함수 호출의 사이드 이펙트 처리
        self.handle_function_side_effects(function_name, function_args)

        # 11. 분석 결과 저장
        result = {
            "line": self.current_start_line,
            "variable": var_name,
            "assigned_interval": [return_interval.min_value, return_interval.max_value]
        }

        # get_analysis_result에 사용될 결과 저장
        self.analysis_results = result

    def process_unary_prefix_operation(self, expr):
        # 1. 현재 타겟 컨트랙트의 CFG 가져오기
        contract_cfg = self.contract_cfgs[self.current_target_contract]
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # 2. 현재 타겟 함수의 CFG 가져오기
        self.current_target_function_cfg = contract_cfg.get_function_cfg(self.current_target_function)
        if not self.current_target_function_cfg:
            raise ValueError("No active function to add variables to.")

        # 3. 현재 블록의 CFG 노드 가져오기
        current_block = self.get_current_block()

        # 4. 변수 이름 또는 배열/구조체 접근자 추출
        var_name = self.extract_variable_name(expr.expression)
        variable_obj = current_block.get_variable(var_name)

        if not variable_obj:
            variable_obj = self.current_target_function_cfg.get_related_variable(var_name)

        if not variable_obj:
            raise ValueError(f"Variable '{var_name}' not found in current CFG node.")

        # 5. 배열 또는 구조체의 경우 처리
        if isinstance(variable_obj, ArrayVariable):
            # 배열 요소에 대해 연산 수행
            index_expr = expr.expression.index  # 배열 인덱스 추출
            index_interval = self.evaluate_expression(index_expr)
            index_value = index_interval.min_value  # 인덱스 값 (단일 값으로 가정)
            element = variable_obj.elements[index_value]
            current_interval = element.value
        elif isinstance(variable_obj, StructVariable):
            # 구조체 멤버에 대해 연산 수행
            member_name = expr.expression.member
            current_interval = variable_obj.members[member_name].value
        else:
            # 기본 변수 처리
            current_interval = variable_obj.value

        # 6. 단항 연산 수행 및 우변 표현식 생성
        if expr.operator == '++':
            # 우변 표현식 생성: 변수 + 1
            right_expr = Expression(
                operator='+',
                left=expr.expression,
                right=Expression(literal=1)
            )
            # 우변 표현식 평가
            new_interval = current_interval.add(IntegerInterval(1, 1))
        elif expr.operator == '--':
            # 우변 표현식 생성: 변수 - 1
            right_expr = Expression(
                operator='-',
                left=expr.expression,
                right=Expression(literal=1)
            )
            # 우변 표현식 평가
            new_interval = current_interval.subtract(IntegerInterval(1, 1))
        else:
            raise ValueError(f"Unsupported unary prefix operator: {expr.operator}")

        # 7. CFG 노드에 업데이트된 변수 정보 저장
        if isinstance(variable_obj, ArrayVariable):
            # 배열 요소에 대한 할당문 추가
            variable_obj.elements[index_value].value = new_interval  # 요소 값 업데이트
            current_block.add_array_assign_statement(variable_obj, right_expr, operator='=')
        elif isinstance(variable_obj, StructVariable):
            # 구조체 멤버에 대한 할당문 추가
            variable_obj.members[member_name].value = new_interval  # 멤버 값 업데이트
            current_block.add_struct_assign_statement(variable_obj, right_expr, operator='=')
        else:
            # 기본 변수에 대한 할당문 추가
            variable_obj.value = new_interval  # 변수 값 업데이트
            current_block.add_assign_statement(variable_obj, right_expr, operator='=')

        if current_block.is_while_body:
            vars = self.fixpoint(current_block)
            self.update_while_body(vars, current_block)

        # 9. 분석 결과 저장
        result = {
            "line": self.current_start_line,
            "variable": var_name,
            "assigned_interval": [new_interval.min_value, new_interval.max_value]
        }

        # get_analysis_result에 사용될 결과 저장
        self.analysis_results = result

        # 10. current_block을 function CFG에 반영
        self.current_target_function_cfg.update_block(current_block)  # 변경된 블록을 반영

        # 11. function_cfg 결과를 contract_cfg에 반영
        contract_cfg.functions[self.current_target_function] = self.current_target_function_cfg

        # 12. contract_cfg를 contract_cfgs에 반영
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        self.current_target_function_cfg = None

    def process_unary_suffix_operation(self, expr):
        # 1. 현재 타겟 컨트랙트의 CFG 가져오기
        contract_cfg = self.contract_cfgs[self.current_target_contract]
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # 2. 현재 타겟 함수의 CFG 가져오기
        self.current_target_function_cfg = contract_cfg.get_function_cfg(self.current_target_function)
        if not self.current_target_function_cfg:
            raise ValueError("No active function to add variables to.")

        # 3. 현재 블록의 CFG 노드 가져오기
        current_block = self.get_current_block()

        # 4. 변수 이름 또는 배열/구조체 접근자 추출
        var_name = self.extract_variable_name(expr.expression)
        variable_obj = current_block.get_variable(var_name)

        if not variable_obj:
            variable_obj = self.current_target_function_cfg.get_related_variable(var_name)

        if not variable_obj:
            raise ValueError(f"Variable '{var_name}' not found in current CFG node.")

        # 5. 배열 또는 구조체의 경우 처리
        if isinstance(variable_obj, ArrayVariable):
            # 배열 요소에 대해 연산 수행
            index_expr = expr.expression.index  # 배열 인덱스 추출
            index_interval = self.evaluate_expression(index_expr)
            index_value = index_interval.min_value  # 인덱스 값 (단일 값으로 가정)
            element = variable_obj.elements[index_value]
            current_interval = element.value
        elif isinstance(variable_obj, StructVariable):
            # 구조체 멤버에 대해 연산 수행
            member_name = expr.expression.member
            current_interval = variable_obj.members[member_name].value
        else:
            # 기본 변수 처리
            current_interval = variable_obj.value

        # 6. 단항 연산 수행 및 우변 표현식 생성
        if expr.operator == '++':
            # 우변 표현식 생성: 변수 + 1
            right_expr = Expression(
                operator='+',
                left=expr.expression,
                right=Expression(literal=1)
            )
            # 우변 표현식 평가
            new_interval = current_interval.add(IntegerInterval(1, 1))
        elif expr.operator == '--':
            # 우변 표현식 생성: 변수 - 1
            right_expr = Expression(
                operator='-',
                left=expr.expression,
                right=Expression(literal=1)
            )
            # 우변 표현식 평가
            new_interval = current_interval.subtract(IntegerInterval(1, 1))
        else:
            raise ValueError(f"Unsupported unary suffix operator: {expr.operator}")

        # 7. CFG 노드에 업데이트된 변수 정보 저장
        if isinstance(variable_obj, ArrayVariable):
            # 배열 요소에 대한 할당문 추가
            variable_obj.elements[index_value].value = new_interval  # 요소 값 업데이트
            current_block.add_array_assign_statement(variable_obj, right_expr, operator='=')
        elif isinstance(variable_obj, StructVariable):
            # 구조체 멤버에 대한 할당문 추가
            variable_obj.members[member_name].value = new_interval  # 멤버 값 업데이트
            current_block.add_struct_assign_statement(variable_obj, right_expr, operator='=')
        else:
            # 기본 변수에 대한 할당문 추가
            variable_obj.value = new_interval  # 변수 값 업데이트
            current_block.add_assign_statement(variable_obj, right_expr, operator='=')

        if current_block.is_while_body:
            vars = self.fixpoint(current_block)
            self.update_while_body(vars, current_block)

        # 9. 분석 결과 저장
        result = {
            "line": self.current_start_line,
            "variable": var_name,
            "assigned_interval": [new_interval.min_value, new_interval.max_value]
        }

        # get_analysis_result에 사용될 결과 저장
        self.analysis_results = result

        # 10. current_block을 function CFG에 반영
        self.current_target_function_cfg.update_block(current_block)  # 변경된 블록을 반영

        # 11. function_cfg 결과를 contract_cfg에 반영
        contract_cfg.functions[self.current_target_function] = self.current_target_function_cfg

        # 12. contract_cfg를 contract_cfgs에 반영
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        self.current_target_function_cfg = None

    def process_function_call(self, expr):
        """
        함수 호출을 처리하는 메소드입니다.
        :param expr: Expression 객체 (FunctionCall)
        :return: 함수 호출 결과 (Interval 또는 None)
        """

        # 1. 현재 타겟 컨트랙트의 CFG 가져오기
        contract_cfg = self.contract_cfgs[self.current_target_contract]
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # 2. 현재 타겟 함수의 CFG 가져오기
        self.current_target_function_cfg = contract_cfg.get_function_cfg(self.current_target_function)
        if not self.current_target_function_cfg:
            raise ValueError("No active function to add variables to.")

        # 3. 함수 표현식 가져오기
        function_expr = expr.function

        # 4. 함수 표현식이 MemberAccessContext인지 확인
        if function_expr.context == 'MemberAccessContext':
            # 4.1 base와 member 가져오기
            base_expr = function_expr.base
            member_name = function_expr.member

            # 4.2 base_expr이 IdentifierExpContext인지 확인
            if base_expr.context == 'IdentifierExpContext':
                identifier = base_expr.identifier

                # 4.3 현재 함수 CFG에서 변수 가져오기
                arr_var = self.current_target_function_cfg.get_variable(identifier)

                if arr_var is None:
                    raise ValueError(f"Variable '{identifier}' not found in current function scope.")

                # 4.4 배열 변수인지 확인
                if isinstance(arr_var, ArrayVariable):
                    # 4.5 배열의 기본 타입을 검증
                    if arr_var.typeInfo.isDynamicArray:
                        # 5. push 함수 처리
                        if member_name == 'push':
                            arguments = expr.arguments

                            if arguments is None or len(arguments) == 0:
                                # push(): 새로운 기본값 요소 추가 (기본값을 타입에 맞춰 생성)
                                base_type = arr_var.typeInfo.arrayBaseType

                                # 기본값 생성 (타입에 따라 처리)
                                if base_type == 'uint' or base_type == 'int':
                                    element_var = Variables(value=IntegerInterval(0, 0), typeInfo=base_type)
                                else:
                                    element_var = Variables(value=None, typeInfo=base_type)

                                arr_var.elements.append(element_var)

                                # 배열의 길이 증가
                                if arr_var.typeInfo.arrayLength is not None:
                                    arr_var.typeInfo.arrayLength += 1

                                # 반환값 처리 (필요시 참조 반환)
                                return element_var
                            elif len(arguments) == 1:
                                # push(value): 인자를 배열에 추가
                                arg_expr = arguments[0]
                                arg_value = self.evaluate_expression(arg_expr)

                                # 타입 호환성 확인 후 요소 추가
                                element_var = Variables(value=arg_value, typeInfo=arr_var.typeInfo.arrayBaseType)
                                arr_var.elements.append(element_var)

                                # 배열의 길이 증가
                                if arr_var.typeInfo.arrayLength is not None:
                                    arr_var.typeInfo.arrayLength += 1

                                # 반환값 없음
                                return None
                            else:
                                raise ValueError("push() function accepts at most one argument.")
                        # 6. pop 함수 처리
                        elif member_name == 'pop':
                            # pop(): 마지막 요소 제거
                            if not arr_var.elements:
                                raise IndexError(f"Cannot pop from empty array '{identifier}'.")

                            arr_var.elements.pop()

                            # 배열의 길이 감소
                            if arr_var.typeInfo.arrayLength is not None:
                                arr_var.typeInfo.arrayLength -= 1

                            # 반환값 없음
                            return None
                        else:
                            raise NotImplementedError(f"Member function '{member_name}' is not implemented.")
                    else:
                        raise TypeError(f"Variable '{identifier}' is not a dynamic array.")
                else:
                    raise TypeError(f"Variable '{identifier}' is not an array variable.")
            else:
                raise NotImplementedError("Only simple identifiers are supported as array variables.")
        else:
            raise NotImplementedError("Only member function calls are supported in this context.")

        if current_block.is_while_body:
            vars = self.fixpoint(current_block)
            self.update_while_body(vars, current_block)

        self.current_target_function_cfg = None

    def process_payable_function_call(self, expr):
        # Handle payable function calls
        pass

    def process_function_call_options(self, expr):
        # Handle function calls with options
        pass

    def process_if_statement(self, condition_expr):
        # 1. 현재 컨트랙트와 함수의 CFG 가져오기
        contract_cfg = self.contract_cfgs[self.current_target_contract]
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        self.current_target_function_cfg = contract_cfg.get_function_cfg(self.current_target_function)
        if not self.current_target_function_cfg:
            raise ValueError("No active function to process the if statement.")

        # 2. 현재 블록 가져오기
        current_block = self.get_current_block()

        # 3. 조건식 블록 생성 및 평가
        condition_block = CFGNode(name=f"if_condition_{self.current_start_line}",
                                  condition_node=True,
                                  condition_node_type="if")
        condition_block.condition_expr = condition_expr
        # 7. True 분기에서 변수 상태 복사 및 업데이트
        condition_block.variables = self.copy_variables(current_block.variables)
        if current_block.is_while_body :
            condition_block.is_while_body = True

        # 4. brace_count 업데이트 - 존재하지 않으면 초기화
        if self.current_start_line not in self.brace_count:
            self.brace_count[self.current_start_line] = {}
        self.brace_count[self.current_start_line]['cfg_node'] = condition_block

        # 5. True 분기 블록 생성
        true_block = CFGNode(name=f"if_true_{self.current_start_line}")

        # 7. True 분기에서 변수 상태 복사 및 업데이트
        true_block.variables = self.copy_variables(condition_block.variables)
        if current_block.is_while_body :
            condition_block.is_while_body = True
        self.update_variables_with_condition(true_block.variables, condition_expr, is_true_branch=True)

        false_block = CFGNode(name=f"if_false_{self.current_start_line}")
        false_block.variables = self.copy_variables(condition_block.variables)
        self.update_variables_with_condition(false_block.variables, condition_expr, is_true_branch=False)

        # 8. 현재 블록의 후속 노드 처리 (기존 current_block의 successors를 가져옴)
        successors = list(self.current_target_function_cfg.graph.successors(current_block))

        # 기존 current_block과 successor들의 edge를 제거
        for successor in successors:
            self.current_target_function_cfg.graph.remove_edge(current_block, successor)

        # 9. CFG 노드 추가
        self.current_target_function_cfg.graph.add_node(condition_block)
        self.current_target_function_cfg.graph.add_node(true_block)
        self.current_target_function_cfg.graph.add_node(false_block)

        # 10. 조건 블록과 True/False 분기 연결
        self.current_target_function_cfg.graph.add_edge(current_block, condition_block)
        self.current_target_function_cfg.graph.add_edge(condition_block, true_block, condition=True)
        self.current_target_function_cfg.graph.add_edge(condition_block, false_block, condition=False)

        # 11. True 분기 후속 노드 연결
        for successor in successors:
            self.current_target_function_cfg.graph.add_edge(true_block, successor)

        # 13. CFG 업데이트
        contract_cfg.functions[self.current_target_function] = self.current_target_function_cfg
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        self.current_target_function_cfg = None

    def process_else_if_statement(self, condition_expr):
        # 1. 현재 컨트랙트와 함수의 CFG 가져오기
        contract_cfg = self.contract_cfgs[self.current_target_contract]
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        self.current_target_function_cfg = contract_cfg.get_function_cfg(self.current_target_function)
        if not self.current_target_function_cfg:
            raise ValueError("No active function to process the else-if statement.")

        # 2. 이전 조건 노드를 가져와서 부정된 조건을 처리
        previous_condition_node = self.find_corresponding_condition_node()
        if not previous_condition_node:
            raise ValueError("No previous if or else if node found for else-if statement.")

        # 3. 이전 조건 노드의 False 분기 제거
        false_successors = list(self.current_target_function_cfg.graph.successors(previous_condition_node))
        for successor in false_successors:
            edge_data = self.current_target_function_cfg.graph.get_edge_data(previous_condition_node, successor)
            if edge_data.get('condition') is False:
                self.current_target_function_cfg.graph.remove_edge(previous_condition_node, successor)

        # 3. 이전 조건 노드에서 False 분기 처리 (가상의 블록)
        temp_variables = self.copy_variables(previous_condition_node.variables)
        self.update_variables_with_condition(temp_variables, previous_condition_node.condition_expr,
                                             is_true_branch=False)

        # 4. else if 조건식 블록 생성
        condition_block = CFGNode(name=f"else_if_condition_{self.current_start_line}",
                                  condition_node=True,
                                  condition_node_type="else if")
        condition_block.condition_expr = condition_expr

        # 5. brace_count 업데이트 - 존재하지 않으면 초기화
        if self.current_start_line not in self.brace_count:
            self.brace_count[self.current_start_line] = {}
        self.brace_count[self.current_start_line]['cfg_node'] = condition_block

        # 6. True 분기 블록 생성
        true_block = CFGNode(name=f"else_if_true_{self.current_start_line + 1}")

        # 7. True 분기에서 변수 상태 복사 및 업데이트
        true_block.variables = self.copy_variables(temp_variables)
        self.update_variables_with_condition(true_block.variables, condition_expr, is_true_branch=True)

        # 5. False 분기 블록 생성
        false_block = CFGNode(name=f"else_if_false_{self.current_start_line}")
        false_block.variables = self.copy_variables(previous_condition_node.variables)
        self.update_variables_with_condition(false_block.variables, previous_condition_node.condition_expr,
                                             is_true_branch=False)

        # 8. 이전 조건 블록과 새로운 else_if_condition 블록 연결
        self.current_target_function_cfg.graph.add_edge(previous_condition_node, condition_block, condition=False)

        # 9. 새로운 조건 블록과 True 블록 연결
        self.current_target_function_cfg.graph.add_node(condition_block)
        self.current_target_function_cfg.graph.add_node(true_block)
        self.current_target_function_cfg.graph.add_node(false_block)

        self.current_target_function_cfg.graph.add_edge(condition_block, true_block, condition=True)
        self.current_target_function_cfg.graph.add_edge(condition_block, false_block, condition=False)

        # 11. CFG 업데이트
        contract_cfg.functions[self.current_target_function] = self.current_target_function_cfg
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        self.current_target_function_cfg = None

    def process_else_statement(self):
        # 1. 현재 컨트랙트와 함수의 CFG 가져오기
        contract_cfg = self.contract_cfgs[self.current_target_contract]
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        self.current_target_function_cfg = contract_cfg.get_function_cfg(self.current_target_function)
        if not self.current_target_function_cfg:
            raise ValueError("No active function to process the else statement.")

        # 2. 대응되는 if 또는 else if의 조건 노드 찾기
        condition_node = self.find_corresponding_condition_node()
        if not condition_node:
            raise ValueError("No corresponding if or else if condition node found for else statement.")

        # 3. 이전 조건 노드의 False 분기 제거
        false_successors = list(self.current_target_function_cfg.graph.successors(condition_node))
        for successor in false_successors:
            edge_data = self.current_target_function_cfg.graph.get_edge_data(condition_node, successor)
            if edge_data.get('condition') is False:
                self.current_target_function_cfg.graph.remove_edge(condition_node, successor)

        # 3. False 분기 블록 생성
        else_block = CFGNode(name=f"else_block_{self.current_start_line}")

        # 5. 변수 상태 관리
        # else 블록의 변수 상태 초기화 (이전 조건 노드의 변수 상태 복사)
        else_block.variables = self.copy_variables(condition_node.variables)

        # 6. 조건식 부정된 상태로 변수 값 업데이트
        self.update_variables_with_condition(else_block.variables, condition_node.condition_expr, is_true_branch=False)

        # 4. CFG 연결 - 조건 노드의 False 브랜치에 else 블록 연결
        self.current_target_function_cfg.graph.add_node(else_block)
        self.current_target_function_cfg.graph.add_edge(condition_node, else_block, condition=False)

        # 5. brace_count 업데이트 - 존재하지 않으면 초기화
        if self.current_start_line not in self.brace_count:
            self.brace_count[self.current_start_line] = {}
        self.brace_count[self.current_start_line]['cfg_node'] = else_block

        # 7. CFG 업데이트
        contract_cfg.functions[self.current_target_function] = self.current_target_function_cfg
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        self.current_target_function_cfg = None

    def process_while_statement(self, condition_expr):
        # 1. Get the current contract and function CFG
        contract_cfg = self.contract_cfgs.get(self.current_target_contract)
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        self.current_target_function_cfg = contract_cfg.get_function_cfg(self.current_target_function)
        if not self.current_target_function_cfg:
            raise ValueError("No active function to process the while statement.")

        # 2. Get the current block
        current_block = self.get_current_block()

        # 3. Create the join point node (entry point for the loop)
        join_node = CFGNode(name=f"while_join_{self.current_start_line}",
                            fixpoint_evaluation_node=True)

        # Copy variables from current_block to join_node
        join_node.variables = self.copy_variables(current_block.variables) # while문 이전에서 들어온 변수의 상태
        join_node.fixpoint_evaluation_node_vars = self.copy_variables(current_block.variables) # join 하면서 변하는 변수의 상태

        successors = list(self.current_target_function_cfg.graph.successors(current_block))

        # 기존 current_block과 successor들의 edge를 제거
        for successor in successors:
            self.current_target_function_cfg.graph.remove_edge(current_block, successor)

        # 4. Create the condition node
        condition_node = CFGNode(name=f"while_condition_{self.current_start_line}",
                                 condition_node=True,
                                 condition_node_type="while")
        condition_node.condition_expr = condition_expr  # Store the condition expression for later use
        condition_node.variables = self.copy_variables(join_node.variables)

        # 5. Connect the current block to the join node (if not already connected)
        self.current_target_function_cfg.graph.add_node(join_node)
        self.current_target_function_cfg.graph.add_edge(current_block, join_node)

        # 6. Connect the join node to the condition node
        self.current_target_function_cfg.graph.add_node(condition_node)
        self.current_target_function_cfg.graph.add_edge(join_node, condition_node)

        # 7. Create the true node (loop body)
        true_node = CFGNode(name=f"while_body_{self.current_start_line}")
        true_node.is_while_body = True
        true_node.variables = self.copy_variables(condition_node.variables)
        self.update_variables_with_condition(true_node.variables, condition_expr, is_true_branch=True)

        # 8. Create the false node (exit block)
        false_node = CFGNode(name=f"while_exit_{self.current_start_line}",
                             loop_exit_node=True)

        # 9. Connect the condition node's true branch to the true node
        self.current_target_function_cfg.graph.add_node(true_node)
        self.current_target_function_cfg.graph.add_edge(condition_node, true_node, condition=True)

        # 10. Connect the condition node's false branch to the false node
        self.current_target_function_cfg.graph.add_node(false_node)
        self.current_target_function_cfg.graph.add_edge(condition_node, false_node, condition=False)

        # 기존 current_block과 successor들을 false block의 successor로
        for successor in successors:
            self.current_target_function_cfg.graph.add_edge(successor, false_node)

        # 11. Connect the true node back to the join node (loop back)
        self.current_target_function_cfg.graph.add_edge(true_node, join_node)

        # 8. Return 노드에 대한 brace_count 업데이트
        if self.current_start_line not in self.brace_count:
            self.brace_count[self.current_start_line] = {}
        self.brace_count[self.current_start_line]['cfg_node'] = condition_node

        # 8. CFG 업데이트
        contract_cfg.functions[self.current_target_function] = self.current_target_function_cfg
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        self.current_target_function_cfg = None

    def process_continue_statement(self):
        # 1. 현재 컨트랙트와 함수의 CFG 가져오기
        contract_cfg = self.contract_cfgs.get(self.current_target_contract)
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        self.current_target_function_cfg = contract_cfg.get_function_cfg(self.current_target_function)
        if not self.current_target_function_cfg:
            raise ValueError("No active function to process the continue statement.")

        # 2. 현재 블록 가져오기 (continue가 발생한 블록)
        current_block = self.get_current_block()

        # 3. 현재 블록에 continue statement 추가 (Statement 객체로 추가)
        continue_statement = Statement(statement_type="continue")
        current_block.statements.append(continue_statement)

        # 4. 재귀적으로 fixpoint_evaluation_node 찾기
        fixpoint_evaluation_node = self.find_fixpoint_evaluation_node(current_block, self.current_target_function_cfg)
        if not fixpoint_evaluation_node:
            raise ValueError("No corresponding loop join node found for continue statement.")

        # 5. 현재 블록의 모든 successor와의 edge 제거
        successors = list(self.current_target_function_cfg.graph.successors(current_block))
        for successor in successors:
            self.current_target_function_cfg.graph.remove_edge(current_block, successor)

        # 6. 현재 블록을 fixpoint_evaluation_node로 연결 (loop로 다시 돌아감)
        self.current_target_function_cfg.graph.add_edge(current_block, fixpoint_evaluation_node)

        if current_block.is_while_body:
            vars = self.fixpoint(current_block)
            self.update_while_body(vars, current_block)

        # 8. Return 노드에 대한 brace_count 업데이트
        if self.current_start_line not in self.brace_count:
            self.brace_count[self.current_start_line] = {}
        self.brace_count[self.current_start_line]['cfg_node'] = current_block

        # 7. CFG 업데이트
        contract_cfg.functions[self.current_target_function] = self.current_target_function_cfg
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        self.current_target_function_cfg = None

    def process_break_statement(self):
        # 1. 현재 컨트랙트와 함수의 CFG 가져오기
        contract_cfg = self.contract_cfgs.get(self.current_target_contract)
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        self.current_target_function_cfg = contract_cfg.get_function_cfg(self.current_target_function)
        if not self.current_target_function_cfg:
            raise ValueError("No active function to process the break statement.")

        # 2. 현재 블록 가져오기 (break가 발생한 블록)
        current_block = self.get_current_block()

        # 3. 현재 블록에 break statement 추가 (Statement 객체로 추가)
        break_statement = Statement(statement_type="break")
        current_block.statements.append(break_statement)

        # 4. 재귀적으로 위로 타고 올라가서 while문 조건 노드를 찾기
        condition_node = self.find_while_condition_node(current_block, self.current_target_function_cfg)
        if not condition_node:
            raise ValueError("No corresponding while condition node found for break statement.")

        # 5. 해당 조건 노드의 false branch를 통해 loop_exit_node 찾기
        loop_exit_node = self.current_target_function_cfg.get_false_block(condition_node)  # 수정된 부분
        if not loop_exit_node or not loop_exit_node.loop_exit_node:
            raise ValueError("No valid loop exit node found for break statement.")

        # 6. 현재 블록의 모든 successor와의 edge 제거
        successors = list(self.current_target_function_cfg.graph.successors(current_block))
        for successor in successors:
            self.current_target_function_cfg.graph.remove_edge(current_block, successor)

        # 7. 현재 블록을 loop_exit_node로 연결 (루프에서 빠져나감)
        self.current_target_function_cfg.graph.add_edge(current_block, loop_exit_node)

        if current_block.is_while_body:
            vars = self.fixpoint(current_block)
            self.update_while_body(vars, current_block)

        # 8. Return 노드에 대한 brace_count 업데이트
        if self.current_start_line not in self.brace_count:
            self.brace_count[self.current_start_line] = {}
        self.brace_count[self.current_start_line]['cfg_node'] = current_block

        # 8. CFG 업데이트
        contract_cfg.functions[self.current_target_function] = self.current_target_function_cfg
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        self.current_target_function_cfg = None

    def find_fixpoint_evaluation_node(self, current_node):
        """
        재귀적으로 predecessor를 탐색하여 fixpoint_evaluation_node를 찾는 함수
        """
        # 현재 노드가 fixpoint_evaluation_node라면 반환
        if current_node.fixpoint_evaluation_node:
            return current_node

        # 직접적인 predecessor를 탐색
        predecessors = list(self.current_target_function_cfg.graph.predecessors(current_node))
        for pred in predecessors:
            # 재귀적으로 predecessor를 탐색하여 fixpoint_evaluation_node를 찾음
            fixpoint_evaluation_node = self.find_fixpoint_evaluation_node(pred)
            if fixpoint_evaluation_node:
                return fixpoint_evaluation_node

        # fixpoint_evaluation_node를 찾지 못하면 None 반환
        return None

    def find_while_condition_node(self, current_node):
        """
                재귀적으로 predecessor를 탐색하여 fixpoint_evaluation_node를 찾는 함수
                """
        # 현재 노드가 fixpoint_evaluation_node라면 반환
        if current_node.condition_node and current_node.condition_node_type == "while":
            return current_node

        # 직접적인 predecessor를 탐색
        predecessors = list(self.current_target_function_cfg.graph.predecessors(current_node))
        for pred in predecessors:
            # 재귀적으로 predecessor를 탐색하여 fixpoint_evaluation_node를 찾음
            while_condition_node = self.find_while_condition_node(pred)
            if while_condition_node:
                return while_condition_node

        # fixpoint_evaluation_node를 찾지 못하면 None 반환
        return None

    def process_return_statement(self, return_expr=None):
        # 1. 현재 컨트랙트와 함수의 CFG 가져오기
        contract_cfg = self.contract_cfgs.get(self.current_target_contract)
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        self.current_target_function_cfg = contract_cfg.get_function_cfg(self.current_target_function)
        if not self.current_target_function_cfg:
            raise ValueError("No active function to process the return statement.")

        # 2. 현재 블록 가져오기
        current_block = self.get_current_block()

        # 3. 반환값이 있는 경우 expression 평가
        if return_expr:
            return_value = self.evaluate_expression(return_expr)
        else:
            return_value = None

        # 4. Return 구문을 current_block에 추가
        current_block.add_return_statement(return_expr=return_expr, evaluated_value=return_value)

        # 5. function_exit_node에 return 값을 저장
        exit_node = self.current_target_function_cfg.get_exit_node()
        exit_node.return_val = return_value  # 반환 값을 exit_node의 return_val에 기록

        # 7. current_block에서 exit_node로 직접 연결
        self.current_target_function_cfg.graph.add_edge(current_block, exit_node)

        if current_block.is_while_body:
            vars = self.fixpoint(current_block)
            self.update_while_body(vars, current_block)

        # 8. CFG 업데이트
        contract_cfg.functions[self.current_target_function] = self.current_target_function_cfg
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        # 9. current_target_function_cfg를 None으로 설정하여 함수 종료
        self.current_target_function_cfg = None

    def process_revert_statement(self, revert_identifier=None, string_literal=None, call_argument_list=None):
        # 1. 현재 타겟 컨트랙트의 CFG 가져오기
        contract_cfg = self.contract_cfgs[self.current_target_contract]
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # 2. 현재 타겟 함수의 CFG 가져오기
        self.current_target_function_cfg = contract_cfg.get_function_cfg(self.current_target_function)
        if not self.current_target_function_cfg:
            raise ValueError("No active function to process the revert statement.")

        # 3. 현재 블록 가져오기
        current_block = self.get_current_block()

        # 4. Revert 문장을 Statement 객체로 만들어서 현재 블록에 추가
        revert_statement = Statement(
            statement_type="revert",
            identifier=revert_identifier,
            string_literal=string_literal,
            arguments=call_argument_list
        )
        current_block.statements.append(revert_statement)

        # 5. 함수의 exit 노드와 현재 노드 간 연결이 이미 존재하는지 확인
        exit_node = self.current_target_function_cfg.get_exit_node()
        if not self.current_target_function_cfg.graph.has_edge(current_block, exit_node):
            # 기존 엣지가 없으면 연결
            self.current_target_function_cfg.graph.add_edge(current_block, exit_node)

        # 7. Revert 노드의 brace_count 업데이트
        if self.current_start_line not in self.brace_count:
            self.brace_count[self.current_start_line] = {}
        self.brace_count[self.current_start_line]['cfg_node'] = current_block

        # 6. CFG 업데이트
        contract_cfg.functions[self.current_target_function] = self.current_target_function_cfg
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        self.current_target_function_cfg = None

    def process_require_statement(self, condition_expr, string_literal):
        # 1. 현재 컨트랙트와 함수의 CFG 가져오기
        contract_cfg = self.contract_cfgs[self.current_target_contract]
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        self.current_target_function_cfg = contract_cfg.get_function_cfg(self.current_target_function)
        if not self.current_target_function_cfg:
            raise ValueError("No active function to process the require statement.")

        # 2. 현재 블록 가져오기
        current_block = self.get_current_block()

        # 3. 기존 current_block의 successor 가져오기
        successors = list(self.current_target_function_cfg.graph.successors(current_block))

        # 4. 조건식 블록 생성 및 평가
        require_condition_node = CFGNode(name=f"require_condition_{self.current_start_line}",
                                         condition_node=True,
                                         condition_node_type="require")
        require_condition_node.condition_expr = condition_expr

        # 5. True 분기 블록 생성
        true_block = CFGNode(name=f"require_true_{self.current_start_line + 1}")

        # 6. True 블록에서 변수 상태 복사 및 업데이트
        true_block.variables = self.copy_variables(current_block.variables)
        self.update_variables_with_condition(true_block.variables, condition_expr, is_true_branch=True)

        # 7. 기존 current_block의 successors를 require_condition_node로 설정
        for successor in successors:
            self.current_target_function_cfg.graph.add_edge(require_condition_node, successor)
            self.current_target_function_cfg.graph.remove_edge(current_block, successor)

        # 8. 기존 current_block과 require_condition_node 연결
        self.current_target_function_cfg.graph.add_node(require_condition_node)
        self.current_target_function_cfg.graph.add_edge(current_block, require_condition_node)

        # 9. False 분기 처리 (조건이 실패할 경우, exit 노드로 연결)
        exit_node = self.current_target_function_cfg.get_exit_node()
        self.current_target_function_cfg.graph.add_edge(require_condition_node, exit_node, condition=False)

        # 10. True 블록 연결
        self.current_target_function_cfg.graph.add_node(true_block)
        self.current_target_function_cfg.graph.add_edge(require_condition_node, true_block, condition=True)

        # 11. brace_count 업데이트
        if self.current_start_line not in self.brace_count:
            self.brace_count[self.current_start_line] = {}
        self.brace_count[self.current_start_line]['cfg_node'] = require_condition_node

        # 12. CFG 업데이트
        contract_cfg.functions[self.current_target_function] = self.current_target_function_cfg
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        self.current_target_function_cfg = None

    def process_assert_statement(self, condition_expr, string_literal):
        # 1. 현재 컨트랙트와 함수의 CFG 가져오기
        contract_cfg = self.contract_cfgs[self.current_target_contract]
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        self.current_target_function_cfg = contract_cfg.get_function_cfg(self.current_target_function)
        if not self.current_target_function_cfg:
            raise ValueError("No active function to process the require statement.")

        # 2. 현재 블록 가져오기
        current_block = self.get_current_block()

        # 3. 기존 current_block의 successor 가져오기
        successors = list(self.current_target_function_cfg.graph.successors(current_block))

        # 4. 조건식 블록 생성 및 평가
        assert_condition_node = CFGNode(name=f"assert_condition_{self.current_start_line}",
                                        condition_node=True,
                                        condition_node_type="assert")
        assert_condition_node.condition_expr = condition_expr

        # 5. True 분기 블록 생성
        true_block = CFGNode(name=f"require_true_{self.current_start_line + 1}")

        # 6. True 블록에서 변수 상태 복사 및 업데이트
        true_block.variables = self.copy_variables(current_block.variables)
        self.update_variables_with_condition(true_block.variables, condition_expr, is_true_branch=True)

        # 7. 기존 current_block의 successors를 require_condition_node로 설정
        for successor in successors:
            self.current_target_function_cfg.graph.add_edge(assert_condition_node, successor)
            self.current_target_function_cfg.graph.remove_edge(current_block, successor)

        # 8. 기존 current_block과 require_condition_node 연결
        self.current_target_function_cfg.graph.add_node(assert_condition_node)
        self.current_target_function_cfg.graph.add_edge(current_block, assert_condition_node)

        # 9. False 분기 처리 (조건이 실패할 경우, exit 노드로 연결)
        exit_node = self.current_target_function_cfg.get_exit_node()
        self.current_target_function_cfg.graph.add_edge(assert_condition_node, exit_node, condition=False)

        # 10. True 블록 연결
        self.current_target_function_cfg.graph.add_node(true_block)
        self.current_target_function_cfg.graph.add_edge(assert_condition_node, true_block, condition=True)

        # 11. brace_count 업데이트
        if self.current_start_line not in self.brace_count:
            self.brace_count[self.current_start_line] = {}
        self.brace_count[self.current_start_line]['cfg_node'] = assert_condition_node

        # 12. CFG 업데이트
        contract_cfg.functions[self.current_target_function] = self.current_target_function_cfg
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        self.current_target_function_cfg = None

    def process_pre_execution_global(self, global_var_obj: GlobalVariable):
        """
        Global pre-execution intent를 처리하여, 예를 들어
          'block.timestamp' = IntegerInterval(1000, 2000, 256)
          'msg.sender' = "address 1"
        와 같이 현재 타겟 컨트랙트의 CFG에 저장합니다.
        """
        # 1) 현재 타겟 컨트랙트의 CFG 가져오기
        contract_cfg = self.contract_cfgs.get(self.current_target_contract)
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # 2) pre_exec_globals에 저장 (키는 완전한 글로벌 변수 이름, 예: "block.timestamp")
        contract_cfg.pre_exec_globals[global_var_obj.identifier] = global_var_obj

    def process_pre_execution_state(self, lhs_expr, value):
        """
        Process a pre-execution-state comment.
          e.g. // @pre-execution-state myMapping[0x123] = 100
               // @pre-execution-state myVar = true

        :param lhs_expr: Expression object (from testingExpression)
                         possible forms:
                           - identifier only    -> myVar
                           - index access       -> myArray[3] or myMapping[0x123]
                           - member access      -> myStruct.member
                           - nested form        -> myStruct.nestedArray[7]
        :param value:    int or bool from numberBoolLiteral
        """
        # 1) Get the current contract CFG
        contract_cfg = self.contract_cfgs.get(self.current_target_contract)
        if contract_cfg is None:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # 2) Get the function CFG (since it's 'pre-execution-state', we assume we are inside a function)
        function_cfg = contract_cfg.get_function_cfg(self.current_target_function)
        if function_cfg is None:
            raise ValueError(f"Unable to find function CFG for {self.current_target_function}")

        # 3) Save it in function_cfg.pre_exec_state
        #    - build a string key from lhs_expr if needed
        lhs_key = lhs_expr.to_string() if hasattr(lhs_expr, "to_string") else self._expression_to_str(lhs_expr)

        if not hasattr(function_cfg, "pre_exec_state"):
            function_cfg.pre_exec_state = {}
        function_cfg.pre_exec_state[lhs_key] = value

        # 4) Actually update the corresponding variable object in function_cfg.related_variables
        #    The main logic: we follow the Expression to find the final variable.

        # --- Start from the root Expression (lhs_expr) and recursively descend. ---
        # e.g. myVar, myArray[3], myStruct.member, myNestedMapping[key].member ...
        updated_var = self._resolve_and_update_expr(lhs_expr, function_cfg, value)

        # 5) (Optional) re-run abstract interpretation to reflect the changes
        # self.re_run_abstract_interpretation(function_cfg)

    def process_pre_execution_local(self, lhs_expr, value):
        """
               Process a pre-execution-state comment.
                 e.g. // @pre-execution-state myMapping[0x123] = 100
                      // @pre-execution-state myVar = true

               :param lhs_expr: Expression object (from testingExpression)
                                possible forms:
                                  - identifier only    -> myVar
                                  - index access       -> myArray[3] or myMapping[0x123]
                                  - member access      -> myStruct.member
                                  - nested form        -> myStruct.nestedArray[7]
               :param value:    int or bool from numberBoolLiteral
               """
        # 1) Get the current contract CFG
        contract_cfg = self.contract_cfgs.get(self.current_target_contract)
        if contract_cfg is None:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # 2) Get the function CFG (since it's 'pre-execution-state', we assume we are inside a function)
        function_cfg = contract_cfg.get_function_cfg(self.current_target_function)
        if function_cfg is None:
            raise ValueError(f"Unable to find function CFG for {self.current_target_function}")

        # 3) Save it in function_cfg.pre_exec_state
        #    - build a string key from lhs_expr if needed
        lhs_key = lhs_expr.to_string() if hasattr(lhs_expr, "to_string") else self._expression_to_str(lhs_expr)

        if not hasattr(function_cfg, "pre_exec_state"):
            function_cfg.pre_exec_local = {}
        function_cfg.pre_exec_local[lhs_key] = value

        # 4) Actually update the corresponding variable object in function_cfg.related_variables
        #    The main logic: we follow the Expression to find the final variable.

        # --- Start from the root Expression (lhs_expr) and recursively descend. ---
        # e.g. myVar, myArray[3], myStruct.member, myNestedMapping[key].member ...
        updated_var = self._resolve_and_update_expr(lhs_expr, function_cfg, value)

        # 5) (Optional) re-run abstract interpretation to reflect the changes
        # self.re_run_abstract_interpretation(function_cfg)

    def _expression_to_str(self, expr):
        """
        Helper to convert a (testing) Expression into a string representation.
        e.g.
          Expression(identifier='myVar') -> "myVar"
          Expression(base=..., member='memberName') -> "base.memberName"
          Expression(base=..., index=someExpr) -> "base[someExpr]"
        This is just for storing in a dict key if we want.
        """
        # If expr is just identifier:
        if expr.member is None and expr.index is None and expr.base is None:
            return expr.identifier  # e.g. "myVar"
        # If it's member access
        if expr.member is not None:
            # build base string, then ".member"
            base_str = self._expression_to_str(expr.base)
            return f"{base_str}.{expr.member}"
        # If it's index access
        if expr.index is not None:
            base_str = self._expression_to_str(expr.base)
            # index part: if index is literal or identifier
            if expr.index.literal is not None:
                idx_str = str(expr.index.literal)
            elif expr.index.identifier is not None:
                idx_str = expr.index.identifier
            else:
                # fallback
                idx_str = self._expression_to_str(expr.index)
            return f"{base_str}[{idx_str}]"

        # fallback: if none of the above logic
        return "EXPR?"

    def _resolve_and_update_expr(self, expr, function_cfg, new_value):
        """
        Recursively resolve expr to find the actual Variables (or MappingVariable, etc.) and update its 'value'.
        Return the updated Variables object if found.

        expr: Expression object
        function_cfg: current function CFG
        new_value: int or bool
        """
        # if expr has no base, we are at root identifier
        if expr.base is None:
            # e.g. "myVar"
            var_name = expr.identifier
            var_obj = function_cfg.get_related_variable(var_name)
            if var_obj is not None:
                self._apply_new_value_to_variable(var_obj, new_value)
                return var_obj
            else:
                print(f"[Warning] var '{var_name}' not found in function '{function_cfg.function_name}'.")
                return None
        else:
            # there's a base expression
            base_obj = self._resolve_and_update_expr(expr.base, function_cfg, None)
            # we don't update the base with new_value, but we do want to navigate
            if base_obj is None:
                # cannot proceed
                return None

            # If it's member access
            if expr.member is not None:
                # base_obj should be e.g. a StructVariable or similar
                if isinstance(base_obj, StructVariable):
                    member_name = expr.member
                    if member_name in base_obj.members:
                        member_var = base_obj.members[member_name]
                        if expr.index is None:
                            # we want to update member_var with new_value (if new_value != None)
                            if new_value is not None:
                                self._apply_new_value_to_variable(member_var, new_value)
                            return member_var
                        else:
                            # theoretically structVar.member[...]?
                            print("[Warning] structVar.member[...] not typical, skipping.")
                            return None
                    else:
                        print(f"[Warning] struct '{base_obj.identifier}' has no member '{member_name}'")
                        return None
                else:
                    print(f"[Warning] Attempting member access on non-struct var '{base_obj.identifier}'")
                    return None

            # If it's index access
            if expr.index is not None:
                # base_obj should be e.g. ArrayVariable or MappingVariable
                if isinstance(base_obj, ArrayVariable):
                    # index might be literal or maybe an expression
                    idx_val = self._extract_index_val(expr.index)
                    idx_int = int(idx_val)  # enforce int
                    if 0 <= idx_int < len(base_obj.elements):
                        element_var = base_obj.elements[idx_int]
                        if new_value is not None:
                            self._apply_new_value_to_variable(element_var, new_value)
                        return element_var
                    else:
                        print(f"[Warning] array index out of range: {idx_int}")
                        return None

                elif isinstance(base_obj, MappingVariable):
                    idx_val = self._extract_index_val(expr.index)  # string or int
                    # we store it as string, typically
                    key_str = str(idx_val)
                    # get or create mapping entry
                    mapped_var = base_obj.mapping.get(key_str)
                    if mapped_var is None:
                        # create new
                        mapped_var = self._create_new_mapping_value(base_obj, key_str)
                        base_obj.mapping[key_str] = mapped_var
                    # update mapped_var if new_value is not None
                    if new_value is not None:
                        self._apply_new_value_to_variable(mapped_var, new_value)
                    return mapped_var
                else:
                    print(
                        f"[Warning] Attempting index access on var '{base_obj.identifier}' which is not array/mapping.")
                    return None

            # fallback
            return None

    def _apply_new_value_to_variable(self, var_obj, new_value):
        """
        Given var_obj (Variables, ArrayVariable, etc.) and new_value (int or bool),
        interpret typeInfo and update var_obj.value accordingly.
        """
        if not hasattr(var_obj, "typeInfo") or var_obj.typeInfo is None:
            # no type info => just store as integer?
            var_obj.value = new_value
            return

        # e.g. elementary type?
        etype = var_obj.typeInfo.elementaryTypeName
        if etype is None:
            # might be array/mapping/struct but let's see typeCategory
            if var_obj.typeInfo.typeCategory == 'array':
                print(f"[Info] _apply_new_value_to_variable: array type update not supported directly.")
                return
            elif var_obj.typeInfo.typeCategory == 'mapping':
                print(f"[Info] _apply_new_value_to_variable: mapping type update not supported directly.")
                return
            elif var_obj.typeInfo.typeCategory == 'struct':
                print(f"[Info] _apply_new_value_to_variable: struct type update not supported directly.")
                return
            else:
                print("[Warning] unknown typeCategory in var_obj.typeInfo")
                return

        # if we do have something like "int", "uint", "bool"
        if etype.startswith("int"):
            bit_len = var_obj.typeInfo.intTypeLength if var_obj.typeInfo.intTypeLength else 256
            if isinstance(new_value, bool):
                # treat as int(0 or 1)
                int_val = 1 if new_value else 0
                var_obj.value = IntegerInterval(int_val, int_val, bit_len)
            else:
                var_obj.value = IntegerInterval(new_value, new_value, bit_len)
        elif etype.startswith("uint"):
            bit_len = var_obj.typeInfo.intTypeLength if var_obj.typeInfo.intTypeLength else 256
            if isinstance(new_value, bool):
                int_val = 1 if new_value else 0
                var_obj.value = UnsignedIntegerInterval(int_val, int_val, bit_len)
            else:
                var_obj.value = UnsignedIntegerInterval(new_value, new_value, bit_len)
        elif etype == "bool":
            if isinstance(new_value, bool):
                var_obj.value = BoolInterval(new_value, new_value)
            else:
                # interpret non-zero => True
                bool_val = (new_value != 0)
                var_obj.value = BoolInterval(bool_val, bool_val)
        else:
            print(f"[Warning] _apply_new_value_to_variable: unrecognized elementary type '{etype}'")

    def _extract_index_val(self, index_expr):
        """
        Attempt to get a concrete index from index_expr (Expression).
        If it's literal: return int(index_expr.literal)
        If it's identifier: we might not have a direct integer => handle carefully
        etc.
        """
        if index_expr.literal is not None:
            return int(index_expr.literal, 0)  # parse w/ base=0 => auto 0x => hex
        elif index_expr.identifier is not None:
            # we could look up if that identifier is known => partial for now
            return index_expr.identifier
        else:
            # fallback => to_string or something
            return "???"

    def _create_new_mapping_value(self, map_var, key_str):
        """
        Create a new default Variables object for the given mapping key if not existing.
        We can look up map_var.typeInfo.mappingValueType and build a suitable variable.
        """
        # e.g. an elementary
        val_type = map_var.typeInfo.mappingValueType
        if val_type.typeCategory == 'elementary':
            etype = val_type.elementaryTypeName
            if etype.startswith('int'):
                bit_len = val_type.intTypeLength if val_type.intTypeLength else 256
                default_val = IntegerInterval(0, 0, bit_len)
                new_obj = Variables(identifier=f"{map_var.identifier}[{key_str}]",
                                    value=default_val,
                                    scope=map_var.scope,
                                    typeInfo=val_type)
                return new_obj
            elif etype.startswith('uint'):
                bit_len = val_type.intTypeLength if val_type.intTypeLength else 256
                default_val = UnsignedIntegerInterval(0, 0, bit_len)
                new_obj = Variables(identifier=f"{map_var.identifier}[{key_str}]",
                                    value=default_val,
                                    scope=map_var.scope,
                                    typeInfo=val_type)
                return new_obj
            elif etype == 'bool':
                default_val = BoolInterval(False, False)
                new_obj = Variables(identifier=f"{map_var.identifier}[{key_str}]",
                                    value=default_val,
                                    scope=map_var.scope,
                                    typeInfo=val_type)
                return new_obj
            else:
                # fallback
                new_obj = Variables(identifier=f"{map_var.identifier}[{key_str}]",
                                    value=None,
                                    scope=map_var.scope,
                                    typeInfo=val_type)
                return new_obj
        else:
            # array / struct / mapping => we'd have to create ArrayVariable, StructVariable, etc.
            print("[Info] _create_new_mapping_value: non-elementary value type => returning simple placeholder.")
            new_obj = Variables(identifier=f"{map_var.identifier}[{key_str}]",
                                value=None,
                                scope=map_var.scope,
                                typeInfo=val_type)
            return new_obj

    def extract_variable_name(self, expression):
        """
        표현식에서 변수 이름을 추출합니다.
        필요한 경우 재귀적으로 접근하여 전체 경로를 문자열로 반환합니다.
        :param expression: Expression 객체
        :return: 변수 이름 문자열 (예: 'a', 'arr[0]', 'struct.member', 'map[key]')
        """
        if expression.identifier:
            # 단순 식별자인 경우
            return expression.identifier
        elif expression.context == 'IndexAccessContext':
            # 인덱스 접근인 경우 (예: arr[0], map[key])
            base_name = self.extract_variable_name(expression.base)
            index_expr = expression.index
            index_value = self.extract_index_value(index_expr)
            return f"{base_name}[{index_value}]"
        elif expression.context == 'MemberAccessContext':
            # 멤버 접근인 경우 (예: struct.member)
            base_name = self.extract_variable_name(expression.base)
            member_name = expression.member
            return f"{base_name}.{member_name}"
        elif expression.context == 'FunctionCallContext':
            # 함수 호출인 경우 (예: func())
            function_name = self.extract_variable_name(expression.function)
            return f"{function_name}()"  # 함수 호출은 변수 이름으로 간주하지 않음
        else:
            raise ValueError(f"Unsupported expression type for variable extraction: {expression}")

    def extract_index_value(self, index_expr):
        """
        인덱스 표현식에서 인덱스 값을 추출합니다.
        :param index_expr: Expression 객체 (인덱스 표현식)
        :return: 인덱스 문자열 (예: '0', 'key', 'i')
        """
        if index_expr.literal is not None:
            return index_expr.literal
        elif index_expr.identifier is not None:
            return index_expr.identifier
        elif index_expr.context in ['IndexAccessContext', 'MemberAccessContext']:
            return self.extract_variable_name(index_expr)
        else:
            # 인덱스 표현식이 복잡한 경우 문자열로 표현
            return str(index_expr)

    def extract_related_variables(self, expr, current_block, function_cfg):
        related_vars = []

        # 우변 표현식에서 변수를 탐색
        for sub_expr in self.flatten_expression(expr):
            if sub_expr is None:
                continue

            # 상수나 리터럴인 경우 관련 변수가 아니므로 무시
            if self.is_literal_expression(sub_expr):
                continue

            var_name = self.extract_variable_name(sub_expr)
            variable_obj = current_block.get_variable(var_name)

            if not variable_obj:
                variable_obj = function_cfg.get_related_variable(var_name)

            if variable_obj:
                related_vars.append(variable_obj)

        return related_vars

    def flatten_expression(self, expr):
        # 표현식에서 모든 서브 표현식을 재귀적으로 탐색하여 평탄화
        expressions = [expr]
        if hasattr(expr, 'left'):
            expressions.extend(self.flatten_expression(expr.left))
        if hasattr(expr, 'right'):
            expressions.extend(self.flatten_expression(expr.right))
        return expressions

    def is_literal_expression(self, expr):
        """
        주어진 표현식이 상수나 리터럴인지 확인하는 함수.
        """
        # 상수나 리터럴인 경우 True를 반환
        if hasattr(expr, 'literal') and expr.literal is not None:
            return True
        return False

    import copy

    def copy_variables(self, variables):
        """
        주어진 변수 딕셔너리(variables)를 깊은 복사하여 반환합니다.
        variables: var_name -> Variables 객체
        """
        copied_variables = {}
        for var_name, var_obj in variables.items():
            if isinstance(var_obj, ArrayVariable):
                copied_array = ArrayVariable(
                    identifier=var_obj.identifier,
                    base_type=var_obj.typeInfo.arrayBaseType,
                    array_length=var_obj.typeInfo.arrayLength,
                    is_dynamic=var_obj.typeInfo.isDynamicArray,
                    value=copy.deepcopy(var_obj.value),
                    isConstant=var_obj.isConstant,
                    scope=var_obj.scope
                )
                # 배열의 각 요소를 깊은 복사
                copied_array.elements = [self.copy_variables({elem.identifier: elem})[elem.identifier] for elem in
                                         var_obj.elements]
                copied_variables[var_name] = copied_array

            elif isinstance(var_obj, StructVariable):
                copied_struct = StructVariable(
                    identifier=var_obj.identifier,
                    struct_type=var_obj.typeInfo.structTypeName,
                    value=copy.deepcopy(var_obj.value),
                    isConstant=var_obj.isConstant,
                    scope=var_obj.scope
                )
                # 구조체 멤버를 깊은 복사
                copied_struct.members = {member_name: self.copy_variables({member_name: member_obj})[member_name] for
                                         member_name, member_obj in var_obj.members.items()}
                copied_variables[var_name] = copied_struct

            elif isinstance(var_obj, MappingVariable):
                copied_mapping = MappingVariable(
                    identifier=var_obj.identifier,
                    key_type=var_obj.typeInfo.mappingKeyType,
                    value_type=var_obj.typeInfo.mappingValueType,
                    value=copy.deepcopy(var_obj.value),
                    isConstant=var_obj.isConstant,
                    scope=var_obj.scope
                )
                # 매핑의 키-값 쌍을 깊은 복사
                copied_mapping.mapping = {}
                for key, value in var_obj.mapping.items():
                    # 값이 Variables 객체인지 확인
                    if isinstance(value, Variables):
                        # Variables 객체인 경우 재귀적으로 복사
                        copied_value = self.copy_variables({key: value})[key]
                    else:
                        # Variables 객체가 아닌 경우 (Interval 등), 값을 그대로 복사
                        copied_value = copy.deepcopy(value)
                    copied_mapping.mapping[key] = copied_value
                copied_variables[var_name] = copied_mapping

            else:
                # 기본 Variables 타입 처리
                copied_variables[var_name] = Variables(
                    identifier=var_obj.identifier,
                    value=copy.deepcopy(var_obj.value),
                    isConstant=var_obj.isConstant,
                    scope=var_obj.scope,
                    typeInfo=var_obj.typeInfo  # SolType 객체 복사
                )

        return copied_variables

    def fixpoint(self, current_block):
        """
        고정점 분석을 수행하여 루프 내의 변수 상태를 수렴시킵니다.
        :param current_block: 현재 블록 (CFGNode)
        :return: 수렴된 변수 상태 딕셔너리 (var_name -> Variables 객체)
        """
        # 1. fixpoint_evaluation_node 찾기
        fixpoint_evaluation_node = self.find_fixpoint_evaluation_node(current_block)
        if not fixpoint_evaluation_node:
            raise ValueError("Join point node not found for the current block.")

        while_condition_node = self.find_while_condition_node(current_block)
        if not while_condition_node :
            raise ValueError("While condition node not found for the current block.")

        # 2. 루프 내의 모든 노드 수집
        loop_nodes = self.traverse_loop_nodes(while_condition_node)

        # 3. 변수 상태 초기화
        in_vars = {}
        out_vars = {}
        for node in loop_nodes:
            in_vars[node] = {}
            out_vars[node] = {}
            if node == while_condition_node:
                in_vars[node] = self.copy_variables(fixpoint_evaluation_node.fixpoint_evaluation_node_vars)

        # 4. 워크리스트 알고리즘 초기화 (집합 사용)
        #worklist = set(loop_nodes)
        worklist = deque([while_condition_node])
        max_iterations = 30  # 최대 반복 횟수 설정
        iteration = 0

        while worklist and iteration < max_iterations:
            iteration += 1
            node = worklist.popleft()

            # 5. 선행 노드들의 out_vars를 조인하여 in_vars 계산
            predecessors = list(self.current_target_function_cfg.graph.predecessors(node))
            new_in_vars = None  # None으로 초기화하여 첫 번째 조인 시 설정되도록 함
            for pred in predecessors:
                if pred in loop_nodes:
                    # pred가 루프 내의 노드인 경우
                    if pred in out_vars and out_vars[pred]:
                        if new_in_vars is None:
                            new_in_vars = self.copy_variables(out_vars[pred])
                        else:
                            new_in_vars = self.join_variables(new_in_vars, out_vars[pred])
                    elif pred in in_vars and in_vars[pred]:
                        if new_in_vars is None:
                            new_in_vars = self.copy_variables(in_vars[pred])
                        else:
                            new_in_vars = self.join_variables(new_in_vars, in_vars[pred])
                else:
                    # pred가 루프 밖의 노드인 경우
                    if new_in_vars is None:
                        new_in_vars = self.copy_variables(fixpoint_evaluation_node.variables)
                    else:
                        new_in_vars = self.join_variables(new_in_vars, fixpoint_evaluation_node.variables)

            # 6. in_vars 변화 확인
            if new_in_vars:
                if not self.variables_equal(in_vars[node], new_in_vars):
                    in_vars[node] = new_in_vars

            # 7. 노드의 transfer function 적용하여 out_vars 계산
            old_out_vars = out_vars[node]
            out_vars[node] = self.transfer_function(node, in_vars[node])

            # 8. out_vars 변화 확인 및 워크리스트 업데이트
            if not self.variables_equal(old_out_vars, out_vars[node]):
                successors = list(self.current_target_function_cfg.graph.successors(node))
                for succ in successors:
                    if succ in loop_nodes:
                        worklist.append(succ)

            if iteration == max_iterations:
                print("Fixpoint analysis did not converge within max iterations.")
                break

        # 9. 수렴된 변수 상태를 루프 내 각 노드에 반영
        for node in loop_nodes:
            node.variables = out_vars[node]

        # 10. 수렴된 변수 상태 반환
        return out_vars[fixpoint_evaluation_node]


    def traverse_loop_nodes(self, loop_node):
        """
        루프 내의 모든 노드를 수집합니다.
        :param loop_node: 루프의 시작 노드 (fixpoint_evaluation_node)
        :return: 루프 내의 노드 집합 (set)
        """
        visited = set()
        stack = [loop_node]
        while stack:
            current_node = stack.pop()
            if current_node in visited:
                continue
            visited.add(current_node)
            successors = list(self.current_target_function_cfg.graph.successors(current_node))
            for succ in successors:
                # 루프 종료 노드로의 에지는 제외
                if current_node.condition_node and current_node.condition_node_type == 'while':
                    if succ.loop_exit_node:
                        continue
                stack.append(succ)
        return visited

    def join_variables(self, vars1, vars2):
        """
        두 변수 상태 딕셔너리를 조인합니다.
        :param vars1: 첫 번째 변수 상태 딕셔너리 (var_name -> Variables 객체)
        :param vars2: 두 번째 변수 상태 딕셔너리 (var_name -> Variables 객체)
        :return: 조인된 변수 상태 딕셔너리 (var_name -> Variables 객체)
        """
        result = self.copy_variables(vars1)
        for var_name, var_obj in vars2.items():
            if var_name in result:
                existing_var = result[var_name]
                # 변수의 타입이 동일한지 확인
                if existing_var.typeInfo.typeCategory != var_obj.typeInfo.typeCategory:
                    raise TypeError(
                        f"Cannot join variables of different types: {existing_var.typeInfo.typeCategory} and {var_obj.typeInfo.typeCategory}")
                # 변수의 타입 카테고리에 따라 처리
                if existing_var.typeInfo.typeCategory == 'array':
                    # 배열 변수의 경우 각 요소를 조인
                    # 배열 길이와 요소 타입이 동일한지 확인
                    if existing_var.typeInfo.arrayLength != var_obj.typeInfo.arrayLength:
                        raise ValueError("Cannot join arrays of different lengths")
                    joined_elements = []
                    for elem1, elem2 in zip(existing_var.elements, var_obj.elements):
                        joined_elem = self.join_variables({elem1.identifier: elem1}, {elem2.identifier: elem2})
                        joined_elements.append(joined_elem[elem1.identifier])
                    existing_var.elements = joined_elements
                elif existing_var.typeInfo.typeCategory == 'struct':
                    # 구조체 변수의 경우 각 멤버를 조인
                    existing_var.members = self.join_variables(existing_var.members, var_obj.members)
                elif existing_var.typeInfo.typeCategory == 'mapping':
                    # mapping 변수의 경우, 키-값 쌍을 조인
                    if not existing_var.mapping:
                        continue  # 매핑 값이 없는 경우 넘어감
                    else:
                        # 매핑 키-값을 비교하고 조인
                        for key, value in var_obj.mapping.items():
                            if key in existing_var.mapping:
                                existing_var.mapping[key] = self.join_variables(
                                    {key: existing_var.mapping[key]}, {key: value}
                                )[key]
                            else:
                                # 없는 키는 새로 추가
                                existing_var.mapping[key] = self.copy_variables({key: value})[key]

                else:
                    # 기본 변수의 경우 value를 조인
                    var_value1 = existing_var.value
                    var_value2 = var_obj.value
                    joined_value = self.join_variable_values(var_value1, var_value2)
                    existing_var.value = joined_value
            else:
                # 새로운 변수 추가 (깊은 복사)
                result[var_name] = self.copy_variables({var_name: var_obj})[var_name]
        return result

    def variables_equal(self, vars1, vars2):
        """
        두 변수 상태 딕셔너리가 동일한지 확인합니다.
        :param vars1: 첫 번째 변수 상태 딕셔너리 (var_name -> Variables 객체)
        :param vars2: 두 번째 변수 상태 딕셔너리 (var_name -> Variables 객체)
        :return: 동일하면 True, 아니면 False
        """
        if vars1.keys() != vars2.keys():
            return False

        for var_name in vars1:
            var_obj1 = vars1[var_name]
            var_obj2 = vars2[var_name]

            # 배열 타입 비교
            if isinstance(var_obj1, ArrayVariable) and isinstance(var_obj2, ArrayVariable):
                # 배열 길이 확인
                if var_obj1.typeInfo.arrayLength != var_obj2.typeInfo.arrayLength:
                    return False
                # 배열의 각 요소 비교
                for elem1, elem2 in zip(var_obj1.elements, var_obj2.elements):
                    if not self.variables_equal({elem1.identifier: elem1}, {elem2.identifier: elem2}):
                        return False

            # 구조체 타입 비교
            elif isinstance(var_obj1, StructVariable) and isinstance(var_obj2, StructVariable):
                # 구조체 멤버 비교
                if not self.variables_equal(var_obj1.members, var_obj2.members):
                    return False

            # 매핑 타입 비교
            elif isinstance(var_obj1, MappingVariable) and isinstance(var_obj2, MappingVariable):
                # 매핑된 키 값 확인
                if var_obj1.mapping.keys() != var_obj2.mapping.keys():
                    return False
                # 매핑된 각 키-값 쌍 비교
                for key in var_obj1.mapping:
                    if not self.variables_equal({key: var_obj1.mapping[key]}, {key: var_obj2.mapping[key]}):
                        return False

            # 기본 타입 비교 (Variables)
            else:
                var_value1 = var_obj1.value
                var_value2 = var_obj2.value
                if not var_value1.equals(var_value2):
                    return False

        return True

    def transfer_function(self, node, in_vars):
        """
        노드의 transfer function을 적용하여 out_vars를 계산합니다.
        :param node: 현재 노드
        :param in_vars: 노드의 입력 변수 상태 (var_name -> Variables 객체)
        :return: 노드의 출력 변수 상태 (var_name -> Variables 객체)
        """
        out_vars = self.copy_variables(in_vars)
        if node.condition_node:
            # 조건 노드 처리
            self.update_variables_with_condition(out_vars, node.condition_expr, is_true_branch=True)
        elif node.fixpoint_evaluation_node:
            return out_vars
        else:
            # 일반 노드 처리: 노드의 모든 statement 평가
            for statement in node.statements:
                self.update_statement_with_variables(statement, out_vars)
        return out_vars

    def update_while_body(self, variables, current_block):
        """
        고정점 분석 결과를 바탕으로 while body 내의 문장들의 Interval을 업데이트합니다.
        :param variables: 수렴된 변수 상태 딕셔너리 (var_name -> Variables 객체)
        :param current_block: 현재 블록 (CFGNode)
        """
        # 1. fixpoint_evaluation_node 찾기
        fixpoint_evaluation_node = self.find_fixpoint_evaluation_node(current_block)
        if not fixpoint_evaluation_node:
            raise ValueError("Join point node not found for the current block.")

        # 2. 루프 내의 모든 노드 수집
        loop_nodes = self.traverse_loop_nodes(fixpoint_evaluation_node)

        # 3. 각 노드의 문장들에 대해 Interval 업데이트
        for node in loop_nodes:
            node_vars = node.variables
            for statement in node.statements:
                self.update_statement_with_variables(statement, node_vars)

    def update_statement_with_variables(self, statement, variables):
        """
        문장의 변수 Interval을 업데이트합니다.
        :param statement: Statement 객체
        :param variables: 변수 상태 딕셔너리 (var_name -> Variables 객체)
        """
        if statement.statement_type == 'assignment':
            # 좌변 변수 이름 추출
            var_name = statement.left.identifier

            # 우변 표현식의 컨텍스트에 따른 분기 처리
            right_expr = statement.right
            if right_expr.context == 'IndexAccessContext':
                # 배열 인덱스 접근 처리
                result = self.evaluate_array_expression(init_expr=right_expr, variables=variables)
                right_interval = result
            elif right_expr.context == 'MemberAccessContext':
                # MemberAccess 처리 (배열의 length 또는 구조체 멤버 접근)
                base_identifier = right_expr.base.identifier
                if base_identifier in variables:
                    base_variable = variables[base_identifier]
                    if isinstance(base_variable, ArrayVariable):
                        # 배열의 멤버 접근 처리 (예: array.length)
                        result = self.evaluate_array_expression(init_expr=right_expr, variables=variables)
                        right_interval = result
                    elif isinstance(base_variable, StructVariable):
                        # 구조체 멤버 접근 처리
                        result = self.evaluate_struct_expression(init_expr=right_expr, variables=variables)
                        right_interval = result
                    else:
                        raise ValueError(f"Unsupported base type for MemberAccess: {type(base_variable)}")
                else:
                    raise ValueError(f"Variable '{base_identifier}' not found in variables.")
            elif right_expr.context == 'InlineArrayExpressionContext':
                # InlineArrayExpression 처리
                result = self.evaluate_array_expression(right_expr, variables)
                right_intervals = result  # 배열 요소들의 Interval 리스트
                # 좌변 변수가 배열인지 확인
                if var_name in variables:
                    var_obj = variables[var_name]
                    if isinstance(var_obj, ArrayVariable):
                        # 배열 변수의 요소들을 업데이트
                        for idx, interval in enumerate(right_intervals):
                            if idx < len(var_obj.elements):
                                var_obj.elements[idx].value = interval
                            else:
                                # 배열 크기를 초과하는 경우 새로운 요소 추가
                                elem_identifier = f"{var_name}[{idx}]"
                                elem_var = Variables(
                                    identifier=elem_identifier,
                                    value=interval,
                                    isConstant=False,
                                    scope=var_obj.scope
                                )
                                elem_var.typeInfo = var_obj.typeInfo.arrayBaseType
                                var_obj.elements.append(elem_var)
                    else:
                        raise TypeError(f"Variable '{var_name}' is not an ArrayVariable.")
                else:
                    raise ValueError(f"Variable '{var_name}' not found in variables.")
                right_interval = None  # 배열 전체를 업데이트하므로 단일 Interval은 없음
            else:
                # 기본 표현식 처리
                right_interval = self.evaluate_expression(right_expr, variables)

            # 복합 할당 연산자 처리
            if statement.operator != '=':
                if var_name in variables:
                    left_value = variables[var_name].value
                    new_value = self.process_compound_assignment(left_value, right_interval, statement.operator)
                    variables[var_name].value = new_value
                else:
                    raise ValueError(f"Variable '{var_name}' not found in variables.")
            else:
                if var_name in variables:
                    if isinstance(variables[var_name], ArrayVariable) and right_interval is None:
                        # 이미 배열 요소들이 업데이트되었으므로 추가 작업 필요 없음
                        pass
                    else:
                        variables[var_name].value = right_interval
                else:
                    raise ValueError(f"Variable '{var_name}' not found in variables.")

    def refine_interval(self, var_interval, value_interval, operator):
        # 조건 연산자에 따라 변수의 Interval을 좁힘
        if operator == '==':
            return var_interval.intersect(value_interval)
        elif operator == '!=':
            return var_interval.subtract(value_interval)
        elif operator == '<':
            return var_interval.less_than(value_interval)
        elif operator == '>':
            return var_interval.greater_than(value_interval)
        elif operator == '<=':
            return var_interval.less_than_or_equal(value_interval)
        elif operator == '>=':
            return var_interval.greater_than_or_equal(value_interval)
        else:
            return var_interval  # 변경하지 않음

    def negate_operator(self, operator):
        negations = {
            '==': '!=',
            '!=': '==',
            '<': '>=',
            '>': '<=',
            '<=': '>',
            '>=': '<'
        }
        return negations.get(operator, operator)

    def analyze_function_call(self, function_name, function_args):
        # 함수의 리턴 타입과 Interval을 추론
        # 함수의 정의를 분석하거나 사전 정의된 정보를 활용
        # 여기서는 간단한 예제로 기본 Interval을 반환
        # 실제 구현에서는 함수의 내용에 따라 리턴값을 추론해야 함
        if function_name == 'getRandomNumber':
            # 예시: getRandomNumber 함수가 0부터 100 사이의 값을 반환한다고 가정
            return IntegerInterval(0, 100, 256)
        else:
            # 알 수 없는 함수의 경우 보수적인 Interval 반환
            return IntegerInterval(None, None, 256)

    def get_current_block(self):
        """
        현재 코드 위치에서 들어갈 CFG 블록을 결정하는 함수입니다.
        블록 아웃을 감지하여 필요한 처리를 수행합니다.
        """
        closeBraceQueue = []

        # 현재 라인부터 위로 올라가면서 brace_count 검사
        for line in range(self.current_start_line - 1, 0, -1):
            brace_info = self.brace_count.get(line, {'open': 0, 'close': 0, 'cfg_node': None})

            if not closeBraceQueue:
                # closeBraceQueue가 비어있는 경우
                if brace_info['cfg_node'] is None and brace_info['open'] == 0 and brace_info['close'] == 0:
                    # 공백 라인 또는 처리할 것이 없는 라인
                    continue
                elif brace_info['cfg_node'] is not None and brace_info['open'] == 0 and brace_info['close'] == 0:
                    # 분기가 없는 일반적인 문장인 경우
                    return brace_info['cfg_node']
                elif brace_info['cfg_node'] is not None and brace_info['open'] == 1 and brace_info['close'] == 0:
                    # 여는 중괄호 '{'를 만난 경우 (entry point 또는 조건 노드)
                    cfg_node = brace_info['cfg_node']
                    if cfg_node.name == "ENTRY":
                        # ENTRY 노드인 경우 새로운 블록 생성 및 반환
                        if self.current_target_function_cfg:
                            entry_node = self.current_target_function_cfg.get_entry_node()
                            new_block = CFGNode(f"Block_{self.current_start_line}")
                            # related_variables 딕셔너리를 복사하고 새로운 블록에 할당
                            new_block.variables = self.copy_variables(
                                self.current_target_function_cfg.related_variables)
                            self.current_target_function_cfg.graph.add_node(new_block)
                            self.current_target_function_cfg.graph.add_edge(entry_node, new_block)
                            return new_block
                        else:
                            raise ValueError("No active function CFG found.")
                    elif cfg_node.condition_node:
                        # 조건 노드인 경우 해당 블록 반환
                        if cfg_node.condition_node_type == 'if':  # if 블록이면 true_block 반환
                            return self.get_true_block(cfg_node)
                        elif cfg_node.condition_node_type == 'else if':  # else_if 블록이면 true_block 반환
                            return self.get_true_block(cfg_node)
                        elif cfg_node.condition_node_type == 'else':  # else 블록이면 false_block 반환
                            return self.get_false_block(cfg_node)
                        elif cfg_node.condition_node_type == 'while' :
                            return self.get_true_block(cfg_node)
                        else:
                            continue  # 다른 조건 노드는 건너뛰기
                    else:
                        # 기타 경우 해당 노드 반환
                        return cfg_node
                elif brace_info['cfg_node'] is None and brace_info['open'] == 0 and brace_info['close'] == 1:
                    # 닫는 중괄호 '}'를 만난 경우 (블록 아웃 감지)
                    closeBraceQueue.append(line)
            else:
                # closeBraceQueue가 비어있지 않은 경우 (추가적인 블록 아웃 감지)
                if brace_info['cfg_node'] is None and brace_info['open'] == 0 and brace_info['close'] == 1:
                    # 또 다른 블록 아웃을 감지
                    closeBraceQueue.append(line)
                elif brace_info['cfg_node'] is None and brace_info['open'] == 0 and brace_info['close'] == 0:
                    # 공백 라인 또는 처리할 것이 없는 라인
                    continue
                else:
                    # 블록 아웃 탐색 완료
                    break

        # 블록 아웃 처리
        if closeBraceQueue:
            return self.process_flow_join(closeBraceQueue)
        else:
            raise ValueError("No active function CFG found.")

    def process_flow_join(self, closeBraceQueue):
        """
        블록 아웃을 처리하는 함수입니다.
        :param closeBraceQueue: 블록 아웃이 감지된 라인 번호의 리스트
        :return: 블록 아웃 처리 후의 CFG 노드
        """
        outSideIfNode = None
        newBlock = None
        hasNode = False

        # closeBraceQueue에서 각 닫는 중괄호에 대해 처리
        for line in closeBraceQueue:
            openBrace = self.find_corresponding_open_brace(line)
            if not openBrace:
                raise ValueError("No open brace are found.")

            cfg_node = openBrace['cfg_node']

            if cfg_node.condition_node_type == "while":
                # while 루프의 경우 고정점 분석 수행
                newBlock = self.apply_fixpoint_to_exit_node(cfg_node)
                break  # while 루프의 블록 아웃 처리는 여기서 종료
            elif not hasNode and cfg_node.condition_node_type == "if":
                outSideIfNode = cfg_node
                hasNode = True

        if hasNode and outSideIfNode:
            newBlock = self.join_leaf_nodes(outSideIfNode)

            # **새로운 블록을 그래프에 추가 및 연결**
            # 조건 노드의 successor들을 새로운 블록의 successor로 설정
            successors = list(self.current_target_function_cfg.graph.successors(outSideIfNode))
            for succ in successors:
                # 조건 노드와 successor 간의 에지를 제거하고, 새로운 블록과 successor를 연결
                self.current_target_function_cfg.graph.remove_edge(outSideIfNode, succ)
                self.current_target_function_cfg.graph.add_edge(newBlock, succ)

            # 조건 노드에서 새로운 블록으로 에지를 추가
            self.current_target_function_cfg.graph.add_edge(outSideIfNode, newBlock)

            return newBlock
        else:
            # 블록 아웃 처리가 완료되지 않았거나 처리할 노드가 없는 경우
            return None

    def apply_fixpoint_to_exit_node(self, while_node):
        """
        함수 호출 시 while 루프의 exit 노드에 고정점 계산된 변수 상태를 적용하고 exit 노드를 반환합니다.
        :param while_node: while 루프의 조건 노드 (CFGNode)
        :return: while 루프의 exit 노드 (CFGNode)
        """
        # 1. 루프의 exit 노드 찾기
        exit_nodes = self.find_loop_exit_nodes(while_node)
        if not exit_nodes:
            raise ValueError("While loop does not have an exit node.")
        exit_node = exit_nodes[0]  # 일반적으로 exit 노드는 하나일 것입니다.

        # 2. 루프 내의 모든 노드 수집
        loop_nodes = self.traverse_loop_nodes(while_node)

        # 3. 변수 상태 초기화
        in_vars = {}
        out_vars = {}
        for node in loop_nodes:
            in_vars[node] = {}
            out_vars[node] = {}
            if node == while_node:
                # while 루프의 진입 시점 변수 상태 초기화
                in_vars[node] = self.copy_variables(while_node.variables)

        # 4. 워크리스트 알고리즘 초기화
        worklist = deque([while_node])
        max_iterations = 30  # 최대 반복 횟수 설정
        iteration = 0

        while worklist and iteration < max_iterations:
            iteration += 1
            node = worklist.popleft()

            # 5. 선행 노드들의 out_vars를 조인하여 in_vars 계산
            predecessors = list(self.current_target_function_cfg.graph.predecessors(node))
            new_in_vars = None  # None으로 초기화하여 첫 번째 조인 시 설정되도록 함
            for pred in predecessors:
                if pred in loop_nodes:
                    # pred가 루프 내의 노드인 경우
                    if pred in out_vars and out_vars[pred]:
                        if new_in_vars is None:
                            new_in_vars = self.copy_variables(out_vars[pred])
                        else:
                            new_in_vars = self.join_variables(new_in_vars, out_vars[pred])
                else:
                    # pred가 루프 밖의 노드인 경우
                    if new_in_vars is None:
                        new_in_vars = self.copy_variables(pred.variables)
                    else:
                        new_in_vars = self.join_variables(new_in_vars, pred.variables)

            # 6. in_vars 변화 확인
            if new_in_vars:
                if not self.variables_equal(in_vars[node], new_in_vars):
                    in_vars[node] = new_in_vars

            # 7. 노드의 transfer function 적용하여 out_vars 계산
            old_out_vars = out_vars[node]
            out_vars[node] = self.transfer_function(node, in_vars[node])

            # 8. out_vars 변화 확인 및 워크리스트 업데이트
            if not self.variables_equal(old_out_vars, out_vars[node]):
                successors = list(self.current_target_function_cfg.graph.successors(node))
                for succ in successors:
                    if succ in loop_nodes:
                        worklist.append(succ)

            if iteration == max_iterations:
                print("Fixpoint analysis did not converge within max iterations.")
                break

        # 9. 수렴된 변수 상태를 exit 노드에 반영
        exit_node.variables = out_vars[exit_node]

        # 10. exit 노드 반환
        return exit_node

    def find_loop_exit_nodes(self, while_node):
        """
        주어진 while 노드의 루프 exit 노드를 찾습니다.
        :param while_node: while 루프의 조건 노드
        :return: 루프 exit 노드들의 리스트
        """
        exit_nodes = []
        visited = set()
        stack = [while_node]

        while stack:
            current_node = stack.pop()
            if current_node in visited:
                continue
            visited.add(current_node)

            successors = list(self.current_target_function_cfg.graph.successors(current_node))
            for succ in successors:
                if succ == while_node:
                    # 루프 백 엣지이므로 무시
                    continue
                if not self.is_node_in_loop(succ, while_node):
                    # 루프 밖의 노드이면 exit 노드로 추가
                    exit_nodes.append(succ)
                else:
                    stack.append(succ)

        return exit_nodes

    def is_node_in_loop(self, node, while_node):
        """
        주어진 노드가 while 루프 내에 속해 있는지 확인합니다.
        :param node: 확인할 노드
        :param while_node: while 루프의 조건 노드
        :return: True 또는 False
        """
        # while_node에서 시작하여 루프 내의 모든 노드를 수집하고, 그 안에 node가 있는지 확인
        loop_nodes = self.traverse_loop_nodes(while_node)
        return node in loop_nodes

    def find_corresponding_open_brace(self, close_line):
        """
        닫는 중괄호에 대응되는 여는 중괄호를 찾는 함수입니다.
        :param close_line: 닫는 중괄호 라인 번호
        :return: 여는 중괄호의 brace_info 딕셔너리
        """
        contextDiff = 0
        for line in range(close_line, 0, -1):
            brace_info = self.brace_count.get(line, {'open': 0, 'close': 0, 'cfg_node': None})
            contextDiff += brace_info['open'] - brace_info['close']

            if contextDiff == 0 and brace_info['open'] > 0:
                cfg_node = brace_info['cfg_node']
                if cfg_node and cfg_node.condition_node_type in ["while", "if"]:
                    return brace_info
                elif cfg_node and cfg_node.condition_node_type in ["else if", "else"] :
                    continue
        return None

    def join_leaf_nodes(self, condition_node):
        """
        주어진 조건 노드의 하위 그래프를 탐색하여 리프 노드들을 수집하고 변수 정보를 조인합니다.
        :param condition_node: 최상위 조건 노드 (if 노드)
        :return: 조인된 변수 정보를 가진 새로운 블록
        """
        # 리프 노드 수집
        leaf_nodes = self.collect_leaf_nodes(condition_node)

        # 리프 노드들의 변수 정보를 조인
        joined_variables = {}
        for node in leaf_nodes:
            if node.function_exit_node:
                continue
            for var_name, var_value in node.variables.items():
                if var_name in joined_variables:
                    # 기존 변수와 조인
                    joined_variables[var_name] = self.join_variable_values(joined_variables[var_name], var_value)
                else:
                    # 새로운 변수 추가
                    joined_variables[var_name] = var_value

        # 새로운 블록 생성 및 변수 정보 저장
        new_block = CFGNode(name=f"JoinBlock_{self.current_start_line}")
        new_block.variables = joined_variables

        # **CFG 그래프에 새로운 블록 추가**
        self.current_target_function_cfg.graph.add_node(new_block)

        # **리프 노드들과 새로운 블록을 에지로 연결**
        for node in leaf_nodes:
            # 기존의 successor가 없으므로, 리프 노드에서 new_block으로 에지를 연결
            self.current_target_function_cfg.graph.add_edge(node, new_block)

        # **조건 노드의 successor를 새로운 블록으로 연결**
        successors = list(self.current_target_function_cfg.graph.successors(condition_node))
        for succ in successors:
            # 조건 노드와 successor 간의 에지를 제거하고, 새로운 블록과 successor를 연결
            self.current_target_function_cfg.graph.remove_edge(condition_node, succ)
            self.current_target_function_cfg.graph.add_edge(new_block, succ)

        return new_block

    def collect_leaf_nodes(self, node):
        """
        주어진 노드의 하위 그래프를 탐색하여 리프 노드들을 수집합니다.
        :param node: 시작 노드
        :return: 리프 노드들의 리스트
        """
        leaf_nodes = []
        visited = set()
        stack = [node]

        while stack:
            current_node = stack.pop()
            if current_node in visited:
                continue
            visited.add(current_node)

            successors = list(self.current_target_function_cfg.graph.successors(current_node))
            if not successors:
                # 자식이 없는 노드 (리프 노드)
                leaf_nodes.append(current_node)
            else:
                # 자식 노드가 있는 경우 스택에 추가
                for successor in successors:
                    stack.append(successor)

        return leaf_nodes

    def join_variable_values(self, value1, value2):
        """
        두 변수의 값을 조인합니다.
        :param value1: 첫 번째 변수의 값 (Interval 등)
        :param value2: 두 번째 변수의 값 (Interval 등)
        :return: 조인된 값
        """
        # 두 값이 모두 Interval의 인스턴스인지 확인
        if isinstance(value1, Interval) and isinstance(value2, Interval):
            # 동일한 타입의 Interval인지 확인
            if type(value1) is type(value2):
                # 동일한 타입의 Interval이면 해당 타입의 join 메소드 호출
                return value1.join(value2)
            else:
                # 타입이 다른 Interval이면 예외 발생 또는 업캐스팅하여 처리
                # 여기서는 예외를 발생시킵니다.
                raise TypeError(
                    f"Cannot join intervals of different types: {type(value1).__name__} and {type(value2).__name__}")
        else:
            # Interval이 아닌 경우, 그대로 value1을 반환하거나 적절히 처리
            return value1

    def update_variables_at_node(self, node, variables):
        """
        주어진 노드의 변수 정보를 업데이트합니다.
        :param node: 대상 노드
        :param variables: 업데이트할 변수 딕셔너리
        """
        node.variables = variables.copy()

    def traverse_loop_nodes(self, loop_node):
        """
        루프 노드부터 시작하여 루프 내의 노드들을 순회합니다.
        :param loop_node: 루프의 조건 노드
        :return: 루프 내의 노드들
        """
        visited = set()
        stack = [loop_node]
        loop_nodes = []

        while stack:
            current_node = stack.pop()
            if current_node in visited:
                continue
            visited.add(current_node)
            loop_nodes.append(current_node)

            successors = list(self.current_target_function_cfg.graph.successors(current_node))
            for successor in successors:
                # 간선의 조건을 확인하여 false_branch를 건너뜀
                edge_data = self.current_target_function_cfg.graph.get_edge_data(current_node, successor)
                if edge_data and edge_data.get('condition') == False:  # False branch는 제외
                    continue

                # False branch가 아니면 순회 계속
                stack.append(successor)
                #if successor != loop_node.false_branch:
                #    stack.append(successor)

        return loop_nodes

    def get_true_block(self, condition_node):
        contract_cfg = self.contract_cfgs[self.current_target_contract]
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        function_cfg = contract_cfg.get_function_cfg(self.current_target_function)
        if not function_cfg:
            raise ValueError("No active function to process the require statement.")

        # 해당 조건 노드에서 true일 때 실행될 블록을 찾아 리턴
        successors = list(function_cfg.graph.successors(condition_node))
        for successor in successors:
            if function_cfg.graph.edges[condition_node, successor].get('condition', False):
                return successor
        return None  # True 블록을 찾지 못하면 None 반환

    def get_false_block(self, condition_node):
        contract_cfg = self.contract_cfgs[self.current_target_contract]
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        function_cfg = contract_cfg.get_function_cfg(self.current_target_function)
        if not function_cfg:
            raise ValueError("No active function to process the require statement.")

        # 해당 조건 노드에서 false일 때 실행될 블록을 찾아 리턴
        successors = list(self.function_cfg.graph.successors(condition_node))
        for successor in successors:
            if not function_cfg.graph.edges[condition_node, successor].get('condition', False):
                return successor
        return None  # False 블록을 찾지 못하면 None 반환

    def find_corresponding_condition_node(self): # else if, else에 대한 처리
        # 현재 라인부터 위로 탐색하면서 대응되는 조건 노드를 찾음
        target_brace = 0
        for line in range(self.current_start_line - 1, 0, -1):
            brace_info = self.brace_count[line]
            if brace_info:
                # '{'와 '}'의 개수 확인
                if brace_info['open'] == 1:
                    target_brace -= 1
                elif brace_info['close'] == 1:
                    target_brace += 1

                # target_brace가 0이 되면 대응되는 블록을 찾은 것
                if target_brace == 0:
                    if brace_info['cfg_node'] != None and \
                            brace_info['cfg_node'].condition_node_type in ['if', 'else if']:
                        return brace_info['cfg_node']
        return None


    """
    Abstract Interpretation part
    """

    @staticmethod
    def calculate_default_interval(var_type):
        # 1. int 타입 처리
        if var_type.startswith("int"):
            length = int(var_type[3:]) if var_type != "int" else 256  # int 타입의 길이 (기본값은 256)
            return IntegerInterval.bottom(length)  # int의 기본 범위 반환

        # 2. uint 타입 처리
        elif var_type.startswith("uint"):
            length = int(var_type[4:]) if var_type != "uint" else 256  # uint 타입의 길이 (기본값은 256)
            return UnsignedIntegerInterval.bottom(length)  # uint의 기본 범위 반환

        # 3. bool 타입 처리
        elif var_type == "bool":
            return BoolInterval()  # bool은 항상 0 또는 1

        # 4. 기타 처리 (필요시 확장 가능)
        else:
            raise ValueError(f"Unsupported type for default interval: {var_type}")

    def evaluate_expression(self, expr: Expression, variables: Variables, callerObject=None, callerContext=None):
        if expr.context == "LiteralExpContext":
            return self.evaluate_literal_context(expr, variables, callerObject, callerContext)
        elif expr.context == "IdentifierExpContext" :
            return self.evaluate_identifier_context(expr, variables, callerObject, callerContext)
        elif expr.context == 'MemberAccessContext' :
            return self.evaluate_member_access_context(expr, variables, callerObject, callerContext)
        elif expr.context == "IndexAccessContext" :
            return self.evaluate_index_access_context(expr, variables, callerObject, callerContext)
        elif expr.context == "TypeConversionContext" :
            return self.evaluate_type_conversion_context(expr, variables, callerObject, callerContext)
        elif expr.context == "ConditionalExpContext" :
            return self.evaluate_conditional_expression_context(expr, variables, callerObject, callerContext)
        elif expr.context == "InlineArrayExpression" :
            return self.evaluate_inline_array_expression_context(expr, variables, callerObject, callerContext)

        # 단항 연산자
        if expr.operator in ['-', '!', '~'] and expr.expression :
            return self.evaluate_unary_operator(expr, variables, callerObject, callerContext)

        # 이항 연산자
        if expr.left is not None and expr.right is not None :
            return self.evaluate_binary_operator(expr, variables, callerObject, callerContext)

    def evaluate_literal_context(self, expr: Expression, variables, callerObject=None, callerContext=None):
        literal_str = expr.literal  # 예: "123", "0x1A", "true", "false", "Hello", ...
        expr_type = expr.expr_type  # 예: 'uint', 'int', 'bool', 'string'

        # 1) if we have a callerObject that is an ArrayVariable, and the literal is a digit
        if callerObject is not None :
            if isinstance(callerObject, ArrayVariable) :
                if literal_str.isdigit() :
                    # 인덱스로 해석 (음수인지도 체크 가능)
                    idx = int(literal_str)
                    if idx < 0 or idx >= len(callerObject.elements):
                        raise IndexError(f"Index {idx} out of range in array '{callerObject.identifier}'")
                    return callerObject.elements[idx]  # element: Variables, ArrayVariable, etc.
                else:
                    raise ValueError(
                        f"Array '{callerObject.identifier}' index must be integer literal, got '{literal_str}'")

            # 1-2) MappingVariable
            elif isinstance(callerObject, MappingVariable):
                # 맵핑 키로 사용. Solidity에선 key가 uint/address/bytes 등 가능하나,
                # 여기선 예시로 'string' key 로 처리
                if literal_str in callerObject.mapping:
                    return callerObject.mapping[literal_str]
                else:
                    # 새로 엔트리 생성
                    new_var_obj = self.create_default_mapping_value(callerObject, literal_str)

                    # callerObject.mapping[literal_str] = new_var_obj
                    # state_variable_node / function_cfg 둘 다 업데이트
                    self.update_mapping_in_cfg(callerObject.identifier, literal_str, new_var_obj)

                    return new_var_obj.value

        if callerContext is not None : # callerObject는 없고 callerContext가 있는 경우
            if callerContext == "IndexAccessContext" : # ident_str이 literal 이면서 IndexAccess면 mapping key 호출 밖에 없을듯?
                return literal_str

        # callerObject, callerContext 둘다 없으면 그냥 값 리턴
        if expr_type == "uint":
            # int() with base=0로 파싱해 다양한 16진/10진 포맷 허용
            val = int(literal_str, 0)
            if val < 0:
                raise ValueError(f"Literal '{literal_str}' is negative, not valid for uint.")
            # 기본 비트 길이 설정
            length = expr.type_length if expr.type_length else 256
            return UnsignedIntegerInterval(val, val, length)

        elif expr_type == "int":
            val = int(literal_str, 0)
            length = expr.type_length if expr.type_length else 256
            return IntegerInterval(val, val, length)

        elif expr_type == "bool":
            lower_str = literal_str.lower()
            if lower_str == "true":
                return BoolInterval(1, 1)
            elif lower_str == "false":
                return BoolInterval(0, 0)
            else:
                raise ValueError(f"Invalid boolean literal '{literal_str}'")

        elif expr_type == "string":
            # 여기서 그대로 문자열 반환.
            # 필요하면 앞뒤 따옴표 제거 로직도 추가할 수 있음.
            return literal_str

        else:
            raise ValueError(f"Unsupported literal expr_type '{expr_type}'")

    def evaluate_identifier_context(self, expr:Expression, variables, callerObject=None, callerContext=None):
        ident_str = expr.identifier

        if callerObject is not None:
            if isinstance(callerObject, ArrayVariable) :
                if ident_str not in variables:
                    raise ValueError(f"Index identifier '{ident_str}' not found in variables.")
                index_var_obj = variables[ident_str]
                if isinstance(index_var_obj, Variables) :
                    if index_var_obj.value.min_value == index_var_obj.value.max_value:
                        idx = index_var_obj.value.min_value
                else :
                    raise ValueError(f"This excuse should be analyzed : '{ident_str}'")

                # 경계검사
                if idx < 0 or idx >= len(callerObject.elements):
                    raise IndexError(f"Index {idx} out of range in array '{callerObject.identifier}'")
                return callerObject.elements[idx]

            elif isinstance(callerObject, StructVariable) :
                if ident_str not in callerObject.members:
                    raise ValueError(f"member identifier '{ident_str}' not found in struct variables.")

                var = callerObject.members[ident_str]

                if isinstance(var, Variables) :
                    return var.value

        # callerObject가 없는 경우
        if callerContext is not None :
            if callerContext in ["IndexAccessContext", "MemberAccessContext", "IndexRangeAccessContext"] : # base에 대한 접근
                if ident_str in variables :
                    return variables[ident_str] # ArrayVariable, StructVariable 자체를 리턴
                else :
                    raise ValueError(f"This '{ident_str}' is may be array or struct but may not be declared")

        # callerContext, callerObject 둘다 없는 경우
        if ident_str in variables: # variables에 있으면
            return variables[ident_str].value # 해당 value 리턴
        else:
            raise ValueError(f"This '{ident_str}' is may be elementary variable but may not be declared")

    def evaluate_member_access_context(self, expr: Expression, variables, callerObject=None, callerContext=None):

        # 1. base expression 재귀적으로 평가
        base_val = self.evaluate_expression(expr.base, variables, None, "MemberAccessContext")
        member = expr.member

        # 2. 글로벌 변수 접근 (예: block, msg, tx)
        if isinstance(base_val, str) and base_val in ["block", "msg", "tx"]:
            if isinstance(member, str) :
                full_name = f"{base_val}.{member}"
                # 예시 글로벌 변수 매핑 (실제 구현 시 더 구체적인 값/Interval 필요)
                contract_cfg = self.contract_cfgs.get(self.current_target_contract)

                if full_name in contract_cfg.pre_exec_globals:
                    return contract_cfg.pre_exec_globals[full_name].value
                else:
                    global_map = {
                        "block.basefee": UnsignedIntegerInterval(1000, 1000, 256),
                        "block.blobbasefee": UnsignedIntegerInterval(1000, 1000, 256),
                        "block.chainid": UnsignedIntegerInterval(1000, 1000, 256),
                        "block.coinbase": "address 0",
                        "block.difficulty": UnsignedIntegerInterval(1000, 1000, 256),
                        "block.gaslimit": UnsignedIntegerInterval(1000, 1000, 256),
                        "block.number": UnsignedIntegerInterval(1000, 1000, 256),
                        "block.prevrandao": UnsignedIntegerInterval(1000, 1000, 256),
                        "block.timestamp": UnsignedIntegerInterval(1000, 1000, 256),
                        "msg.sender": "address 100",
                        "msg.value": UnsignedIntegerInterval(1000, 1000, 256),
                        "tx.gasprice": UnsignedIntegerInterval(1000, 1000, 256),
                        "tx.origin": "address 10"
                    }
                    return global_map[full_name]
            else :
                ValueError(f"member '{member}' is not global variable member'.")

        elif isinstance(base_val, str) and base_val in variables : # base_val이 variables에 들어있는 경우
            variable_obj = variables[base_val]

            # 3. 배열의 내장 속성 접근 (예: myArray.length)
            if isinstance(variable_obj, ArrayVariable) :
                if member.context == "IdentifierContext" :
                    memberVal = self.evaluate_expression(member, variables, None, "MemberAccessContext")
                    if isinstance(memberVal, str) :
                        if memberVal == "length":
                            # 배열 크기 = elements 길이
                            length_val = len(variable_obj.elements)
                            return UnsignedIntegerInterval(length_val, length_val, 256)

            # 4. 구조체 필드 접근 (base가 dict인 경우)
            elif isinstance(variable_obj, StructVariable) :
                if member.context == "IdentifierContext" :
                    return self.evaluate_expression(member, variables, variable_obj, "MemberAccessContext")
                elif member.context == "MemberAccessContext" :
                    memberBaseVal = self.evaluate_expression(member.base, variables, None, "MemberAccessContext")
                elif member.context == "IndexAccessContext" :
                    pass



        # 5. 타입 정보 접근 (예: type(uint256).max, type(uint256).min)
        if isinstance(base_val, dict) and base_val.get("isType", False):
            T = base_val["typeName"]
            if member == "max":
                if T.startswith("uint"):
                    length = int(T[4:]) if len(T) > 4 else 256
                    return UnsignedIntegerInterval(2 ** length - 1, 2 ** length - 1, length)
                elif T.startswith("int"):
                    length = int(T[3:]) if len(T) > 3 else 256
                    return IntegerInterval(2 ** (length - 1) - 1, 2 ** (length - 1) - 1, length)
                else:
                    raise ValueError(f"Unsupported type for max: {T}")
            elif member == "min":
                if T.startswith("uint"):
                    return UnsignedIntegerInterval(0, 0, 256)
                elif T.startswith("int"):
                    length = int(T[3:]) if len(T) > 3 else 256
                    return IntegerInterval(-2 ** (length - 1), -2 ** (length - 1), length)
                else:
                    raise ValueError(f"Unsupported type for min: {T}")
            else:
                raise ValueError(f"Unsupported type member '{member}' for type '{T}'")

        # 6. Enum 멤버 접근 (base가 enum type을 나타내는 dict)
        if isinstance(base_val, dict) and "enumType" in base_val:
            enum_type = base_val["enumType"]
            # 심볼릭하게 "EnumType.Member"를 리턴 (실제 구현은 contract_cfg에서 값 조회 필요)
            return f"{enum_type}.{member}"

        # 7. 컨트랙트 인스턴스 접근 (base가 contract instance를 나타내는 dict)
        if isinstance(base_val, dict) and "contractInstance" in base_val:
            if member == "address":
                return base_val["address"]
            return f"{base_val['contractInstance']}.{member}"

        # 8. 라이브러리 확장 메소드 (callerContext가 "library")
        if callerObject == "library":
            return f"library_function({base_val}).{member}"

        # 9. 만약 위 케이스에 해당하지 않으면 심볼릭하게 표현
        return f"symbolic({base_val}.{member})"

    def evaluate_index_access_context(self, expr, variables, callerObject=None, callerContext=None):
        return

    def evaluate_type_conversion_context(self, expr, variables, callerObject=None, callerContext=None):
        return

    def evaluate_conditional_expression_context(self, expr, variables, callerObject=None, callerContext=None):
        return

    def evaluate_inline_array_expression_context(self, expr, variables, callerObject=None, callerContext=None):
        return

    def evaluate_unary_operator(self, expr, variables, callerObject=None, callerContext=None):
        operand_interval = self.evaluate_expression(expr.expression, variables, None, "Unary")
        if operand_interval is not None:
            if expr.operator == '-':
                return operand_interval.negate()
            elif expr.operator == '!':
                return operand_interval.logical_not()
            elif expr.operator == '~':
                return operand_interval.bitwise_not()
        else:
            raise ValueError(f"Unable to evaluate operand in unary expression: {expr}")

    def evaluate_binary_operator(self, expr, variables, callerObject=None, callerContext=None):
        leftInterval = self.evaluate_expression(expr.left, variables, None, "Binary")
        rightInterval = self.evaluate_expression(expr.right, variables, None, "Binary")
        operator = expr.operator

        if operator == '+':
            return leftInterval.add(rightInterval)
        elif operator == '-':
            return leftInterval.subtract(rightInterval)
        elif operator == '*':
            return leftInterval.multiply(rightInterval)
        elif operator == '/':
            return leftInterval.divide(rightInterval)
        elif operator == '%':
            return leftInterval.modulo(rightInterval)
        elif operator == '**':
            return leftInterval.exponentiate(rightInterval)
        # 시프트 연산자 처리
        elif operator in ['<<', '>>', '>>>']:
            if 'int' in expr.expr_type:
                return IntegerInterval.shift(leftInterval, rightInterval, operator)
            elif 'uint' in expr.expr_type:
                return UnsignedIntegerInterval.shift(leftInterval, rightInterval, operator)
            else:
                raise ValueError(f"Unsupported type '{expr.expr_type}' for shift operation")
        # 비교 연산자 처리
        elif operator in ['==', '!=', '<', '>', '<=', '>=']:
            return self.compare_intervals(leftInterval, rightInterval, operator)
        # 논리 연산자 처리
        elif operator in ['&&', '||']:
            return leftInterval.logical_op(rightInterval, operator)
        else:
            raise ValueError(f"Unsupported operator '{operator}' in expression: {expr}")


    def evaluate_array_expression(self, variable_obj=None, init_expr=None, variables=None):
        return

    def evaluate_enum_expression(self, expr, variables=None):
        return

    def evaluate_struct_expression(self, variable_obj, init_expr):
        return

    def create_default_mapping_value(self, mappingVar: MappingVariable, key_str: str):
        """
        mappingVar: MappingVariable
        key_str: 키 문자열
        이 매핑에 새로 들어갈 기본값(Variables 객체)을 생성해 반환
        예: int/uint -> 0, bool -> False, ...
        """
        value_type_info = mappingVar.typeInfo.mappingValueType
        # 일단 elementary 가정
        if value_type_info.elementaryTypeName.startswith("int"):
            length = value_type_info.intTypeLength or 256
            zero_interval = IntegerInterval(0, 0, length)
            new_obj = Variables(identifier=f"{mappingVar.identifier}[{key_str}]",
                                value=zero_interval,
                                typeInfo=value_type_info)
            mappingVar.mapping[key_str] = new_obj
            return new_obj
        elif value_type_info.elementaryTypeName.startswith("uint"):
            length = value_type_info.intTypeLength or 256
            zero_interval = UnsignedIntegerInterval(0, 0, length)
            new_obj = Variables(identifier=f"{mappingVar.identifier}[{key_str}]",
                                value=zero_interval,
                                typeInfo=value_type_info)
            mappingVar.mapping[key_str] = new_obj
            return new_obj
        elif value_type_info.elementaryTypeName == "bool":
            bool_obj = Variables(identifier=f"{mappingVar.identifier}[{key_str}]",
                                 value=BoolInterval(0, 0),
                                 typeInfo=value_type_info)
            mappingVar.mapping[key_str] = bool_obj
            return bool_obj
        else:
            # fallback for other types - struct, array, ...
            # possibly create a symbolic placeholder
            sym_obj = Variables(identifier=f"{mappingVar.identifier}[{key_str}]",
                                value=f"symbolicDefault({value_type_info.elementaryTypeName})",
                                typeInfo=value_type_info)
            mappingVar.mapping[key_str] = sym_obj
            return sym_obj

    def update_mapping_in_cfg(self, mapVarName: str, key_str: str, new_var_obj: Variables):
        """
        mapVarName: "myMapping"
        key_str: "someKey"
        new_var_obj: 새로 만든 Variables(...) for the mapping value
        여기에 state_variable_node, function_cfg 등을 업데이트
        """
        contract_cfg = self.contract_cfgs.get(self.current_target_contract)
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # state_variable_node 갱신
        if contract_cfg.state_variable_node and mapVarName in contract_cfg.state_variable_node.variables:
            mapVar = contract_cfg.state_variable_node.variables[mapVarName]
            if isinstance(mapVar, MappingVariable):
                mapVar.mapping[key_str] = new_var_obj

        # 함수 CFG 갱신
        function_cfg = contract_cfg.get_function_cfg(self.current_target_function)
        if function_cfg:
            if mapVarName in function_cfg.related_variables:
                mapVar2 = function_cfg.related_variables[mapVarName]
                if isinstance(mapVar2, MappingVariable):
                    mapVar2.mapping[key_str] = new_var_obj

    def update_variables_with_condition(self, variables, condition_expr, is_true_branch):
        """
        조건식을 분석하여 변수들의 상태(Interval)를 True/False 분기에서 업데이트합니다.
        variables: var_name -> Variables 객체
        condition_expr: 조건식(Expression 객체)
        is_true_branch: True 분기일 경우 True, False 분기일 경우 False
        """

        # 조건 연산자에 따른 변수 업데이트
        if condition_expr.operator in ['==', '!=', '<', '>', '<=', '>=']:
            left_expr = condition_expr.left
            right_expr = condition_expr.right

            # 좌측 표현식이 MemberAccessContext 또는 IndexAccessContext인 경우 처리
            if left_expr.context == 'MemberAccessContext' or left_expr.context == 'IndexAccessContext':
                base_expr = left_expr.base
                var_name = base_expr.identifier

                # 변수 찾기 (배열 또는 구조체 변수 확인)
                if var_name in variables:
                    var_obj = variables[var_name]

                    if isinstance(var_obj, ArrayVariable):
                        left_interval = self.evaluate_array_expression(var_obj, left_expr)
                    elif isinstance(var_obj, StructVariable):
                        left_interval = self.evaluate_struct_expression(var_obj, left_expr)
                        # 매핑 변수 처리
                    elif isinstance(var_obj, MappingVariable):
                        key_expr = left_expr.index  # 인덱스 표현식
                        key_value = self.evaluate_expression(key_expr)  # 매핑 키 값 평가

                        # 매핑에서 특정 키에 해당하는 값을 가져오기
                        if key_value in var_obj.mapping:
                            left_interval = var_obj.mapping[key_value]
                        else:
                            # 키가 매핑에 없는 경우 기본 Interval 설정 (new entry)
                            value_type = var_obj.typeInfo.mappingValueType
                            if value_type.elementaryTypeName.startswith("int"):
                                left_interval = IntegerInterval()
                            elif value_type.elementaryTypeName.startswith("uint"):
                                left_interval = UnsignedIntegerInterval()
                            elif value_type.elementaryTypeName == "bool":
                                left_interval = BoolInterval()
                            else:
                                raise TypeError(
                                    f"Unsupported type '{value_type.elementaryTypeName}' for mapping values")

                            # 매핑에 새로운 키-값 쌍 추가
                            var_obj.mapping[key_value] = Variables(value=left_interval)
                    else:
                        raise TypeError(f"Variable '{var_name}' is neither an array nor a struct.")
                else:
                    raise ValueError(f"Variable '{var_name}' not found in the current context.")
            else:
                # 일반적인 표현식 처리
                left_interval = self.evaluate_expression(left_expr)

            # 우측 표현식 처리 (MemberAccessContext 또는 IndexAccessContext 체크)
            if right_expr.context == 'MemberAccessContext' or right_expr.context == 'IndexAccessContext':
                base_expr = right_expr.base
                var_name = base_expr.identifier

                if var_name in variables:
                    var_obj = variables[var_name]

                    if isinstance(var_obj, ArrayVariable):
                        right_interval = self.evaluate_array_expression(var_obj, right_expr)
                    elif isinstance(var_obj, StructVariable):
                        right_interval = self.evaluate_struct_expression(var_obj, right_expr)
                    else:
                        raise TypeError(f"Variable '{var_name}' is neither an array nor a struct.")
                else:
                    raise ValueError(f"Variable '{var_name}' not found in the current context.")
            else:
                # 일반적인 표현식 처리
                right_interval = self.evaluate_expression(right_expr)

            # 좌측 표현식이 변수인 경우
            if left_expr.identifier:
                var_name = left_expr.identifier
                var_obj = variables.get(var_name)

                if var_obj:
                    # 조건에 따라 변수 Interval 업데이트
                    if is_true_branch:
                        # True 분기에서 조건이 성립하는 경우 Interval 좁히기
                        var_obj.value = self.refine_interval(var_obj.value, right_interval, condition_expr.operator)
                    else:
                        # False 분기에서 조건이 성립하지 않는 경우 Interval 좁히기
                        negated_operator = self.negate_operator(condition_expr.operator)
                        var_obj.value = self.refine_interval(var_obj.value, right_interval, negated_operator)

            elif left_expr.context == 'IndexAccessContext' :
                base_name = left_expr.base.identifier
                var_obj = variables.get(base_name)
                if isinstance(var_obj,MappingVariable) :
                    if is_true_branch :
                        var_obj.mapping[key_value] = self.refine_interval(left_interval, right_interval, condition_expr.operator)
                    else :
                        negated_operator = self.negate_operator(condition_expr.operator)
                        var_obj.mapping[key_value] = self.refine_interval(left_interval, right_interval,
                                                                          negated_operator)

        elif condition_expr.operator in ['&&', '||']:
            # 논리 연산자가 포함된 복합 조건식 처리
            left_expr = condition_expr.left
            right_expr = condition_expr.right

            # 좌측 조건식이 MemberAccessContext 또는 IndexAccessContext인 경우 처리
            if left_expr.context == 'MemberAccessContext' or left_expr.context == 'IndexAccessContext':
                base_expr = left_expr.base
                var_name = base_expr.identifier

                if var_name in variables:
                    var_obj = variables[var_name]

                    if isinstance(var_obj, ArrayVariable):
                        self.evaluate_array_expression(var_obj, left_expr)
                    elif isinstance(var_obj, StructVariable):
                        self.evaluate_struct_expression(var_obj, left_expr)
                    else:
                        raise TypeError(f"Variable '{var_name}' is neither an array nor a struct.")
                else:
                    raise ValueError(f"Variable '{var_name}' not found in the current context.")

            # 우측 조건식이 MemberAccessContext 또는 IndexAccessContext인 경우 처리
            if right_expr.context == 'MemberAccessContext' or right_expr.context == 'IndexAccessContext':
                base_expr = right_expr.base
                var_name = base_expr.identifier

                if var_name in variables:
                    var_obj = variables[var_name]

                    if isinstance(var_obj, ArrayVariable):
                        self.evaluate_array_expression(var_obj, right_expr)
                    elif isinstance(var_obj, StructVariable):
                        self.evaluate_struct_expression(var_obj, right_expr)
                    else:
                        raise TypeError(f"Variable '{var_name}' is neither an array nor a struct.")
                else:
                    raise ValueError(f"Variable '{var_name}' not found in the current context.")

            # 좌우 조건식에 대해 재귀적으로 처리
            self.update_variables_with_condition(variables, left_expr, is_true_branch)
            self.update_variables_with_condition(variables, right_expr, is_true_branch)

    def function_abstract_interpretation(self, function_expr, current_variables):
        """
        주어진 함수 호출 표현식을 abstract interpretation하여 반환 값을 돌려줍니다.
        :param function_expr: Expression 객체 (FunctionCallContext)
        :param current_variables: 현재 변수 상태 딕셔너리
        :return: 함수의 반환 값 (Interval 또는 기타 값)
        """
        # 1. 호출할 함수 이름 추출
        if function_expr.function.identifier:
            function_name = function_expr.function.identifier
        else:
            raise ValueError("Unsupported function expression for function call.")

        # 2. 현재 컨트랙트의 CFG 가져오기
        contract_cfg = self.contract_cfgs.get(self.current_target_contract)
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        function_cfg = contract_cfg.get_function_cfg(function_name)
        if not function_cfg:
            raise ValueError(f"Function '{function_name}' not found in contract '{self.current_target_contract}'.")

        # 이전 함수 컨텍스트 저장
        saved_current_target_function = self.current_target_function
        self.current_target_function = function_name

        # 3. 함수 파라미터, 인자 매핑
        function_params = function_cfg.parameters
        arguments = function_expr.arguments if function_expr.arguments else []
        named_arguments = function_expr.named_arguments if function_expr.named_arguments else {}

        total_params = len(function_params)
        total_args = len(arguments) + len(named_arguments)
        if total_params != total_args:
            raise ValueError(f"Argument count mismatch in function call to '{function_name}'.")

        # function_cfg.related_variables 내 파라미터 변수들에 인자값 할당
        for param_name, arg_expr in zip(function_params, arguments):
            arg_value = self.evaluate_expression(arg_expr, current_variables)
            if param_name in function_cfg.related_variables:
                function_cfg.related_variables[param_name].value = arg_value
            else:
                raise ValueError(f"Parameter '{param_name}' not found in function '{function_name}' variables.")

        for param_name, arg_expr in named_arguments.items():
            if param_name not in function_params:
                raise ValueError(f"Parameter '{param_name}' not found in function '{function_name}'.")
            arg_value = self.evaluate_expression(arg_expr, current_variables)
            if param_name in function_cfg.related_variables:
                function_cfg.related_variables[param_name].value = arg_value
            else:
                raise ValueError(f"Parameter '{param_name}' not found in function '{function_name}' variables.")

        # 4. 함수 CFG 해석
        # 함수 CFG를 재귀적으로 해석
        # interpret_function_cfg가 함수 해석 로직을 가지고 있으며,
        # 함수 내에서 또 다른 함수 호출 시 function_abstract_interpretation이 재귀 호출될 수 있음
        return_value = self.interpret_function_cfg(function_cfg)

        # 컨텍스트 복원
        self.current_target_function = saved_current_target_function

        return return_value

    def interpret_function_cfg(self, function_cfg):
        """
        수정된 interpret_function_cfg 로직 예시
        """
        entry_block = function_cfg.get_entry_node()
        successors = list(function_cfg.graph.successors(entry_block))
        if len(successors) != 1:
            raise ValueError("Entry block must have exactly one successor.")
        start_block = successors[0]

        # block_queue에는 now just nodes, no variables
        block_queue = deque()
        block_queue.append(start_block)

        # 함수 내 변수 환경은 CFG 노드에 저장됨.
        # entry_block의 successor 시작 시, entry_block.variables를 start_block에 전달
        # entry_block.variables는 아마 constructor나 state_variable_node 해석 후 초기값이 세팅되어 있을 것이라 가정
        # start_block은 predecessor가 entry_block 하나이므로 그냥 그 값 복사
        start_block.variables = self.copy_variables(entry_block.variables)

        # return_values를 모아둘 자료구조 (나중에 exit node에서 join)
        return_values = []

        visited = set()

        while block_queue:
            analyzingNode = block_queue.popleft()
            if analyzingNode in visited:
                continue
            visited.add(analyzingNode)

            # 이전 block 분석 결과 반영
            # join_point_node인 경우 predecessor들의 결과를 join한뒤 analyzingNode에 반영
            # 아니면 predecessor 하나가 있을 것이므로 그 predecessor의 variables를 복사
            predecessors = list(function_cfg.graph.predecessors(analyzingNode))

            if analyzingNode.join_point_node:
                # join node 처리
                # predecessor들의 variables를 join
                joined_vars = None
                for pred in predecessors:
                    if joined_vars is None:
                        joined_vars = self.copy_variables(pred.variables)
                    else:
                        joined_vars = self.join_variables(joined_vars, pred.variables)
                analyzingNode.variables = joined_vars
            else:
                # join point가 아니라면 predecessor가 하나라고 가정
                if len(predecessors) == 1:
                    analyzingNode.variables = self.copy_variables(predecessors[0].variables)
                else:
                    raise ValueError("Non-join node with multiple predecessors is unexpected.")

            current_block = analyzingNode
            current_variables = current_block.variables

            # condition node 처리
            if current_block.condition_node:
                condition_expr = current_block.condition_expr

                if current_block.condition_node_type in ["if", "else if"]:
                    # true/false branch 각각 하나의 successor 가정
                    true_successors = [s for s in function_cfg.graph.successors(current_block) if
                                       function_cfg.graph.edges[current_block, s].get('condition') == True]
                    false_successors = [s for s in function_cfg.graph.successors(current_block) if
                                        function_cfg.graph.edges[current_block, s].get('condition') == False]

                    # 각각 한 개라 가정
                    if len(true_successors) != 1 or len(false_successors) != 1:
                        raise ValueError(
                            "if/else if node must have exactly one true successor and one false successor.")

                    true_variables = self.copy_variables(current_variables)
                    false_variables = self.copy_variables(current_variables)

                    self.update_variables_with_condition(true_variables, condition_expr, is_true_branch=True)
                    self.update_variables_with_condition(false_variables, condition_expr, is_true_branch=False)

                    # true branch로 이어지는 successor enqueue
                    true_succ = true_successors[0]
                    true_succ.variables = true_variables
                    block_queue.append(true_succ)

                    # false branch로 이어지는 successor enqueue
                    false_succ = false_successors[0]
                    false_succ.variables = false_variables
                    block_queue.append(false_succ)

                    # 현재 노드 해석 종료
                    continue

                elif current_block.condition_node_type in ["require", "assert"]:
                    # true branch만 존재한다고 가정
                    true_successors = [s for s in function_cfg.graph.successors(current_block) if
                                       function_cfg.graph.edges[current_block, s].get('condition') == True]

                    if len(true_successors) != 1:
                        raise ValueError("require/assert node must have exactly one true successor.")

                    true_variables = self.copy_variables(current_variables)
                    self.update_variables_with_condition(true_variables, condition_expr, is_true_branch=True)

                    true_succ = true_successors[0]
                    true_succ.variables = true_variables
                    block_queue.append(true_succ)

                    # false branch는 exit node로 가거나 revert하므로 별도 처리 필요 없음
                    continue

                elif current_block.condition_node_type in ["while", "for", "do_while"]:
                    # while 루프 처리
                    # fixpoint 계산 후 exit_node 반환
                    exit_node = self.apply_fixpoint_to_exit_node(current_block)
                    # exit_node의 successor는 하나라고 가정
                    successors = list(function_cfg.graph.successors(exit_node))
                    if len(successors) == 1:
                        next_node = successors[0]
                        next_node.variables = self.copy_variables(exit_node.variables)
                        block_queue.append(next_node)
                    elif len(successors) == 0:
                        # while 종료 후 아무 successor도 없으면 끝
                        pass
                    else:
                        raise ValueError("While exit node must have exactly one successor.")
                    continue

                elif current_block.fixpoint_evaluation_node:
                    # 그냥 continue
                    continue
                else:
                    raise ValueError(f"Unknown condition node type: {current_block.condition_node_type}")

            else:
                # condition node가 아닌 일반 블록
                # 블록 내 문장 해석
                for stmt in current_block.statements:
                    if stmt.statement_type == 'assignment':
                        variables = self.interpret_assignment_statement(stmt, current_variables)
                    elif stmt.statement_type == 'array_assignment':
                        variables = self.interpret_array_assignment_statement(stmt, current_variables)
                    elif stmt.statement_type == 'struct_assignment':
                        variables = self.interpret_struct_assignment_statement(stmt, current_variables)
                    elif stmt.statement_type == 'mapping_assignment':
                        variables = self.interpret_mapping_assignment_statement(stmt, current_variables)
                    elif stmt.statement_type == 'function_call':
                        variables = self.interpret_function_call_statement(stmt, current_variables)
                    elif stmt.statement_type == 'return':
                        ret_val = self.evaluate_expression(stmt.return_expr, current_variables)
                        return_values.append(ret_val)
                        break
                    elif stmt.statement_type == 'revert':
                        break
                    else:
                        raise ValueError(f"Statement '{stmt.statement_type}' is not implemented.")


                # return이나 revert를 만나지 않았다면 successors 방문
                successors = list(function_cfg.graph.successors(current_block))
                if len(successors) == 1:
                    next_node = successors[0]
                    # next_node에 현재 변수 상태를 반영
                    next_node.variables = self.copy_variables(current_variables)
                    block_queue.append(next_node)
                elif len(successors) > 1:
                    raise ValueError("Non-condition, non-join node should not have multiple successors.")
                # successors가 없으면 리프노드이므로 그냥 끝.

        # exit node에 도달했다면 return_values join
        # 모든 return을 모아 exit node에서 join 처리할 수 있으나, 여기서는 단순히 top-level에서 return_values를 join
        if len(return_values) == 0:
            return None
        elif len(return_values) == 1:
            return return_values[0]
        else:
            # 여러 return 값 join 로직 필요 (정수 interval join 등)
            joined_ret = return_values[0]
            for rv in return_values[1:]:
                joined_ret = joined_ret.join(rv)
            return joined_ret

    def interpret_assignment_statement(self, stmt, variables):
        var_name = stmt.left.identifier
        variable_obj = variables.get(var_name)
        if not variable_obj:
            raise ValueError(f"Variable '{var_name}' not found in current variables.")

        # 우변 표현식 평가
        right_value = self.evaluate_expression(stmt.right, variables)

        # 복합 할당 연산자 처리
        if stmt.operator != '=':
            new_value = self.process_compound_assignment(variable_obj.value, right_value, stmt.operator)
        else:
            new_value = right_value

        # 변수 값 업데이트
        variable_obj.value = new_value
        variables[var_name] = variable_obj
        return variables

    def interpret_array_assignment_statement(self, stmt, variables):
        var_name = stmt.left.identifier
        variable_obj = variables.get(var_name)
        if not variable_obj or not isinstance(variable_obj, ArrayVariable):
            raise ValueError(f"Array variable '{var_name}' not found in current variables.")

        # 우변 표현식 평가 (배열 요소들의 값 리스트)
        elements_value = self.evaluate_array_expression(stmt.right, variables)

        # 배열 요소 값 업데이트
        variable_obj.elements = elements_value
        variables[var_name] = variable_obj
        return variables

    def interpret_struct_assignment_statement(self, stmt, variables):
        var_name = stmt.left.identifier
        variable_obj = variables.get(var_name)
        if not variable_obj or not isinstance(variable_obj, StructVariable):
            raise ValueError(f"Struct variable '{var_name}' not found in current variables.")

        # 우변 표현식 평가 (구조체 멤버들의 값 딕셔너리)
        members_value = self.evaluate_struct_expression(stmt.right, variables)

        # 구조체 멤버 값 업데이트
        variable_obj.members = members_value
        variables[var_name] = variable_obj
        return variables

    def interpret_mapping_assignment_statement(self, stmt, variables):
        mapping_var_name = stmt.left.base.identifier
        key_expr = stmt.left.index
        key_value = self.evaluate_expression(key_expr, variables)

        mapping_var = variables.get(mapping_var_name)
        if not mapping_var or not isinstance(mapping_var, MappingVariable):
            raise ValueError(f"Mapping variable '{mapping_var_name}' not found in current variables.")

        # 우변 표현식 평가
        right_value = self.evaluate_expression(stmt.right, variables)

        # 매핑 변수의 특정 키에 대한 값 업데이트
        mapping_var.mapping[key_value] = right_value
        variables[mapping_var_name] = mapping_var
        return variables

    def interpret_function_call_statement(self, stmt, variables):
        function_expr = stmt.function_call_expr
        return_value = self.function_abstract_interpretation(function_expr, variables)
        # 함수 호출 결과를 어느 변수에 할당하는 로직이 필요하다면 추가.
        # 현재는 단순 호출만 가정하므로 변수 환경 변화 없음.
        return variables

    def is_true_branch(self, current_block, successor_node, function_cfg):
        """
        successor_node가 참 분기인지 확인합니다.
        :param current_block: 현재 CFGNode (조건 노드)
        :param successor_node: successor CFGNode
        :param function_cfg: 현재 함수의 CFG
        :return: True 또는 False
        """
        edge_data = function_cfg.graph.get_edge_data(current_block, successor_node)
        return edge_data.get('condition') == True

    def is_false_branch(self, current_block, successor_node, function_cfg):
        """
        successor_node가 거짓 분기인지 확인합니다.
        :param current_block: 현재 CFGNode (조건 노드)
        :param successor_node: successor CFGNode
        :param function_cfg: 현재 함수의 CFG
        :return: True 또는 False
        """
        edge_data = function_cfg.graph.get_edge_data(current_block, successor_node)
        return edge_data.get('condition') == False

    def merge_variables_from_predecessors(self, current_block, function_cfg):
        """
        조인 포인트 노드에서 predecessor들의 변수 환경을 합칩니다.
        :param current_block: 현재 CFGNode (조인 포인트 노드)
        :param function_cfg: 현재 함수의 CFG
        :return: 합쳐진 변수 환경 (dict)
        """
        merged_variables = {}

        # 각 predecessor의 변수 환경을 가져옴
        predecessor_variables_list = []
        for pred in function_cfg.graph.predecessors(current_block):
            # 각 predecessor 노드에서 변수 환경을 가져와야 함
            # 이를 위해 노드와 변수 환경을 매핑하는 구조가 필요함
            # 예를 들어, 노드 객체에 변수 환경을 저장하거나 별도의 딕셔너리를 사용
            pred_variables = pred.variables if hasattr(pred, 'variables') else {}
            predecessor_variables_list.append(pred_variables)

        # 변수별로 범위를 합침
        variable_names = set()
        for vars in predecessor_variables_list:
            variable_names.update(vars.keys())

        for var_name in variable_names:
            var_objs = [vars[var_name] for vars in predecessor_variables_list if var_name in vars]
            merged_var = self.merge_variable_intervals(var_objs)
            merged_variables[var_name] = merged_var

        return merged_variables


    def find_variable_by_identifier(self, expr):
        """
        식별자에 해당하는 변수를 찾아서 반환하는 함수.
        :param expr: Expression 객체 또는 identifier 이름
        :param variables: 현재 변수 상태 딕셔너리 (var_name -> Variables 객체)
        :return: Variables 객체
        """
        var_name = expr.identifier if hasattr(expr, 'identifier') else expr

        # Function CFG의 related_variables 또는 contract CFG에서 변수 찾기
        if self.current_target_function_cfg.related_variables[var_name] != None:
            return self.current_target_function_cfg.related_variables[var_name]
        else :
            raise ValueError(f"Variable '{var_name}' not found in the current context.")

    def compare_intervals(self, left_interval, right_interval, operator):
        """
        두 Interval 간의 비교를 수행하여 BooleanInterval을 반환합니다.
        """
        if left_interval.min_value is None or left_interval.max_value is None \
                or right_interval.min_value is None or right_interval.max_value is None:
            # Interval 중 하나라도 값이 없으면 결과를 확정할 수 없음
            return BoolInterval(False, True)

        # 비교 결과를 나타내는 변수
        is_true = False
        is_false = False

        if operator == '==':
            if left_interval.max_value < right_interval.min_value or left_interval.min_value > right_interval.max_value:
                is_false = True
            elif left_interval.min_value == left_interval.max_value == right_interval.min_value == right_interval.max_value:
                is_true = True
            else:
                is_true = is_false = True  # 불확실함
        elif operator == '!=':
            if left_interval.max_value < right_interval.min_value or left_interval.min_value > right_interval.max_value:
                is_true = True
            elif left_interval.min_value == left_interval.max_value == right_interval.min_value == right_interval.max_value:
                is_false = True
            else:
                is_true = is_false = True  # 불확실함
        elif operator == '<':
            if left_interval.max_value < right_interval.min_value:
                is_true = True
            elif left_interval.min_value >= right_interval.max_value:
                is_false = True
            else:
                is_true = is_false = True
        elif operator == '>':
            if left_interval.min_value > right_interval.max_value:
                is_true = True
            elif left_interval.max_value <= right_interval.min_value:
                is_false = True
            else:
                is_true = is_false = True
        elif operator == '<=':
            if left_interval.max_value <= right_interval.min_value:
                is_true = True
            elif left_interval.min_value > right_interval.max_value:
                is_false = True
            else:
                is_true = is_false = True
        elif operator == '>=':
            if left_interval.min_value >= right_interval.max_value:
                is_true = True
            elif left_interval.max_value < right_interval.min_value:
                is_false = True
            else:
                is_true = is_false = True
        else:
            raise ValueError(f"Unsupported comparison operator: {operator}")

        return BoolInterval(is_true, is_false)

    def get_variable_info_from_expr(self, expr, current_variables):
        """
        expr( Expression )를 분석하여
        - var_obj (실제 MappingVariable, ArrayVariable, Variables, etc.)
        - key/index (만약 mapping이나 array면)
        - member_name (만약 struct.member이면)
        등등을 파악해 반환
        예: { "var_obj": mappingVar, "mapping_key": addressValue, ... }
        """
        # 이 부분은 기존 process_assignment_expression에서 구현된 로직과 유사
        # 아래는 매우 간단한 예시(식별자만 다룬다거나), 실제론 IndexAccessContext, MemberAccessContext 등을 다뤄야 함
        result = {
            "var_obj": None,
            "key_or_index": None,
            "member_name": None
        }

        if expr.identifier:
            # 단순 변수 명
            var_name = expr.identifier
            var_obj = current_variables.get(var_name)
            if var_obj is not None:
                result["var_obj"] = var_obj
            return result

        # 나머지 IndexAccess, MemberAccess, etc.는 기존 evaluate_expression나 process_assignment_expression에서
        # 어떻게 변수·인덱스를 찾아오는지 참고해서 구현
        # ...

        return result


    def get_variable_interval(self, var_name):
        """
        변수의 interval 값을 반환하는 함수.
        함수 내 변수인지, 상태 변수인지 구분하여 처리.
        """
        # 1. 현재 타겟 컨트랙트의 CFG 가져오기
        contract_cfg = self.contract_cfgs.get(self.current_target_contract)
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # 2. 현재 타겟 함수의 CFG 가져오기 (local variable 포함)
        function_cfg = contract_cfg.get_function_cfg(self.current_target_function)

        # 3. 함수 내에서 정의된 변수 (related_variables) 먼저 확인
        if function_cfg:
            if function_cfg.get_related_variable(var_name) is not None :
                return function_cfg.get_related_variable(var_name).value
            else :
                # 5. 변수를 찾지 못한 경우 에러 발생
                raise ValueError(f"Variable '{var_name}' not found in function or contract scope")

    def get_variable_from_expression(self, expr, variables):
        if expr.identifier:
            var_name = expr.identifier
            var_obj = variables.get(var_name)
            return var_obj, var_name, None, None  # element_var, key_or_index는 None
        elif expr.context == 'IndexAccessContext':
            base_expr = expr.base
            index_expr = expr.index

            base_var_obj, base_var_name, _, _ = self.get_variable_from_expression(base_expr, variables)
            if not base_var_obj:
                return None, None, None, None

            key_or_index = self.evaluate_expression(index_expr, variables)
            key_str = str(key_or_index)

            var_name = f"{base_var_name}[{key_str}]"

            # 매핑 또는 배열의 경우 처리
            if isinstance(base_var_obj, MappingVariable):
                mapping_var = base_var_obj
                element_var = mapping_var.mapping.get(key_str)
                if not element_var:
                    # 요소가 없으면 생성
                    value_type = mapping_var.typeInfo.mappingValueType
                    element_var = Variables(identifier=var_name)
                    element_var.typeInfo = value_type
                    mapping_var.mapping[key_str] = element_var
                return mapping_var, var_name, element_var, key_or_index
            elif isinstance(base_var_obj, ArrayVariable):
                array_var = base_var_obj
                index = int(key_or_index)
                if index < 0 or index >= len(array_var.elements):
                    raise IndexError(f"Array index out of bounds: {index}")
                element_var = array_var.elements[index]
                return array_var, var_name, element_var, key_or_index
            else:
                return None, None, None, None
        elif expr.context == 'MemberAccessContext':
            base_expr = expr.base
            member_name = expr.member

            base_var_obj, base_var_name, _, _ = self.get_variable_from_expression(base_expr, variables)
            if not base_var_obj:
                return None, None, None, None

            var_name = f"{base_var_name}.{member_name}"

            # 구조체 멤버의 경우 처리
            if isinstance(base_var_obj, StructVariable):
                struct_var = base_var_obj
                member_var = struct_var.members.get(member_name)
                if not member_var:
                    # 멤버 변수가 없으면 생성
                    member_var = Variables(identifier=var_name)
                    struct_var.members[member_name] = member_var
                return struct_var, var_name, member_var, member_name
            else:
                return None, None, None, None
        else:
            return None, None, None, None

    def set_bottom_for_array(self, variable_obj):
        """
        배열 변수에 대해 bottom 값을 설정하는 함수.
        """
        for element in variable_obj.elements:
            element.value = self.calculate_default_interval(variable_obj.typeInfo.arrayBaseType.elementaryTypeName)

    def set_bottom_for_struct(self, variable_obj):
        """
        구조체 변수에 대해 bottom 값을 설정하는 함수.
        """
        for member_name, member_var in variable_obj.members.items():
            member_var.value = self.calculate_default_interval(member_var.typeInfo.elementaryTypeName)

    def set_bottom_for_mapping(self, variable_obj):
        """
        맵핑 변수에 대해 bottom 값을 설정하는 함수.
        """
        # 맵핑의 키와 값에 대해 기본값을 설정
        for key, value in variable_obj.mapping.items():
            value.value = self.calculate_default_interval(value.typeInfo.elementaryTypeName)

    """
    intent analysis part
    """

    def parse_intent(self, line_comment):
        """
        개발자의 의도를 파싱하여 변수별로 interval을 반환하는 함수.
        @intent <variable> <comparison> <value>
        예: // @intent x >= 5 && x <= 10
        """
        # 패턴: @intent 뒤에 나오는 비교 표현식을 파싱
        intent_pattern = r'@intent\s+([\w\[\]\.]+)\s*(>=|<=|>|<|==|!=)\s*(\d+)'  # 변수명, 연산자, 값 추출
        matches = re.findall(intent_pattern, line_comment)

        # 의도된 interval 결과 저장
        intent_intervals = {}

        for match in matches:
            var_name, operator, value = match
            value = int(value)

            # 변수를 기준으로 비교 연산자에 따른 interval 설정
            if var_name not in intent_intervals:
                intent_intervals[var_name] = [None, None]  # min, max 초기화

            # 비교 연산자 처리
            if operator == '>=':
                intent_intervals[var_name][0] = value
            elif operator == '>':
                intent_intervals[var_name][0] = value + 1
            elif operator == '<=':
                intent_intervals[var_name][1] = value
            elif operator == '<':
                intent_intervals[var_name][1] = value - 1
            elif operator == '==':
                intent_intervals[var_name] = [value, value]
            elif operator == '!=':
                # != 연산은 범위 처리에 부적합하므로 제외 처리하거나 경고 가능
                pass

        # 각 변수에 대한 Interval 객체 생성
        parsed_intervals = {}
        for var_name, (min_val, max_val) in intent_intervals.items():
            # min, max 값이 없을 경우 Interval(None, None) 반환
            parsed_intervals[var_name] = Interval(min_val, max_val)

        return parsed_intervals

    def get_analysis_result(self):
        # 가장 최근의 분석 결과를 반환
        return self.analysis_results if self.analysis_results else {}