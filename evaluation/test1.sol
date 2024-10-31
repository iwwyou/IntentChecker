// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract USDs {
    mapping(address => uint256) private _creditBalances;
    mapping(address => uint256) private nonRebasingCreditsPerToken;
    uint256 private rebasingCreditsPerToken;
    uint256 private nonRebasingSupply;
    mapping(address => RebaseOptions) private _rebaseState;
    enum RebaseOptions { NotSet, Rebased }

    function _isNonRebasingAccount(address _account) internal view returns (bool) {
        bool isContract = _isContract(_account);
        if (isContract && _rebaseState[_account] == RebaseOptions.NotSet) {
            _ensureRebasingMigration(_account);
        }
        return nonRebasingCreditsPerToken[_account] > 0;
    }

    function _ensureRebasingMigration(address _account) internal {
        if (nonRebasingCreditsPerToken[_account] == 0) {
            nonRebasingCreditsPerToken[_account] = 1;
            if (_creditBalances[_account] != 0) {
                uint256 bal = _balanceOf(_account);
                nonRebasingSupply = nonRebasingSupply + bal;
                _creditBalances[_account] = bal;
            }
        }
    }

    function _balanceOf(address _account) private view returns (uint256) {
        uint256 credits = _creditBalances[_account];
        if (credits > 0) {
            if (nonRebasingCreditsPerToken[_account] > 0) {
                return credits;
            }
            return credits / rebasingCreditsPerToken;
        }
        return 0;
    }
    
    function _isContract(address _account) private view returns (bool) {
        uint32 size = _account.code.length;
        if (size > 0) {
            return true;
        }
        return false;
    }
}

/*
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

    # 상태 변수 mapping 선언 - _rebaseState
    {
        'code': 'mapping(address => uint8) private _rebaseState;',
        'startLine': 6,
        'endLine': 6
    },

    # enum RebaseOptions 선언 - enumDefinition
    {
        'code': 'enum RebaseOptions { \n };',
        'startLine': 7,
        'endLine': 8
    },

    # enum RebaseOptions - enumItem 추가
    {
        'code': 'NotSet, Rebased',
        'startLine': 8,
        'endLine': 8
    },

    # _isContract 함수 선언
    {
        'code': 'function _isContract(address _account) private view returns (bool) { \n }',
        'startLine': 9,
        'endLine': 10
    },

    # _isContract 함수 내용 - size 체크
    {
        'code': 'uint32 size = _account.code.length;',
        'startLine': 10,
        'endLine': 10
    },

    # _isContract 함수 내용 - if문 작성
    {
        'code': 'if (size > 0) { \n }',
        'startLine': 11,
        'endLine': 11
    },

    # _isContract 함수 내용 - return true
    {
        'code': 'return true;',
        'startLine': 12,
        'endLine': 12
    },

    # _isContract 함수 내용 - return false
    {
        'code': 'return false;',
        'startLine': 13,
        'endLine': 13
    },

    # _balanceOf 함수 선언
    {
        'code': 'function _balanceOf(address _account) private view returns (uint256) { \n }',
        'startLine': 14,
        'endLine': 15
    },

    # _balanceOf 함수 내용 - credits 변수 선언 및 초기화
    {
        'code': 'uint256 credits = _creditBalances[_account];',
        'startLine': 15,
        'endLine': 15
    },

    # _balanceOf 함수 내용 - if문 체크 - credits > 0
    {
        'code': 'if (credits > 0) { \n }',
        'startLine': 16,
        'endLine': 16
    },

    # _balanceOf 함수 내용 - if문 체크 - nonRebasingCreditsPerToken
    {
        'code': 'if (nonRebasingCreditsPerToken[_account] > 0) { \n }',
        'startLine': 17,
        'endLine': 17
    },

    # _balanceOf 함수 내용 - return credits
    {
        'code': 'return credits;',
        'startLine': 18,
        'endLine': 18
    },

    # _balanceOf 함수 내용 - return credits / rebasingCreditsPerToken
    {
        'code': 'return credits / rebasingCreditsPerToken;',
        'startLine': 19,
        'endLine': 19
    },

    # _balanceOf 함수 내용 - return 0
    {
        'code': 'return 0;',
        'startLine': 20,
        'endLine': 20
    },

    # _ensureRebasingMigration 함수 선언
    {
        'code': 'function _ensureRebasingMigration(address _account) internal { \n }',
        'startLine': 21,
        'endLine': 22
    },

    # _ensureRebasingMigration 함수 내용 - if문 체크 - nonRebasingCreditsPerToken[_account] == 0
    {
        'code': 'if (nonRebasingCreditsPerToken[_account] == 0) { \n }',
        'startLine': 22,
        'endLine': 22
    },

    # _ensureRebasingMigration 함수 내용 - nonRebasingCreditsPerToken[_account] = 1;
    {
        'code': 'nonRebasingCreditsPerToken[_account] = 1;',
        'startLine': 23,
        'endLine': 23
    },

    # _ensureRebasingMigration 함수 내용 - if문 체크 - _creditBalances[_account] != 0
    {
        'code': 'if (_creditBalances[_account] != 0) { \n }',
        'startLine': 24,
        'endLine': 24
    },

    # _ensureRebasingMigration 함수 내용 - uint256 bal = _balanceOf(_account);
    {
        'code': 'uint256 bal = _balanceOf(_account);',
        'startLine': 25,
        'endLine': 25
    },

    # _ensureRebasingMigration 함수 내용 - nonRebasingSupply 증가
    {
        'code': 'nonRebasingSupply = nonRebasingSupply + bal;',
        'startLine': 26,
        'endLine': 26
    },

    # _ensureRebasingMigration 함수 내용 - _creditBalances[_account] 업데이트
    {
        'code': '_creditBalances[_account] = bal;',
        'startLine': 27,
        'endLine': 27
    },

    # _isNonRebasingAccount 함수 선언
    {
        'code': 'function _isNonRebasingAccount(address _account) internal view returns (bool) { \n }',
        'startLine': 28,
        'endLine': 29
    },

    # _isNonRebasingAccount 함수 내용 - isContract 체크
    {
        'code': 'bool isContract = _isContract(_account);',
        'startLine': 29,
        'endLine': 29
    },

    # _isNonRebasingAccount 함수 내용 - if문 작성
    {
        'code': 'if (isContract && _rebaseState[_account] == RebaseOptions.NotSet) { \n }',
        'startLine': 30,
        'endLine': 30
    },

    # _isNonRebasingAccount 함수 내용 - _ensureRebasingMigration 호출
    {
        'code': '_ensureRebasingMigration(_account);',
        'startLine': 31,
        'endLine': 31
    },

    # _isNonRebasingAccount 함수 내용 - return 조건
    {
        'code': 'return nonRebasingCreditsPerToken[_account] > 0;',
        'startLine': 32,
        'endLine': 32
    }
]
*/