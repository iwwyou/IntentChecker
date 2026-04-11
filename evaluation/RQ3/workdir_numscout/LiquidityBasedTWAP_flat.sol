

// Sources flattened with hardhat v2.22.0 https://hardhat.org

// SPDX-License-Identifier: CC-BY-4.0 AND GPL-3.0-or-later AND MIT AND Unlicense

// File @openzeppelin/contracts/utils/Context.sol@v4.3.2

// Original license: SPDX_License_Identifier: MIT

pragma solidity ^0.8.0;

/**
 * @dev Provides information about the current execution context, including the
 * sender of the transaction and its data. While these are generally available
 * via msg.sender and msg.data, they should not be accessed in such a direct
 * manner, since when dealing with meta-transactions the account sending and
 * paying for execution may not be the actual sender (as far as an application
 * is concerned).
 *
 * This contract is only required for intermediate, library-like contracts.
 */
abstract contract Context {
    function _msgSender() internal view virtual returns (address) {
        return msg.sender;
    }

    function _msgData() internal view virtual returns (bytes calldata) {
        return msg.data;
    }
}


// File @openzeppelin/contracts/access/Ownable.sol@v4.3.2

// Original license: SPDX_License_Identifier: MIT


/**
 * @dev Contract module which provides a basic access control mechanism, where
 * there is an account (an owner) that can be granted exclusive access to
 * specific functions.
 *
 * By default, the owner account will be the one that deploys the contract. This
 * can later be changed with {transferOwnership}.
 *
 * This module is used through inheritance. It will make available the modifier
 * `onlyOwner`, which can be applied to your functions to restrict their use to
 * the owner.
 */
abstract contract Ownable is Context {
    address private _owner;

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    /**
     * @dev Initializes the contract setting the deployer as the initial owner.
     */
    constructor() {
        _setOwner(_msgSender());
    }

    /**
     * @dev Returns the address of the current owner.
     */
    function owner() public view virtual returns (address) {
        return _owner;
    }

    /**
     * @dev Throws if called by any account other than the owner.
     */
    modifier onlyOwner() {
        require(owner() == _msgSender(), "Ownable: caller is not the owner");
        _;
    }

    /**
     * @dev Leaves the contract without owner. It will not be possible to call
     * `onlyOwner` functions anymore. Can only be called by the current owner.
     *
     * NOTE: Renouncing ownership will leave the contract without an owner,
     * thereby removing any functionality that is only available to the owner.
     */
    function renounceOwnership() public virtual onlyOwner {
        _setOwner(address(0));
    }

    /**
     * @dev Transfers ownership of the contract to a new account (`newOwner`).
     * Can only be called by the current owner.
     */
    function transferOwnership(address newOwner) public virtual onlyOwner {
        require(newOwner != address(0), "Ownable: new owner is the zero address");
        _setOwner(newOwner);
    }

    function _setOwner(address newOwner) private {
        address oldOwner = _owner;
        _owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }
}


// File @openzeppelin/contracts/token/ERC20/IERC20.sol@v4.3.2

// Original license: SPDX_License_Identifier: MIT


/**
 * @dev Interface of the ERC20 standard as defined in the EIP.
 */
interface IERC20 {
    /**
     * @dev Returns the amount of tokens in existence.
     */
    function totalSupply() external view returns (uint256);

    /**
     * @dev Returns the amount of tokens owned by `account`.
     */
    function balanceOf(address account) external view returns (uint256);

    /**
     * @dev Moves `amount` tokens from the caller's account to `recipient`.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * Emits a {Transfer} event.
     */
    function transfer(address recipient, uint256 amount) external returns (bool);

    /**
     * @dev Returns the remaining number of tokens that `spender` will be
     * allowed to spend on behalf of `owner` through {transferFrom}. This is
     * zero by default.
     *
     * This value changes when {approve} or {transferFrom} are called.
     */
    function allowance(address owner, address spender) external view returns (uint256);

    /**
     * @dev Sets `amount` as the allowance of `spender` over the caller's tokens.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * IMPORTANT: Beware that changing an allowance with this method brings the risk
     * that someone may use both the old and the new allowance by unfortunate
     * transaction ordering. One possible solution to mitigate this race
     * condition is to first reduce the spender's allowance to 0 and set the
     * desired value afterwards:
     * https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729
     *
     * Emits an {Approval} event.
     */
    function approve(address spender, uint256 amount) external returns (bool);

    /**
     * @dev Moves `amount` tokens from `sender` to `recipient` using the
     * allowance mechanism. `amount` is then deducted from the caller's
     * allowance.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * Emits a {Transfer} event.
     */
    function transferFrom(
        address sender,
        address recipient,
        uint256 amount
    ) external returns (bool);

    /**
     * @dev Emitted when `value` tokens are moved from one account (`from`) to
     * another (`to`).
     *
     * Note that `value` may be zero.
     */
    event Transfer(address indexed from, address indexed to, uint256 value);

    /**
     * @dev Emitted when the allowance of a `spender` for an `owner` is set by
     * a call to {approve}. `value` is the new allowance.
     */
    event Approval(address indexed owner, address indexed spender, uint256 value);
}


// File @openzeppelin/contracts/token/ERC20/extensions/IERC20Metadata.sol@v4.3.2

// Original license: SPDX_License_Identifier: MIT


/**
 * @dev Interface for the optional metadata functions from the ERC20 standard.
 *
 * _Available since v4.1._
 */
interface IERC20Metadata is IERC20 {
    /**
     * @dev Returns the name of the token.
     */
    function name() external view returns (string memory);

    /**
     * @dev Returns the symbol of the token.
     */
    function symbol() external view returns (string memory);

    /**
     * @dev Returns the decimals places of the token.
     */
    function decimals() external view returns (uint8);
}


// File @openzeppelin/contracts/utils/introspection/IERC165.sol@v4.3.2

// Original license: SPDX_License_Identifier: MIT


/**
 * @dev Interface of the ERC165 standard, as defined in the
 * https://eips.ethereum.org/EIPS/eip-165[EIP].
 *
 * Implementers can declare support of contract interfaces, which can then be
 * queried by others ({ERC165Checker}).
 *
 * For an implementation, see {ERC165}.
 */
interface IERC165 {
    /**
     * @dev Returns true if this contract implements the interface defined by
     * `interfaceId`. See the corresponding
     * https://eips.ethereum.org/EIPS/eip-165#how-interfaces-are-identified[EIP section]
     * to learn more about how these ids are created.
     *
     * This function call must use less than 30 000 gas.
     */
    function supportsInterface(bytes4 interfaceId) external view returns (bool);
}


// File @openzeppelin/contracts/token/ERC721/IERC721.sol@v4.3.2

// Original license: SPDX_License_Identifier: MIT


/**
 * @dev Required interface of an ERC721 compliant contract.
 */
interface IERC721 is IERC165 {
    /**
     * @dev Emitted when `tokenId` token is transferred from `from` to `to`.
     */
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);

    /**
     * @dev Emitted when `owner` enables `approved` to manage the `tokenId` token.
     */
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);

    /**
     * @dev Emitted when `owner` enables or disables (`approved`) `operator` to manage all of its assets.
     */
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);

    /**
     * @dev Returns the number of tokens in ``owner``'s account.
     */
    function balanceOf(address owner) external view returns (uint256 balance);

    /**
     * @dev Returns the owner of the `tokenId` token.
     *
     * Requirements:
     *
     * - `tokenId` must exist.
     */
    function ownerOf(uint256 tokenId) external view returns (address owner);

    /**
     * @dev Safely transfers `tokenId` token from `from` to `to`, checking first that contract recipients
     * are aware of the ERC721 protocol to prevent tokens from being forever locked.
     *
     * Requirements:
     *
     * - `from` cannot be the zero address.
     * - `to` cannot be the zero address.
     * - `tokenId` token must exist and be owned by `from`.
     * - If the caller is not `from`, it must be have been allowed to move this token by either {approve} or {setApprovalForAll}.
     * - If `to` refers to a smart contract, it must implement {IERC721Receiver-onERC721Received}, which is called upon a safe transfer.
     *
     * Emits a {Transfer} event.
     */
    function safeTransferFrom(
        address from,
        address to,
        uint256 tokenId
    ) external;

    /**
     * @dev Transfers `tokenId` token from `from` to `to`.
     *
     * WARNING: Usage of this method is discouraged, use {safeTransferFrom} whenever possible.
     *
     * Requirements:
     *
     * - `from` cannot be the zero address.
     * - `to` cannot be the zero address.
     * - `tokenId` token must be owned by `from`.
     * - If the caller is not `from`, it must be approved to move this token by either {approve} or {setApprovalForAll}.
     *
     * Emits a {Transfer} event.
     */
    function transferFrom(
        address from,
        address to,
        uint256 tokenId
    ) external;

    /**
     * @dev Gives permission to `to` to transfer `tokenId` token to another account.
     * The approval is cleared when the token is transferred.
     *
     * Only a single account can be approved at a time, so approving the zero address clears previous approvals.
     *
     * Requirements:
     *
     * - The caller must own the token or be an approved operator.
     * - `tokenId` must exist.
     *
     * Emits an {Approval} event.
     */
    function approve(address to, uint256 tokenId) external;

    /**
     * @dev Returns the account approved for `tokenId` token.
     *
     * Requirements:
     *
     * - `tokenId` must exist.
     */
    function getApproved(uint256 tokenId) external view returns (address operator);

    /**
     * @dev Approve or remove `operator` as an operator for the caller.
     * Operators can call {transferFrom} or {safeTransferFrom} for any token owned by the caller.
     *
     * Requirements:
     *
     * - The `operator` cannot be the caller.
     *
     * Emits an {ApprovalForAll} event.
     */
    function setApprovalForAll(address operator, bool _approved) external;

    /**
     * @dev Returns if the `operator` is allowed to manage all of the assets of `owner`.
     *
     * See {setApprovalForAll}
     */
    function isApprovedForAll(address owner, address operator) external view returns (bool);

    /**
     * @dev Safely transfers `tokenId` token from `from` to `to`.
     *
     * Requirements:
     *
     * - `from` cannot be the zero address.
     * - `to` cannot be the zero address.
     * - `tokenId` token must exist and be owned by `from`.
     * - If the caller is not `from`, it must be approved to move this token by either {approve} or {setApprovalForAll}.
     * - If `to` refers to a smart contract, it must implement {IERC721Receiver-onERC721Received}, which is called upon a safe transfer.
     *
     * Emits a {Transfer} event.
     */
    function safeTransferFrom(
        address from,
        address to,
        uint256 tokenId,
        bytes calldata data
    ) external;
}


// File contracts/external/libraries/Babylonian.sol

// Original license: SPDX_License_Identifier: GPL-3.0-or-later


// computes square roots using the babylonian method
// https://en.wikipedia.org/wiki/Methods_of_computing_square_roots#Babylonian_method
library Babylonian {
    // credit for this implementation goes to
    // https://github.com/abdk-consulting/abdk-libraries-solidity/blob/master/ABDKMath64x64.sol#L687
    function sqrt(uint256 x) internal pure returns (uint256) {
        if (x == 0) return 0;
        // this block is equivalent to r = uint256(1) << (BitMath.mostSignificantBit(x) / 2);
        // however that code costs significantly more gas
        uint256 xx = x;
        uint256 r = 1;
        if (xx >= 0x100000000000000000000000000000000) {
            xx >>= 128;
            r <<= 64;
        }
        if (xx >= 0x10000000000000000) {
            xx >>= 64;
            r <<= 32;
        }
        if (xx >= 0x100000000) {
            xx >>= 32;
            r <<= 16;
        }
        if (xx >= 0x10000) {
            xx >>= 16;
            r <<= 8;
        }
        if (xx >= 0x100) {
            xx >>= 8;
            r <<= 4;
        }
        if (xx >= 0x10) {
            xx >>= 4;
            r <<= 2;
        }
        if (xx >= 0x8) {
            r <<= 1;
        }
        r = (r + x / r) >> 1;
        r = (r + x / r) >> 1;
        r = (r + x / r) >> 1;
        r = (r + x / r) >> 1;
        r = (r + x / r) >> 1;
        r = (r + x / r) >> 1;
        r = (r + x / r) >> 1; // Seven iterations should be enough
        uint256 r1 = x / r;
        return (r < r1 ? r : r1);
    }
}


// File contracts/external/libraries/BitMath.sol

// Original license: SPDX_License_Identifier: GPL-3.0-or-later

library BitMath {
    // returns the 0 indexed position of the most significant bit of the input x
    // s.t. x >= 2**msb and x < 2**(msb+1)
    function mostSignificantBit(uint256 x) internal pure returns (uint8 r) {
        require(x > 0, "BitMath::mostSignificantBit: zero");

        if (x >= 0x100000000000000000000000000000000) {
            x >>= 128;
            r += 128;
        }
        if (x >= 0x10000000000000000) {
            x >>= 64;
            r += 64;
        }
        if (x >= 0x100000000) {
            x >>= 32;
            r += 32;
        }
        if (x >= 0x10000) {
            x >>= 16;
            r += 16;
        }
        if (x >= 0x100) {
            x >>= 8;
            r += 8;
        }
        if (x >= 0x10) {
            x >>= 4;
            r += 4;
        }
        if (x >= 0x4) {
            x >>= 2;
            r += 2;
        }
        if (x >= 0x2) r += 1;
    }

    // returns the 0 indexed position of the least significant bit of the input x
    // s.t. (x & 2**lsb) != 0 and (x & (2**(lsb) - 1)) == 0)
    // i.e. the bit at the index is set and the mask of all lower bits is 0
    function leastSignificantBit(uint256 x) internal pure returns (uint8 r) {
        require(x > 0, "BitMath::leastSignificantBit: zero");

        r = 255;
        if (x & type(uint128).max > 0) {
            r -= 128;
        } else {
            x >>= 128;
        }
        if (x & type(uint64).max > 0) {
            r -= 64;
        } else {
            x >>= 64;
        }
        if (x & type(uint32).max > 0) {
            r -= 32;
        } else {
            x >>= 32;
        }
        if (x & type(uint16).max > 0) {
            r -= 16;
        } else {
            x >>= 16;
        }
        if (x & type(uint8).max > 0) {
            r -= 8;
        } else {
            x >>= 8;
        }
        if (x & 0xf > 0) {
            r -= 4;
        } else {
            x >>= 4;
        }
        if (x & 0x3 > 0) {
            r -= 2;
        } else {
            x >>= 2;
        }
        if (x & 0x1 > 0) r -= 1;
    }
}


// File contracts/external/libraries/FullMath.sol

// Original license: SPDX_License_Identifier: CC-BY-4.0

// taken from https://medium.com/coinmonks/math-in-solidity-part-3-percents-and-proportions-4db014e080b1
// license is CC-BY-4.0
library FullMath {
    function fullMul(uint256 x, uint256 y)
        internal
        pure
        returns (uint256 l, uint256 h)
    {
        uint256 mm = mulmod(x, y, type(uint256).max);
        l = x * y;
        h = mm - l;
        if (mm < l) h -= 1;
    }

    function fullDiv(
        uint256 l,
        uint256 h,
        uint256 d
    ) private pure returns (uint256) {
        uint256 pow2 = d & uint256(-int256(d));
        d /= pow2;
        l /= pow2;
        l += h * (uint256(-int256(pow2)) / pow2 + 1);
        uint256 r = 1;
        r *= 2 - d * r;
        r *= 2 - d * r;
        r *= 2 - d * r;
        r *= 2 - d * r;
        r *= 2 - d * r;
        r *= 2 - d * r;
        r *= 2 - d * r;
        r *= 2 - d * r;
        return l * r;
    }

    function mulDiv(
        uint256 x,
        uint256 y,
        uint256 d
    ) internal pure returns (uint256) {
        (uint256 l, uint256 h) = fullMul(x, y);

        uint256 mm = mulmod(x, y, d);
        if (mm > l) h -= 1;
        l -= mm;

        if (h == 0) return l / d;

        require(h < d, "FullMath: FULLDIV_OVERFLOW");
        return fullDiv(l, h, d);
    }
}


// File contracts/external/libraries/FixedPoint.sol

// Original license: SPDX_License_Identifier: GPL-3.0-or-later
// a library for handling binary fixed point numbers (https://en.wikipedia.org/wiki/Q_(number_format))
library FixedPoint {
    // range: [0, 2**112 - 1]
    // resolution: 1 / 2**112
    struct uq112x112 {
        uint224 _x;
    }

    // range: [0, 2**144 - 1]
    // resolution: 1 / 2**112
    struct uq144x112 {
        uint256 _x;
    }

    uint8 public constant RESOLUTION = 112;
    uint256 public constant Q112 = 0x10000000000000000000000000000; // 2**112
    uint256 private constant Q224 =
        0x100000000000000000000000000000000000000000000000000000000; // 2**224
    uint256 private constant LOWER_MASK = 0xffffffffffffffffffffffffffff; // decimal of UQ*x112 (lower 112 bits)

    // encode a uint112 as a UQ112x112
    function encode(uint112 x) internal pure returns (uq112x112 memory) {
        return uq112x112(uint224(x) << RESOLUTION);
    }

    // encodes a uint144 as a UQ144x112
    function encode144(uint144 x) internal pure returns (uq144x112 memory) {
        return uq144x112(uint256(x) << RESOLUTION);
    }

    // decode a UQ112x112 into a uint112 by truncating after the radix point
    function decode(uq112x112 memory self) internal pure returns (uint112) {
        return uint112(self._x >> RESOLUTION);
    }

    // decode a UQ144x112 into a uint144 by truncating after the radix point
    function decode144(uq144x112 memory self) internal pure returns (uint144) {
        return uint144(self._x >> RESOLUTION);
    }

    // multiply a UQ112x112 by a uint, returning a UQ144x112
    // reverts on overflow
    function mul(uq112x112 memory self, uint256 y)
        internal
        pure
        returns (uq144x112 memory)
    {
        uint256 z = 0;
        require(
            y == 0 || (z = self._x * y) / y == self._x,
            "FixedPoint::mul: overflow"
        );
        return uq144x112(z);
    }

    // multiply a UQ112x112 by an int and decode, returning an int
    // reverts on overflow
    function muli(uq112x112 memory self, int256 y)
        internal
        pure
        returns (int256)
    {
        uint256 z = FullMath.mulDiv(self._x, uint256(y < 0 ? -y : y), Q112);
        require(z < 2**255, "FixedPoint::muli: overflow");
        return y < 0 ? -int256(z) : int256(z);
    }

    // multiply a UQ112x112 by a UQ112x112, returning a UQ112x112
    // lossy
    function muluq(uq112x112 memory self, uq112x112 memory other)
        internal
        pure
        returns (uq112x112 memory)
    {
        if (self._x == 0 || other._x == 0) {
            return uq112x112(0);
        }
        uint112 upper_self = uint112(self._x >> RESOLUTION); // * 2^0
        uint112 lower_self = uint112(self._x & LOWER_MASK); // * 2^-112
        uint112 upper_other = uint112(other._x >> RESOLUTION); // * 2^0
        uint112 lower_other = uint112(other._x & LOWER_MASK); // * 2^-112

        // partial products
        uint224 upper = uint224(upper_self) * upper_other; // * 2^0
        uint224 lower = uint224(lower_self) * lower_other; // * 2^-224
        uint224 uppers_lowero = uint224(upper_self) * lower_other; // * 2^-112
        uint224 uppero_lowers = uint224(upper_other) * lower_self; // * 2^-112

        // so the bit shift does not overflow
        require(
            upper <= type(uint112).max,
            "FixedPoint::muluq: upper overflow"
        );

        // this cannot exceed 256 bits, all values are 224 bits
        uint256 sum = uint256(upper << RESOLUTION) +
            uppers_lowero +
            uppero_lowers +
            (lower >> RESOLUTION);

        // so the cast does not overflow
        require(sum <= type(uint224).max, "FixedPoint::muluq: sum overflow");

        return uq112x112(uint224(sum));
    }

    // divide a UQ112x112 by a UQ112x112, returning a UQ112x112
    function divuq(uq112x112 memory self, uq112x112 memory other)
        internal
        pure
        returns (uq112x112 memory)
    {
        require(other._x > 0, "FixedPoint::divuq: division by zero");
        if (self._x == other._x) {
            return uq112x112(uint224(Q112));
        }
        if (self._x <= type(uint144).max) {
            uint256 value = (uint256(self._x) << RESOLUTION) / other._x;
            require(value <= type(uint224).max, "FixedPoint::divuq: overflow");
            return uq112x112(uint224(value));
        }

        uint256 result = FullMath.mulDiv(Q112, self._x, other._x);
        require(result <= type(uint224).max, "FixedPoint::divuq: overflow");
        return uq112x112(uint224(result));
    }

    // returns a UQ112x112 which represents the ratio of the numerator to the denominator
    // can be lossy
    function fraction(uint256 numerator, uint256 denominator)
        internal
        pure
        returns (uq112x112 memory)
    {
        require(denominator > 0, "FixedPoint::fraction: division by zero");
        if (numerator == 0) return FixedPoint.uq112x112(0);

        if (numerator <= type(uint144).max) {
            uint256 result = (numerator << RESOLUTION) / denominator;
            require(
                result <= type(uint224).max,
                "FixedPoint::fraction: overflow"
            );
            return uq112x112(uint224(result));
        } else {
            uint256 result = FullMath.mulDiv(numerator, Q112, denominator);
            require(
                result <= type(uint224).max,
                "FixedPoint::fraction: overflow"
            );
            return uq112x112(uint224(result));
        }
    }

    // take the reciprocal of a UQ112x112
    // reverts on overflow
    // lossy
    function reciprocal(uq112x112 memory self)
        internal
        pure
        returns (uq112x112 memory)
    {
        require(self._x != 0, "FixedPoint::reciprocal: reciprocal of zero");
        require(self._x != 1, "FixedPoint::reciprocal: overflow");
        return uq112x112(uint224(Q224 / self._x));
    }

    // square root of a UQ112x112
    // lossy between 0/1 and 40 bits
    function sqrt(uq112x112 memory self)
        internal
        pure
        returns (uq112x112 memory)
    {
        if (self._x <= type(uint144).max) {
            return uq112x112(uint224(Babylonian.sqrt(uint256(self._x) << 112)));
        }

        uint8 safeShiftBits = 255 - BitMath.mostSignificantBit(self._x);
        safeShiftBits -= safeShiftBits % 2;
        return
            uq112x112(
                uint224(
                    Babylonian.sqrt(uint256(self._x) << safeShiftBits) <<
                        ((112 - safeShiftBits) / 2)
                )
            );
    }
}


// File contracts/interfaces/external/uniswap/IUniswapV2ERC20.sol

// Original license: SPDX_License_Identifier: MIT

interface IUniswapV2ERC20 {
    event Approval(
        address indexed owner,
        address indexed spender,
        uint256 value
    );
    event Transfer(address indexed from, address indexed to, uint256 value);

    function name() external pure returns (string memory);

    function symbol() external pure returns (string memory);

    function decimals() external pure returns (uint8);

    function totalSupply() external view returns (uint256);

    function balanceOf(address owner) external view returns (uint256);

    function allowance(address owner, address spender)
        external
        view
        returns (uint256);

    function approve(address spender, uint256 value) external returns (bool);

    function transfer(address to, uint256 value) external returns (bool);

    function transferFrom(
        address from,
        address to,
        uint256 value
    ) external returns (bool);

    function DOMAIN_SEPARATOR() external view returns (bytes32);

    function PERMIT_TYPEHASH() external pure returns (bytes32);

    function nonces(address owner) external view returns (uint256);

    function permit(
        address owner,
        address spender,
        uint256 value,
        uint256 deadline,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external;
}


// File contracts/interfaces/external/uniswap/IUniswapV2Pair.sol

// Original license: SPDX_License_Identifier: MIT
interface IUniswapV2Pair is IUniswapV2ERC20 {
    event Mint(address indexed sender, uint256 amount0, uint256 amount1);
    event Burn(
        address indexed sender,
        uint256 amount0,
        uint256 amount1,
        address indexed to
    );
    event Swap(
        address indexed sender,
        uint256 amount0In,
        uint256 amount1In,
        uint256 amount0Out,
        uint256 amount1Out,
        address indexed to
    );
    event Sync(uint112 reserve0, uint112 reserve1);

    function MINIMUM_LIQUIDITY() external pure returns (uint256);

    function factory() external view returns (address);

    function token0() external view returns (address);

    function token1() external view returns (address);

    function getReserves()
        external
        view
        returns (
            uint112 reserve0,
            uint112 reserve1,
            uint32 blockTimestampLast
        );

    function price0CumulativeLast() external view returns (uint256);

    function price1CumulativeLast() external view returns (uint256);

    function kLast() external view returns (uint256);

    function mint(address to) external returns (uint256 liquidity);

    function burn(address to)
        external
        returns (uint256 amount0, uint256 amount1);

    function swap(
        uint256 amount0Out,
        uint256 amount1Out,
        address to,
        bytes calldata data
    ) external;

    function skim(address to) external;

    function sync() external;

    function initialize(address, address) external;
}


// File contracts/external/libraries/UniswapV2OracleLibrary.sol

// Original license: SPDX_License_Identifier: Unlicense

// library with helper methods for oracles that are concerned with computing average prices
library UniswapV2OracleLibrary {
    using FixedPoint for *;

    // helper function that returns the current block timestamp within the range of uint32, i.e. [0, 2**32 - 1]
    function currentBlockTimestamp() internal view returns (uint32) {
        return uint32(block.timestamp % 2**32);
    }

    // produces the cumulative price using counterfactuals to save gas and avoid a call to sync.
    function currentCumulativePrices(address pair)
        internal
        view
        returns (
            uint256 price0Cumulative,
            uint256 price1Cumulative,
            uint32 blockTimestamp
        )
    {
        blockTimestamp = currentBlockTimestamp();
        price0Cumulative = IUniswapV2Pair(pair).price0CumulativeLast();
        price1Cumulative = IUniswapV2Pair(pair).price1CumulativeLast();

        // if time has elapsed since the last update on the pair, mock the accumulated price values
        (
            uint112 reserve0,
            uint112 reserve1,
            uint32 blockTimestampLast
        ) = IUniswapV2Pair(pair).getReserves();
        if (blockTimestampLast != blockTimestamp) {
            // subtraction overflow is desired
            uint32 timeElapsed = blockTimestamp - blockTimestampLast;
            // addition overflow is desired
            // counterfactual
            price0Cumulative +=
                uint256(FixedPoint.fraction(reserve1, reserve0)._x) *
                timeElapsed;
            // counterfactual
            price1Cumulative +=
                uint256(FixedPoint.fraction(reserve0, reserve1)._x) *
                timeElapsed;
        }
    }
}


// File contracts/interfaces/dex-v2/pool/IBasePoolV2.sol

// Original license: SPDX_License_Identifier: Unlicense

interface IBasePoolV2 {
    /* ========== STRUCTS ========== */

    struct Position {
        IERC20 foreignAsset;
        uint256 creation;
        uint256 liquidity;
        uint256 originalNative;
        uint256 originalForeign;
    }

    struct PairInfo {
        uint256 totalSupply;
        uint112 reserveNative;
        uint112 reserveForeign;
        uint32 blockTimestampLast;
        PriceCumulative priceCumulative;
    }

    struct PriceCumulative {
        uint256 nativeLast;
        uint256 foreignLast;
    }

    /* ========== FUNCTIONS ========== */

    function getReserves(
        IERC20 foreignAsset
    ) external view returns (
        uint112 reserve0,
        uint112 reserve1,
        uint32 blockTimestampLast
    );

    function nativeAsset() external view returns (IERC20);

    function supported(IERC20 token) external view returns (bool);

    function positionForeignAsset(uint256 id) external view returns (IERC20);

    function pairSupply(IERC20 foreignAsset) external view returns (uint256);

    function doubleSwap(
        IERC20 foreignAssetA,
        IERC20 foreignAssetB,
        uint256 foreignAmountIn,
        address to
    ) external returns (uint256);

    function swap(
        IERC20 foreignAsset,
        uint256 nativeAmountIn,
        uint256 foreignAmountIn,
        address to
    ) external returns (uint256);

    function mint(
        IERC20 foreignAsset,
        uint256 nativeDeposit,
        uint256 foreignDeposit,
        address from,
        address to
    ) external returns (uint256 liquidity);

    /* ========== EVENTS ========== */

    event Mint(
        address indexed sender,
        address indexed to,
        uint256 amount0,
        uint256 amount1
    ); // Adjustment -> new argument to which didnt exist
    event Burn(
        address indexed sender,
        uint256 amount0,
        uint256 amount1,
        address indexed to
    );
    event Swap(
        IERC20 foreignAsset,
        address indexed sender,
        uint256 amount0In,
        uint256 amount1In,
        uint256 amount0Out,
        uint256 amount1Out,
        address indexed to
    );
    event Sync(IERC20 foreignAsset, uint256 reserve0, uint256 reserve1); // Adjustment -> 112 to 256
    event PositionOpened(
        address indexed from,
        address indexed to,
        uint256 id,
        uint256 liquidity
    );
    event PositionClosed(
        address indexed sender,
        uint256 id,
        uint256 liquidity,
        uint256 loss
    );
}


// File contracts/interfaces/dex-v2/pool/IVaderPoolV2.sol

// Original license: SPDX_License_Identifier: Unlicense

interface IVaderPoolV2 is IBasePoolV2, IERC721 {
    /* ========== STRUCTS ========== */
    /* ========== FUNCTIONS ========== */

    function cumulativePrices(IERC20 foreignAsset)
        external
        view
        returns (
            uint256 price0CumulativeLast,
            uint256 price1CumulativeLast,
            uint32 blockTimestampLast
        );

    function mintSynth(
        IERC20 foreignAsset,
        uint256 nativeDeposit,
        address from,
        address to
    ) external returns (uint256 amountSynth);

    function burnSynth(
        IERC20 foreignAsset,
        uint256 synthAmount,
        address to
    ) external returns (uint256 amountNative);

    function mintFungible(
        IERC20 foreignAsset,
        uint256 nativeDeposit,
        uint256 foreignDeposit,
        address from,
        address to
    ) external returns (uint256 liquidity);

    function burnFungible(
        IERC20 foreignAsset,
        uint256 liquidity,
        address to
    ) external returns (uint256 amountNative, uint256 amountForeign);

    function burn(uint256 id, address to)
        external
        returns (
            uint256 amountNative,
            uint256 amountForeign,
            uint256 coveredLoss
        );

    function setQueue(bool _queueActive) external;

    function setTokenSupport(
        IERC20 foreignAsset,
        bool support,
        uint256 nativeDeposit,
        uint256 foreignDeposit,
        address from,
        address to
    ) external returns (uint256 liquidity);

    function setFungibleTokenSupport(IERC20 foreignAsset) external;

    function setGasThrottle(bool _gasThrottleEnabled) external;

    /* ========== EVENTS ========== */

    event QueueActive(bool activated);
}


// File contracts/interfaces/lbt/ILiquidityBasedTWAP.sol

// Original license: SPDX_License_Identifier: Unlicense

interface ILiquidityBasedTWAP {
    /* ========== STRUCTS ========== */

    struct ExchangePair {
        uint256 nativeTokenPriceCumulative;
        FixedPoint.uq112x112 nativeTokenPriceAverage;
        uint256 lastMeasurement;
        uint256 updatePeriod;
        uint256 pastLiquidityEvaluation;
        address foreignAsset;
        uint96 foreignUnit;
    }

    enum Paths {
        VADER,
        USDV
    }

    /* ========== FUNCTIONS ========== */

    function previousPrices(uint256 i) external returns (uint256);

    function maxUpdateWindow() external returns (uint256);

    function getVaderPrice() external returns (uint256);

    function syncVaderPrice()
        external
        returns (
            uint256[] memory pastLiquidityWeights,
            uint256 pastTotalLiquidityWeight
        );

    function getUSDVPrice() external returns (uint256);

    function syncUSDVPrice()
        external
        returns (
            uint256[] memory pastLiquidityWeights,
            uint256 pastTotalLiquidityWeight
        );

    /* ========== EVENTS ========== */
}


// File contracts/interfaces/external/chainlink/IAggregatorV3.sol

// Original license: SPDX_License_Identifier: MIT

interface IAggregatorV3 {
    function decimals() external view returns (uint8);

    function description() external view returns (string memory);

    function version() external view returns (uint256);

    // getRoundData and latestRoundData should both raise "No data present"
    // if they do not have data to report, instead of returning unset values
    // which could be misinterpreted as actual reported values.
    function getRoundData(uint80 _roundId)
        external
        view
        returns (
            uint80 roundId,
            int256 answer,
            uint256 startedAt,
            uint256 updatedAt,
            uint80 answeredInRound
        );

    function latestRoundData()
        external
        view
        returns (
            uint80 roundId,
            int256 answer,
            uint256 startedAt,
            uint256 updatedAt,
            uint80 answeredInRound
        );
}


// File contracts/lbt/LiquidityBasedTWAP.sol

// Original license: SPDX_License_Identifier: Unlicense

contract LiquidityBasedTWAP is ILiquidityBasedTWAP, Ownable {
    /* ========== LIBRARIES ========== */

    using FixedPoint for FixedPoint.uq112x112;
    using FixedPoint for FixedPoint.uq144x112;

    /* ========== STATE VARIABLES ========== */

    address public immutable vader;
    IVaderPoolV2 public immutable vaderPool;

    IUniswapV2Pair[] public vaderPairs;
    IERC20[] public usdvPairs;

    uint256 public override maxUpdateWindow;
    uint256[2] public totalLiquidityWeight;
    uint256[2] public override previousPrices;
    mapping(address => ExchangePair) public twapData;
    mapping(address => IAggregatorV3) public oracles;

    /* ========== CONSTRUCTOR ========== */

    constructor(address _vader, IVaderPoolV2 _vaderPool) {
        require(
            _vader != address(0) && _vaderPool != IVaderPoolV2(address(0)),
            "LBTWAP::construction: Zero Address"
        );
        vader = _vader;
        vaderPool = _vaderPool;
    }

    /* ========== VIEWS ========== */

    function getStaleVaderPrice() external view returns (uint256) {
        uint256 totalPairs = vaderPairs.length;
        uint256[] memory pastLiquidityWeights = new uint256[](totalPairs);
        uint256 pastTotalLiquidityWeight = totalLiquidityWeight[
            uint256(Paths.VADER)
        ];

        for (uint256 i; i < totalPairs; ++i)
            pastLiquidityWeights[i] = twapData[address(vaderPairs[i])]
                .pastLiquidityEvaluation;

        return
            _calculateVaderPrice(
                pastLiquidityWeights,
                pastTotalLiquidityWeight
            );
    }

    function getStaleUSDVPrice() external view returns (uint256) {
        uint256 totalPairs = usdvPairs.length;
        uint256[] memory pastLiquidityWeights = new uint256[](totalPairs);
        uint256 pastTotalLiquidityWeight = totalLiquidityWeight[
            uint256(Paths.USDV)
        ];

        for (uint256 i; i < totalPairs; ++i)
            pastLiquidityWeights[i] = twapData[address(usdvPairs[i])]
                .pastLiquidityEvaluation;

        return
            _calculateUSDVPrice(pastLiquidityWeights, pastTotalLiquidityWeight);
    }

    function getChainlinkPrice(address asset) public view returns (uint256) {
        IAggregatorV3 oracle = oracles[asset];

        (uint80 roundID, int256 price, , , uint80 answeredInRound) = oracle
            .latestRoundData();

        require(
            answeredInRound >= roundID,
            "LBTWAP::getChainlinkPrice: Stale Chainlink Price"
        );

        require(price > 0, "LBTWAP::getChainlinkPrice: Chainlink Malfunction");

        return uint256(price);
    }

    /* ========== MUTATIVE FUNCTIONS ========== */

    function getVaderPrice() external returns (uint256) {
        (
            uint256[] memory pastLiquidityWeights,
            uint256 pastTotalLiquidityWeight
        ) = syncVaderPrice();

        return
            _calculateVaderPrice(
                pastLiquidityWeights,
                pastTotalLiquidityWeight
            );
    }

    function syncVaderPrice()
        public
        override
        returns (
            uint256[] memory pastLiquidityWeights,
            uint256 pastTotalLiquidityWeight
        )
    {
        uint256 _totalLiquidityWeight;
        uint256 totalPairs = vaderPairs.length;
        pastLiquidityWeights = new uint256[](totalPairs);
        pastTotalLiquidityWeight = totalLiquidityWeight[uint256(Paths.VADER)];

        for (uint256 i; i < totalPairs; ++i) {
            IUniswapV2Pair pair = vaderPairs[i];
            ExchangePair storage pairData = twapData[address(pair)];
            uint256 timeElapsed = block.timestamp - pairData.lastMeasurement;

            if (timeElapsed < pairData.updatePeriod) continue;

            uint256 pastLiquidityEvaluation = pairData.pastLiquidityEvaluation;
            uint256 currentLiquidityEvaluation = _updateVaderPrice(
                pair,
                pairData,
                timeElapsed
            );

            pastLiquidityWeights[i] = pastLiquidityEvaluation;

            pairData.pastLiquidityEvaluation = currentLiquidityEvaluation;

            _totalLiquidityWeight += currentLiquidityEvaluation;
        }

        totalLiquidityWeight[uint256(Paths.VADER)] = _totalLiquidityWeight;
    }

    function _updateVaderPrice(
        IUniswapV2Pair pair,
        ExchangePair storage pairData,
        uint256 timeElapsed
    ) internal returns (uint256 currentLiquidityEvaluation) {
        bool isFirst = pair.token0() == vader;

        (uint256 reserve0, uint256 reserve1, ) = pair.getReserves();

        (uint256 reserveNative, uint256 reserveForeign) = isFirst
            ? (reserve0, reserve1)
            : (reserve1, reserve0);

        (
            uint256 price0Cumulative,
            uint256 price1Cumulative,
            uint256 currentMeasurement
        ) = UniswapV2OracleLibrary.currentCumulativePrices(address(pair));

        uint256 nativeTokenPriceCumulative = isFirst
            ? price0Cumulative
            : price1Cumulative;

        unchecked {
            pairData.nativeTokenPriceAverage = FixedPoint.uq112x112(
                uint224(
                    (nativeTokenPriceCumulative -
                        pairData.nativeTokenPriceCumulative) / timeElapsed
                )
            );
        }

        pairData.nativeTokenPriceCumulative = nativeTokenPriceCumulative;

        pairData.lastMeasurement = currentMeasurement;

        currentLiquidityEvaluation =
            (reserveNative * previousPrices[uint256(Paths.VADER)]) +
            (reserveForeign * getChainlinkPrice(pairData.foreignAsset));
    }

    function _calculateVaderPrice(
        uint256[] memory liquidityWeights,
        uint256 totalVaderLiquidityWeight
    ) internal view returns (uint256) {
        uint256 totalUSD;
        uint256 totalVader;
        uint256 totalPairs = vaderPairs.length;

        for (uint256 i; i < totalPairs; ++i) {
            IUniswapV2Pair pair = vaderPairs[i];
            ExchangePair storage pairData = twapData[address(pair)];

            uint256 foreignPrice = getChainlinkPrice(pairData.foreignAsset);

            totalUSD +=
                (foreignPrice * liquidityWeights[i]) /
                totalVaderLiquidityWeight;

            totalVader +=
                (pairData
                    .nativeTokenPriceAverage
                    .mul(pairData.foreignUnit)
                    .decode144() * liquidityWeights[i]) /
                totalVaderLiquidityWeight;
        }

        // NOTE: Accuracy of VADER & USDV is 18 decimals == 1 ether
        return (totalUSD * 1 ether) / totalVader;
    }

    function setupVader(
        IUniswapV2Pair pair,
        IAggregatorV3 oracle,
        uint256 updatePeriod,
        uint256 vaderPrice
    ) external onlyOwner {
        require(
            previousPrices[uint256(Paths.VADER)] == 0,
            "LBTWAP::setupVader: Already Initialized"
        );

        previousPrices[uint256(Paths.VADER)] = vaderPrice;

        _addVaderPair(pair, oracle, updatePeriod);
    }

    // NOTE: Discuss whether minimum paired liquidity value should be enforced at code level
    function addVaderPair(
        IUniswapV2Pair pair,
        IAggregatorV3 oracle,
        uint256 updatePeriod
    ) external onlyOwner {
        require(
            previousPrices[uint256(Paths.VADER)] != 0,
            "LBTWAP::addVaderPair: Vader Uninitialized"
        );

        _addVaderPair(pair, oracle, updatePeriod);
    }

    function _addVaderPair(
        IUniswapV2Pair pair,
        IAggregatorV3 oracle,
        uint256 updatePeriod
    ) internal {
        require(
            updatePeriod != 0,
            "LBTWAP::addVaderPair: Incorrect Update Period"
        );

        require(oracle.decimals() == 8, "LBTWAP::addVaderPair: Non-USD Oracle");

        ExchangePair storage pairData = twapData[address(pair)];

        bool isFirst = pair.token0() == vader;

        (address nativeAsset, address foreignAsset) = isFirst
            ? (pair.token0(), pair.token1())
            : (pair.token1(), pair.token0());

        oracles[foreignAsset] = oracle;

        require(nativeAsset == vader, "LBTWAP::addVaderPair: Unsupported Pair");

        pairData.foreignAsset = foreignAsset;
        pairData.foreignUnit = uint96(
            10**uint256(IERC20Metadata(foreignAsset).decimals())
        );

        pairData.updatePeriod = updatePeriod;
        pairData.lastMeasurement = block.timestamp;

        pairData.nativeTokenPriceCumulative = isFirst
            ? pair.price0CumulativeLast()
            : pair.price1CumulativeLast();

        (uint256 reserve0, uint256 reserve1, ) = pair.getReserves();

        (uint256 reserveNative, uint256 reserveForeign) = isFirst
            ? (reserve0, reserve1)
            : (reserve1, reserve0);

        uint256 pairLiquidityEvaluation = (reserveNative *
            previousPrices[uint256(Paths.VADER)]) +
            (reserveForeign * getChainlinkPrice(foreignAsset));

        pairData.pastLiquidityEvaluation = pairLiquidityEvaluation;

        totalLiquidityWeight[uint256(Paths.VADER)] += pairLiquidityEvaluation;

        vaderPairs.push(pair);

        if (maxUpdateWindow < updatePeriod) maxUpdateWindow = updatePeriod;
    }

    function getUSDVPrice() external returns (uint256) {
        (
            uint256[] memory pastLiquidityWeights,
            uint256 pastTotalLiquidityWeight
        ) = syncUSDVPrice();

        return
            _calculateUSDVPrice(pastLiquidityWeights, pastTotalLiquidityWeight);
    }

    function syncUSDVPrice()
        public
        override
        returns (
            uint256[] memory pastLiquidityWeights,
            uint256 pastTotalLiquidityWeight
        )
    {
        uint256 _totalLiquidityWeight;
        uint256 totalPairs = usdvPairs.length;
        pastLiquidityWeights = new uint256[](totalPairs);
        pastTotalLiquidityWeight = totalLiquidityWeight[uint256(Paths.USDV)];

        for (uint256 i; i < totalPairs; ++i) {
            IERC20 foreignAsset = usdvPairs[i];
            ExchangePair storage pairData = twapData[address(foreignAsset)];
            uint256 timeElapsed = block.timestamp - pairData.lastMeasurement;

            if (timeElapsed < pairData.updatePeriod) continue;

            uint256 pastLiquidityEvaluation = pairData.pastLiquidityEvaluation;
            uint256 currentLiquidityEvaluation = _updateUSDVPrice(
                foreignAsset,
                pairData,
                timeElapsed
            );

            pastLiquidityWeights[i] = pastLiquidityEvaluation;

            pairData.pastLiquidityEvaluation = currentLiquidityEvaluation;

            _totalLiquidityWeight += currentLiquidityEvaluation;
        }

        totalLiquidityWeight[uint256(Paths.USDV)] = _totalLiquidityWeight;
    }

    function _updateUSDVPrice(
        IERC20 foreignAsset,
        ExchangePair storage pairData,
        uint256 timeElapsed
    ) internal returns (uint256 currentLiquidityEvaluation) {
        (uint256 reserveNative, uint256 reserveForeign, ) = vaderPool
            .getReserves(foreignAsset);

        (
            uint256 nativeTokenPriceCumulative,
            ,
            uint256 currentMeasurement
        ) = vaderPool.cumulativePrices(foreignAsset);

        unchecked {
            pairData.nativeTokenPriceAverage = FixedPoint.uq112x112(
                uint224(
                    (nativeTokenPriceCumulative -
                        pairData.nativeTokenPriceCumulative) / timeElapsed
                )
            );
        }

        pairData.nativeTokenPriceCumulative = nativeTokenPriceCumulative;

        pairData.lastMeasurement = currentMeasurement;

        currentLiquidityEvaluation =
            (reserveNative * previousPrices[uint256(Paths.USDV)]) +
            (reserveForeign * getChainlinkPrice(address(foreignAsset)));
    }

    function _calculateUSDVPrice(
        uint256[] memory liquidityWeights,
        uint256 totalUSDVLiquidityWeight
    ) internal view returns (uint256) {
        uint256 totalUSD;
        uint256 totalUSDV;
        uint256 totalPairs = usdvPairs.length;

        for (uint256 i; i < totalPairs; ++i) {
            IERC20 foreignAsset = usdvPairs[i];
            ExchangePair storage pairData = twapData[address(foreignAsset)];

            uint256 foreignPrice = getChainlinkPrice(address(foreignAsset));

            totalUSD +=
                (foreignPrice * liquidityWeights[i]) /
                totalUSDVLiquidityWeight;

            totalUSDV +=
                (pairData
                    .nativeTokenPriceAverage
                    .mul(pairData.foreignUnit)
                    .decode144() * liquidityWeights[i]) /
                totalUSDVLiquidityWeight;
        }

        // NOTE: Accuracy of VADER & USDV is 18 decimals == 1 ether
        return (totalUSD * 1 ether) / totalUSDV;
    }

    function setupUSDV(
        IERC20 foreignAsset,
        IAggregatorV3 oracle,
        uint256 updatePeriod,
        uint256 usdvPrice
    ) external onlyOwner {
        require(
            previousPrices[uint256(Paths.USDV)] == 0,
            "LBTWAP::setupUSDV: Already Initialized"
        );

        previousPrices[uint256(Paths.USDV)] = usdvPrice;

        _addUSDVPair(foreignAsset, oracle, updatePeriod);
    }

    // NOTE: Discuss whether minimum paired liquidity value should be enforced at code level
    function addUSDVPair(
        IERC20 foreignAsset,
        IAggregatorV3 oracle,
        uint256 updatePeriod
    ) external onlyOwner {
        require(
            previousPrices[uint256(Paths.USDV)] != 0,
            "LBTWAP::addUSDVPair: USDV Uninitialized"
        );

        _addUSDVPair(foreignAsset, oracle, updatePeriod);
    }

    function _addUSDVPair(
        IERC20 foreignAsset,
        IAggregatorV3 oracle,
        uint256 updatePeriod
    ) internal {
        require(
            updatePeriod != 0,
            "LBTWAP::addUSDVPair: Incorrect Update Period"
        );

        require(oracle.decimals() == 8, "LBTWAP::addUSDVPair: Non-USD Oracle");

        oracles[address(foreignAsset)] = oracle;

        ExchangePair storage pairData = twapData[address(foreignAsset)];

        // NOTE: Redundant
        // pairData.foreignAsset = foreignAsset;

        pairData.foreignUnit = uint96(
            10**uint256(IERC20Metadata(address(foreignAsset)).decimals())
        );

        pairData.updatePeriod = updatePeriod;
        pairData.lastMeasurement = block.timestamp;

        (uint256 nativeTokenPriceCumulative, , ) = vaderPool.cumulativePrices(
            foreignAsset
        );

        pairData.nativeTokenPriceCumulative = nativeTokenPriceCumulative;

        (uint256 reserveNative, uint256 reserveForeign, ) = vaderPool
            .getReserves(foreignAsset);

        uint256 pairLiquidityEvaluation = (reserveNative *
            previousPrices[uint256(Paths.USDV)]) +
            (reserveForeign * getChainlinkPrice(address(foreignAsset)));

        pairData.pastLiquidityEvaluation = pairLiquidityEvaluation;

        totalLiquidityWeight[uint256(Paths.USDV)] += pairLiquidityEvaluation;

        usdvPairs.push(foreignAsset);

        if (maxUpdateWindow < updatePeriod) maxUpdateWindow = updatePeriod;
    }
}
