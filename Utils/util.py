from Utils.Interval import *

class Statement:
    def __init__(self, statement_type, **kwargs):
        self.statement_type = statement_type  # 'assignment', 'if', 'while', 'for', 'return', 'require', 'assert' 등

        # 공통 속성
        self.expressions = []  # 해당 문에서 사용하는 Expression 객체들
        self.statements = []   # 블록 내에 포함된 Statement 객체들

        # 각 statement_type별로 필요한 속성 설정
        if statement_type == 'assignment':
            self.left = kwargs.get('left')        # 좌변 Expression
            self.operator = kwargs.get('operator')  # 할당 연산자 (예: '=', '+=', '-=' 등)
            self.right = kwargs.get('right')      # 우변 Expression
            self.evaluated_value = kwargs.get('evaluated_value')  # 우변 표현식을 평가한 Interval 값



class Expression:
    def __init__(self, left=None, operator=None, right=None, identifier=None, literal=None, var_type=None,
                 function=None, arguments=None, named_arguments=None, base=None, access=None,
                 index=None, start_index=None, end_index=None, member=None, options=None,
                 type_name=None, expression=None, condition=None, true_expr=None, false_expr=None,
                 is_postfix=None, elements=None, expr_type=None, type_length=256, context=None):
        self.left = left                # 좌측 피연산자 (Expression)
        self.operator = operator        # 연산자 (문자열)
        self.right = right              # 우측 피연산자 (Expression)
        self.identifier = identifier    # 식별자 (변수 이름, 함수 이름 등)
        self.literal = literal          # 리터럴 값 (숫자, 문자열 등)
        self.var_type = var_type        # 변수 타입 (문자열)
        self.function = function        # 함수 표현식 (Expression)
        self.arguments = arguments      # 위치 기반 인자 목록 (리스트)
        self.named_arguments = named_arguments  # 이름 지정 인자 (딕셔너리)
        self.base = base                # 인덱스 또는 멤버 접근의 대상 표현식 (Expression)
        self.access = access            # index_access 등
        self.index = index              # 단일 인덱스 표현식 (Expression)
        self.start_index = start_index  # 슬라이싱의 시작 인덱스 (Expression)
        self.end_index = end_index      # 슬라이싱의 끝 인덱스 (Expression)
        self.member = member            # 멤버 이름 (문자열)
        self.options = options          # 함수 호출 옵션 (딕셔너리)
        self.type_name = type_name      # 타입 변환의 대상 타입 이름 (문자열)
        self.expression = expression    # 변환될 표현식 또는 단일 표현식 (Expression)
        self.condition = condition      # 조건식 (삼항 연산자용) (Expression)
        self.true_expr = true_expr      # 조건식이 참일 때의 표현식 (Expression)
        self.false_expr = false_expr    # 조건식이 거짓일 때의 표현식 (Expression)
        self.is_postfix = is_postfix    # 후위 연산자 여부 (Boolean)
        self.elements = elements        # 튜플 또는 배열의 요소들 (리스트)
        self.expr_type = expr_type      # 표현식의 타입 (예: 'int', 'uint', 'bool')
        self.type_length = type_length  # 타입의 길이 (예: 256)
        self.context = context



class Variables:
    def __init__(self, identifier=None, value=None,
                 isConstant=False, scope=None, typeInfo=None):
        # 기본 속성
        self.identifier = identifier  # 변수명
        self.scope = scope  # 변수의 스코프 (local, state 등)
        self.isConstant = isConstant  # 상수 여부
        self.typeInfo = typeInfo # SolType

        # 값 정보
        self.value = value  # interval



class ArrayVariable(Variables):
    def __init__(self, identifier=None, base_type=None, array_length=None, is_dynamic=False, value=None,
                 isConstant=False, scope=None):
        super().__init__(identifier, value, isConstant, scope)
        self.typeInfo = SolType()
        self.typeInfo.typeCategory = 'array'
        self.typeInfo.arrayBaseType = base_type  # SolType 객체 (배열의 기본 타입이 배열일 수도 있음)
        self.typeInfo.arrayLength = array_length
        self.typeInfo.isDynamicArray = is_dynamic
        self.elements = []  # 배열의 요소들: Variables 객체의 리스트

    def initialize_elements(self, initial_interval):
        """
        정적 배열의 요소들을 초기화하는 메소드.
        기본 타입이 배열인 경우 재귀적으로 요소들을 초기화합니다.
        :param initial_interval: 각 배열 요소에 할당될 초기 interval 값
        """
        if self.typeInfo.arrayLength is not None:
            for i in range(self.typeInfo.arrayLength):
                # 배열의 기본 타입이 또 다른 배열인 경우 처리 (이중 배열)
                if isinstance(self.typeInfo.arrayBaseType, SolType) and self.typeInfo.arrayBaseType.typeCategory == 'array':
                    sub_array = ArrayVariable(
                        identifier=f"{self.identifier}[{i}]",
                        base_type=self.typeInfo.arrayBaseType.arrayBaseType,  # 하위 배열의 타입
                        array_length=self.typeInfo.arrayBaseType.arrayLength,
                        is_dynamic=self.typeInfo.arrayBaseType.isDynamicArray,
                        scope=self.scope
                    )
                    sub_array.initialize_elements(initial_interval)  # 재귀적으로 초기화
                    self.elements.append(sub_array)
                else:
                    # 일반 배열 요소인 경우 Variables 객체로 처리
                    element = Variables(identifier=f"{self.identifier}[{i}]", value=initial_interval,
                                        typeInfo=self.typeInfo.arrayBaseType)
                    self.elements.append(element)

class MappingVariable(Variables):
    def __init__(self, identifier=None, key_type=None, value_type=None, value=None,
                 isConstant=False, scope=None):
        super().__init__(identifier, value, isConstant, scope)
        self.typeInfo = SolType()
        self.typeInfo.typeCategory = 'mapping'
        self.typeInfo.mappingKeyType = key_type  # 키 타입: SolType 객체
        self.typeInfo.mappingValueType = value_type  # 값 타입: SolType 객체
        self.mapping = {}  # 매핑된 키-값 쌍 저장: key -> Variables 객체

    def add_mapping(self, key, value):
        """
        매핑에 새로운 키-값 쌍을 추가합니다.
        :param key: 매핑 키 (키 타입에 맞는 값이어야 함)
        :param value: 매핑 값 (Variables 객체 또는 그 하위 클래스)
        """
        if not isinstance(key, Variables):
            raise ValueError(f"Invalid key type: {key} is not a valid Variables object.")
        if not isinstance(value, Variables):
            raise ValueError(f"Invalid value type: {value} is not a valid Variables object.")

        # 키와 값의 타입이 적합한지 확인
        if key.typeInfo.elementaryTypeName != self.typeInfo.mappingKeyType.elementaryTypeName:
            raise TypeError(
                f"Key type mismatch: Expected {self.typeInfo.mappingKeyType.elementaryTypeName}, but got {key.typeInfo.elementaryTypeName}")

        # 매핑의 값 타입이 다른 매핑, 배열, 구조체인 경우 처리
        if isinstance(value, MappingVariable):
            # 이중 매핑의 경우
            if value.typeInfo.typeCategory != 'mapping':
                raise TypeError(f"Value type mismatch: Expected 'mapping', but got {value.typeInfo.typeCategory}")
        elif isinstance(value, ArrayVariable):
            # 값이 배열일 경우
            if value.typeInfo.typeCategory != 'array':
                raise TypeError(f"Value type mismatch: Expected 'array', but got {value.typeInfo.typeCategory}")
        elif isinstance(value, StructVariable):
            # 값이 구조체일 경우
            if value.typeInfo.typeCategory != 'struct':
                raise TypeError(f"Value type mismatch: Expected 'struct', but got {value.typeInfo.typeCategory}")
        else:
            # 기본 타입의 경우 처리
            if value.typeInfo.elementaryTypeName != self.typeInfo.mappingValueType.elementaryTypeName:
                raise TypeError(
                    f"Value type mismatch: Expected {self.typeInfo.mappingValueType.elementaryTypeName}, but got {value.typeInfo.elementaryTypeName}")

        # 매핑 추가
        self.mapping[key.identifier] = value

    def get_mapping(self, key):
        """
        주어진 키에 해당하는 값을 반환합니다.
        :param key: 매핑 키 (키 타입에 맞는 값이어야 함)
        :return: 매핑된 Variables 객체 또는 None
        """
        if key in self.mapping:
            return self.mapping[key]
        else:
            raise KeyError(f"Key '{key}' not found in the mapping.")

    def remove_mapping(self, key):
        """
        매핑에서 주어진 키를 제거합니다.
        :param key: 매핑 키
        """
        if key in self.mapping:
            del self.mapping[key]
        else:
            raise KeyError(f"Key '{key}' not found in the mapping.")


class StructVariable(Variables):
    def __init__(self, identifier=None, struct_type=None, value=None, isConstant=False, scope=None):
        super().__init__(identifier, value, isConstant, scope)
        self.typeInfo = SolType()
        self.typeInfo.typeCategory = 'struct'
        self.typeInfo.structTypeName = struct_type  # 구조체 이름
        self.members = {}  # 멤버 변수들: 필드명 -> Variables 객체

class StructDefinition:
    def __init__(self, struct_name):
        self.struct_name = struct_name
        self.members = {}  # 멤버 변수들: 필드명 -> SolType 객체

class EnumVariable(Variables):
    def __init__(self, identifier=None, enum_type=None, value=None, isConstant=False, scope=None):
        super().__init__(identifier, value, isConstant, scope)
        self.typeInfo = SolType()
        self.typeInfo.typeCategory = 'enum'
        self.typeInfo.enumTypeName = enum_type  # 열거형 이름
        self.members = {}  # 멤버 변수들: 멤버명 -> 정수 값 (열거형의 각 멤버는 정수 값에 매핑됨)
        self.current_value = None  # 현재 설정된 멤버의 이름

    def set_member_value(self, member_name):
        """
        열거형 변수의 값을 특정 멤버로 설정합니다.
        :param member_name: 열거형 멤버 이름
        """
        if member_name in self.members:
            self.current_value = member_name
            self.value = self.members[member_name]  # 멤버의 정수 값을 변수의 값으로 설정
        else:
            raise ValueError(f"Member '{member_name}' not found in enum '{self.typeInfo.enumTypeName}'.")

    def get_member_value(self):
        """
        열거형 변수의 현재 값을 반환합니다.
        :return: 현재 설정된 멤버의 이름
        """
        return self.current_value

class EnumDefinition:
    def __init__(self, enum_name):
        self.enum_name = enum_name
        self.members = []  # 멤버들의 리스트

    def add_member(self, member_name):
        if member_name not in self.members:
            self.members.append(member_name)
        else:
            raise ValueError(f"Member '{member_name}' is already defined in enum '{self.enum_name}'.")


class SolType:
    def __init__(self):
        self.typeCategory = None  # 'elementary', 'array', 'mapping', 'struct', 'function', 'unknown'

        # elementary 타입 정보
        self.elementaryTypeName = None  # 예: 'uint256', 'address'
        self.intTypeLength = None  # 정수 타입의 비트 길이 (예: 256)

        # 배열 타입 정보
        self.arrayBaseType = None  # Type 객체
        self.arrayLength = None  # 배열 길이
        self.isDynamicArray = False  # 동적 배열 여부

        # mapping 타입 정보
        self.mappingKeyType = None  # Type 객체
        self.mappingValueType = None  # Type 객체

        # 구조체 타입 정보
        self.structTypeName = None  # 구조체 이름 (문자열)

        # 기타 필요한 속성 추가 가능
