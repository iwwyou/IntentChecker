test_inputs = [

    # contract 선언
    {
        'code': 'contract TestContract { \n }',
        'startLine': 1,
        'endLine': 2
    },

    # 상태 변수 uint256 선언
    {
        'code': 'uint256 public a;',  # 상태 변수 uint256 추가
        'startLine': 2,
        'endLine': 2
    },

    # 상태 변수 total 선언
    {
        'code': 'uint256 public total;',  # 상태 변수 total 추가
        'startLine': 3,
        'endLine': 3
    },

    # 상태 변수 balance 선언
    {
        'code': 'uint256 public balance;',  # 상태 변수 balance 추가
        'startLine': 4,
        'endLine': 4
    },

    # 상태 변수 배열 선언
    {
        'code': 'uint256[5] public numbers;',  # 배열 변수 선언
        'startLine': 5,
        'endLine': 5
    },

    # 상태 변수 mapping 선언
    {
        'code': 'mapping(address => uint256) public balances;',  # mapping 선언
        'startLine': 6,
        'endLine': 6
    },

    # 빈 줄 추가
    {
        'code': '\n',  # 공백 라인
        'startLine': 7,
        'endLine': 7
    },

    # 함수 complexFunction 선언
    {
        'code': 'function complexFunction(uint256 _a) public returns (uint256) { \n }',
        'startLine': 8,
        'endLine': 9
    },

    # 함수 내용 추가 - 초기화 (i 초기화)
    {
        'code': 'uint256 i = 0;',
        'startLine': 9,
        'endLine': 9
    },

    # 함수 내용 추가 - a 할당
    {
        'code': 'a = _a;',
        'startLine': 10,
        'endLine': 10
    },

    # 함수 내용 추가 - balance 초기화
    {
        'code': 'balance = 100;',
        'startLine': 11,
        'endLine': 11
    },

    # 배열 elements를 1, 2, 3, 4, 5로 초기화
    {
        'code': 'uint256[5] memory amounts = [1, 2, 3, 4, 5];',
        'startLine': 12,
        'endLine': 12
    },

    # while문 선언
    {
        'code': 'while (i < amounts.length) { \n }',
        'startLine': 13,
        'endLine': 14
    },

    # while문 내용 - 배열 요소 접근
    {
        'code': 'uint256 currentAmount = amounts[i];',
        'startLine': 14,
        'endLine': 14
    },

    # while문 내용 - balance 증가
    {
        'code': 'balance += currentAmount;',
        'startLine': 15,
        'endLine': 15
    },

    # if문 선언
    {
        'code': 'if (i == 10) { \n }',
        'startLine': 16,
        'endLine': 17
    },

    # if문 내용 - return a;
    {
        'code': 'return a;',
        'startLine': 17,
        'endLine': 17
    },

    # else if문 선언
    {
        'code': 'else if (i < 5) { \n }',
        'startLine': 18,
        'endLine': 19
    },

    # else if문 내용 - a 증가
    {
        'code': 'a += 1;',
        'startLine': 19,
        'endLine': 19
    },

    # else if문 내용 - i 증가
    {
        'code': 'i += 1;',
        'startLine': 20,
        'endLine': 20
    },

    # else if문 내용 - continue
    {
        'code': 'continue;',
        'startLine': 21,
        'endLine': 21
    },

    # else if문 추가
    {
        'code': 'else if (i >= 15) { \n }',
        'startLine': 22,
        'endLine': 23
    },

    # else if문 내용 - break
    {
        'code': 'break;',
        'startLine': 23,
        'endLine': 23
    },

    # else문 선언
    {
        'code': 'else { \n }',
        'startLine': 24,
        'endLine': 25
    },

    # else문 내용 - balance 감소
    {
        'code': 'balance -= 2;',
        'startLine': 25,
        'endLine': 25
    },

    # else문 내용 - a 계산
    {
        'code': 'a = a * 2 + 3;',
        'startLine': 26,
        'endLine': 26
    },

    # else문 내용 - i 증가
    {
        'code': 'i += 1;',
        'startLine': 27,
        'endLine': 27
    },

    # while문 종료 후 내용 - total 계산
    {
        'code': 'total = a * i;',
        'startLine': 28,
        'endLine': 28
    },

    # 잔액 추가
    {
        'code': 'balance += total;',
        'startLine': 29,
        'endLine': 29
    },

    # balances에 최종 a 값을 할당
    {
        'code': 'balances[msg.sender] = balance;',
        'startLine': 30,
        'endLine': 30
    },

    # 함수 종료 - 최종 반환
    {
        'code': 'return balance;',
        'startLine': 31,
        'endLine': 31
    }
]