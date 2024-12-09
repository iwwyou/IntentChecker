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

test_inputs = [
    # Contract 선언
    {
        'code': 'contract USDs { \n }',
        'startLine': 1,
        'endLine': 2
    },

    # 상태 변수 mapping 선언 - _creditBalances
    {
        'code': 'mapping(address => uint256) private _creditBalances;',
        'startLine': 2,
        'endLine': 2
    },

    # 상태 변수 mapping 선언 - nonRebasingCreditsPerToken
    {
        'code': 'mapping(address => uint256) private nonRebasingCreditsPerToken;',
        'startLine': 3,
        'endLine': 3
    },

    # 상태 변수 uint256 선언 - rebasingCreditsPerToken
    {
        'code': 'uint256 private rebasingCreditsPerToken;',
        'startLine': 4,
        'endLine': 4
    },

    # 상태 변수 uint256 선언 - nonRebasingSupply
    {
        'code': 'uint256 private nonRebasingSupply;',
        'startLine': 5,
        'endLine': 5
    },


    {
        'code': 'enum RebaseOptions { \n };',
        'startLine': 6,
        'endLine': 7
    },


    {
        'code': 'NotSet, Rebased',
        'startLine': 7,
        'endLine': 7
    },

    {
        'code': 'mapping(address => RebaseOptions) private _rebaseState;',
        'startLine': 9,
        'endLine': 9
    },

    # _isContract 함수 선언
    {
        'code': 'function _isContract(address _account) private view returns (bool) { \n }',
        'startLine': 10,
        'endLine': 11
    },

    # _isContract 함수 내용 - size 체크
    {
        'code': 'uint32 size = _account.code.length;',
        'startLine': 11,
        'endLine': 11
    },

    # _isContract 함수 내용 - if문 작성
    {
        'code': 'if (size > 0) { \n }',
        'startLine': 12,
        'endLine': 13
    },

    # _isContract 함수 내용 - return true
    {
        'code': 'return true;',
        'startLine': 13,
        'endLine': 13
    },

    # _isContract 함수 내용 - return false
    {
        'code': 'return false;',
        'startLine': 15,
        'endLine': 15
    },

    {
        'code': '\n',
        'startLine': 17,
        'endLine': 17
    },

    # _balanceOf 함수 선언
    {
        'code': 'function _balanceOf(address _account) private view returns (uint256) { \n }',
        'startLine': 18,
        'endLine': 19
    },

    # _balanceOf 함수 내용 - credits 변수 선언 및 초기화
    {
        'code': 'uint256 credits = _creditBalances[_account];',
        'startLine': 19,
        'endLine': 19
    },

    # _balanceOf 함수 내용 - if문 체크 - credits > 0
    {
        'code': 'if (credits > 0) { \n }',
        'startLine': 20,
        'endLine': 21
    },

    # _balanceOf 함수 내용 - if문 체크 - nonRebasingCreditsPerToken
    {
        'code': 'if (nonRebasingCreditsPerToken[_account] > 0) { \n }',
        'startLine': 21,
        'endLine': 22
    },

    # _balanceOf 함수 내용 - return credits
    {
        'code': 'return credits;',
        'startLine': 22,
        'endLine': 22
    },

    # _balanceOf 함수 내용 - return credits / rebasingCreditsPerToken
    {
        'code': 'return credits / rebasingCreditsPerToken;',
        'startLine': 24,
        'endLine': 24
    },

    # _balanceOf 함수 내용 - return 0
    {
        'code': 'return 0;',
        'startLine': 26,
        'endLine': 26
    },

    {
        'code': '\n',
        'startLine': 28,
        'endLine': 28
    },

    # _ensureRebasingMigration 함수 선언
    {
        'code': 'function _ensureRebasingMigration(address _account) internal { \n }',
        'startLine': 29,
        'endLine': 30
    },

    # _ensureRebasingMigration 함수 내용 - if문 체크 - nonRebasingCreditsPerToken[_account] == 0
    {
        'code': 'if (nonRebasingCreditsPerToken[_account] == 0) { \n }',
        'startLine': 30,
        'endLine': 31
    },

    # _ensureRebasingMigration 함수 내용 - nonRebasingCreditsPerToken[_account] = 1;
    {
        'code': 'nonRebasingCreditsPerToken[_account] = 1;',
        'startLine': 31,
        'endLine': 31
    },

    # _ensureRebasingMigration 함수 내용 - if문 체크 - _creditBalances[_account] != 0
    {
        'code': 'if (_creditBalances[_account] != 0) { \n }',
        'startLine': 32,
        'endLine': 33
    },

    # _ensureRebasingMigration 함수 내용 - uint256 bal = _balanceOf(_account);
    {
        'code': 'uint256 bal = _balanceOf(_account);',
        'startLine': 33,
        'endLine': 33
    },

    # _ensureRebasingMigration 함수 내용 - nonRebasingSupply 증가
    {
        'code': 'nonRebasingSupply = nonRebasingSupply + bal;',
        'startLine': 34,
        'endLine': 34
    },

    # _ensureRebasingMigration 함수 내용 - _creditBalances[_account] 업데이트
    {
        'code': '_creditBalances[_account] = bal;',
        'startLine': 35,
        'endLine': 35
    },

    {
        'code': '\n',
        'startLine': 39,
        'endLine': 39
    },

    # _isNonRebasingAccount 함수 선언
    {
        'code': 'function _isNonRebasingAccount(address _account) internal view returns (bool) { \n }',
        'startLine': 40,
        'endLine': 41
    },

    # _isNonRebasingAccount 함수 내용 - isContract 체크
    {
        'code': 'bool isContract = _isContract(_account);',
        'startLine': 41,
        'endLine': 41
    },

    # _isNonRebasingAccount 함수 내용 - if문 작성
    {
        'code': 'if (isContract && _rebaseState[_account] == RebaseOptions.NotSet) { \n }',
        'startLine': 42,
        'endLine': 43
    },

    # _isNonRebasingAccount 함수 내용 - _ensureRebasingMigration 호출
    {
        'code': '_ensureRebasingMigration(_account);',
        'startLine': 43,
        'endLine': 43
    },

    # _isNonRebasingAccount 함수 내용 - return 조건
    {
        'code': 'return nonRebasingCreditsPerToken[_account] > 0;',
        'startLine': 45,
        'endLine': 45
    }
]




# Simulate input as if coming from VSCode with block structure assumptions
simulate_input(test_inputs)