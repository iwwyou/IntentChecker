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
        return IntegerInterval(max(self.min_value, other.min_value), min(self.max_value, other.max_value))

    def subtract(self, other):
        # != 연산을 처리하기 위해 두 인터벌의 교차를 뺌 (즉, 교집합을 제외한 나머지를 의미)
        return IntegerInterval(float('-inf'), float('inf')) if self == other else self

    def less_than(self, other):
        return IntegerInterval(self.min_value, min(self.max_value, other.min_value - 1))

    def greater_than(self, other):
        return IntegerInterval(max(self.min_value, other.max_value + 1), self.max_value)

    def less_than_or_equal(self, other):
        return IntegerInterval(self.min_value, min(self.max_value, other.max_value))

    def greater_than_or_equal(self, other):
        return IntegerInterval(max(self.min_value, other.min_value), self.max_value)

    def widen(self, current_interval):
        new_min = float('-inf') if self.min_value > current_interval.min_value else self.min_value
        new_max = float('inf') if self.max_value < current_interval.max_value else self.max_value
        return IntegerInterval(new_min, new_max)

    def narrow(self, new_interval):
        if self.min_value == float('-inf') or self.max_value == float('inf'):
            return new_interval

        new_min = new_interval.min_value if self.min_value == float('-inf') else self.min_value
        new_max = new_interval.max_value if self.max_value == float('inf') else min(self.max_value,
                                                                                    new_interval.max_value)
        return IntegerInterval(new_min, new_max)

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

    def divide(self, other_interval):  # aexp
        def safe_divide(numerator, denominator):
            if numerator is None or denominator is None or denominator == 0:
                return None
            return numerator // denominator

        if self.type_length != other_interval.type_length:
            raise ValueError("Cannot divide intervals of different type lengths")

        if 0 in [other_interval.min_value, other_interval.max_value]:
            return IntegerInterval(None, None, self.type_length)

        possible_results = [
            safe_divide(self.min_value, other_interval.min_value),
            safe_divide(self.min_value, other_interval.max_value),
            safe_divide(self.max_value, other_interval.min_value),
            safe_divide(self.max_value, other_interval.max_value),
        ]

        # Remove None values from possible results
        filtered_results = [x for x in possible_results if x is not None]

        if not filtered_results:
            return IntegerInterval(None, None, self.type_length)

        min_quotient = min(filtered_results)
        max_quotient = max(filtered_results)

        return IntegerInterval(min_quotient, max_quotient, self.type_length)

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
        return UnsignedIntegerInterval(max(self.min_value, other.min_value), min(self.max_value, other.max_value))

    def subtract(self, other):
        # == 연산을 제외한 값들의 interval
        return UnsignedIntegerInterval(float('-inf'), float('inf')) if self == other else self

    def less_than(self, other):
        return UnsignedIntegerInterval(self.min_value, min(self.max_value, other.min_value - 1))

    def greater_than(self, other):
        return UnsignedIntegerInterval(max(self.min_value, other.max_value + 1), self.max_value)

    def less_than_or_equal(self, other):
        return UnsignedIntegerInterval(self.min_value, min(self.max_value, other.max_value))

    def greater_than_or_equal(self, other):
        return UnsignedIntegerInterval(max(self.min_value, other.min_value), self.max_value)

    def widen(self, current_interval):
        new_min = 0 if self.min_value > current_interval.min_value else self.min_value
        new_max = float('inf') if self.max_value < current_interval.max_value else self.max_value
        return UnsignedIntegerInterval(new_min, new_max)

    def narrow(self, new_interval):
        if self.max_value == float('inf'):
            return new_interval

        new_min = new_interval.min_value if self.min_value == 0 else self.min_value
        new_max = new_interval.max_value if self.max_value == float('inf') else min(self.max_value,
                                                                                    new_interval.max_value)
        return UnsignedIntegerInterval(new_min, new_max)

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
        # 결과가 음수가 되지 않도록 조정
        min_diff = max(self.min_value - other_interval.max_value, 0)
        max_diff = max(self.max_value - other_interval.min_value, 0)

        return UnsignedIntegerInterval(min_diff, max_diff, self.type_length)

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
        return BoolInterval(
            is_true=self.is_true and other.is_true,
            is_false=self.is_false and other.is_false
        )

    def subtract(self, other):
        # != 연산을 처리하기 위해 부정 연산을 수행
        return BoolInterval(not self.is_true, not self.is_false) if self == other else self

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
        # 최소값이 0이면 결과는 0이 될 수 있음
        min_value = 0 if self.min_value == 0 or other_interval.min_value == 0 else 1
        # 최대값이 1이면 결과는 1이 될 수 있음
        max_value = 1 if self.max_value == 1 and other_interval.max_value == 1 else 0
        return BoolInterval(min_value, max_value)

    def logical_or(self, other_interval):
        # 최소값이 1이면 결과는 1이 될 수 있음
        min_value = 1 if self.min_value == 1 or other_interval.min_value == 1 else 0
        # 최대값이 1이면 결과는 1이 될 수 있음
        max_value = 1 if self.max_value == 1 or other_interval.max_value == 1 else 0
        return BoolInterval(min_value, max_value)

    def logical_not(self):
        if self.min_value is None or self.max_value is None:
            return BoolInterval(None, None)

        # NOT 연산 결과 계산
        min_value = 0 if self.max_value == 1 else 1
        max_value = 1 if self.min_value == 0 else 0
        return BoolInterval(min_value, max_value)

    def equality(self, other_interval):
        # 결과는 불리언 값 (0 또는 1)
        return BoolInterval(0, 1)

    def inequality(self, other_interval):
        # 결과는 불리언 값 (0 또는 1)
        return BoolInterval(0, 1)
