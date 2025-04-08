# SolidityGuardian/Utils/CFG.py
import networkx as nx
import re
from Utils.util import *
from Utils.Interval import *

class CFGNode:
    def __init__(self, name,
                 condition_node=False,
                 condition_node_type=None,
                 fixpoint_evaluation_node=False,
                 loop_exit_node=False):
        self.name = name

        self.condition_node = condition_node
        self.condition_expr = None
        self.condition_node_type = condition_node_type

        self.join_point_node = False

        self.fixpoint_evaluation_node = fixpoint_evaluation_node
        self.loop_exit_node = loop_exit_node
        self.is_while_body = False
        self.fixpoint_evaluation_node_vars = {} # 고정점 분석을 위한 while문 진입 전에 var 상태, join 하면서 변하는 변수의 상태

        self.statements = []  # 기본 블록 내의 명령어 리스트
        self.variables = {}  # var_name -> Variables 객체

        self.function_exit_node = False
        self.return_val = None

    def add_assign_statement(self, variable_obj: Variables, expr: Expression, operator='='):
        """
        변수에 대한 할당문을 CFG에 추가하고 변수 정보를 업데이트합니다.
        :param variable_obj: Variables 객체
        :param expr: 우변 Expression 객체
        :param evaluated_value: 우변 표현식을 평가한 Interval 값
        :param operator: 할당 연산자
        """
        # Statement 생성
        assignment_stmt = Statement(
            statement_type='assignment',
            left=Expression(identifier=variable_obj.identifier),
            operator=operator,
            right=expr
        )
        self.statements.append(assignment_stmt)

        # 변수 정보 업데이트
        self.variables[variable_obj.identifier] = variable_obj

    def add_array_assign_statement(self, variable_obj: ArrayVariable, expr: Expression, operator='='):
        """
        배열 변수에 대한 할당문을 CFG에 추가합니다.
        :param variable_obj: ArrayVariable 객체
        :param expr: 우변 Expression 객체
        :param evaluated_value: 배열 요소들의 Interval 값 리스트
        :param operator: 할당 연산자
        """
        assignment_stmt = Statement(
            statement_type='array_assignment',
            left=Expression(identifier=variable_obj.identifier),
            operator=operator,
            right=expr
        )
        self.statements.append(assignment_stmt)

        # 변수 정보 업데이트
        self.variables[variable_obj.identifier] = variable_obj

    def add_struct_assign_statement(self, variable_obj: StructVariable, expr: Expression, operator='='):
        """
        구조체 변수에 대한 할당문을 CFG에 추가합니다.
        :param variable_obj: StructVariable 객체
        :param expr: 우변 Expression 객체
        :param evaluated_value: 구조체 멤버들의 Interval 값 딕셔너리
        :param operator: 할당 연산자
        """
        assignment_stmt = Statement(
            statement_type='struct_assignment',
            left=Expression(identifier=variable_obj.identifier),
            operator=operator,
            right=expr
        )
        self.statements.append(assignment_stmt)

        # 변수 정보 업데이트
        self.variables[variable_obj.identifier] = variable_obj

    def add_mapping_assign_statement(self, mapping_var: MappingVariable, left_expr: Expression,
                                     right_expr: Expression, operator='='):
        """
        매핑 변수의 특정 키에 대한 할당문을 CFG에 추가하고 변수 정보를 업데이트합니다.
        :param mapping_var: MappingVariable 객체 (매핑 변수)
        :param element_var: Variables 객체 (매핑의 특정 키에 해당하는 변수)
        :param left_expr: 좌변 Expression 객체
        :param right_expr: 우변 Expression 객체
        :param evaluated_value: 우변 표현식을 평가한 값
        :param operator: 할당 연산자
        """
        # Statement 생성
        assignment_stmt = Statement(
            statement_type='mapping_assignment',
            left=left_expr,
            operator=operator,
            right=right_expr
        )
        self.statements.append(assignment_stmt)

        # 매핑 변수의 정보 업데이트는 필요에 따라 수행
        self.variables[mapping_var.identifier] = mapping_var

    def add_function_call_statement(self, function_expr: Expression, evaluated_value=None):
        """
        함수 호출문을 CFG에 추가합니다.
        :param function_expr: 함수 호출 Expression 객체
        :param evaluated_value: 함수 호출의 평가 결과 (필요한 경우)
        """
        function_call_stmt = Statement(
            statement_type='function_call',
            function_call_expr=function_expr,
            evaluated_value=evaluated_value
        )
        self.statements.append(function_call_stmt)

    def add_return_statement(self, return_expr: Expression = None, evaluated_value=None):
        """
        반환 구문을 CFG에 추가하고, 반환 값을 업데이트합니다.
        :param return_expr: 반환할 Expression 객체
        :param evaluated_value: 평가된 Interval 값
        """
        return_stmt = Statement(
            statement_type='return',
            return_expr=return_expr,
            evaluated_value=evaluated_value
        )
        self.statements.append(return_stmt)
        self.return_val = evaluated_value  # exit 노드에 저장할 반환 값으로 사용

    def get_variable(self, var_name: str) -> Variables:
        """
        변수 이름을 받아 관련 변수를 반환합니다.
        :param var_name: 변수 이름 (identifier)
        :return: Variables 객체
        """
        return self.variables.get(var_name)

class CFG:
    def __init__(self, cfg_type):
        self.graph = nx.DiGraph()
        self.cfg_type = cfg_type
        self.entry_node = CFGNode("ENTRY")
        self.exit_node = CFGNode("EXIT")
        self.graph.add_node(self.entry_node)
        self.graph.add_node(self.exit_node)
        self.graph.add_edge(self.entry_node, self.exit_node)

    def get_entry_node(self):
        return self.entry_node

    def get_exit_node(self):
        return self.exit_node


class ContractCFG(CFG):
    def __init__(self, contract_name):
        super().__init__('contract')
        self.contract_name = contract_name
        self.state_variable_node = None

        self.structDefs = {}  # name -> StructDefinition 객체
        self.structVars = {} # name -> StructVariable 객체

        self.enumDefs = {} # name -> EnumDefinition 객체
        self.enumVars = {} # name -> EnumVariable 객체

        self.constructor = None  # FunctionCFG (Constructor Type)
        self.fallback = None
        self.receive = None

        self.modifiers = {}  # name -> FunctionCFG
        self.functions = {}  # name -> FunctionCFG

        # 새로 추가: pre-execution 글로벌 설정
        self.pre_exec_globals = {}  # e.g. { "block.timestamp": 100, ... }

    # Enum 정의 추가
    def define_enum(self, enum_name, enum_def):
        if enum_name not in self.enums:
            self.enumDefs[enum_name] = enum_def
        else:
            raise ValueError(f"Enum {enum_name} is already defined.")

    # Struct 정의 추가
    def define_struct(self, struct_def_obj):
        self.structDefs[struct_def_obj.struct_name] = struct_def_obj

    def add_enum_member(self, enum_name, member_name):
        if enum_name in self.enums:
            self.enumDefs[enum_name].add_member(member_name)
        else:
            raise ValueError(f"Enum {enum_name} is not defined.")

    def add_struct_member(self, struct_def_name, var_name, var_obj):
        if struct_def_name in self.structDefs :
            self.structDefs[struct_def_name].add_member(var_name, var_obj)
        else :
            raise ValueError(f"Struct {struct_def_name} is not defined/")

    def add_state_variable(self, variable, expr=None): # variable : Variables, expr : Interval
        # 상태 변수 노드가 없는 경우 생성
        if not self.state_variable_node:
            self.state_variable_node = CFGNode('State_Variable')
            self.graph.add_node(self.state_variable_node)

            # 기존 entry node의 successor를 새로운 state variable node의 successor로 설정
            successors = list(self.graph.successors(self.entry_node))
            for succ in successors:
                self.graph.add_edge(self.state_variable_node, succ)
                self.graph.remove_edge(self.entry_node, succ)

            # 새로운 state variable node를 entry node의 successor로 설정
            self.graph.add_edge(self.entry_node, self.state_variable_node)

        # 상태 변수 정보를 노드에 추가
        self.state_variable_node.add_assign_statement(variable_obj=variable, expr=expr)

    def add_constant_variable(self, variable, expr=None):
        if not self.state_variable_node:
            self.state_variable_node = CFGNode('State_Variable')
            self.graph.add_node(self.state_variable_node)

        # 상수 변수 정보를 노드에 추가
        self.state_variable_node.variables[variable.identifier] = {'variable' : variable, 'expression' : expr}

    def add_constructor_to_cfg(self, constructor_cfg):
        # 1. 상태변수 노드의 successor가 생성자가 되도록 설정
        if self.state_variable_node:
            # 상태변수 노드의 모든 successor를 가져옴
            successors = list(self.graph.successors(self.state_variable_node))
            for succ in successors:
                # 기존 상태변수 노드의 successor를 생성자의 exit_node와 연결
                self.graph.add_edge(constructor_cfg.exit_node, succ)
                # 상태변수 노드의 기존 successor 간선 삭제
                self.graph.remove_edge(self.state_variable_node, succ)

            # 상태변수 노드를 생성자의 entry_node와 연결
            self.graph.add_edge(self.state_variable_node, constructor_cfg.entry_node)
        else:
            # 상태변수 노드가 없을 경우 entry_node와 생성자 entry_node 연결
            self.graph.add_edge(self.entry_node, constructor_cfg.entry_node)

        # 2. ContractCFG에 생성자 CFG 추가
        self.constructor = constructor_cfg

    def get_modifier_cfg(self, modifier_name):
        # modifier가 존재하면 해당 CFG를 반환하고, 없으면 None을 반환
        return self.modifiers.get(modifier_name)

    def add_function_cfg(self, function_name, function_cfg):
        self.functions[function_name] = function_cfg

    def get_function_cfg(self, function_name):
        return self.functions[function_name]


class FunctionCFG(CFG):
    def __init__(self, function_type, function_name=None):
        super().__init__('function')
        self.function_type = function_type # constructor, fallback, receive, function
        self.function_name = function_name
        self.modifiers = {}
        self.related_variables = {}
        self.exit_node.function_exit_node = True

        self.pre_exec_state = {}
        self.pre_exec_local = {}

    def update_block(self, block_node):
        """
        FunctionCFG 내에서 블록을 업데이트하는 메서드.
        기존 그래프에 블록을 찾아 업데이트하거나, 새로운 블록이 추가된 경우 이를 반영.
        """
        # 그래프에서 block_node의 ID에 해당하는 노드를 찾아서 업데이트
        if self.graph.has_node(block_node):
            # 이미 해당 노드가 그래프에 있으면, 노드 정보를 업데이트
            existing_node = self.graph.nodes[block_node]
            # 필요에 따라 기존 노드의 속성을 업데이트 (여기선 덮어쓰기)
            self.graph.nodes[block_node].update(block_node.__dict__)

        else:
            raise ValueError(f"There is no {block_node} in functionCFG")

    def add_related_variable(self, variable_obj):
        # 배열 타입 처리
        if isinstance(variable_obj, ArrayVariable):
            # 배열은 각 요소를 따로 처리해야 함
            if not variable_obj.elements:
                initial_interval = IntegerInterval() if variable_obj.typeInfo.arrayBaseType.elementaryTypeName.startswith(
                    "int") \
                    else UnsignedIntegerInterval()  # 기본 interval 설정
                variable_obj.initialize_elements(initial_interval)
            self.related_variables[variable_obj.identifier] = variable_obj

        # 구조체 타입 처리
        elif isinstance(variable_obj, StructVariable):
            # 구조체 멤버 변수들 처리
            for member_name, member_var in variable_obj.members.items():
                self.add_related_variable(member_var)  # 각 멤버 변수에 대해 재귀적으로 처리

        # 기본 elementary 타입 처리 (로컬 변수)
        elif variable_obj.scope == 'local':
            # int 또는 uint 타입 처리
            if variable_obj.typeInfo.elementaryTypeName.startswith("int"):
                if variable_obj.value is None:
                    interval = IntegerInterval()
                    variable_obj.value = interval.bottom()  # IntegerInterval의 기본 bottom 값

            elif variable_obj.typeInfo.elementaryTypeName.startswith("uint"):
                if variable_obj.value is None:
                    interval = UnsignedIntegerInterval()
                    variable_obj.value = interval.bottom()  # UnsignedIntegerInterval의 기본 bottom 값

            # bool 타입 처리
            elif variable_obj.typeInfo.elementaryTypeName == "bool":
                if variable_obj.value is None:
                    variable_obj.value = BoolInterval.bottom()  # BooleanInterval의 기본 bottom 값

            self.related_variables[variable_obj.identifier] = variable_obj

        else :
            self.related_variables[variable_obj.identifier] = variable_obj


    def get_predecessor_node(self, cfg_node):
        if self.graph.has_node(cfg_node) :
            if self.graph.has_predecessor(cfg_node) :
                return self.graph.predecessors(cfg_node)
            else :
                raise ValueError("There is no predecessor")
        else :
            raise ValueError(f"There is no node in graph about {cfg_node}")

    def get_related_variable(self, var_name):
        # 변수를 반환
        return self.related_variables.get(var_name, None)

    def integrate_modifier(self, modifier_cfg):
        # 1. 기존 function entry node의 successor들을 저장
        successors = list(self.graph.successors(self.get_entry_node()))

        # 2. 기존 function entry node의 successor를 modifier entry node로 설정
        self.graph.add_edge(self.get_entry_node(), modifier_cfg.get_entry_node())

        # 3. Modifier의 exit node를 기존 function entry node의 successor로 연결
        for succ in successors:
            self.graph.add_edge(modifier_cfg.get_exit_node(), succ)
            self.graph.remove_edge(self.get_entry_node(), succ)

    def get_true_block(self, condition_node):
        """
        주어진 조건 노드의 true branch를 통해 true block을 반환
        """
        successors = list(self.graph.successors(condition_node))
        for successor in successors:
            if self.graph.edges[condition_node, successor].get('condition', False):  # True branch
                return successor
        return None  # True block을 찾지 못한 경우 None 반환

    def get_false_block(self, condition_node):
        """
        주어진 조건 노드의 false branch를 통해 false block을 반환
        """
        successors = list(self.graph.successors(condition_node))
        for successor in successors:
            if not self.graph.edges[condition_node, successor].get('condition', False):  # False branch
                return successor
        return None  # False block을 찾지 못한 경우 None 반환