# SolidityGuardian/Utils/CFG.py
import networkx as nx
import re
from Utils.util import *
from Utils.Interval import *

class CFGNode:
    def __init__(self, name,
                 condition_node=False,
                 condition_node_type=None,
                 join_point_node=False,
                 loop_exit_node=False):
        self.name = name
        self.condition_node = condition_node
        self.condition_expr = None
        self.condition_node_type = condition_node_type
        self.join_point_node = join_point_node
        self.loop_exit_node = loop_exit_node
        self.statements = []  # 기본 블록 내의 명령어 리스트
        self.variables = {}  # var_name -> Variables 객체

    def add_assign_statement(self, variable_obj: Variables, val: Interval):
        """
        변수에 대한 할당문을 CFG에 추가하고 변수 정보를 업데이트합니다.
        :param variable_obj: Variables 객체
        :param val: Interval 값
        """

        # 1. 할당문을 Statement 객체로 생성
        assignment_stmt = Statement(
            statement_type='assignment',
            left=Expression(identifier=variable_obj.identifier),
            operator='=',
            right=Expression(literal=val),
            var_type=variable_obj.typeInfo.typeCategory
        )
        self.statements.append(assignment_stmt)

        # 2. Variables 객체에 값 업데이트
        variable_obj.value = val

        # 3. 변수 정보 업데이트 (변수 이름 -> Variables 객체)
        self.variables[variable_obj.identifier] = variable_obj

    def copy_variables_to_node(self):

        return

    def get_variable(self, var_name: str) -> Variables:
        """
        변수 이름을 받아 관련 변수를 반환합니다.
        :param var_name: 변수 이름 (identifier)
        :return: Variables 객체
        """
        return self.variables.get(var_name)

    def add_if_statement(self):
        return

    def add_expression_statement(self, expr):
        self.statements.append(expr)



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
        self.enums = {} # name -> member list
        self.structs = {} #

        self.constructor = None # functionCFG (Constructor Type)
        self.fallback = None
        self.receive = None

        self.modifiers = {} # name -> functionCFG
        self.functions = {} # name -> functionCFG

    # for interactiveEnumDefinition in Solidity.g4
    def define_enum(self, enum_name):
        if enum_name not in self.enums:
            self.enums[enum_name] = []
        else:
            raise ValueError(f"Enum {enum_name} is already defined.")

    # for interactiveStructDefinition in Solidity.g4
    def define_struct(self, struct_name):
        if struct_name not in self.structs:
            self.structs[struct_name] = {}
        else:
            raise ValueError(f"Enum {struct_name} is already defined.")

    def add_enum_member(self, enum_name, member_name):
        if enum_name in self.enums:
            self.enums[enum_name].append(member_name)
        else:
            raise ValueError(f"Enum {enum_name} is not defined.")

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
        self.state_variable_node.add_assign_statement(variable, expr)


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

    def add_related_variable(self, variable_obj):
        # 추가적인 처리: 만약 로컬 변수의 경우 필요한 값들을 기본값으로 설정할 수 있음
        if variable_obj.scope == 'local':
            # int 또는 uint 타입 처리
            if variable_obj.typeInfo.elementaryTypeName.startswith("int"):
                if variable_obj.value is None :
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

        # 상태 변수든 로컬 변수든 상관없이 Variables 객체를 그대로 related_variables에 추가
        self.related_variables[variable_obj.identifier] = variable_obj

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