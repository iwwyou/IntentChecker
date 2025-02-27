pragma solidity ^0.8.0;

contract USDs {
    enum RebaseOptions { NotSet, Rebased }

    mapping(address => uint256) private _creditBalances;
    mapping(address => uint256) private nonRebasingCreditsPerToken;
    uint256 private rebasingCreditsPerToken = 10;
    uint256 private nonRebasingSupply;
    mapping(address => RebaseOptions) private _rebaseState;

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

    // _balanceOf @testing _account = "0x1234567890abcdef1234567890abcdef12345678"
    // _balanceOf @testing _creditBalances[_account] = 100
    function _balanceOf(address _account) private view returns (uint256) {
        uint256 credits = _creditBalances[_account];
        if (credits > 0) {
            if (nonRebasingCreditsPerToken[_account] > 0) {
                return credits; // @assign credits > @current credits
            }
            return credits / rebasingCreditsPerToken;
        }
        return;
    }
    
    function _isContract(address _account) private view returns (bool) {
        uint32 size = _account.code.length;
        if (size > 0) {
            return true;
        }
        return false;
    }
}