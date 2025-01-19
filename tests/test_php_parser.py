"""Tests for PHP parser."""

import pytest
from codeconcat.parser.language_parsers.php_parser import parse_php


def test_parse_php_class():
    """Test parsing PHP classes."""
    code = """<?php
class Person {
    private $name;
    private $age;
    
    public function __construct(string $name, int $age) {
        $this->name = $name;
        $this->age = $age;
    }
    
    public function getName(): string {
        return $this->name;
    }
}

class Employee extends Person {
    private $salary;
    
    public function __construct(string $name, int $age, float $salary) {
        parent::__construct($name, $age);
        $this->salary = $salary;
    }
}
"""
    result = parse_php("test.php", code)
    assert result is not None
    assert len(result.declarations) == 2

    person = next(d for d in result.declarations if d.name == "Person")
    assert person.kind == "class"
    assert person.start_line == 2

    employee = next(d for d in result.declarations if d.name == "Employee")
    assert employee.kind == "class"
    assert employee.start_line == 15


def test_parse_php_interface():
    """Test parsing PHP interfaces."""
    code = """<?php
interface Readable {
    public function read(): string;
}

interface Writable {
    public function write(string $data): void;
}
"""
    result = parse_php("test.php", code)
    assert result is not None
    assert len(result.declarations) == 2

    readable = next(d for d in result.declarations if d.name == "Readable")
    assert readable.kind == "interface"
    assert readable.start_line == 2

    writable = next(d for d in result.declarations if d.name == "Writable")
    assert writable.kind == "interface"
    assert writable.start_line == 6


def test_parse_php_trait():
    """Test parsing PHP traits."""
    code = """<?php
trait Logger {
    private $logFile;
    
    public function log(string $message): void {
        file_put_contents($this->logFile, $message . PHP_EOL, FILE_APPEND);
    }
}

trait Timestampable {
    private $createdAt;
    private $updatedAt;
    
    public function setCreatedAt(): void {
        $this->createdAt = new DateTime();
    }
}
"""
    result = parse_php("test.php", code)
    assert result is not None
    assert len(result.declarations) == 2

    logger = next(d for d in result.declarations if d.name == "Logger")
    assert logger.kind == "trait"
    assert logger.start_line == 2

    timestampable = next(d for d in result.declarations if d.name == "Timestampable")
    assert timestampable.kind == "trait"
    assert timestampable.start_line == 10


def test_parse_php_function():
    """Test parsing PHP functions."""
    code = """<?php
function hello(): void {
    echo "Hello, World!";
}

function add(int $x, int $y): int {
    return $x + $y;
}

// Arrow function
$multiply = fn($x, $y) => $x * $y;
"""
    result = parse_php("test.php", code)
    assert result is not None
    assert len(result.declarations) == 3

    hello = next(d for d in result.declarations if d.name == "hello")
    assert hello.kind == "function"
    assert hello.start_line == 2

    add = next(d for d in result.declarations if d.name == "add")
    assert add.kind == "function"
    assert add.start_line == 6

    multiply = next(d for d in result.declarations if d.name == "multiply")
    assert multiply.kind == "function"
    assert multiply.start_line == 10


def test_parse_php_namespace():
    """Test parsing PHP namespaces."""
    code = """<?php
namespace App\\Models;

class User {
    private $id;
    private $email;
}

namespace App\\Controllers;

class UserController {
    public function index(): array {
        return [];
    }
}
"""
    result = parse_php("test.php", code)
    assert result is not None
    assert len(result.declarations) == 4

    models_ns = next(d for d in result.declarations if d.name == "App\\Models")
    assert models_ns.kind == "namespace"
    assert models_ns.start_line == 2

    user = next(d for d in result.declarations if d.name == "User")
    assert user.kind == "class"
    assert user.start_line == 4

    controllers_ns = next(d for d in result.declarations if d.name == "App\\Controllers")
    assert controllers_ns.kind == "namespace"
    assert controllers_ns.start_line == 9

    controller = next(d for d in result.declarations if d.name == "UserController")
    assert controller.kind == "class"
    assert controller.start_line == 11


def test_parse_php_empty():
    """Test parsing empty PHP file."""
    result = parse_php("test.php", "")
    assert result is not None
    assert len(result.declarations) == 0


def test_parse_php_invalid():
    """Test parsing invalid PHP code."""
    code = """
this is not valid php code
"""
    result = parse_php("test.php", code)
    assert result is not None
    assert len(result.declarations) == 0
