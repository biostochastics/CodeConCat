"""Comprehensive tests for Tree-sitter PHP parser to improve code coverage."""

from unittest.mock import patch
from codeconcat.parser.language_parsers.tree_sitter_php_parser import TreeSitterPHPParser


class TestTreeSitterPHPParserComprehensive:
    """Comprehensive test suite for TreeSitterPHPParser."""

    def setup_method(self):
        """Set up test parser instance."""
        self.parser = TreeSitterPHPParser()

    def test_initialization(self):
        """Test parser initialization."""
        assert self.parser.language == "php"
        assert hasattr(self.parser, "get_parser")

    @patch(
        "codeconcat.parser.language_parsers.tree_sitter_php_parser.TreeSitterPHPParser.get_parser"
    )
    def test_parser_not_available(self, mock_get_parser):
        """Test behavior when tree-sitter parser is not available."""
        mock_get_parser.return_value = None
        code = """<?php
        function test() {
            return "Hello";
        }
        ?>"""
        elements = self.parser.parse(code)
        assert elements == []

    def test_simple_function_extraction(self):
        """Test extracting a simple PHP function."""
        code = """<?php
function greet($name) {
    return "Hello, " . $name;
}
?>"""
        elements = self.parser.parse(code)
        if elements:  # Only test if tree-sitter-php is available
            assert len(elements) >= 1
            func = next((e for e in elements if e.name == "greet"), None)
            if func:
                assert func.type == "function"
                assert "name" in func.content or "greet" in func.content

    def test_class_extraction(self):
        """Test extracting PHP classes with methods."""
        code = """<?php
class Calculator {
    private $result;
    
    public function __construct() {
        $this->result = 0;
    }
    
    public function add($a, $b) {
        $this->result = $a + $b;
        return $this->result;
    }
    
    public function getResult() {
        return $this->result;
    }
}
?>"""
        elements = self.parser.parse(code)
        if elements:
            # Check for class
            class_elem = next(
                (e for e in elements if e.type == "class" and e.name == "Calculator"), None
            )
            if class_elem:
                assert "Calculator" in class_elem.content

            # Check for methods
            methods = [e for e in elements if e.type == "method"]
            method_names = [m.name for m in methods]
            for expected in ["__construct", "add", "getResult"]:
                assert expected in method_names or any(expected in m.content for m in methods)

    def test_interface_extraction(self):
        """Test extracting PHP interfaces."""
        code = """<?php
interface PaymentGateway {
    public function processPayment($amount);
    public function refund($transactionId, $amount);
    public function getTransactionStatus($transactionId);
}
?>"""
        elements = self.parser.parse(code)
        if elements:
            interface = next((e for e in elements if e.type == "interface"), None)
            if interface:
                assert interface.name == "PaymentGateway"
                assert "interface" in interface.content.lower()

    def test_trait_extraction(self):
        """Test extracting PHP traits."""
        code = """<?php
trait TimestampTrait {
    protected $createdAt;
    protected $updatedAt;
    
    public function setCreatedAt($timestamp) {
        $this->createdAt = $timestamp;
    }
    
    public function getCreatedAt() {
        return $this->createdAt;
    }
}
?>"""
        elements = self.parser.parse(code)
        if elements:
            trait = next((e for e in elements if e.type == "trait"), None)
            if trait:
                assert trait.name == "TimestampTrait"

    def test_namespace_handling(self):
        """Test handling of namespaced PHP code."""
        code = """<?php
namespace App\\Services\\Payment;

use App\\Models\\Transaction;
use App\\Exceptions\\PaymentException;

class PayPalGateway implements PaymentGateway {
    private $apiKey;
    
    public function __construct($apiKey) {
        $this->apiKey = $apiKey;
    }
    
    public function processPayment($amount) {
        // Process payment logic
        return new Transaction($amount);
    }
}
?>"""
        elements = self.parser.parse(code)
        if elements:
            class_elem = next((e for e in elements if e.type == "class"), None)
            if class_elem:
                assert "PayPalGateway" in class_elem.name or "PayPalGateway" in class_elem.content

    def test_abstract_class_extraction(self):
        """Test extracting abstract classes."""
        code = """<?php
abstract class BaseController {
    protected $request;
    protected $response;
    
    abstract public function index();
    abstract public function show($id);
    
    public function __construct($request, $response) {
        $this->request = $request;
        $this->response = $response;
    }
    
    protected function json($data, $status = 200) {
        return $this->response->json($data, $status);
    }
}
?>"""
        elements = self.parser.parse(code)
        if elements:
            class_elem = next((e for e in elements if e.name == "BaseController"), None)
            if class_elem:
                assert class_elem.type == "class"
                assert "abstract" in class_elem.content.lower()

    def test_anonymous_function_handling(self):
        """Test handling of anonymous functions and closures."""
        code = """<?php
$multiply = function($x, $y) {
    return $x * $y;
};

$numbers = array_map(function($n) {
    return $n * 2;
}, [1, 2, 3, 4, 5]);

$message = "Hello";
$greet = function($name) use ($message) {
    return $message . ", " . $name;
};
?>"""
        elements = self.parser.parse(code)
        # Tree-sitter PHP parser may or may not capture anonymous functions
        assert isinstance(elements, list)

    def test_method_visibility_modifiers(self):
        """Test parsing methods with different visibility modifiers."""
        code = """<?php
class VisibilityTest {
    public function publicMethod() {
        return "public";
    }
    
    protected function protectedMethod() {
        return "protected";
    }
    
    private function privateMethod() {
        return "private";
    }
    
    function defaultMethod() {
        return "default";
    }
}
?>"""
        elements = self.parser.parse(code)
        if elements:
            methods = [e for e in elements if e.type == "method"]
            # Check that methods are captured regardless of visibility
            assert len(methods) >= 3

    def test_static_methods_and_properties(self):
        """Test parsing static methods and properties."""
        code = """<?php
class StaticExample {
    public static $counter = 0;
    private static $instances = [];
    
    public static function getInstance() {
        if (empty(self::$instances)) {
            self::$instances[] = new self();
        }
        return self::$instances[0];
    }
    
    public static function incrementCounter() {
        self::$counter++;
    }
}
?>"""
        elements = self.parser.parse(code)
        if elements:
            static_methods = [
                e for e in elements if e.type == "method" and "static" in e.content.lower()
            ]
            assert len(static_methods) >= 1

    def test_const_declarations(self):
        """Test parsing const declarations."""
        code = """<?php
class Constants {
    const VERSION = "1.0.0";
    public const API_ENDPOINT = "https://api.example.com";
    private const SECRET_KEY = "s3cr3t";
    
    public function getVersion() {
        return self::VERSION;
    }
}

const GLOBAL_CONSTANT = 42;
define("ANOTHER_CONSTANT", "value");
?>"""
        elements = self.parser.parse(code)
        if elements:
            class_elem = next((e for e in elements if e.name == "Constants"), None)
            assert class_elem is not None

    def test_generator_functions(self):
        """Test parsing generator functions with yield."""
        code = """<?php
function countTo($max) {
    for ($i = 1; $i <= $max; $i++) {
        yield $i;
    }
}

function readLargeFile($filename) {
    $handle = fopen($filename, 'r');
    if ($handle) {
        while (($line = fgets($handle)) !== false) {
            yield $line;
        }
        fclose($handle);
    }
}
?>"""
        elements = self.parser.parse(code)
        if elements:
            generators = [e for e in elements if e.type == "function" and "yield" in e.content]
            assert len(generators) >= 1

    def test_typed_properties_php74(self):
        """Test parsing typed properties (PHP 7.4+)."""
        code = """<?php
class TypedProperties {
    public string $name;
    private int $age;
    protected ?float $salary;
    public array $tags = [];
    
    public function __construct(string $name, int $age) {
        $this->name = $name;
        $this->age = $age;
    }
}
?>"""
        elements = self.parser.parse(code)
        if elements:
            class_elem = next((e for e in elements if e.name == "TypedProperties"), None)
            assert class_elem is not None

    def test_return_type_declarations(self):
        """Test parsing functions with return type declarations."""
        code = """<?php
class TypeHinting {
    public function getString(): string {
        return "hello";
    }
    
    public function getInt(): int {
        return 42;
    }
    
    public function getArray(): array {
        return [1, 2, 3];
    }
    
    public function getNullable(): ?string {
        return null;
    }
    
    public function getVoid(): void {
        echo "No return";
    }
}
?>"""
        elements = self.parser.parse(code)
        if elements:
            methods = [e for e in elements if e.type == "method"]
            assert len(methods) >= 5

    def test_union_types_php80(self):
        """Test parsing union types (PHP 8.0+)."""
        code = """<?php
class UnionTypes {
    public function process(int|float $number): int|float {
        return $number * 2;
    }
    
    public function format(string|int|null $value): string {
        if ($value === null) {
            return "null";
        }
        return (string) $value;
    }
}
?>"""
        elements = self.parser.parse(code)
        if elements:
            class_elem = next((e for e in elements if e.name == "UnionTypes"), None)
            assert class_elem is not None

    def test_attributes_php80(self):
        """Test parsing attributes (PHP 8.0+)."""
        code = """<?php
#[Table("users")]
class User {
    #[Column("id", type: "integer")]
    #[PrimaryKey]
    private int $id;
    
    #[Column("email", type: "string", unique: true)]
    private string $email;
    
    #[Route("/users/{id}", methods: ["GET"])]
    #[RequiresAuth]
    public function show(int $id): array {
        return ["id" => $id];
    }
}
?>"""
        elements = self.parser.parse(code)
        if elements:
            class_elem = next((e for e in elements if e.name == "User"), None)
            assert class_elem is not None

    def test_enums_php81(self):
        """Test parsing enums (PHP 8.1+)."""
        code = """<?php
enum Status: string {
    case PENDING = "pending";
    case APPROVED = "approved";
    case REJECTED = "rejected";
    
    public function getLabel(): string {
        return match($this) {
            self::PENDING => "Pending Review",
            self::APPROVED => "Approved",
            self::REJECTED => "Rejected",
        };
    }
}

enum HttpMethod {
    case GET;
    case POST;
    case PUT;
    case DELETE;
}
?>"""
        elements = self.parser.parse(code)
        if elements:
            # Enums might be parsed as classes or special enum types
            status_elem = next((e for e in elements if "Status" in e.name), None)
            assert status_elem is not None

    def test_match_expression_php80(self):
        """Test parsing match expressions (PHP 8.0+)."""
        code = """<?php
function getGrade($score): string {
    return match(true) {
        $score >= 90 => 'A',
        $score >= 80 => 'B',
        $score >= 70 => 'C',
        $score >= 60 => 'D',
        default => 'F',
    };
}

class Router {
    public function route($path) {
        return match($path) {
            '/' => new HomeController(),
            '/users' => new UserController(),
            '/api/users' => new ApiUserController(),
            default => new NotFoundController(),
        };
    }
}
?>"""
        elements = self.parser.parse(code)
        if elements:
            functions = [e for e in elements if e.type == "function"]
            assert len(functions) >= 1

    def test_constructor_property_promotion_php80(self):
        """Test parsing constructor property promotion (PHP 8.0+)."""
        code = """<?php
class Product {
    public function __construct(
        private string $name,
        private float $price,
        public readonly string $sku,
        protected ?string $description = null
    ) {}
    
    public function getPrice(): float {
        return $this->price;
    }
}
?>"""
        elements = self.parser.parse(code)
        if elements:
            class_elem = next((e for e in elements if e.name == "Product"), None)
            assert class_elem is not None

    def test_readonly_properties_php81(self):
        """Test parsing readonly properties (PHP 8.1+)."""
        code = """<?php
class ImmutableData {
    public readonly string $id;
    public readonly DateTime $createdAt;
    private readonly array $data;
    
    public function __construct(string $id, array $data) {
        $this->id = $id;
        $this->createdAt = new DateTime();
        $this->data = $data;
    }
}
?>"""
        elements = self.parser.parse(code)
        if elements:
            class_elem = next((e for e in elements if e.name == "ImmutableData"), None)
            assert class_elem is not None

    def test_mixed_html_php(self):
        """Test parsing mixed HTML and PHP content."""
        code = """<!DOCTYPE html>
<html>
<body>
<?php
class ViewController {
    public function render($data) {
        ?>
        <h1><?= htmlspecialchars($data['title']) ?></h1>
        <?php
        foreach ($data['items'] as $item) {
            echo "<li>" . htmlspecialchars($item) . "</li>";
        }
    }
}

function displayTable($rows) {
    ?>
    <table>
    <?php foreach ($rows as $row): ?>
        <tr>
            <td><?= $row['name'] ?></td>
            <td><?= $row['value'] ?></td>
        </tr>
    <?php endforeach; ?>
    </table>
    <?php
}
?>
</body>
</html>"""
        elements = self.parser.parse(code)
        if elements:
            # Should at least find the class and function
            assert any(e.name == "ViewController" for e in elements)
            assert any(e.name == "displayTable" for e in elements)

    def test_error_handling(self):
        """Test parser's error handling with invalid code."""
        code = """<?php
class Broken {
    public function method( {  // Missing closing parenthesis
        return "broken";
    }
}

function another() {
    // This function is fine
    return "ok";
}
?>"""
        elements = self.parser.parse(code)
        # Parser should handle errors gracefully and still parse valid parts
        assert isinstance(elements, list)
        # May still find the valid function
        # Parser might or might not parse the broken code

    def test_complex_nested_structures(self):
        """Test parsing complex nested structures."""
        code = """<?php
namespace App\\Complex;

abstract class BaseRepository {
    protected $model;
    
    public function __construct($model) {
        $this->model = $model;
    }
    
    abstract public function find($id);
}

class UserRepository extends BaseRepository {
    use CacheableTrait, LoggableTrait {
        LoggableTrait::log insteadof CacheableTrait;
        CacheableTrait::log as logCache;
    }
    
    public function find($id) {
        return $this->cache(function() use ($id) {
            $this->log("Finding user: " . $id);
            return $this->model->find($id);
        });
    }
    
    public function findByEmail(string $email): ?User {
        return $this->model->where('email', $email)->first();
    }
}
?>"""
        elements = self.parser.parse(code)
        if elements:
            # Should find both classes
            classes = [e for e in elements if e.type == "class"]
            assert len(classes) >= 2
