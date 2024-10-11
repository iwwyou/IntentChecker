class Statement:
    def __init__(self, statement_type, identifier=None, string_literal=None, arguments=None):
        self.statement_type = statement_type  # 예: 'revert', 'require', 'assert'
        self.identifier = identifier          # Revert, require 등의 식별자
        self.string_literal = string_literal  # 문자열 리터럴 (에러 메시지)
        self.arguments = arguments            # 함수 호출의 인자 목록


class Expression:
    def __init__(self, left=None, operator=None, right=None, identifier=None, literal=None, var_type=None,
                 function=None, arguments=None, named_arguments=None, base=None,
                 index=None, start_index=None, end_index=None, member=None, options=None,
                 type_name=None, expression=None, condition=None, true_expr=None, false_expr=None,
                 is_postfix=None, elements=None, expr_type=None, type_length=256):
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


class Variables:
    def __init__(self, identifier=None, metaType=None, varType=None,
                 intTypeLength=None, arrayLength=None, isDynamic=False,
                 structName=None, enumName=None, value=None,
                 isConstant=False, scope=None, mappingKeyType=None,
                 mappingValueType=None):
        # 기본 속성
        self.identifier = identifier  # 변수명
        self.metaType = metaType  # 변수 메타타입: elementary, struct, array, mapping, enum 등
        self.scope = scope  # 변수의 스코프 (local, state 등)
        self.isConstant = isConstant  # 상수 여부

        # 타입 정보
        self.varType = varType  # 타입 이름 (ex. uint256)
        self.intTypeLength = intTypeLength  # int, uint 타입의 경우 길이

        # Mapping 관련 정보
        self.mappingKeyType = mappingKeyType  # mapping key의 타입 (없으면 None)
        self.mappingValueType = mappingValueType  # mapping value의 타입 (없으면 None)

        # 배열 타입 관련 속성
        self.arrayLength = arrayLength  # 배열 크기
        self.isDynamic = isDynamic  # 동적 배열 여부

        # 구조체 이름
        self.structName = structName  # 구조체 이름 (struct인 경우)

        # enum 이름
        self.enumName = enumName  # enum 이름 (enum인 경우)

        # 값 정보
        self.value = value  # interval





        # 변경 이력
        self.history = []  # 변수의 변경 이력을 저장하는 리스트 (block number, line number, value)

    def add_to_history(self, block_number, line_number, expression, value):
        """변수 값 변경 시 이력 기록"""
        self.history.append({
            "block_number": block_number,
            "line_number": line_number,
            "expression": expression,
            "value": value
        })

    def update_value(self, new_value):
        """변수 값 업데이트"""
        self.value = new_value

    def get_value(self):
        """현재 변수 값 반환"""
        return self.value

    def get_meta_type(self):
        """변수의 메타타입 반환 (elementary, struct, array, mapping, enum)"""
        return self.metaType

    def get_type_info(self):
        """변수의 타입 정보 반환"""
        return {
            "type": self.var_type,
            "length": self.intTypeLength,
            "array_length": self.arrayLength,
            "is_dynamic": self.isDynamic,
            "struct_name": self.structName,
            "enum_name": self.enumName
        }

    def get_mapping_info(self):
        """mapping의 key-value 타입 정보 반환"""
        return {
            "key_type": self.mappingKeyType,
            "value_type": self.mappingValueType
        }

    def is_state_variable(self):
        """상태 변수인지 여부 확인"""
        return self.scope == 'state'

    def is_local_variable(self):
        """로컬 변수인지 여부 확인"""
        return self.scope == 'local'

    def is_constant(self):
        """상수 여부 확인"""
        return self.isConstant
