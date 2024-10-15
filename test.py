import json
from Analyzer.EnhancedSolidityVisitor import EnhancedSolidityVisitor
from Analyzer.ContractAnalyzer import ContractAnalyzer
from antlr4 import *
from Parser.SolidityLexer import SolidityLexer
from Parser.SolidityParser import SolidityParser

contract_analyzer = ContractAnalyzer()

def map_context_type(context_type):
    context_mapping = {
        'contract': 'interactiveSourceUnit',
        'library': 'interactiveSourceUnit',
        'interface': 'interactiveSourceUnit',
        'enum': 'interactiveSourceUnit',
        'struct': 'interactiveSourceUnit',
        'function': 'interactiveSourceUnit',
        'constructor': 'interactiveSourceUnit',
        'fallback': 'interactiveSourceUnit',
        'receive': 'interactiveSourceUnit',
        'event': 'interactiveSourceUnit',
        'error': 'interactiveSourceUnit',
        'modifier': 'interactiveSourceUnit',
        'stateVariableDeclaration': 'interactiveSourceUnit',
        'enumMember': 'interactiveEnumUnit',
        'structMember': 'interactiveStructUnit',
        'simpleStatement': 'interactiveBlockUnit',
        'if': 'interactiveBlockUnit',
        'for': 'interactiveBlockUnit',
        'while': 'interactiveBlockUnit',
        'do': 'interactiveBlockUnit',
        'try': 'interactiveBlockUnit',
        'return': 'interactiveBlockUnit',
        'break': 'interactiveBlockUnit',
        'continue': 'interactiveBlockUnit',
        'emit': 'interactiveBlockUnit',
        'doWhileWhile': 'interactiveDoWhileUnit',
        'catch': 'interactiveCatchClauseUnit',
        'else_if': 'interactiveIfElseUnit',
        'else': 'interactiveIfElseUnit'
    }

    try:
        return context_mapping[context_type]
    except KeyError:
        print(f"Warning: No mapping found for context_type '{context_type}'. Returning None.")
        return None

def generate_parse_tree(input_stream, context_type):
    input_stream = InputStream(input_stream)
    lexer = SolidityLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = SolidityParser(token_stream)

    context_rule = map_context_type(context_type)

    if context_rule == 'interactiveStructUnit':
        tree = parser.interactiveStructUnit()
    elif context_rule == 'interactiveEnumUnit':
        tree = parser.interactiveEnumUnit()
    elif context_rule == 'interactiveBlockUnit':
        tree = parser.interactiveBlockUnit()
    elif context_rule == 'interactiveDoWhileUnit':
        tree = parser.interactiveDoWhileUnit()
    elif context_rule == 'interactiveIfElseUnit':
        tree = parser.interactiveIfElseUnit()
    elif context_rule == 'interactiveCatchClauseUnit':
        tree = parser.interactiveCatchClauseUnit()
    else:
        tree = parser.interactiveSourceUnit()

    return tree

def simulate_input(test_inputs):
    for input_data in test_inputs:
        code = input_data['code']
        start_line = input_data['startLine']
        end_line = input_data['endLine']

        contract_analyzer.update_code(start_line, end_line, code)

        if code == "\n" :
            continue

        # Parse the received code based on context_type
        tree = generate_parse_tree(code, contract_analyzer.get_current_context_type())

        visitor = EnhancedSolidityVisitor(contract_analyzer)
        visitor.visit(tree)

        # Get and print the analysis result
        result = contract_analyzer.get_analysis_result()
        print(json.dumps(result, indent=4))

# Test inputs (replicating multiple steps)
test_inputs = [

    # contract 선언
    {
        'code': 'contract TestContract { \n }',
        'startLine': 1,
        'endLine': 2
    },

    # 상태 변수 uint256 선언
    {
        'code': 'uint256 public a = 1 + 2;',  # 상태 변수 uint256 추가
        'startLine': 2,
        'endLine': 2
    },

    # 상태 변수 배열 선언
    {
        'code': 'uint256[] public numbers;',  # 배열 변수 선언
        'startLine': 3,
        'endLine': 3
    },

    # 상태 변수 mapping 선언
    {
        'code': 'mapping(address => uint256) public balances;',  # mapping 선언
        'startLine': 4,
        'endLine': 4
    },

    # 빈 줄 추가
    {
        'code': '\n',  # 공백 라인
        'startLine': 5,
        'endLine': 5
    },

    # 함수 setA 선언
    {
        'code': 'function setA(uint256 _a) public { \n }',  # 함수 선언
        'startLine': 6,
        'endLine': 7
    },

    # 함수 내용 추가 - 상태 변수 할당
    {
        'code': 'a = _a;',  # a에 값 할당
        'startLine': 7,
        'endLine': 7
    },

    # if문 선언
    {
        'code': 'if(_a > 10) { \n }',  # if문 선언
        'startLine': 8,
        'endLine': 9
    },

    # if 블록 안 내용 추가
    {
        'code': 'a = 10;',  # if 블록 내 내용
        'startLine': 9,
        'endLine': 9
    },

    # else if문 선언
    {
        'code': 'else if (_a == 10) { \n }',  # else if 선언
        'startLine': 11,
        'endLine': 12
    },

    # else if 블록 안 내용 추가
    {
        'code': 'a = 5;',  # else if 블록 내 내용
        'startLine': 12,
        'endLine': 12
    },

    # else문 선언
    {
        'code': 'else { \n }',  # else 선언
        'startLine': 14,
        'endLine': 15
    },

    # else 블록 안 내용 추가
    {
        'code': 'a = 1;',  # else 블록 내 내용
        'startLine': 15,
        'endLine': 15
    },

    # 배열에 값 추가
    {
        'code': 'numbers.push(_a);',  # 배열에 값 추가
        'startLine': 17,
        'endLine': 17
    },

    # 조건에 따른 a 값 balances에 할당
    {
        'code': 'balances[msg.sender] = a;',  # balances에 a 값을 할당
        'startLine': 18,
        'endLine': 18
    }
]


# Simulate input as if coming from VSCode with block structure assumptions
simulate_input(test_inputs)