# file: tests/integration/test_solidity_corpus.py

"""Integration tests for Solidity parser using real-world contract examples."""

import logging
from pathlib import Path
from typing import List

import pytest

from codeconcat.parser.language_parsers.base_tree_sitter_parser import (
    TREE_SITTER_AVAILABLE,
)

if TREE_SITTER_AVAILABLE:
    from codeconcat.parser.language_parsers.tree_sitter_solidity_parser import (
        TreeSitterSolidityParser,
    )

logger = logging.getLogger(__name__)


# Sample contracts for testing
UNISWAP_V2_PAIR_SNIPPET = '''
pragma solidity ^0.8.0;

interface IUniswapV2Pair {
    function mint(address to) external returns (uint liquidity);
    function burn(address to) external returns (uint amount0, uint amount1);
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external;
}

contract UniswapV2Pair is IUniswapV2Pair {
    uint public constant MINIMUM_LIQUIDITY = 10**3;
    bytes4 private constant SELECTOR = bytes4(keccak256(bytes('transfer(address,uint256)')));

    address public factory;
    address public token0;
    address public token1;

    uint112 private reserve0;
    uint112 private reserve1;
    uint32 private blockTimestampLast;

    uint public price0CumulativeLast;
    uint public price1CumulativeLast;
    uint public kLast;

    uint private unlocked = 1;
    modifier lock() {
        require(unlocked == 1, 'LOCKED');
        unlocked = 0;
        _;
        unlocked = 1;
    }

    event Mint(address indexed sender, uint amount0, uint amount1);
    event Burn(address indexed sender, uint amount0, uint amount1, address indexed to);
    event Swap(
        address indexed sender,
        uint amount0In,
        uint amount1In,
        uint amount0Out,
        uint amount1Out,
        address indexed to
    );

    constructor() {
        factory = msg.sender;
    }

    function mint(address to) external lock override returns (uint liquidity) {
        (uint112 _reserve0, uint112 _reserve1,) = getReserves();
        uint balance0 = IERC20(token0).balanceOf(address(this));
        uint balance1 = IERC20(token1).balanceOf(address(this));
        uint amount0 = balance0 - _reserve0;
        uint amount1 = balance1 - _reserve1;

        uint _totalSupply = totalSupply;
        if (_totalSupply == 0) {
            liquidity = sqrt(amount0 * amount1) - MINIMUM_LIQUIDITY;
           _mint(address(0), MINIMUM_LIQUIDITY);
        } else {
            liquidity = min(amount0 * _totalSupply / _reserve0, amount1 * _totalSupply / _reserve1);
        }
        require(liquidity > 0, 'INSUFFICIENT_LIQUIDITY_MINTED');
        _mint(to, liquidity);

        _update(balance0, balance1, _reserve0, _reserve1);
        emit Mint(msg.sender, amount0, amount1);
    }

    function burn(address to) external lock override returns (uint amount0, uint amount1) {
        // Implementation
    }

    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external lock override {
        // Implementation with external call
        if (data.length > 0) IUniswapV2Callee(to).uniswapV2Call(msg.sender, amount0Out, amount1Out, data);
    }

    function getReserves() public view returns (uint112 _reserve0, uint112 _reserve1, uint32 _blockTimestampLast) {
        _reserve0 = reserve0;
        _reserve1 = reserve1;
        _blockTimestampLast = blockTimestampLast;
    }

    function _update(uint balance0, uint balance1, uint112 _reserve0, uint112 _reserve1) private {
        // Update reserves
    }

    function _mint(address to, uint value) private {
        // Mint logic
    }

    function sqrt(uint y) internal pure returns (uint z) {
        if (y > 3) {
            z = y;
            uint x = y / 2 + 1;
            while (x < z) {
                z = x;
                x = (y / x + x) / 2;
            }
        } else if (y != 0) {
            z = 1;
        }
    }

    function min(uint x, uint y) internal pure returns (uint) {
        return x < y ? x : y;
    }

    uint public totalSupply;

    interface IERC20 {
        function balanceOf(address) external view returns (uint);
    }

    interface IUniswapV2Callee {
        function uniswapV2Call(address sender, uint amount0, uint amount1, bytes calldata data) external;
    }
}
'''

OPENZEPPELIN_REENTRANCY_GUARD = '''
pragma solidity ^0.8.0;

abstract contract ReentrancyGuard {
    uint256 private constant _NOT_ENTERED = 1;
    uint256 private constant _ENTERED = 2;

    uint256 private _status;

    constructor() {
        _status = _NOT_ENTERED;
    }

    modifier nonReentrant() {
        _require(_status != _ENTERED, "ReentrancyGuard: reentrant call");
        _status = _ENTERED;
        _;
        _status = _NOT_ENTERED;
    }

    function _require(bool condition, string memory errorMessage) private pure {
        require(condition, errorMessage);
    }
}

contract SecureVault is ReentrancyGuard {
    mapping(address => uint256) private balances;

    event Deposit(address indexed user, uint256 amount);
    event Withdrawal(address indexed user, uint256 amount);

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    function withdraw(uint256 amount) public nonReentrant {
        require(balances[msg.sender] >= amount, "Insufficient balance");

        balances[msg.sender] -= amount;

        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");

        emit Withdrawal(msg.sender, amount);
    }

    function getBalance(address user) public view returns (uint256) {
        return balances[user];
    }
}
'''

VULNERABLE_CONTRACT = '''
pragma solidity ^0.8.0;

contract VulnerableBank {
    mapping(address => uint256) public balances;
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    // Vulnerable to reentrancy
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient funds");

        // Vulnerable: state change after external call
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");

        balances[msg.sender] -= amount;
    }

    // Uses deprecated suicide
    function destroyContract() public {
        require(msg.sender == owner, "Only owner");
        suicide(payable(owner));
    }

    // Dangerous delegatecall
    function delegateOperation(address target, bytes memory data) public {
        require(msg.sender == owner, "Only owner");
        (bool success, ) = target.delegatecall(data);
        require(success, "Delegate call failed");
    }

    // Uses assembly for low-level operations
    function getCodeSize(address account) public view returns (uint256 size) {
        assembly {
            size := extcodesize(account)
        }
    }
}
'''

ERC20_TOKEN = '''
pragma solidity ^0.8.0;

interface IERC20 {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
}

contract ERC20Token is IERC20 {
    mapping(address => uint256) private _balances;
    mapping(address => mapping(address => uint256)) private _allowances;

    uint256 private _totalSupply;

    string public name;
    string public symbol;
    uint8 public decimals;

    constructor(string memory _name, string memory _symbol) {
        name = _name;
        symbol = _symbol;
        decimals = 18;
        _totalSupply = 1000000 * 10**uint256(decimals);
        _balances[msg.sender] = _totalSupply;
        emit Transfer(address(0), msg.sender, _totalSupply);
    }

    function totalSupply() public view override returns (uint256) {
        return _totalSupply;
    }

    function balanceOf(address account) public view override returns (uint256) {
        return _balances[account];
    }

    function transfer(address recipient, uint256 amount) public override returns (bool) {
        _transfer(msg.sender, recipient, amount);
        return true;
    }

    function allowance(address owner, address spender) public view override returns (uint256) {
        return _allowances[owner][spender];
    }

    function approve(address spender, uint256 amount) public override returns (bool) {
        _approve(msg.sender, spender, amount);
        return true;
    }

    function transferFrom(address sender, address recipient, uint256 amount) public override returns (bool) {
        uint256 currentAllowance = _allowances[sender][msg.sender];
        require(currentAllowance >= amount, "ERC20: transfer amount exceeds allowance");

        _transfer(sender, recipient, amount);
        _approve(sender, msg.sender, currentAllowance - amount);

        return true;
    }

    function _transfer(address sender, address recipient, uint256 amount) internal virtual {
        require(sender != address(0), "ERC20: transfer from the zero address");
        require(recipient != address(0), "ERC20: transfer to the zero address");

        uint256 senderBalance = _balances[sender];
        require(senderBalance >= amount, "ERC20: transfer amount exceeds balance");

        _balances[sender] = senderBalance - amount;
        _balances[recipient] += amount;

        emit Transfer(sender, recipient, amount);
    }

    function _approve(address owner, address spender, uint256 amount) internal virtual {
        require(owner != address(0), "ERC20: approve from the zero address");
        require(spender != address(0), "ERC20: approve to the zero address");

        _allowances[owner][spender] = amount;
        emit Approval(owner, spender, amount);
    }
}
'''

LIBRARY_EXAMPLE = '''
pragma solidity ^0.8.0;

library SafeMath {
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        uint256 c = a + b;
        require(c >= a, "SafeMath: addition overflow");
        return c;
    }

    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b <= a, "SafeMath: subtraction underflow");
        return a - b;
    }

    function mul(uint256 a, uint256 b) internal pure returns (uint256) {
        if (a == 0) return 0;
        uint256 c = a * b;
        require(c / a == b, "SafeMath: multiplication overflow");
        return c;
    }

    function div(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b > 0, "SafeMath: division by zero");
        return a / b;
    }
}

contract Calculator {
    using SafeMath for uint256;

    function calculate(uint256 a, uint256 b) public pure returns (uint256) {
        uint256 sum = a.add(b);
        uint256 product = sum.mul(2);
        return product.div(2);
    }
}
'''


@pytest.mark.skipif(
    not TREE_SITTER_AVAILABLE, reason="tree-sitter not available"
)
class TestSolidityCorpus:
    """Test Solidity parser against real-world contract patterns."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = TreeSitterSolidityParser()

    def test_uniswap_v2_pair_parsing(self):
        """Test parsing Uniswap V2 pair contract patterns."""
        result = self.parser.parse(UNISWAP_V2_PAIR_SNIPPET)

        assert not result.errors

        # Check interface parsing
        interfaces = [d for d in result.declarations if d.type == "interface"]
        assert len(interfaces) >= 1
        assert any(i.name == "IUniswapV2Pair" for i in interfaces)

        # Check contract with inheritance
        contracts = [d for d in result.declarations if d.type == "class"]
        assert len(contracts) >= 1
        uniswap_pair = next((c for c in contracts if c.name == "UniswapV2Pair"), None)
        assert uniswap_pair is not None

        # Check events
        events = [d for d in result.declarations if d.type == "event"]
        assert len(events) >= 3
        event_names = {e.name for e in events}
        assert "Mint" in event_names
        assert "Burn" in event_names
        assert "Swap" in event_names

        # Check modifier (lock)
        modifiers = [d for d in result.declarations if d.type == "modifier"]
        assert len(modifiers) >= 1
        assert any(m.name == "lock" for m in modifiers)

        # Check functions with modifiers
        functions = [d for d in result.declarations if d.type == "function"]
        lock_functions = [
            f for f in functions
            if f.metadata and "modifiers" in f.metadata and "lock" in f.metadata["modifiers"]
        ]
        assert len(lock_functions) >= 2  # mint, burn, swap should have lock

    def test_openzeppelin_reentrancy_guard(self):
        """Test parsing OpenZeppelin ReentrancyGuard pattern."""
        result = self.parser.parse(OPENZEPPELIN_REENTRANCY_GUARD)

        assert not result.errors

        # Check abstract contract
        contracts = [d for d in result.declarations if d.type == "class"]
        assert len(contracts) >= 2
        assert any(c.name == "ReentrancyGuard" for c in contracts)
        assert any(c.name == "SecureVault" for c in contracts)

        # Check nonReentrant modifier
        modifiers = [d for d in result.declarations if d.type == "modifier"]
        assert len(modifiers) >= 1
        assert any(m.name == "nonReentrant" for m in modifiers)

        # Check function with nonReentrant modifier
        functions = [d for d in result.declarations if d.type == "function"]
        withdraw_func = next((f for f in functions if f.name == "withdraw"), None)
        assert withdraw_func is not None
        if withdraw_func.metadata and "modifiers" in withdraw_func.metadata:
            assert "nonReentrant" in withdraw_func.metadata["modifiers"]

        # Check security patterns - should identify external call
        if result.metadata and "external_calls" in result.metadata:
            assert len(result.metadata["external_calls"]) > 0

    def test_vulnerable_contract_detection(self):
        """Test detection of vulnerable patterns."""
        result = self.parser.parse(VULNERABLE_CONTRACT)

        assert not result.errors

        # Check security pattern detection
        assert result.metadata is not None
        assert "security_patterns" in result.metadata

        patterns = result.metadata["security_patterns"]

        # Should detect deprecated suicide
        assert any("suicide" in p.lower() for p in patterns)

        # Should detect delegatecall
        assert any("delegatecall" in p.lower() for p in patterns)

        # Should detect assembly block
        assert any("assembly" in p.lower() for p in patterns)

        # Should detect external calls
        if "external_calls" in result.metadata:
            assert len(result.metadata["external_calls"]) > 0

        # Check pattern counts
        if "pattern_counts" in result.metadata:
            counts = result.metadata["pattern_counts"]
            assert counts.get("suicide_call", 0) >= 1
            assert counts.get("delegatecall_usage", 0) >= 1
            assert counts.get("assembly_block", 0) >= 1

    def test_erc20_token_parsing(self):
        """Test parsing standard ERC20 token implementation."""
        result = self.parser.parse(ERC20_TOKEN)

        assert not result.errors

        # Check interface
        interfaces = [d for d in result.declarations if d.type == "interface"]
        assert len(interfaces) == 1
        assert interfaces[0].name == "IERC20"

        # Check contract with interface implementation
        contracts = [d for d in result.declarations if d.type == "class"]
        assert len(contracts) == 1
        assert contracts[0].name == "ERC20Token"

        # Check events
        events = [d for d in result.declarations if d.type == "event"]
        assert len(events) >= 2
        event_names = {e.name for e in events}
        assert "Transfer" in event_names
        assert "Approval" in event_names

        # Check all interface functions are implemented
        functions = [d for d in result.declarations if d.type == "function"]
        function_names = {f.name for f in functions}
        required_functions = {
            "totalSupply", "balanceOf", "transfer",
            "allowance", "approve", "transferFrom"
        }
        assert required_functions.issubset(function_names)

        # Check constructor
        constructors = [d for d in result.declarations if d.type == "constructor"]
        assert len(constructors) == 1

    def test_library_usage_parsing(self):
        """Test parsing library declarations and usage."""
        result = self.parser.parse(LIBRARY_EXAMPLE)

        assert not result.errors

        # Check library
        libraries = [d for d in result.declarations if d.type == "library"]
        assert len(libraries) == 1
        assert libraries[0].name == "SafeMath"

        # Check library functions
        functions = [d for d in result.declarations if d.type == "function"]
        library_functions = ["add", "sub", "mul", "div", "calculate"]
        function_names = {f.name for f in functions}
        for func in library_functions:
            assert func in function_names

        # Check contract using library
        contracts = [d for d in result.declarations if d.type == "class"]
        assert len(contracts) == 1
        assert contracts[0].name == "Calculator"

    def test_parse_accuracy_metrics(self):
        """Test overall parsing accuracy on corpus."""
        test_contracts = [
            ("Uniswap", UNISWAP_V2_PAIR_SNIPPET),
            ("ReentrancyGuard", OPENZEPPELIN_REENTRANCY_GUARD),
            ("Vulnerable", VULNERABLE_CONTRACT),
            ("ERC20", ERC20_TOKEN),
            ("Library", LIBRARY_EXAMPLE),
        ]

        total_contracts = len(test_contracts)
        successful_parses = 0
        total_declarations = 0
        parse_errors = []

        for name, contract_code in test_contracts:
            try:
                result = self.parser.parse(contract_code)

                if not result.errors:
                    successful_parses += 1
                    total_declarations += len(result.declarations)
                else:
                    parse_errors.append((name, result.errors))

            except Exception as e:
                parse_errors.append((name, str(e)))

        # Calculate accuracy
        parse_accuracy = (successful_parses / total_contracts) * 100

        # Log results
        logger.info(f"Parse accuracy: {parse_accuracy:.1f}%")
        logger.info(f"Successfully parsed: {successful_parses}/{total_contracts}")
        logger.info(f"Total declarations extracted: {total_declarations}")

        if parse_errors:
            for name, errors in parse_errors:
                logger.warning(f"Parse errors in {name}: {errors}")

        # Assert minimum accuracy threshold (97% as per requirements)
        assert parse_accuracy >= 97, f"Parse accuracy {parse_accuracy}% below 97% threshold"

    def test_security_pattern_detection_accuracy(self):
        """Test accuracy of security pattern detection."""
        # Known patterns in vulnerable contract
        known_patterns = {
            "suicide_call": 1,  # One suicide call
            "delegatecall_usage": 1,  # One delegatecall
            "assembly_block": 1,  # One assembly block
            "external_call": 1,  # At least one external call
        }

        result = self.parser.parse(VULNERABLE_CONTRACT)

        assert not result.errors
        assert result.metadata is not None

        detected_patterns = result.metadata.get("pattern_counts", {})

        # Calculate detection accuracy
        detected_count = 0
        expected_count = len(known_patterns)

        for pattern, expected_min in known_patterns.items():
            if pattern == "external_call":
                # External calls tracked differently
                if "external_calls" in result.metadata:
                    if len(result.metadata["external_calls"]) >= expected_min:
                        detected_count += 1
            else:
                actual = detected_patterns.get(pattern, 0)
                if actual >= expected_min:
                    detected_count += 1

        detection_rate = (detected_count / expected_count) * 100

        logger.info(f"Security pattern detection rate: {detection_rate:.1f}%")

        # Note: We aim for high detection but acknowledge syntactic limitations
        # as per consensus feedback - focusing on flagging patterns for review
        assert detection_rate >= 75, f"Detection rate {detection_rate}% below minimum threshold"
