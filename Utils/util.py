class Statement:
    def __init__(self, statement_type, **kwargs):
        self.statement_type = statement_type  # 'assignment', 'if', 'while', 'for', 'return', 'require', 'assert' 등

        # 공통 속성
        self.expressions = []  # 해당 문에서 사용하는 Expression 객체들
        self.statements = []   # 블록 내에 포함된 Statement 객체들

        # 각 statement_type별로 필요한 속성 설정
        if statement_type == 'assignment':
            self.left = kwargs.get('left')        # 좌변 Expression
            self.operator = kwargs.get('operator')  # 할당 연산자 (예: '=')
            self.right = kwargs.get('right')      # 우변 Expression
        elif statement_type == 'if':
            self.condition = kwargs.get('condition')  # 조건 Expression
            self.then_body = kwargs.get('then_body', [])  # 참인 경우 실행할 Statement 리스트
            self.else_body = kwargs.get('else_body', [])  # 거짓인 경우 실행할 Statement 리스트
        elif statement_type == 'while':
            self.condition = kwargs.get('condition')  # 조건 Expression
            self.body = kwargs.get('body', [])        # 반복문 본문 Statement 리스트
        elif statement_type == 'for':
            self.initialization = kwargs.get('initialization')  # 초기화 Statement
            self.condition = kwargs.get('condition')            # 조건 Expression
            self.increment = kwargs.get('increment')            # 증감 Expression
            self.body = kwargs.get('body', [])                  # 반복문 본문 Statement 리스트
        elif statement_type in ['require', 'assert']:
            self.condition = kwargs.get('condition')  # 조건 Expression
            self.message = kwargs.get('message')      # 에러 메시지 (옵션)
        elif statement_type == 'return':
            self.expression = kwargs.get('expression')  # 반환할 Expression
        elif statement_type == 'expression_statement':
            self.expression = kwargs.get('expression')  # 표현식 자체가 문인 경우
        elif statement_type == 'block':
            self.statements = kwargs.get('statements', [])  # 블록 내의 Statement 리스트
        # 추가적인 문법 규칙에 대한 속성도 필요한 경우 추가



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
                 isConstant=False, scope=None):
        # 기본 속성
        self.identifier = identifier  # 변수명
        self.scope = scope  # 변수의 스코프 (local, state 등)
        self.isConstant = isConstant  # 상수 여부
        self.typeInfo = None # SolType

        # 값 정보
        self.value = value  # interval


class ArrayVariable(Variables):
    def __init__(self, identifier=None, base_type=None, array_length=None, is_dynamic=False, value=None,
                 isConstant=False, scope=None):
        super().__init__(identifier, value, isConstant, scope)
        self.typeInfo = SolType()
        self.typeInfo.typeCategory = 'array'
        self.typeInfo.arrayBaseType = base_type  # SolType 객체
        self.typeInfo.arrayLength = array_length
        self.typeInfo.isDynamicArray = is_dynamic
        self.elements = []  # 배열의 요소들: Variables 객체의 리스트

    def initialize_elements(self, initial_interval):
        """
        정적 배열의 요소들을 초기화하는 메소드
        :param initial_interval: 각 배열 요소에 할당될 초기 interval 값
        """
        if self.typeInfo.arrayLength is not None:
            for i in range(self.typeInfo.arrayLength):
                element = Variables(identifier=f"{self.identifier}[{i}]", value=initial_interval)
                self.elements.append(element)



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
