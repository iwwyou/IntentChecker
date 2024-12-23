class Interval:
    def __init__(self, min_value=None, max_value=None):
        self.min_value = min_value
        self.max_value = max_value

    def encompass(self, intended_interval):
        """
        실제 interval이 의도된 interval에 포함되는지 여부를 판단하는 연산자.
        """
        return self.min_value >= intended_interval.min_value and self.max_value <= intended_interval.max_value

    def equals(self, other):
        return self.min_value == other.min_value and self.max_value == other.max_value

    def copy(self):
        return Interval(self.min_value, self.max_value)

class IntegerInterval(Interval):
    def __init__(self, min_value=None, max_value=None, type_length=None):
        super().__init__(min_value, max_value)
        self.type_length = type_length

    def initialize_range(self, type_name):
        # type_name에서 숫자 부분 추출
        if type_name == "int" or type_name == "uint":
            bits = 256  # 기본값으로 256비트 설정
        else:
            bits = int(''.join(filter(str.isdigit, type_name)))

        if "int" in type_name:
            # Signed integer
            min_value = -2 ** (bits - 1)
            max_value = 2 ** (bits - 1) - 1
        else:
            # Unsigned integer
            min_value = 0
            max_value = 2 ** bits - 1

        self.min_value = min_value
        self.max_value = max_value
        self.type_length = bits

    def calculate_interval(self, right_interval, operator):
        # 연산자에 따라 interval 계산 수행
        if operator == '+':
            return self.add(right_interval)
        elif operator == '-':
            return self.subtract(right_interval)
        elif operator == '*':
            return self.multiply(right_interval)
        elif operator == '/':
            return self.divide(right_interval)
        elif operator == '%':
            return self.modulo(right_interval)
        elif operator == '<<':
            return self.left_shift(right_interval)
        elif operator == '>>' or operator == '>>>':
            return self.right_shift(right_interval)
        elif operator == '&':
            return self.bitwise_and(right_interval)
        elif operator == '|':
            return self.bitwise_or(right_interval)
        elif operator == '^':
            return self.bitwise_xor(right_interval)
        elif operator == '&&':
            return self.logical_and(right_interval)
        elif operator == '||':
            return self.logical_or(right_interval)
        else:
            raise ValueError(f"Unsupported operator: {operator}")

    def intersect(self, other):
        return IntegerInterval(max(self.min_value, other.min_value), min(self.max_value, other.max_value),
                               self.type_length)

    def less_than(self, other):
        # a < b 상황에서 a의 상한을 b.min_value - 1로 줄여나감
        return IntegerInterval(self.min_value, min(self.max_value, other.min_value - 1), self.type_length)

    def greater_than(self, other):
        # a > b 상황에서 a의 하한을 b.max_value + 1로 올려나감
        return IntegerInterval(max(self.min_value, other.max_value + 1), self.max_value, self.type_length)

    def less_than_or_equal(self, other):
        # a <= b 상황에서 a의 상한을 b.max_value로 줄여나감
        return IntegerInterval(self.min_value, min(self.max_value, other.max_value), self.type_length)

    def greater_than_or_equal(self, other):
        # a >= b 상황에서 a의 하한을 b.min_value로 올려나감
        return IntegerInterval(max(self.min_value, other.min_value), self.max_value, self.type_length)

    def widen(self, current_interval):
        new_min = float('-inf') if self.min_value > current_interval.min_value else self.min_value
        new_max = float('inf') if self.max_value < current_interval.max_value else self.max_value
        return IntegerInterval(new_min, new_max, self.type_length)

    def narrow(self, new_interval):
        if self.min_value == float('-inf') or self.max_value == float('inf'):
            return new_interval

        new_min = new_interval.min_value if self.min_value == float('-inf') else self.min_value
        new_max = new_interval.max_value if self.max_value == float('inf') else min(self.max_value,
                                                                                    new_interval.max_value)
        return IntegerInterval(new_min, new_max, self.type_length)

    def top(self):
        min_value = -2 ** (self.type_length - 1)
        max_value = 2 ** (self.type_length - 1) - 1
        return IntegerInterval(min_value, max_value, self.type_length)

    def bottom(self):
        return IntegerInterval(None, None, self.type_length)

    def join(self, other_interval):
        if self.type_length != other_interval.type_length:
            raise ValueError("Cannot join intervals of different type lengths")

        if self.min_value is None:
            return other_interval
        if other_interval.min_value is None:
            return self

        new_min = min(self.min_value, other_interval.min_value)
        new_max = max(self.max_value, other_interval.max_value)
        return IntegerInterval(new_min, new_max, self.type_length)

    def meet(self, other_interval):
        if self.type_length != other_interval.type_length:
            raise ValueError("Cannot meet intervals of different type lengths")

        if self.min_value is None:
            return other_interval
        if other_interval.min_value is None:
            return self

        new_min = max(self.min_value, other_interval.min_value)
        new_max = min(self.max_value, other_interval.max_value)
        if new_min > new_max:
            return self.bottom()
        return IntegerInterval(new_min, new_max, self.type_length)

    def negate(self):
        if self.min_value is not None and self.max_value is not None:
            return IntegerInterval(-self.max_value, -self.min_value, self.type_length)
        else:
            return IntegerInterval(None, None, self.type_length)

    def add(self, other_interval):  # aexp
        if self.type_length != other_interval.type_length:
            raise ValueError("Cannot add intervals of different type lengths")

        if self.min_value is None or other_interval.min_value is None:
            min_sum = None
        else:
            min_sum = self.min_value + other_interval.min_value

        if self.max_value is None or other_interval.max_value is None:
            max_sum = None
        else:
            max_sum = self.max_value + other_interval.max_value

        return IntegerInterval(min_sum, max_sum, self.type_length)

    def prefix_increment(self):  # aexp
        if self.min_value is not None and self.max_value is not None:
            return IntegerInterval(self.min_value + 1, self.max_value + 1, self.type_length)
        return self

    def prefix_decrement(self):  # aexp
        if self.min_value is not None and self.max_value is not None:
            return IntegerInterval(self.min_value - 1, self.max_value - 1, self.type_length)
        return self

    def postfix_increment(self):  # aexp
        # 후위 증감 연산자 처리 (값을 반환한 후 증가)
        result = IntegerInterval(self.min_value, self.max_value, self.type_length)
        if self.min_value is not None and self.max_value is not None:
            self.min_value += 1
            self.max_value += 1
        return result

    def postfix_decrement(self):  # aexp
        # 후위 증감 연산자 처리 (값을 반환한 후 감소)
        result = IntegerInterval(self.min_value, self.max_value, self.type_length)
        if self.min_value is not None and self.max_value is not None:
            self.min_value -= 1
            self.max_value -= 1
        return result

    def subtract(self, other_interval):  # aexp
        if self.type_length != other_interval.type_length:
            raise ValueError("Cannot subtract intervals of different type lengths")

        if self.min_value is None or other_interval.max_value is None:
            min_diff = None
        else:
            min_diff = self.min_value - other_interval.max_value

        if self.max_value is None or other_interval.min_value is None:
            max_diff = None
        else:
            max_diff = self.max_value - other_interval.min_value

        return IntegerInterval(min_diff, max_diff, self.type_length)

    def multiply(self, other_interval):  # aexp
        if self.type_length != other_interval.type_length:
            raise ValueError("Cannot multiply intervals of different type lengths")

        possible_results = [
            self.min_value * other_interval.min_value,
            self.min_value * other_interval.max_value,
            self.max_value * other_interval.min_value,
            self.max_value * other_interval.max_value,
        ]

        # Remove None values from possible results
        filtered_results = [x for x in possible_results if x is not None]

        if not filtered_results:
            return IntegerInterval(None, None, self.type_length)

        min_product = min(filtered_results)
        max_product = max(filtered_results)

        return IntegerInterval(min_product, max_product, self.type_length)

    def divide(self, other_interval):
        # 개선된 예:
        # 0 division 체크
        if (other_interval.min_value is not None and other_interval.min_value == 0) or \
                (other_interval.max_value is not None and other_interval.max_value == 0):
            # 나눌 수 없음(0포함), 불확실로 처리
            return IntegerInterval(None, None, self.type_length)

        # 음수 범위 처리
        # 일단 간단히 min, max로 // 수행
        possible_results = []

        def safe_div(n, d):
            if n is not None and d is not None and d != 0:
                return n // d
            return None

        candidates = [
            safe_div(self.min_value, other_interval.min_value),
            safe_div(self.min_value, other_interval.max_value),
            safe_div(self.max_value, other_interval.min_value),
            safe_div(self.max_value, other_interval.max_value)
        ]
        candidates = [c for c in candidates if c is not None]
        if not candidates:
            return IntegerInterval(None, None, self.type_length)

        return IntegerInterval(min(candidates), max(candidates), self.type_length)

    def exponentiation(self, exponent_interval):  # aexp
        if self.min_value is None or exponent_interval.min_value is None:
            return IntegerInterval(None, None, self.type_length)

        # 간단한 경우에 대한 예측
        possible_results = [
            self.min_value ** exponent_interval.min_value,
            self.min_value ** exponent_interval.max_value,
            self.max_value ** exponent_interval.min_value,
            self.max_value ** exponent_interval.max_value,
        ]

        min_result = min(possible_results)
        max_result = max(possible_results)

        return IntegerInterval(min_result, max_result, self.type_length)

    def modulo(self, other_interval):  # aexp
        # 나누는 수가 0이 될 수 있는 경우, 결과를 예측할 수 없으므로 None 반환
        if other_interval.min_value is None or other_interval.max_value is None or 0 in [other_interval.min_value, other_interval.max_value]:
            return IntegerInterval(None, None, self.type_length)

        # 나머지의 가능한 최대 범위는 0부터 (나누는 수의 최대값 - 1)까지
        max_divisor = max(abs(other_interval.min_value), abs(other_interval.max_value))
        return IntegerInterval(0, max_divisor - 1, self.type_length)

    def bitwise_and(self, other_interval):
        # 두 값의 가능한 최소 및 최대값을 고려하여 결과의 범위를 추정
        min_value = 0  # AND 연산의 결과는 항상 0 이상
        max_value = min(self.max_value, other_interval.max_value)  # 최대값은 두 입력값 중 작은 값으로 제한됨

        return IntegerInterval(min_value, max_value, self.type_length)

    def bitwise_or(self, other_interval):
        # 두 값의 가능한 최소 및 최대값을 고려하여 결과의 범위를 추정
        min_value = max(self.min_value, other_interval.min_value)  # 최소값은 두 입력값 중 큰 값으로 제한됨
        max_value = max(self.max_value, other_interval.max_value)  # 최대값은 두 입력값 중 큰 값

        return IntegerInterval(min_value, max_value, self.type_length)

    def bitwise_xor(self, other_interval):
        # 두 값의 가능한 최소 및 최대값을 고려하여 결과의 범위를 추정
        min_value = 0  # XOR 연산의 결과는 0 이상
        max_value = max(self.max_value, other_interval.max_value)  # 최대값은 두 입력값 중 큰 값

        return IntegerInterval(min_value, max_value, self.type_length)

    def bitwise_not(self):
        # 비트 반전 연산 처리 (보수 연산)
        if self.min_value is not None and self.max_value is not None:
            type_max = 2 ** self.type_length - 1
            min_value = (~self.max_value) & type_max
            max_value = (~self.min_value) & type_max
            return IntegerInterval(min_value, max_value, self.type_length)
        else:
            return IntegerInterval(None, None, self.type_length)

    def shift(self, shift_interval, operator):
        if operator == '<<':
            return self.left_shift(shift_interval)
        elif operator == '>>' or operator == '>>>':
            return self.right_shift(shift_interval)
        else:
            raise ValueError(f"Unsupported shift operator: {operator}")

    def left_shift(self, shift_interval):
        # 시프트 양이 음수이거나 정의되지 않았다면, 결과를 예측할 수 없음
        if shift_interval.min_value is None or shift_interval.min_value < 0:
            return IntegerInterval(None, None, self.type_length)

        # 가능한 최소 및 최대 시프트 양을 고려하여 결과 범위 계산
        min_shifted = self.min_value << shift_interval.min_value
        max_shifted = self.max_value << shift_interval.max_value

        # 오버플로우를 고려하여 타입 길이에 맞는 범위로 조정
        type_min = -2 ** (self.type_length - 1)
        type_max = 2 ** (self.type_length - 1) - 1

        min_shifted = max(min_shifted, type_min)
        max_shifted = min(max_shifted, type_max)

        return IntegerInterval(min_shifted, max_shifted, self.type_length)

    def right_shift(self, shift_interval):
        # 시프트 양이 음수이거나 정의되지 않았다면, 결과를 예측할 수 없음
        if shift_interval.min_value is None or shift_interval.min_value < 0:
            return IntegerInterval(None, None, self.type_length)

        # 가능한 최소 및 최대 시프트 양을 고려하여 결과 범위 계산
        min_shifted = self.min_value >> shift_interval.max_value
        max_shifted = self.max_value >> shift_interval.min_value

        return IntegerInterval(min_shifted, max_shifted, self.type_length)

    def logical_and(self, other_interval):
        return BoolInterval(0, 1)

    def logical_or(self, other_interval):
        return BoolInterval(0, 1)

    def logical_not(self):
        # 불리언 연산의 결과는 0 또는 1
        return BoolInterval(0, 1)

    def add_assign(self, other_interval):
        # 'x += y' 연산을 처리
        return self.add(other_interval)

    def subtract_assign(self, other_interval):
        # 'x -= y' 연산을 처리
        return self.subtract(other_interval)

    def multiply_assign(self, other_interval):
        # 'x *= y' 연산을 처리
        return self.multiply(other_interval)

    def divide_assign(self, other_interval):
        # 'x /= y' 연산을 처리
        return self.divide(other_interval)

    def modulo_assign(self, other_interval):
        # 'x %= y' 연산을 처리
        return self.modulo(other_interval)

    def bitwise_and_assign(self, other_interval):
        # 'x &= y' 연산을 처리
        return self.bitwise_and(other_interval)

    def bitwise_or_assign(self, other_interval):
        # 'x |= y' 연산을 처리
        return self.bitwise_or(other_interval)

    def bitwise_xor_assign(self, other_interval):
        # 'x ^= y' 연산을 처리
        return self.bitwise_xor(other_interval)

    def shift_left_assign(self, shift_interval):
        # 'x <<= y' 연산을 처리
        return self.left_shift(shift_interval)

    def shift_right_assign(self, shift_interval):
        # 'x >>= y' 연산을 처리
        return self.right_shift(shift_interval)

class UnsignedIntegerInterval(Interval):
    def __init__(self, min_value=None, max_value=None, type_length=None):
        super().__init__(min_value, max_value)
        self.type_length = type_length

    def initialize_range(self, type_name):
        # type_name에서 숫자 부분 추출
        if type_name == "uint":
            bits = 256  # 기본값으로 256비트 설정
        else:
            bits = int(''.join(filter(str.isdigit, type_name)))

        min_value = 0
        max_value = 2 ** bits - 1

        self.min_value = min_value
        self.max_value = max_value
        self.type_length = bits

    def calculate_interval(self, right_interval, operator):
        # 연산자에 따라 interval 계산 수행
        if operator == '+':
            return self.add(right_interval)
        elif operator == '-':
            return self.subtract(right_interval)
        elif operator == '*':
            return self.multiply(right_interval)
        elif operator == '/':
            return self.divide(right_interval)
        elif operator == '%':
            return self.modulo(right_interval)
        elif operator == '<<':
            return self.left_shift(right_interval)
        elif operator == '>>' or operator == '>>>':
            return self.right_shift(right_interval)
        elif operator == '&':
            return self.bitwise_and(right_interval)
        elif operator == '|':
            return self.bitwise_or(right_interval)
        elif operator == '^':
            return self.bitwise_xor(right_interval)
        elif operator == '&&':
            return self.logical_and(right_interval)
        elif operator == '||':
            return self.logical_or(right_interval)
        else:
            raise ValueError(f"Unsupported operator: {operator}")

    def intersect(self, other):
        return UnsignedIntegerInterval(max(self.min_value, other.min_value),
                                       min(self.max_value, other.max_value),
                                       self.type_length)

    def less_than(self, other):
        return UnsignedIntegerInterval(self.min_value, min(self.max_value, other.min_value - 1), self.type_length)

    def greater_than(self, other):
        return UnsignedIntegerInterval(max(self.min_value, other.max_value + 1), self.max_value, self.type_length)

    def less_than_or_equal(self, other):
        return UnsignedIntegerInterval(self.min_value, min(self.max_value, other.max_value), self.type_length)

    def greater_than_or_equal(self, other):
        return UnsignedIntegerInterval(max(self.min_value, other.min_value), self.max_value, self.type_length)

    def widen(self, current_interval):
        new_min = 0 if self.min_value > current_interval.min_value else self.min_value
        new_max = float('inf') if self.max_value < current_interval.max_value else self.max_value
        return UnsignedIntegerInterval(new_min, new_max, self.type_length)

    def narrow(self, new_interval):
        if self.max_value == float('inf'):
            return new_interval

        new_min = new_interval.min_value if self.min_value == 0 else self.min_value
        new_max = new_interval.max_value if self.max_value == float('inf') else min(self.max_value,
                                                                                    new_interval.max_value)
        return UnsignedIntegerInterval(new_min, new_max, self.type_length)

    def top(self):
        min_value = 0
        max_value = 2 ** self.type_length - 1
        return UnsignedIntegerInterval(min_value, max_value, self.type_length)

    def bottom(self):
        return UnsignedIntegerInterval(None, None, self.type_length)

    def join(self, other_interval):
        if self.type_length != other_interval.type_length:
            raise ValueError("Cannot join intervals of different type lengths")

        if self.min_value is None:
            return other_interval
        if other_interval.min_value is None:
            return self

        new_min = min(self.min_value, other_interval.min_value)
        new_max = max(self.max_value, other_interval.max_value)
        return UnsignedIntegerInterval(new_min, new_max, self.type_length)

    def meet(self, other_interval):
        if self.type_length != other_interval.type_length:
            raise ValueError("Cannot meet intervals of different type lengths")

        if self.min_value is None or other_interval.min_value is None:
            return self.bottom()

        new_min = max(self.min_value, other_interval.min_value)
        new_max = min(self.max_value, other_interval.max_value)
        if new_min > new_max:
            return self.bottom()
        return UnsignedIntegerInterval(new_min, new_max, self.type_length)

    def add(self, other_interval):
        # 오버플로우를 고려하여 결과 범위 계산
        min_sum = self.min_value + other_interval.min_value
        max_sum = self.max_value + other_interval.max_value
        type_max = 2 ** self.type_length - 1

        min_sum = min(min_sum, type_max)
        max_sum = min(max_sum, type_max)

        return UnsignedIntegerInterval(min_sum, max_sum, self.type_length)

    def subtract(self, other_interval):
        """
        var_interval에서 other_interval을 제외한 집합 차집합을 의미.
        즉 var_interval ∖ other_interval을 interval 형태로 근사하여 반환.
        가능한 단순화:
        1. 교집합 없으면 var_interval 그대로 반환
        2. 교집합이 var_interval 전체를 덮으면 bottom 반환
        3. 교집합이 var_interval 일부를 덮을 경우 단순화.
        """
        # 교집합 계산
        inter_min = max(self.min_value, other_interval.min_value)
        inter_max = min(self.max_value, other_interval.max_value)

        if inter_min > inter_max:
            # 교집합 없음
            return self  # 그대로 반환

        # 여기서 inter_min ≤ inter_max 이므로 교집합 존재
        # 교집합 [inter_min, inter_max]

        if inter_min <= self.min_value and inter_max >= self.max_value:
            # 교집합이 var_interval 전체를 덮음
            return self.bottom()

        # 교집합이 부분 덮는 경우 처리
        # Case A: 교집합이 시작부분(하한 포함) 덮음
        if inter_min <= self.min_value:
            # [self.min_value, self.max_value]에서 [self.min_value, inter_max]를 제외하면
            # [inter_max+1, self.max_value] 반환 (정수 interval 가정)
            new_min = inter_max + 1
            if new_min > self.max_value:
                # 오버플로우시 bottom
                return self.bottom()
            return type(self)(new_min, self.max_value, self.type_length)

        # Case B: 교집합이 끝부분(상한 포함) 덮음
        if inter_max >= self.max_value:
            # [self.min_value, self.max_value]에서 [inter_min, self.max_value] 제외
            # [self.min_value, inter_min-1] 반환
            new_max = inter_min - 1
            if new_max < self.min_value:
                return self.bottom()
            return type(self)(self.min_value, new_max, self.type_length)

        # Case C: 교집합이 내부에 있어서 구멍이 생김 (예: var = [0,10], other=[5,5])
        # 단일 interval로 표현 곤란. 여기서는 단순히 교집합 상한 이후 부분만 남기거나,
        # 하한 이전 부분만 남기는 식으로 근사.
        # 여기서는 inter_min > self.min_value이고 inter_max < self.max_value 이므로
        # 내부에서 잘리는 경우.
        # 일단 lower 파트를 반환 (self.min_value ~ inter_min - 1)
        # 또는 upper 파트를 반환 (inter_max+1 ~ self.max_value)
        # 여기서는 하한쪽 부분을 남기기로 함.
        new_max = inter_min - 1
        if new_max < self.min_value:
            # 하한쪽 아무것도 남지 않으면 상한쪽을 시도
            new_min = inter_max + 1
            if new_min > self.max_value:
                # 양쪽 다 안되면 bottom
                return self.bottom()
            return type(self)(new_min, self.max_value, self.type_length)
        else:
            return type(self)(self.min_value, new_max, self.type_length)

    def multiply(self, other_interval):
        min_product = self.min_value * other_interval.min_value
        max_product = self.max_value * other_interval.max_value
        type_max = 2 ** self.type_length - 1

        min_product = min(min_product, type_max)
        max_product = min(max_product, type_max)

        return UnsignedIntegerInterval(min_product, max_product, self.type_length)

    def divide(self, other_interval):
        # 0으로 나누는 경우 처리
        if other_interval.min_value == 0 or other_interval.max_value == 0:
            return UnsignedIntegerInterval(None, None, self.type_length)

        min_quotient = self.min_value // max(other_interval.max_value, 1)
        max_quotient = self.max_value // max(other_interval.min_value, 1)

        return UnsignedIntegerInterval(min_quotient, max_quotient, self.type_length)

    def modulo(self, other_interval):
        # 0으로 나누는 경우 처리
        if other_interval.min_value == 0 or other_interval.max_value == 0:
            return UnsignedIntegerInterval(None, None, self.type_length)

        max_divisor = other_interval.max_value
        max_remainder = max_divisor - 1

        return UnsignedIntegerInterval(0, max_remainder, self.type_length)

    def left_shift(self, shift_interval):
        min_shifted = self.min_value << shift_interval.min_value
        max_shifted = self.max_value << shift_interval.max_value
        type_max = 2 ** self.type_length - 1

        min_shifted = min(min_shifted, type_max)
        max_shifted = min(max_shifted, type_max)

        return UnsignedIntegerInterval(min_shifted, max_shifted, self.type_length)

    def right_shift(self, shift_interval):
        min_shifted = self.min_value >> shift_interval.max_value
        max_shifted = self.max_value >> shift_interval.min_value

        return UnsignedIntegerInterval(min_shifted, max_shifted, self.type_length)

    def bitwise_and(self, other_interval):
        min_value = 0
        max_value = min(self.max_value, other_interval.max_value)
        return UnsignedIntegerInterval(min_value, max_value, self.type_length)

    def bitwise_or(self, other_interval):
        max_value = max(self.max_value, other_interval.max_value)
        return UnsignedIntegerInterval(0, max_value, self.type_length)

    def bitwise_xor(self, other_interval):
        max_value = max(self.max_value, other_interval.max_value)
        return UnsignedIntegerInterval(0, max_value, self.type_length)

    def logical_and(self, other_interval):
        # 불리언 결과는 0 또는 1
        return BoolInterval(0, 1)

    def logical_or(self, other_interval):
        # 불리언 결과는 0 또는 1
        return BoolInterval(0, 1)

    def logical_not(self):
        return BoolInterval(0, 1)

class BoolInterval(Interval):
    def __init__(self, min_value=None, max_value=None):
        super().__init__(min_value, max_value)

    def initialize_range(self):
        # 불리언은 0 또는 1만 가질 수 있음
        self.min_value = 0
        self.max_value = 1

    def calculate_interval(self, right_interval, operator):
        if operator == '&&':
            return self.logical_and(right_interval)
        elif operator == '||':
            return self.logical_or(right_interval)
        elif operator == '!':
            return self.logical_not()
        elif operator in ['==', '!=']:
            return BoolInterval(0, 1)
        else:
            raise ValueError(f"Unsupported operator for bool: {operator}")

    def intersect(self, other):
        # 교집합: 두 인터벌이 모두 참일 수 있는 경우는?
        # 참일 가능성을 계산
        # self와 other 각각 0 또는 1 범위
        # min_value가 1이면 True 가능, max_value가 0이면 False만 가능
        # 교집합은 가능한 부분의 교차를 의미

        if self.min_value is None or other.min_value is None:
            return self.bottom()

        new_min = max(self.min_value, other.min_value)
        new_max = min(self.max_value, other.max_value)
        if new_min > new_max:
            return self.bottom()
        return BoolInterval(new_min, new_max)

    def subtract(self, other):
        # 현재 subtract는 == 연산과 관련되었던 것으로 보이나
        # 불리언 범위에서 다른 범위를 빼는 연산 정의가 명확치 않음
        # 여기서는 단순히 self와 other 교집합 부분을 제외한다고 가정
        # 즉 self와 other가 공유하는 부분을 제거
        inter = self.intersect(other)
        if inter.min_value is None:
            # 교집합 없으면 self 그대로
            return self
        # 교집합 있으면 self에서 교집합 제거
        # 예: self = (0,1), other = (1,1) 이면 교집합 = (1,1)
        # self - 교집합 = (0,0)
        # 비트 단위로 단순 처리
        candidates = []
        # false만 남길 수 있으면
        if self.min_value == 0 and self.max_value == 1 and inter.min_value == 1:
            # True를 제거하면 False만 남음
            candidates.append(BoolInterval(0,0))
        if self.min_value == 0 and self.max_value == 1 and inter.min_value == 0:
            # False를 제거하면 True만 남음
            candidates.append(BoolInterval(1,1))
        if not candidates:
            return self.bottom()
        # 일단 candidates 중 하나 반환(여기선 첫번째)
        return candidates[0]

    def less_than(self, other):
        # Boolean에선 less_than 비교가 의미가 없으므로 그대로 반환
        return self

    def greater_than(self, other):
        # Boolean에선 greater_than 비교가 의미가 없으므로 그대로 반환
        return self

    def less_than_or_equal(self, other):
        return self  # Boolean에서 비교는 없음

    def greater_than_or_equal(self, other):
        return self  # Boolean에서 비교는 없음

    def widen(self, current_interval):
        # Boolean widen 결과는 항상 [0, 1]이므로 고정
        return BoolInterval(0, 1)

    def narrow(self, new_interval):
        if self.min_value == 0 and self.max_value == 1:
            return new_interval

        new_min = new_interval.min_value if self.min_value == 0 else self.min_value
        new_max = new_interval.max_value if self.max_value == 1 else min(self.max_value, new_interval.max_value)
        return BoolInterval(new_min, new_max)

    def top(self):
        return BoolInterval(0, 1)

    def bottom(self):
        return BoolInterval(None, None)

    def join(self, other_interval):
        if self.min_value is None:
            return other_interval
        if other_interval.min_value is None:
            return self

        new_min = min(self.min_value, other_interval.min_value)
        new_max = max(self.max_value, other_interval.max_value)
        return BoolInterval(new_min, new_max)

    def meet(self, other_interval):
        if self.min_value is None or other_interval.min_value is None:
            return self.bottom()

        new_min = max(self.min_value, other_interval.min_value)
        new_max = min(self.max_value, other_interval.max_value)
        if new_min > new_max:
            return self.bottom()
        return BoolInterval(new_min, new_max)

    def logical_and(self, other_interval):
        # AND 논리:
        # 둘 다 참(1,1)일 때만 항상 참이 됨
        # 한 쪽이라도 False 확정(0,0)이면 항상 False
        # 나머지는 불확실(0,1)
        if self.min_value == 1 and self.max_value == 1 and other_interval.min_value == 1 and other_interval.max_value == 1:
            # 둘 다 항상 true
            return BoolInterval(1,1)
        if (self.max_value == 0) or (other_interval.max_value == 0):
            # 한쪽이라도 항상 false
            return BoolInterval(0,0)
        # 그 외는 불확실
        return BoolInterval(0,1)

    def logical_or(self, other_interval):
        # OR 논리:
        # 한 쪽이라도 항상 True(1,1)이면 항상 True
        # 둘 다 항상 False(0,0)이면 항상 False
        if (self.min_value == 1 and self.max_value == 1) or (
                other_interval.min_value == 1 and other_interval.max_value == 1):
            return BoolInterval(1, 1)
        if self.max_value == 0 and other_interval.max_value == 0:
            return BoolInterval(0, 0)
        # 나머지는 불확실
        return BoolInterval(0, 1)

    def logical_not(self):
        # NOT:
        # True->False, False->True, 불확실->불확실
        if self.min_value == 1 and self.max_value == 1:
            return BoolInterval(0,0)  # 항상True -> 항상False
        if self.min_value == 0 and self.max_value == 0:
            return BoolInterval(1,1)  # 항상False -> 항상True
        if self.min_value is None and self.max_value is None:
            return self.bottom()
        # 불확실 -> 여전히 불확실
        return BoolInterval(0,1)

    def equality(self, other_interval):
        # 결과는 불리언 값 (0 또는 1)
        return BoolInterval(0, 1)

    def inequality(self, other_interval):
        # 결과는 불리언 값 (0 또는 1)
        return BoolInterval(0, 1)
