# SolidityGuardian/Analyzers/ContractAnalyzer.py
from Utils.Interval import *
from Utils.cfg import *
from Utils.util import *
from solcx import compile_source, install_solc
import solcx
import re


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

        # for Multiple Contract
        self.contract_cfgs = {} # name -> CFG
        #self.current_contract_cfg = None

        self.analysis_results = None

    """
    Prev analysis part
    """

    def update_code(self, start_line, end_line, new_code):
        self.current_start_line = start_line
        self.current_end_line = end_line

        lines = new_code.split('\n')

        if not self.full_code_lines:  # initialize
            for i, line in enumerate(range(start_line, end_line + 1)):
                self.full_code_lines[line] = lines[i]
                self.update_brace_count(line, lines[i])

        else:  # 이미 있는 경우
            offset = end_line - start_line + 1

            # 새 코드가 들어갈 위치 이후의 기존 라인들을 뒤로 밀기
            keys_to_shift = sorted([line for line in self.full_code_lines.keys() if line >= start_line], reverse=True)
            for line in keys_to_shift:
                self.full_code_lines[line + offset] = self.full_code_lines.pop(line)
                self.update_brace_count(line + offset, self.full_code_lines[line + offset])

            # 새로운 코드를 해당 위치에 추가
            for i, line in enumerate(range(start_line, end_line + 1)):
                self.full_code_lines[line] = lines[i]
                self.update_brace_count(line, lines[i])

        # 전체 코드를 다시 합쳐서 full_code 갱신
        self.full_code = '\n'.join([self.full_code_lines[line] for line in sorted(self.full_code_lines.keys())])

        # 문법 오류 체크 및 컨텍스트 분석
        if new_code != "\n":  # 단순 엔터 입력이 아닌 경우에만 분석 실행
            self.analyze_context(start_line, new_code)

    def compile_check(self):
        try:
            install_solc('0.8.6')  # 필요한 Solidity 컴파일러 버전을 설치합니다.
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

        # 매 분석마다 초기화
        self.current_context_type = None
        self.current_target_contract = None
        self.current_target_function = None

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
            else : # constructor, function, --- # 시작 규칙 : interactiveBlockUnit
                self.current_context_type = "simpleStatement"
                self.current_target_contract = self.find_contract_context(start_line)
                self.current_target_function = self.find_function_context(start_line)

        elif ',' in stripped_code:  # enum
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
        contract_cfg = self.contract_cfgs[self.current_target_contract]

        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        contract_cfg.define_enum(enum_name)

        # 10. contract_cfg를 contract_cfgs에 반영
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        # brace_count 업데이트
        self.brace_count[self.current_start_line]['enums'] = contract_cfg.enums

    # for interactiveStructDefinition in Solidity.g4
    def process_struct_definition(self, struct_name):
        contract_cfg = self.contract_cfgs[self.current_target_contract]

        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        contract_cfg.define_enum(struct_name)

        # 10. contract_cfg를 contract_cfgs에 반영
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        # brace_count 업데이트
        self.brace_count[self.current_start_line]['structs'] = contract_cfg.structs

    def process_struct_member(self, var_name, var_type):
        # 1. 현재 타겟 컨트랙트의 CFG를 가져옴
        contract_cfg = self.contract_cfgs[self.current_target_contract]
        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # 2. 현재 타겟 구조체를 확인하고 멤버 추가
        if not self.current_target_struct:
            raise ValueError("No target struct to add members to.")

        contract_cfg.add_struct_member(self.current_target_struct, var_name, var_type)

        # 10. contract_cfg를 contract_cfgs에 반영
        self.contract_cfgs[self.current_target_contract] = contract_cfg

    def process_state_variable(self, variable_obj, init_expr):
        # 1. 현재 타겟 컨트랙트의 CFG 가져오기
        contract_cfg = self.contract_cfgs[self.current_target_contract]

        if not contract_cfg:
            raise ValueError(f"Unable to find contract CFG for {self.current_target_contract}")

        # 2. abstract interpretation 수행
        interval_result = None
        # ArrayVariable 처리
        if isinstance(variable_obj, ArrayVariable):
            if variable_obj.typeInfo.isDynamicArray:
                # 동적 배열인 경우 interval 설정을 건너뜀
                interval_result = None  # push 전에는 초기화 불가
            else:
                # 정적 배열인 경우 arrayLength만큼 초기화
                interval_result = IntegerInterval(0, 0)  # 기본값
                variable_obj.initialize_elements(interval_result)  # 배열 요소 초기화

        # 일반 변수 처리 (Variables)
        elif isinstance(variable_obj, Variables) and variable_obj.typeInfo.typeCategory == "elementary":
            elementary_type = variable_obj.typeInfo.elementaryTypeName
            int_length = variable_obj.typeInfo.intTypeLength if variable_obj.typeInfo.intTypeLength else 256

            if elementary_type.startswith("int"):
                interval_result = IntegerInterval(0, 0, int_length)
            elif elementary_type.startswith("uint"):
                interval_result = UnsignedIntegerInterval(0, 0, int_length)
            elif elementary_type == "bool":
                interval_result = BoolInterval(False, False)

        # 3. Variables 객체에 interval 값 추가
        variable_obj.value = interval_result

        # 4. 분석 결과 저장
        intervals_info = {
            "left": {
                "variable": variable_obj.identifier,
                "assigned_interval": [interval_result.min_value,
                                      interval_result.max_value] if interval_result else None,
            },
            "right": []
        }

        self.analysis_results = {
            "line": self.current_start_line,
            "variables_info": intervals_info,
            "intent_check": {}  # 상태 변수 선언에 대해서는 의도 분석이 없으므로 빈 dict로 설정
        }

        # 4. 상태 변수를 ContractCFG에 추가
        contract_cfg.add_state_variable(variable_obj, init_expr)

        # 5. ContractCFG에 있는 모든 FunctionCFG에 상태 변수 추가
        for function_cfg in contract_cfg.functions.values():
            function_cfg.add_related_variable(variable_obj.identifier, variable_obj)

        # 10. contract_cfg를 contract_cfgs에 반영
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        # 6. brace_count 업데이트
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

        # 3. 파라미터 추가
        for variable in parameters:
            function_cfg.add_related_variable(variable)

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

    def process_variable_declaration(self, variable_obj, init_expr=None, line_comment=None):
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

        # 4. 변수 선언 시 초기화 값이 있는 경우 처리
        if init_expr is None:
            interval = self.calculate_default_interval(variable_obj.var_type)
        else:
            interval = self.evaluate_expression(init_expr)

        # 5. Variables 객체의 값 업데이트
        variable_obj.value = interval

        # 6. CFG 노드에 할당문 추가 및 변수 정보 업데이트
        current_block.add_assign_statement(variable_obj.identifier, variable_obj.var_type, interval)

        # 7. 함수 CFG의 related_variables에 추가
        self.current_target_function_cfg.related_variables[variable_obj.identifier] = variable_obj

        if current_block.is_while_body:
            vars = self.fixpoint(current_block)
            self.update_while_body(vars, current_block)

        # 9. 분석 결과에 interval 값 저장
        interval_result = {
            "variable": variable_obj.identifier,
            "type": variable_obj.var_type,
            "value": [interval.min_value, interval.max_value]
        }

        # 10. 의도 체크 결과 저장 (lineComment가 있을 경우)
        intent_result = {"expected": [], "actual": [interval.min_value, interval.max_value], "message": ""}

        if line_comment is not None:
            # 개발자의 의도 파싱
            expected_interval = self.parse_intent(line_comment)

            # 실제 interval이 의도된 interval 안에 포함되는지 확인
            if expected_interval and not interval.encompass(expected_interval):
                intent_result["expected"] = [expected_interval.min_value, expected_interval.max_value]
                intent_result[
                    "message"] = f"Error: {variable_obj.identifier} out of intended range {expected_interval.min_value} " \
                                 f"to {expected_interval.max_value}"

        # 11. 분석 결과를 저장
        result = {
            "line": self.current_start_line,
            "interval": interval_result,
            "intent_check": intent_result
        }

        # get_analysis_result에 사용될 결과 저장
        self.analysis_results = result

        # 9. function_cfg 결과를 contract_cfg에 반영
        contract_cfg.functions[self.current_target_function] = self.current_target_function_cfg

        # 10. contract_cfg를 contract_cfgs에 반영
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        # 7. brace_count에 CFG 노드 정보 업데이트 (함수의 시작 라인 정보 사용)
        self.brace_count[self.current_start_line]['cfg_node'] = current_block

        self.current_target_function_cfg = None

    def process_compound_assignment(self, left_interval, right_interval, operator):
        """
        좌변과 우변의 Interval을 연산자에 맞게 처리합니다.
        """
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

    def process_assignment_expression(self, expr, line_comment=None):
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

        # 4. 좌변 변수 정보 가져오기 (CFGNode에서)
        var_name = self.extract_variable_name(expr.left)
        variable_obj = current_block.get_variable(var_name)

        if not variable_obj:
            variable_obj = self.current_target_function_cfg.get_related_variable(var_name)

        if not variable_obj:
            raise ValueError(f"Variable '{var_name}' not found in current CFG node.")

        # 5. 좌변 Interval 가져오기
        left_interval = variable_obj.value

        # 6. 우변 표현식 평가
        right_interval = self.evaluate_expression(expr.right)

        # 7. 복합 할당 연산자 처리
        if expr.operator == '=':
            new_interval = right_interval
        else:
            new_interval = self.process_compound_assignment(left_interval, right_interval, expr.operator)

        # 8. CFG 노드에 할당문 추가
        current_block.add_assign_statement(variable_obj, new_interval)

        # 9. 우변의 관련 변수 정보 추출
        related_vars = self.extract_related_variables(expr.right, current_block, self.current_target_function_cfg)

        # 10. 좌변, 우변 관련 Interval 정보 생성
        intervals_info = {
            "left": {
                "variable": var_name,
                "assigned_interval": [new_interval.min_value, new_interval.max_value],
            },
            "right": []
        }

        for related_var in related_vars:
            # 우변 변수도 CFG 노드에 추가
            if related_var.identifier not in current_block.variables:
                current_block.variables[related_var.identifier] = related_var

            intervals_info["right"].append({
                "variable": related_var.identifier,
                "interval": [related_var.value.min_value, related_var.value.max_value]
            })

        if current_block.is_while_body:
            vars = self.fixpoint(current_block)
            self.update_while_body(vars, current_block)

        # 11. 개발자의 의도 파싱 및 비교
        intent_result = {"expected": [], "actual": [], "message": ""}
        if line_comment is not None:
            expected_interval = self.parse_intent(line_comment)
            if expected_interval and var_name in expected_interval:
                intended_interval = expected_interval[var_name]
                if not new_interval.encompass(intended_interval):
                    intent_result["expected"] = [intended_interval.min_value, intended_interval.max_value]
                    intent_result["actual"] = [new_interval.min_value, new_interval.max_value]
                    intent_result["message"] = f"Variable '{var_name}' is out of the intended range."

        # 12. 분석 결과 저장
        result = {
            "line": self.current_start_line,
            "variables_info": intervals_info,
            "intent_check": intent_result
        }

        # get_analysis_result에 사용될 결과 저장
        self.analysis_results = result

        # 9. function_cfg 결과를 contract_cfg에 반영
        contract_cfg.functions[self.current_target_function] = self.current_target_function_cfg

        # 10. contract_cfg를 contract_cfgs에 반영
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        # 7. brace_count에 CFG 노드 정보 업데이트 (함수의 시작 라인 정보 사용)
        self.brace_count[self.current_start_line]['cfg_node'] = current_block

        self.current_target_function_cfg = None

    def process_assignment_function_call(self, expr, line_comment=None):
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

        # 10. 개발자의 의도 파싱 및 비교
        intent_result = {"expected": [], "actual": [], "message": ""}
        if line_comment is not None:
            expected_interval = self.parse_intent(line_comment)
            if expected_interval and var_name in expected_interval:
                intended_interval = expected_interval[var_name]
                if not return_interval.encompass(intended_interval):
                    intent_result["expected"] = [intended_interval.min_value, intended_interval.max_value]
                    intent_result["actual"] = [return_interval.min_value, return_interval.max_value]
                    intent_result["message"] = f"Variable '{var_name}' is out of the intended range."

        # 11. 분석 결과 저장
        result = {
            "line": self.current_start_line,
            "variable": var_name,
            "assigned_interval": [return_interval.min_value, return_interval.max_value],
            "intent_check": intent_result
        }

        # get_analysis_result에 사용될 결과 저장
        self.analysis_results = result

    def process_unary_prefix_operation(self, expr, line_comment=None):
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

        # 4. 변수 이름 추출
        var_name = self.extract_variable_name(expr.expression)

        # 5. 변수의 기존 interval 가져오기
        current_interval = self.get_variable_interval(var_name)

        # 6. 단항 연산 수행 (++i, --i)
        if expr.operator == '++':
            new_interval = current_interval.add(IntegerInterval(1, 1))
        elif expr.operator == '--':
            new_interval = current_interval.subtract(IntegerInterval(1, 1))
        else:
            raise ValueError(f"Unsupported unary prefix operator: {expr.operator}")

        # 7. CFG 노드에 업데이트된 변수 정보 저장
        current_block.add_assign_statement(var_name, expr.expr_type, new_interval)

        if current_block.is_while_body:
            vars = self.fixpoint(current_block)
            self.update_while_body(vars, current_block)

        # 9. 개발자의 의도 파싱 및 비교
        intent_result = {"expected": [], "actual": [], "message": ""}
        if line_comment is not None:
            expected_interval = self.parse_intent(line_comment)
            if expected_interval and var_name in expected_interval:
                intended_interval = expected_interval[var_name]
                if not new_interval.encompass(intended_interval):
                    intent_result["expected"] = [intended_interval.min_value, intended_interval.max_value]
                    intent_result["actual"] = [new_interval.min_value, new_interval.max_value]
                    intent_result["message"] = f"Variable '{var_name}' is out of the intended range."

        # 10. 분석 결과 저장
        result = {
            "line": self.current_start_line,
            "variable": var_name,
            "assigned_interval": [new_interval.min_value, new_interval.max_value],
            "intent_check": intent_result
        }

        # get_analysis_result에 사용될 결과 저장
        self.analysis_results = result

        # 9. function_cfg 결과를 contract_cfg에 반영
        contract_cfg.functions[self.current_target_function] = self.current_target_function_cfg

        # 10. contract_cfg를 contract_cfgs에 반영
        self.contract_cfgs[self.current_target_contract] = contract_cfg

        self.current_target_function_cfg = None

    def process_unary_suffix_operation(self, expr, line_comment=None):
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

        # 4. 변수 이름 추출
        var_name = self.extract_variable_name(expr.expression)

        # 5. 변수의 기존 interval 가져오기
        current_interval = self.get_variable_interval(var_name)

        # 6. 단항 연산 수행 (i++, i--)
        if expr.operator == '++':
            new_interval = current_interval.add(IntegerInterval(1, 1))
        elif expr.operator == '--':
            new_interval = current_interval.subtract(IntegerInterval(1, 1))
        else:
            raise ValueError(f"Unsupported unary suffix operator: {expr.operator}")

        # 7. CFG 노드에 업데이트된 변수 정보 저장
        current_block.add_assign_statement(var_name, expr.expr_type, new_interval)

        if current_block.is_while_body:
            vars = self.fixpoint(current_block)
            self.update_while_body(vars, current_block)

        # 9. 개발자의 의도 파싱 및 비교
        intent_result = {"expected": [], "actual": [], "message": ""}
        if line_comment is not None:
            expected_interval = self.parse_intent(line_comment)
            if expected_interval and var_name in expected_interval:
                intended_interval = expected_interval[var_name]
                if not new_interval.encompass(intended_interval):
                    intent_result["expected"] = [intended_interval.min_value, intended_interval.max_value]
                    intent_result["actual"] = [new_interval.min_value, new_interval.max_value]
                    intent_result["message"] = f"Variable '{var_name}' is out of the intended range."

        # 10. 분석 결과 저장
        result = {
            "line": self.current_start_line,
            "variable": var_name,
            "assigned_interval": [new_interval.min_value, new_interval.max_value],
            "intent_check": intent_result
        }

        # get_analysis_result에 사용될 결과 저장
        self.analysis_results = result

        # 9. function_cfg 결과를 contract_cfg에 반영
        contract_cfg.functions[self.current_target_function] = self.current_target_function_cfg

        # 10. contract_cfg를 contract_cfgs에 반영
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

        # 1. 함수 표현식 가져오기
        function_expr = expr.function

        # 2. 함수 표현식이 MemberAccessContext인지 확인
        if function_expr.context == 'MemberAccessContext':
            # 2.1 base와 member 가져오기
            base_expr = function_expr.base
            member_name = function_expr.member

            # 2.2 base_expr이 IdentifierExpContext인지 확인
            if base_expr.context == 'IdentifierExpContext':
                identifier = base_expr.identifier

                # 2.3 현재 함수 CFG에서 변수 가져오기
                arr_var = self.self.current_target_function_cfg.get_variable(identifier)

                if arr_var is None:
                    raise ValueError(f"Variable '{identifier}' not found in current function scope.")

                # 2.4 배열 변수인지 확인
                if isinstance(arr_var, ArrayVariable) and arr_var.typeInfo.isDynamicArray:
                    # 2.5 멤버 함수 처리
                    if member_name == 'push':
                        arguments = expr.arguments

                        if arguments is None or len(arguments) == 0:
                            # 빈 괄호 push(): 새로운 기본값 요소를 추가하고, 참조를 반환
                            # 여기서는 기본값 요소를 추가합니다.
                            base_type = arr_var.typeInfo.arrayBaseType

                            # 기본값 생성 (타입에 따라 다름, 여기서는 None으로 처리)
                            element_var = Variables(value=None, typeInfo=base_type)

                            arr_var.elements.append(element_var)

                            # 배열의 길이 증가
                            if arr_var.typeInfo.arrayLength is not None:
                                arr_var.typeInfo.arrayLength += 1

                            # 반환값 처리 (필요에 따라 구현)
                            return element_var  # 참조를 반환 (여기서는 Variables 객체)
                        elif len(arguments) == 1:
                            # push(value): 인자를 배열에 추가
                            arg_expr = arguments[0]
                            arg_value = self.evaluate_expression(arg_expr)

                            # 타입 호환성 검사는 생략합니다.

                            element_var = Variables(value=arg_value, typeInfo=arr_var.typeInfo.arrayBaseType)
                            arr_var.elements.append(element_var)

                            # 배열의 길이 증가
                            if arr_var.typeInfo.arrayLength is not None:
                                arr_var.typeInfo.arrayLength += 1

                            # push()는 반환값이 없음
                            return None
                        else:
                            raise ValueError("push() function accepts at most one argument.")
                    elif member_name == 'pop':
                        # pop(): 마지막 요소를 제거
                        if not arr_var.elements:
                            raise IndexError(f"Cannot pop from empty array '{identifier}'.")

                        arr_var.elements.pop()

                        # 배열의 길이 감소
                        if arr_var.typeInfo.arrayLength is not None:
                            arr_var.typeInfo.arrayLength -= 1

                        # pop()은 반환값이 없음
                        return None
                    else:
                        raise NotImplementedError(f"Member function '{member_name}' is not implemented.")
                else:
                    raise TypeError(f"Variable '{identifier}' is not a dynamic array.")
            else:
                raise NotImplementedError("Only simple identifiers are supported as array variables.")
        else:
            raise NotImplementedError("Only member function calls are supported in this context.")

        if current_block.is_while_body:
            vars = self.fixpoint(current_block)
            self.update_while_body(vars, current_block)

        self.current_target_function_cfg = None

    def process_payable_function_call(self, expr, line_comment=None):
        # Handle payable function calls
        pass

    def process_function_call_options(self, expr, line_comment=None):
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

        # 4. brace_count 업데이트 - 존재하지 않으면 초기화
        if self.current_start_line not in self.brace_count:
            self.brace_count[self.current_start_line] = {}
        self.brace_count[self.current_start_line]['cfg_node'] = condition_block

        # 5. True 분기 블록 생성
        true_block = CFGNode(name=f"if_true_{self.current_start_line}")

        # 7. True 분기에서 변수 상태 복사 및 업데이트
        true_block.variables = self.copy_variables(condition_block.variables)
        self.update_variables_with_condition(true_block.variables, condition_expr, is_true_branch=True)

        # 8. 현재 블록의 후속 노드 처리 (기존 current_block의 successors를 가져옴)
        successors = list(self.current_target_function_cfg.graph.successors(current_block))

        # 기존 current_block과 successor들의 edge를 제거
        for successor in successors:
            self.current_target_function_cfg.graph.remove_edge(current_block, successor)

        # 9. CFG 노드 추가
        self.current_target_function_cfg.graph.add_node(condition_block)
        self.current_target_function_cfg.graph.add_node(true_block)

        # 10. 조건 블록과 True/False 분기 연결
        self.current_target_function_cfg.graph.add_edge(current_block, condition_block)
        self.current_target_function_cfg.graph.add_edge(condition_block, true_block, condition=True)

        # 11. True 분기 후속 노드 연결
        for successor in successors:
            self.current_target_function_cfg.graph.add_edge(true_block, successor)

        # 12. False 분기 처리: False일 경우 기존 current_block의 후속 노드로 연결
        for successor in successors:
            self.current_target_function_cfg.graph.add_edge(condition_block, successor, condition=False)

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

        # 8. 이전 조건 블록과 새로운 else_if_condition 블록 연결
        self.current_target_function_cfg.graph.add_edge(previous_condition_node, condition_block, condition=False)

        # 9. 새로운 조건 블록과 True 블록 연결
        self.current_target_function_cfg.graph.add_node(condition_block)
        self.current_target_function_cfg.graph.add_node(true_block)
        self.current_target_function_cfg.graph.add_edge(condition_block, true_block, condition=True)

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
                            join_point_node=True)

        # Copy variables from current_block to join_node
        join_node.variables = self.copy_variables(current_block.variables)
        join_node.join_point_node_vars = self.copy_variables(current_block.variables)


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
        self.current_target_function_cfg.add_node(join_node)
        self.current_target_function_cfg.add_edge(current_block, join_node)

        # 6. Connect the join node to the condition node
        self.current_target_function_cfg.add_node(condition_node)
        self.current_target_function_cfg.add_edge(join_node, condition_node)

        # 7. Create the true node (loop body)
        true_node = CFGNode(name=f"while_body_{self.current_start_line}")
        true_node.is_while_body = True
        self.update_variables_with_condition(true_node.variables, condition_expr, is_true_branch=True)

        # 8. Create the false node (exit block)
        false_node = CFGNode(name=f"while_exit_{self.current_start_line}",
                             loop_exit_node=True)

        # 9. Connect the condition node's true branch to the true node
        self.current_target_function_cfg.add_node(true_node)
        self.current_target_function_cfg.add_edge(condition_node, true_node, condition=True)

        # 10. Connect the condition node's false branch to the false node
        self.current_target_function_cfg.add_node(false_node)
        self.current_target_function_cfg.add_edge(condition_node, false_node, condition=False)

        # 기존 current_block과 successor들을 false block의 successor로
        for successor in successors:
            self.current_target_function_cfg.graph.add_edge(successor, false_node)

        # 11. Connect the true node back to the join node (loop back)
        self.current_target_function_cfg.add_edge(true_node, join_node)

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

        # 4. 재귀적으로 join_point_node 찾기
        join_point_node = self.find_join_point_node(current_block, self.current_target_function_cfg)
        if not join_point_node:
            raise ValueError("No corresponding loop join node found for continue statement.")

        # 5. 현재 블록의 모든 successor와의 edge 제거
        successors = list(self.current_target_function_cfg.graph.successors(current_block))
        for successor in successors:
            self.current_target_function_cfg.graph.remove_edge(current_block, successor)

        # 6. 현재 블록을 join_point_node로 연결 (loop로 다시 돌아감)
        self.current_target_function_cfg.graph.add_edge(current_block, join_point_node)

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

    def find_join_point_node(self, current_node):
        """
        재귀적으로 predecessor를 탐색하여 join_point_node를 찾는 함수
        """
        # 현재 노드가 join_point_node라면 반환
        if current_node.join_point_node:
            return current_node

        # 직접적인 predecessor를 탐색
        predecessors = list(self.current_target_function_cfg.graph.predecessors(current_node))
        for pred in predecessors:
            # 재귀적으로 predecessor를 탐색하여 join_point_node를 찾음
            join_point_node = self.find_join_point_node(pred)
            if join_point_node:
                return join_point_node

        # join_point_node를 찾지 못하면 None 반환
        return None

    def find_while_condition_node(self, current_block, function_cfg):
        """
        현재 블록에서 위로 올라가면서 조건 노드 중 타입이 'while'인 노드를 찾음
        """
        predecessors = list(function_cfg.graph.predecessors(current_block))
        for pred in predecessors:
            if pred.condition_node and pred.condition_node_type == "while":
                return pred
            # 재귀적으로 위로 탐색
            result = self.find_while_condition_node(pred, function_cfg)
            if result:
                return result
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

        # 4. Return 노드 생성
        return_node = CFGNode(name=f"return_{self.current_start_line}")
        return_node.statements.append(f"return {return_value}" if return_value else "return;")

        # 5. 기존 current_block과 그 successors 사이의 edge 제거
        successors = list(self.current_target_function_cfg.graph.successors(current_block))
        for successor in successors:
            self.current_target_function_cfg.graph.remove_edge(current_block, successor)

        # 6. 기존 current_block에서 return_node로 edge 추가
        self.current_target_function_cfg.graph.add_edge(current_block, return_node)

        # 7. 기존 successors에서 return_node로 edge 추가
        for successor in successors:
            self.current_target_function_cfg.graph.add_edge(return_node, successor)

        if current_block.is_while_body:
            vars = self.fixpoint(current_block)
            self.update_while_body(vars, current_block)

        # 8. Return 노드에 대한 brace_count 업데이트
        if self.current_start_line not in self.brace_count:
            self.brace_count[self.current_start_line] = {}
        self.brace_count[self.current_start_line]['cfg_node'] = return_node

        # 8. CFG 업데이트
        contract_cfg.functions[self.current_target_function] = self.current_target_function_cfg
        self.contract_cfgs[self.current_target_contract] = contract_cfg

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
        require_condition_node = CFGNode(name=f"require_condition_{self.current_start_line}", condition_node=True)
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
        assert_condition_node = CFGNode(name=f"require_condition_{self.current_start_line}", condition_node=True)
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

    def extract_variable_name(self, expression):
        # 좌변 표현식에서 변수 이름을 추출
        # 필요한 경우 재귀적으로 접근하여 전체 경로를 문자열로 반환
        if expression.identifier:
            return expression.identifier
        elif expression.operator == '.' and expression.left and expression.right:
            left_name = self.extract_variable_name(expression.left)
            right_name = expression.right.identifier
            return f"{left_name}.{right_name}"
        elif expression.operator == '[' and expression.left and expression.index:
            left_name = self.extract_variable_name(expression.left)
            index_expr = expression.index
            index_value = self.evaluate_expression(index_expr)
            index_str = f"[{index_value}]"
            return f"{left_name}{index_str}"
        else:
            raise ValueError(f"Unsupported left-hand side expression: {expression}")

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

    def copy_variables(self, variables):
        """
        주어진 변수 딕셔너리(variables)를 깊은 복사하여 반환합니다.
        variables: var_name -> Variables 객체
        """
        copied_variables = {}
        for var_name, var_obj in variables.items():
            # ArrayVariable 타입 처리
            if isinstance(var_obj, ArrayVariable):
                copied_array = ArrayVariable(
                    identifier=var_obj.identifier,
                    base_type=var_obj.typeInfo.arrayBaseType,
                    array_length=var_obj.typeInfo.arrayLength,
                    is_dynamic=var_obj.typeInfo.isDynamicArray,
                    value=var_obj.value,
                    isConstant=var_obj.isConstant,
                    scope=var_obj.scope
                )
                # 배열의 각 요소를 깊은 복사
                copied_array.elements = [self.copy_variables({elem.identifier: elem})[elem.identifier] for elem in
                                         var_obj.elements]
                copied_variables[var_name] = copied_array

            # StructVariable 타입 처리
            elif isinstance(var_obj, StructVariable):
                copied_struct = StructVariable(
                    identifier=var_obj.identifier,
                    struct_type=var_obj.typeInfo.structTypeName,
                    value=var_obj.value,
                    isConstant=var_obj.isConstant,
                    scope=var_obj.scope
                )
                # 구조체 멤버를 깊은 복사
                copied_struct.members = {member_name: self.copy_variables({member_name: member_obj})[member_name] for
                                         member_name, member_obj in var_obj.members.items()}
                copied_variables[var_name] = copied_struct

            # 기본 Variables 타입 처리
            else:
                copied_variables[var_name] = Variables(
                    identifier=var_obj.identifier,
                    value=var_obj.value,
                    isConstant=var_obj.isConstant,
                    scope=var_obj.scope
                )
                copied_variables[var_name].typeInfo = var_obj.typeInfo  # SolType 객체 복사

        return copied_variables

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

            # 좌우 표현식에 대해 Interval 평가
            left_interval = self.evaluate_expression(left_expr)
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

        elif condition_expr.operator in ['&&', '||']:
            # 논리 연산자가 포함된 복합 조건식 처리
            left_expr = condition_expr.left
            right_expr = condition_expr.right

            # 좌우 조건식에 대해 재귀적으로 처리
            self.update_variables_with_condition(variables, left_expr, is_true_branch)
            self.update_variables_with_condition(variables, right_expr, is_true_branch)

    def fixpoint(self, current_block):
        """
        고정점 분석을 수행하여 루프 내의 변수 상태를 수렴시킵니다.
        :param current_block: 현재 블록 (CFGNode)
        :return: 수렴된 변수 상태 딕셔너리 (var_name -> Variables 객체)
        """
        # 1. join_point_node 찾기
        join_point_node = self.find_join_point_node(current_block)
        if not join_point_node:
            raise ValueError("Join point node not found for the current block.")

        # 2. 루프 내의 모든 노드 수집
        loop_nodes = self.traverse_loop_nodes(join_point_node)

        # 3. 변수 상태 초기화
        in_vars = {}
        out_vars = {}
        for node in loop_nodes:
            in_vars[node] = {}
            out_vars[node] = {}
            if node == join_point_node:
                # join_point_node의 변수 상태 초기화
                in_vars[node] = self.copy_variables(join_point_node.join_point_node_vars)

        # 4. 워크리스트 알고리즘 초기화
        worklist = loop_nodes.copy()
        max_iterations = 100  # 최대 반복 횟수 설정
        iteration = 0
        while worklist and iteration < max_iterations:
            iteration += 1
            node = worklist.pop(0)

            # 5. 선행 노드들의 out_vars를 조인하여 in_vars 계산
            predecessors = list(self.current_target_function_cfg.graph.predecessors(node))
            new_in_vars = {}
            for pred in predecessors:
                if pred in out_vars:
                    new_in_vars = self.join_variables(new_in_vars, out_vars[pred])
                else:
                    new_in_vars = self.join_variables(new_in_vars, in_vars.get(pred, {}))
            if node == join_point_node:
                new_in_vars = self.join_variables(new_in_vars, join_point_node.join_point_node_vars)

            # 6. in_vars 변화 확인
            if not self.variables_equal(in_vars[node], new_in_vars):
                in_vars[node] = new_in_vars

            # 7. 노드의 transfer function 적용하여 out_vars 계산
            old_out_vars = out_vars[node]
            out_vars[node] = self.transfer_function(node, in_vars[node])

            # 8. out_vars 변화 확인 및 워크리스트 업데이트
            if not self.variables_equal(old_out_vars, out_vars[node]):
                successors = list(self.current_target_function_cfg.graph.successors(node))
                for succ in successors:
                    if succ in loop_nodes and succ not in worklist:
                        worklist.append(succ)

        if iteration == max_iterations:
            print("Fixpoint analysis did not converge within max iterations.")

        # 9. 수렴된 변수 상태를 루프 내 각 노드에 반영
        for node in loop_nodes:
            node.variables = out_vars[node]

        # 10. 수렴된 변수 상태 반환
        return out_vars[join_point_node]

    def traverse_loop_nodes(self, loop_node):
        """
        루프 내의 모든 노드를 수집합니다.
        :param loop_node: 루프의 시작 노드 (join_point_node)
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
                # Variables 객체의 value 속성을 조인
                var_value1 = result[var_name].value
                var_value2 = var_obj.value
                joined_value = self.join_variable_values(var_value1, var_value2)
                result[var_name].value = joined_value
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
            var_value1 = vars1[var_name].value
            var_value2 = vars2[var_name].value
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
        # 1. join_point_node 찾기
        join_point_node = self.find_join_point_node(current_block)
        if not join_point_node:
            raise ValueError("Join point node not found for the current block.")

        # 2. 루프 내의 모든 노드 수집
        loop_nodes = self.traverse_loop_nodes(join_point_node)

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
            # 좌변 변수의 Interval 업데이트
            var_name = statement.left.identifier
            if var_name in variables:
                variables[var_name].value = self.evaluate_expression(statement.right, variables)
            else:
                # 새로운 변수인 경우 Variables 객체 생성
                variables[var_name] = Variables(
                    identifier=var_name,
                    value=self.evaluate_expression(statement.right, variables),
                    scope='local'
                )
        # 추가적인 문장 유형에 대한 처리 필요 시 구현

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

    def merge_variables(self, variables_list):
        merged_variables = {}
        var_names = set().union(*[vars.keys() for vars in variables_list])

        for var_name in var_names:
            intervals = [vars[var_name] for vars in variables_list if var_name in vars]
            merged_interval = intervals[0]
            for interval in intervals[1:]:
                merged_interval = merged_interval.join(interval)
            merged_variables[var_name] = merged_interval

        return merged_variables

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

    def handle_function_side_effects(self, function_name, function_args):
        # 함수 호출로 인해 상태 변수가 변경되는 경우 등을 처리
        # 함수의 정의를 분석하여 상태 변수의 업데이트를 추적
        # 여기서는 예시로 아무 작업도 수행하지 않음
        pass

    def process_unary_operation(self, expr, line_comment=None):
        # 단항 연산자(++, -- 등)에 대한 처리 로직
        # 변수의 값을 업데이트하고, 인터벌 분석 수행
        # 개발자의 의도(line_comment)가 있는 경우 처리
        pass

    def process_function_call(self, expr, line_comment=None):
        # 함수 호출에 대한 처리 로직
        # 함수의 효과를 추론하거나, 사이드 이펙트를 고려
        # 개발자의 의도(line_comment)가 있는 경우 처리
        pass

    def process_new_expression(self, expr, line_comment=None):
        # new 연산자에 대한 처리 로직
        # 객체 생성에 따른 영향 분석
        # 개발자의 의도(line_comment)가 있는 경우 처리
        pass

    def process_general_expression(self, expr, line_comment=None):
        # 기타 일반적인 표현식에 대한 처리 로직
        # 필요에 따라 추가적인 분석 수행
        pass

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
            return self.process_block_out(closeBraceQueue)
        else:
            raise ValueError("No active function CFG found.")

    def process_block_out(self, closeBraceQueue):
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
                join_point_node = cfg_node
                pred = self.current_target_function_cfg.get_predecessor_node(cfg_node)
                if len(pred) == 1 :
                    join_point_node = pred[0]
                else :
                    raise ValueError(f"There are too much precedecssors of {cfg_node}")
                newBlock = self.find_fixpoint(join_point_node)
                # while 조건 노드의 false branch에 결과 반영
                self.update_variables_at_node(join_point_node.false_branch, newBlock.variables)
                break  # while 루프의 블록 아웃 처리는 여기서 종료
            elif not hasNode and cfg_node.condition_node_type == "if":
                outSideIfNode = cfg_node
                hasNode = True

        if hasNode and outSideIfNode:
            newBlock = self.join_leaf_nodes(outSideIfNode)
            return newBlock
        else:
            # 블록 아웃 처리가 완료되지 않았거나 처리할 노드가 없는 경우
            return None

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
            if 'return' in [stmt.statement_type for stmt in node.statements]:
                continue  # return 문이 있는 리프 노드는 제외
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

        # 조건 노드의 후속 노드로 연결
        function_cfg = self.get_current_function_cfg()
        function_cfg.graph.add_node(new_block)
        function_cfg.graph.add_edge(condition_node, new_block)

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

            successors = list(self.get_current_function_cfg().graph.successors(current_node))
            if not successors:
                # 자식이 없는 노드 (리프 노드)
                leaf_nodes.append(current_node)
            else:
                # 자식 노드가 있는 경우 스택에 추가
                for successor in successors:
                    stack.append(successor)

        return leaf_nodes

    def join_variable_values(self, value1, value2):
        # 변수 타입에 따라 조인 연산 수행
        # 여기서는 예시로 Interval 값을 조인한다고 가정합니다.
        if isinstance(value1, Interval) and isinstance(value2, Interval):
            return value1.join(value2)
        else:
            # 기타 타입에 대한 처리
            return value1  # 또는 다른 조인 로직 적용
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

            successors = list(self.get_current_function_cfg().graph.successors(current_node))
            for successor in successors:
                if successor != loop_node.false_branch:
                    stack.append(successor)

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
            return IntegerInterval(-2 ** (length - 1), 2 ** (length - 1) - 1, length)  # int의 기본 범위 반환

        # 2. uint 타입 처리
        elif var_type.startswith("uint"):
            length = int(var_type[4:]) if var_type != "uint" else 256  # uint 타입의 길이 (기본값은 256)
            return UnsignedIntegerInterval(0, 2 ** length - 1, length)  # uint의 기본 범위 반환

        # 3. bool 타입 처리
        elif var_type == "bool":
            return BoolInterval()  # bool은 항상 0 또는 1

        # 4. 기타 처리 (필요시 확장 가능)
        else:
            raise ValueError(f"Unsupported type for default interval: {var_type}")

    def evaluate_expression(self, expr, variables=None):
        """
        주어진 Expression 객체를 평가하여 그 Interval을 반환합니다.
        :param expr: Expression 객체
        :param variables: 현재 변수 상태 딕셔너리 (var_name -> Variables 객체)
        :return: Interval 객체
        """

        # 1. 리터럴 값인 경우 처리
        if expr.literal is not None:
            try:
                # 숫자 리터럴 처리 (진법 자동 감지)
                numeric_value = int(expr.literal, 0)
                if 'int' == expr.expr_type:
                    return IntegerInterval(numeric_value, numeric_value, expr.type_length)
                elif 'uint' == expr.expr_type:
                    return UnsignedIntegerInterval(numeric_value, numeric_value, expr.type_length)
                else:
                    raise ValueError(f"Unsupported type '{expr.expr_type}' for literal '{expr.literal}'")
            except ValueError:
                # Boolean 리터럴 처리
                if expr.literal.lower() == 'true':
                    return BoolInterval(is_true=True, is_false=False)
                elif expr.literal.lower() == 'false':
                    return BoolInterval(is_true=False, is_false=True)
                else:
                    raise ValueError(f"Unable to parse literal value '{expr.literal}'")

        # 2. 식별자인 경우 (변수)
        elif expr.identifier is not None:
            var_name = expr.identifier
            if variables is not None:
                if var_name in variables:
                    return variables[var_name].value
                else:
                    raise ValueError(f"Variable '{var_name}' not found in current context.")
            else:
                return self.get_variable_interval(var_name)

        # 3. 단항 연산자 처리
        if expr.operator in ['-', '!', '~'] and expr.expression:
            operand_interval = self.evaluate_expression(expr.expression, variables)
            if operand_interval is not None:
                if expr.operator == '-':
                    return operand_interval.negate()
                elif expr.operator == '!':
                    return operand_interval.logical_not()
                elif expr.operator == '~':
                    return operand_interval.bitwise_not()
            else:
                raise ValueError(f"Unable to evaluate operand in unary expression: {expr}")

        # 4. 이항 연산자 처리
        left_interval = self.evaluate_expression(expr.left, variables) if expr.left else None
        right_interval = self.evaluate_expression(expr.right, variables) if expr.right else None

        if left_interval is not None and right_interval is not None:
            operator = expr.operator
            # 산술 연산자 처리
            if operator == '+':
                return left_interval.add(right_interval)
            elif operator == '-':
                return left_interval.subtract(right_interval)
            elif operator == '*':
                return left_interval.multiply(right_interval)
            elif operator == '/':
                return left_interval.divide(right_interval)
            elif operator == '%':
                return left_interval.modulo(right_interval)
            elif operator == '**':
                return left_interval.exponentiate(right_interval)
            # 시프트 연산자 처리
            elif operator in ['<<', '>>', '>>>']:
                if 'int' in expr.expr_type:
                    return IntegerInterval.shift(left_interval, right_interval, operator)
                elif 'uint' in expr.expr_type:
                    return UnsignedIntegerInterval.shift(left_interval, right_interval, operator)
                else:
                    raise ValueError(f"Unsupported type '{expr.expr_type}' for shift operation")
            # 비교 연산자 처리
            elif operator in ['==', '!=', '<', '>', '<=', '>=']:
                result_interval = self.compare_intervals(left_interval, right_interval, operator)
                return result_interval
            # 논리 연산자 처리
            elif operator in ['&&', '||']:
                return left_interval.logical_op(right_interval, operator)
            else:
                raise ValueError(f"Unsupported operator '{operator}' in expression: {expr}")
        else:
            # 피연산자 중 하나라도 None인 경우 예외 발생
            raise ValueError(f"Unable to evaluate expression due to missing operand intervals: {expr}")

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

    """
    analysis result
    {
  "line": <start_line>,
  "interval": {
    "variable": <var_name>,
    "type": <var_type>,
    "value": [<min_value>, <max_value>]
  },
  "intent_check": {
    "expected": [<expected_min>, <expected_max>],
    "actual": [<actual_min>, <actual_max>],
    "message": <error_message>  # 없을 경우는 빈 문자열
  }
}
    """

    def get_analysis_result(self):
        # 가장 최근의 분석 결과를 반환
        return self.analysis_results if self.analysis_results else {}