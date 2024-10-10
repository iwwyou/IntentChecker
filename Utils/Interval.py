class Interval:
    def __init__(self, min_value=None, max_value=None):
        self.min_value = min_value
        self.max_value = max_value

    def encompass(self, intended_interval):
        """
        실제 interval이 의도된 interval에 포함되는지 여부를 판단하는 연산자.
        """
        return self.min_value >= intended_interval.min_value and self.max_value <= intended_interval.max_value

class IntegerInterval(Interval):
    def __init__(self, min_value, max_value, type_length):
        super().__init__(min_value, max_value)
        self.type_length = type_length

    @staticmethod
    def initialize_range(type_name):
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

        return min_value, max_value

    @staticmethod
    def calculate_interval(left_interval, right_interval, operator):
        # 연산자에 따라 interval 계산 수행
        if operator == '+':
            return IntegerInterval.add(left_interval, right_interval)
        elif operator == '-':
            return IntegerInterval.subtract(left_interval, right_interval)
        elif operator == '*':
            return IntegerInterval.multiply(left_interval, right_interval)
        elif operator == '/':
            return IntegerInterval.divide(left_interval, right_interval)
        elif operator == '%':
            return IntegerInterval.modulo(left_interval, right_interval)
        elif operator == '<<':
            return IntegerInterval.left_shift(left_interval, right_interval)
        elif operator == '>>':
            return IntegerInterval.right_shift(left_interval, right_interval)
        elif operator == '&':
            return IntegerInterval.bitwise_and(left_interval, right_interval)
        elif operator == '|':
            return IntegerInterval.bitwise_or(left_interval, right_interval)
        elif operator == '^':
            return IntegerInterval.bitwise_xor(left_interval, right_interval)
        elif operator == '&&':
            return IntegerInterval.logical_and(left_interval, right_interval)
        elif operator == '||':
            return IntegerInterval.logical_or(left_interval, right_interval)
        else:
            raise ValueError(f"Unsupported operator: {operator}")



    @staticmethod
    def top(type_length):
        if type_length == 256:  # 예를 들어, int256의 경우
            min_value = -2 ** (type_length - 1)
            max_value = 2 ** (type_length - 1) - 1
        else:
            # 다른 타입에 대한 처리...
            min_value = -2 ** (type_length - 1)
            max_value = 2 ** (type_length - 1) - 1

        return IntegerInterval(min_value, max_value, type_length)

    @staticmethod
    def bottom():
        return IntegerInterval(None, None, None)

    @staticmethod
    def join(interval1, interval2):
        if interval1.type_length != interval2.type_length:
            raise ValueError("Cannot join intervals of different type lengths")

        if interval1.min_value is None:
            return interval2
        if interval2.min_value is None:
            return interval1

        new_min = min(interval1.min_value, interval2.min_value)
        new_max = max(interval1.max_value, interval2.max_value)
        return IntegerInterval(new_min, new_max, interval1.type_length)

    @staticmethod
    def meet(interval1, interval2):
        if interval1.type_length != interval2.type_length:
            raise ValueError("Cannot meet intervals of different type lengths")

        if interval1.min_value is None:
            return interval2
        if interval2.min_value is None:
            return interval1

        new_min = max(interval1.min_value, interval2.min_value)
        new_max = min(interval1.max_value, interval2.max_value)
        if new_min > new_max:
            return IntegerInterval.bottom()
        return IntegerInterval(new_min, new_max, interval1.type_length)

    @staticmethod
    def negate(interval):
        if interval.min_value is not None and interval.max_value is not None:
            return IntegerInterval(-interval.max_value, -interval.min_value, self.type_length)
        else:
            return IntegerInterval(None, None, interval.type_length)

    @staticmethod
    def add(interval1, interval2): # aexp
        if interval1.type_length != interval2.type_length:
            raise ValueError("Cannot add intervals of different type lengths")

        if interval1.min_value is None or interval2.min_value is None:
            min_sum = None
        else:
            min_sum = interval1.min_value + interval2.min_value

        if interval1.max_value is None or interval2.max_value is None:
            max_sum = None
        else:
            max_sum = interval1.max_value + interval2.max_value

        return IntegerInterval(min_sum, max_sum, interval1.type_length)

    @staticmethod
    def prefix_increment(interval): # aexp
        if interval.min_value is not None and interval.max_value is not None:
            return IntegerInterval(interval.min_value + 1, interval.max_value + 1, interval.type_length)
        return interval

    @staticmethod
    def prefix_decrement(interval): # aexp
        if interval.min_value is not None and interval.max_value is not None:
            return IntegerInterval(interval.min_value - 1, interval.max_value - 1, interval.type_length)
        return interval

    @staticmethod
    def postfix_increment(interval): # aexp
        # 후위 증감 연산자 처리 (값을 반환한 후 증가)
        result = IntegerInterval(interval.min_value, interval.max_value, interval.type_length)
        if interval.min_value is not None and interval.max_value is not None:
            interval.min_value += 1
            interval.max_value += 1
        return result

    @staticmethod
    def postfix_decrement(interval): # aexp
        # 후위 증감 연산자 처리 (값을 반환한 후 감소)
        result = IntegerInterval(interval.min_value, interval.max_value, interval.type_length)
        if interval.min_value is not None and interval.max_value is not None:
            interval.min_value -= 1
            interval.max_value -= 1
        return result

    @staticmethod
    def subtract(interval1, interval2): # aexp
        if interval1.type_length != interval2.type_length:
            raise ValueError("Cannot add intervals of different type lengths")

        if interval1.min_value is None or interval2.max_value is None:
            min_diff = None
        else:
            min_diff = interval1.min_value - interval2.max_value

        if interval1.max_value is None or interval2.min_value is None:
            max_diff = None
        else:
            max_diff = interval1.max_value - interval2.min_value

        return IntegerInterval(min_diff, max_diff, interval1.type_length)

    @staticmethod
    def multiply(interval1, interval2): # aexp
        if interval1.type_length != interval2.type_length:
            raise ValueError("Cannot add intervals of different type lengths")

        possible_results = [
            interval1.min_value * interval2.min_value,
            interval1.min_value * interval2.max_value,
            interval1.max_value * interval2.min_value,
            interval1.max_value * interval2.max_value,
        ]

        # Remove None values from possible results
        filtered_results = [x for x in possible_results if x is not None]

        if not filtered_results:
            return IntegerInterval(None, None, interval1.type_length)

        min_product = min(filtered_results)
        max_product = max(filtered_results)

        return IntegerInterval(min_product, max_product, interval1.type_length)

    @staticmethod
    def divide(interval1, interval2): # aexp
        def safe_divide(numerator, denominator):
            if numerator is None or denominator is None or denominator == 0:
                return None
            return numerator // denominator

        if interval1.type_length != interval2.type_length:
            raise ValueError("Cannot add intervals of different type lengths")

        if 0 in [interval2.min_value, interval2.max_value]:
            return IntegerInterval(None, None, interval1.type_length)

        possible_results = [
            safe_divide(interval1.min_value, interval2.min_value),
            safe_divide(interval1.min_value, interval2.max_value),
            safe_divide(interval1.max_value, interval2.min_value),
            safe_divide(interval1.max_value, interval2.max_value),
        ]

        # Remove None values from possible results
        filtered_results = [x for x in possible_results if x is not None]

        if not filtered_results:
            return IntegerInterval(None, None, interval1.type_length)

        min_quotient = min(filtered_results)
        max_quotient = max(filtered_results)

        return IntegerInterval(min_quotient, max_quotient, interval1.type_length)

    @staticmethod
    def exponentiation(base_interval, exponent_interval): # aexp
        if base_interval.min_value is None or exponent_interval.min_value is None:
            return IntegerInterval(None, None, base_interval.type_length)

        # 간단한 경우에 대한 예측
        min_result = min(base_interval.min_value ** exponent_interval.min_value,
                         base_interval.min_value ** exponent_interval.max_value,
                         base_interval.max_value ** exponent_interval.min_value,
                         base_interval.max_value ** exponent_interval.max_value)

        max_result = max(base_interval.min_value ** exponent_interval.min_value,
                         base_interval.min_value ** exponent_interval.max_value,
                         base_interval.max_value ** exponent_interval.min_value,
                         base_interval.max_value ** exponent_interval.max_value)

        return IntegerInterval(min_result, max_result, base_interval.type_length)

    @staticmethod
    def modulo(dividend_interval, divisor_interval): # aexp
        # 나누는 수가 0이 될 수 있는 경우, 결과를 예측할 수 없으므로 None 반환
        if divisor_interval.min_value is None or divisor_interval.max_value is None or 0 in divisor_interval:
            return IntegerInterval(None, None, dividend_interval.type_length)

        # 나머지의 가능한 최대 범위는 0부터 (나누는 수의 최대값 - 1)까지
        max_divisor = max(abs(divisor_interval.min_value), abs(divisor_interval.max_value))
        return IntegerInterval(0, max_divisor - 1, dividend_interval.type_length)

    @staticmethod
    def bitwise_and(interval1, interval2):
        # 두 값의 가능한 최소 및 최대값을 고려하여 결과의 범위를 추정
        min_value = 0  # AND 연산의 결과는 항상 0 이상
        max_value = min(interval1.max_value, interval2.max_value)  # 최대값은 두 입력값 중 작은 값으로 제한됨

        return IntegerInterval(min_value, max_value, interval1.type_length)

    @staticmethod
    def bitwise_or(interval1, interval2):
        # 두 값의 가능한 최소 및 최대값을 고려하여 결과의 범위를 추정
        min_value = max(interval1.min_value, interval2.min_value)  # 최소값은 두 입력값 중 큰 값으로 제한됨
        max_value = max(interval1.max_value, interval2.max_value)  # 최대값은 두 입력값 중 큰 값

        return IntegerInterval(min_value, max_value, interval1.type_length)

    @staticmethod
    def bitwise_xor(interval1, interval2):
        # 두 값의 가능한 최소 및 최대값을 고려하여 결과의 범위를 추정
        min_value = 0  # XOR 연산의 결과는 0 이상
        max_value = max(interval1.max_value, interval2.max_value)  # 최대값은 두 입력값 중 큰 값

        return IntegerInterval(min_value, max_value, interval1.type_length)

    @staticmethod
    def bitwise_not(interval):
        # 비트 반전 연산 처리 (보수 연산)
        if interval.min_value is not None and interval.max_value is not None:
            type_max = 2 ** interval.type_length - 1
            return IntegerInterval(~interval.max_value & type_max, ~interval.min_value & type_max, interval.type_length)
        else:
            return IntegerInterval(None, None, interval.type_length)

    @staticmethod
    def shift(value_interval, shift_interval, operator):
        if operator == '<<':
            return IntegerInterval.left_shift(value_interval, shift_interval)
        elif operator == '>>' or operator == '>>>':
            return IntegerInterval.right_shift(value_interval, shift_interval)
        else:
            raise ValueError(f"Unsupported shift operator: {operator}")

    @staticmethod
    def left_shift(value_interval, shift_interval):
        # 시프트 양이 음수이거나 정의되지 않았다면, 결과를 예측할 수 없음
        if shift_interval.min_value is None or shift_interval.min_value < 0:
            return IntegerInterval(None, None, value_interval.type_length)

        # 가능한 최소 및 최대 시프트 양을 고려하여 결과 범위 계산
        min_shifted = value_interval.min_value << shift_interval.min_value
        max_shifted = value_interval.max_value << shift_interval.max_value

        # 오버플로우를 고려하여 타입 길이에 맞는 범위로 조정
        type_max = 2 ** (value_interval.type_length) - 1
        min_shifted = min(max(min_shifted, -2 ** (value_interval.type_length - 1)),
                          2 ** (value_interval.type_length - 1) - 1)
        max_shifted = min(max(max_shifted, -2 ** (value_interval.type_length - 1)),
                          2 ** (value_interval.type_length - 1) - 1)

        return IntegerInterval(min_shifted, max_shifted, value_interval.type_length)

    @staticmethod
    def right_shift(value_interval, shift_interval):
        # 시프트 양이 음수이거나 정의되지 않았다면, 결과를 예측할 수 없음
        if shift_interval.min_value is None or shift_interval.min_value < 0:
            return IntegerInterval(None, None, value_interval.type_length)

        # 가능한 최소 및 최대 시프트 양을 고려하여 결과 범위 계산
        min_shifted = value_interval.min_value >> shift_interval.max_value
        max_shifted = value_interval.max_value >> shift_interval.min_value

        return IntegerInterval(min_shifted, max_shifted, value_interval.type_length)

    @staticmethod
    def logical_and(interval1, interval2):
        return IntegerInterval(0, 1, None)

    @staticmethod
    def logical_or(interval1, interval2):
        return IntegerInterval(0, 1, None)

    @staticmethod
    def logical_not(interval):
        # 불리언 연산의 결과는 0 또는 1
        return IntegerInterval(0, 1, None)

    @staticmethod
    def add_assign(interval1, interval2):
        # 'x += y' 연산을 처리
        return IntegerInterval.add(interval1, interval2)

    @staticmethod
    def subtract_assign(interval1, interval2):
        # 'x -= y' 연산을 처리
        return IntegerInterval.subtract(interval1, interval2)

    @staticmethod
    def multiply_assign(interval1, interval2):
        # 'x *= y' 연산을 처리
        return IntegerInterval.multiply(interval1, interval2)

    @staticmethod
    def divide_assign(interval1, interval2):
        # 'x /= y' 연산을 처리
        return IntegerInterval.divide(interval1, interval2)

    @staticmethod
    def modulo_assign(interval1, interval2):
        # 'x %= y' 연산을 처리
        return IntegerInterval.modulo(interval1, interval2)

    @staticmethod
    def bitwise_and_assign(interval1, interval2):
        # 'x &= y' 연산을 처리
        return IntegerInterval.bitwise_and(interval1, interval2)

    @staticmethod
    def bitwise_or_assign(interval1, interval2):
        # 'x |= y' 연산을 처리
        return IntegerInterval.bitwise_or(interval1, interval2)

    @staticmethod
    def bitwise_xor_assign(interval1, interval2):
        # 'x ^= y' 연산을 처리
        return IntegerInterval.bitwise_xor(interval1, interval2)

    @staticmethod
    def shift_left_assign(interval1, shift_interval):
        # 'x <<= y' 연산을 처리
        return IntegerInterval.left_shift(interval1, shift_interval)

    @staticmethod
    def shift_right_assign(interval1, shift_interval):
        # 'x >>= y' 연산을 처리
        return IntegerInterval.right_shift(interval1, shift_interval)

# UnsignedIntegerInterval 클래스
class UnsignedIntegerInterval(Interval):
    def __init__(self, min_value, max_value, type_length):
        super().__init__(min_value, max_value)
        self.type_length = type_length

    # Unsigned-specific methods
    # ...
    @staticmethod
    def shift(value_interval, shift_interval, operator):
        if operator == '<<':
            return UnsignedIntegerInterval.left_shift(value_interval, shift_interval)
        elif operator == '>>' or operator == '>>>':
            return UnsignedIntegerInterval.right_shift(value_interval, shift_interval)
        else:
            raise ValueError(f"Unsupported shift operator: {operator}")

    @staticmethod
    def left_shift(value_interval, shift_interval):
        if shift_interval.min_value is None or shift_interval.min_value < 0:
            return UnsignedIntegerInterval(None, None, value_interval.type_length)

        min_shifted = value_interval.min_value << shift_interval.min_value
        max_shifted = value_interval.max_value << shift_interval.max_value

        # 오버플로우를 고려하여 타입 길이에 맞는 범위로 조정
        type_max = 2 ** value_interval.type_length - 1
        min_shifted = min(max(min_shifted, 0), type_max)
        max_shifted = min(max(max_shifted, 0), type_max)

        return UnsignedIntegerInterval(min_shifted, max_shifted, value_interval.type_length)

    @staticmethod
    def right_shift(value_interval, shift_interval):
        if shift_interval.min_value is None or shift_interval.min_value < 0:
            return UnsignedIntegerInterval(None, None, value_interval.type_length)

        min_shifted = value_interval.min_value >> shift_interval.max_value
        max_shifted = value_interval.max_value >> shift_interval.min_value

        return UnsignedIntegerInterval(min_shifted, max_shifted, value_interval.type_length)

# BooleanInterval 클래스
class BooleanInterval(Interval):
    def __init__(self, is_true=False, is_false=False):
        super().__init__(0 if is_false else None, 1 if is_true else None)
        self.is_true = is_true
        self.is_false = is_false

    def logical_and(self, other):
        # 논리 AND 연산 수행
        is_true = self.is_true and other.is_true
        is_false = self.is_false or other.is_false
        return BooleanInterval(is_true, is_false)

    def logical_or(self, other):
        # 논리 OR 연산 수행
        is_true = self.is_true or other.is_true
        is_false = self.is_false and other.is_false
        return BooleanInterval(is_true, is_false)

    def logical_not(self):
        return BooleanInterval(is_true=self.is_false, is_false=self.is_true)
