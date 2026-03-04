pragma solidity ^0.8.0;

library Balances {
    using LibMath for int256;
    using LibMath for uint256;
    using PRBMathSD59x18 for int256;
    using PRBMathUD60x18 for uint256;

    uint256 public constant MAX_DECIMALS = 18;

    struct Position {
        int256 quote;
        int256 base;
    }

    struct Trade {
        uint256 price;
        uint256 amount;
        Perpetuals.Side side;
    }

    struct Account {
        Position position;
        uint256 totalLeveragedValue;
        uint256 lastUpdatedIndex;
        uint256 lastUpdatedGasPrice;
    }

    function notionalValue(Position memory position, uint256 price) internal pure returns (uint256) {
        return PRBMathUD60x18.mul(uint256(PRBMathSD59x18.abs(position.base)), price);
    }

    function margin(Position memory position, uint256 price) internal pure returns (int256) {
        int256 signedPrice = LibMath.toInt256(price);
        return position.quote + PRBMathSD59x18.mul(position.base, signedPrice);
    }

    function leveragedNotionalValue(Position memory position, uint256 price) internal pure returns (uint256) {
        uint256 _notionalValue = notionalValue(position, price);
        int256 marginValue = margin(position, price);

        int256 signedNotionalValue = LibMath.toInt256(_notionalValue);

        if (signedNotionalValue - marginValue < 0) {
            return 0;
        } else {
            return uint256(signedNotionalValue - marginValue);
        }
    }

    function minimumMargin(
        Position memory position,
        uint256 price,
        uint256 liquidationGasCost,
        uint256 maximumLeverage
    ) internal pure returns (uint256) {
        if (position.base == 0) {
            return 0;
        }

        uint256 _notionalValue = notionalValue(position, price);

        uint256 adjustedLiquidationGasCost = liquidationGasCost * 6;

        uint256 minimumMarginWithoutGasCost = PRBMathUD60x18.div(_notionalValue, maximumLeverage);

        return adjustedLiquidationGasCost + minimumMarginWithoutGasCost;
    }

    function marginIsValid(
        Balances.Position memory position,
        uint256 liquidationGasCost,
        uint256 price,
        uint256 trueMaxLeverage
    ) internal pure returns (bool) {
        uint256 minMargin = minimumMargin(position, price, liquidationGasCost, trueMaxLeverage);
        int256 _margin = margin(position, price);

        if (_margin < 0) {
            return false;
        }

        return (uint256(_margin) >= minMargin);
    }

    function fillAmount(
        Perpetuals.Order memory orderA,
        uint256 fillA,
        Perpetuals.Order memory orderB,
        uint256 fillB
    ) internal pure returns (uint256) {
        return LibMath.min(orderA.amount - fillA, orderB.amount - fillB);
    }

    function applyTrade(
        Position memory position,
        Trade memory trade,
        uint256 feeRate
    ) internal pure returns (Position memory) {
        int256 signedAmount = LibMath.toInt256(trade.amount);
        int256 signedPrice = LibMath.toInt256(trade.price);
        int256 quoteChange = PRBMathSD59x18.mul(signedAmount, signedPrice);
        int256 fee = getFee(trade.amount, trade.price, feeRate);

        int256 newQuote = 0;
        int256 newBase = 0;

        if (trade.side == Perpetuals.Side.Long) {
            newBase = position.base + signedAmount;
            newQuote = position.quote - quoteChange + fee;
        } else if (trade.side == Perpetuals.Side.Short) {
            newBase = position.base - signedAmount;
            newQuote = position.quote + quoteChange - fee;
        }

        Position memory newPosition = Position(newQuote, newBase);

        return newPosition;
    }

    function getFee(
        uint256 amount,
        uint256 executionPrice,
        uint256 feeRate
    ) internal pure returns (int256) {
        uint256 quoteChange = PRBMathUD60x18.mul(amount, executionPrice);

        int256 fee = PRBMathUD60x18.mul(quoteChange, feeRate).toInt256();
        return fee;
    }

    function tokenToWad(uint256 tokenDecimals, uint256 amount) internal pure returns (int256) {
        uint256 scaler = 10**(MAX_DECIMALS - tokenDecimals);
        return amount.toInt256() * scaler.toInt256();
    }

    function wadToToken(uint256 tokenDecimals, uint256 wadAmount) internal pure returns (uint256) {
        uint256 scaler = uint256(10**(MAX_DECIMALS - tokenDecimals));
        return uint256(wadAmount / scaler);
    }
}
