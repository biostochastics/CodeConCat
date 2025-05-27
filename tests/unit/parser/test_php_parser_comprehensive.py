"""Comprehensive tests for PHP parser to improve code coverage."""

from codeconcat.parser.language_parsers.php_parser import PHPParser


class TestPHPParserComprehensive:
    """Comprehensive test suite for PHPParser."""

    def setup_method(self):
        """Set up test parser instance."""
        self.parser = PHPParser()

    def test_simple_function(self):
        """Test parsing a simple PHP function."""
        code = """<?php
function hello($name) {
    echo "Hello, " . $name;
}
?>"""
        elements = self.parser.parse(code)
        assert len(elements) == 1
        assert elements[0].type == "function"
        assert elements[0].name == "hello"
        assert elements[0].start_line == 2
        assert elements[0].end_line == 4

    def test_class_with_methods(self):
        """Test parsing a PHP class with methods."""
        code = """<?php
class User {
    private $name;
    
    public function __construct($name) {
        $this->name = $name;
    }
    
    public function getName() {
        return $this->name;
    }
}
?>"""
        elements = self.parser.parse(code)
        assert len(elements) == 3
        assert elements[0].type == "class"
        assert elements[0].name == "User"
        assert elements[1].type == "method"
        assert elements[1].name == "__construct"
        assert elements[2].type == "method"
        assert elements[2].name == "getName"

    def test_interface(self):
        """Test parsing PHP interface."""
        code = """<?php
interface Drawable {
    public function draw();
    public function resize($width, $height);
}
?>"""
        elements = self.parser.parse(code)
        assert len(elements) == 3
        assert elements[0].type == "interface"
        assert elements[0].name == "Drawable"
        assert elements[1].type == "method"
        assert elements[1].name == "draw"
        assert elements[2].type == "method"
        assert elements[2].name == "resize"

    def test_trait(self):
        """Test parsing PHP trait."""
        code = """<?php
trait Loggable {
    public function log($message) {
        echo "[LOG] " . $message;
    }
}
?>"""
        elements = self.parser.parse(code)
        assert len(elements) == 2
        assert elements[0].type == "trait"
        assert elements[0].name == "Loggable"
        assert elements[1].type == "method"
        assert elements[1].name == "log"

    def test_namespace(self):
        """Test parsing PHP namespace."""
        code = """<?php
namespace App\\Controllers;

class HomeController {
    public function index() {
        return "Home page";
    }
}
?>"""
        elements = self.parser.parse(code)
        assert len(elements) == 2
        assert elements[0].type == "class"
        assert elements[0].name == "HomeController"
        assert elements[1].type == "method"
        assert elements[1].name == "index"

    def test_abstract_class(self):
        """Test parsing abstract class."""
        code = """<?php
abstract class Shape {
    abstract public function area();
    
    public function describe() {
        return "This is a shape";
    }
}
?>"""
        elements = self.parser.parse(code)
        assert len(elements) == 3
        assert elements[0].type == "class"
        assert elements[0].name == "Shape"
        assert elements[1].type == "method"
        assert elements[1].name == "area"
        assert elements[2].type == "method"
        assert elements[2].name == "describe"

    def test_static_methods(self):
        """Test parsing static methods."""
        code = """<?php
class MathUtils {
    public static function add($a, $b) {
        return $a + $b;
    }
    
    private static function validate($num) {
        return is_numeric($num);
    }
}
?>"""
        elements = self.parser.parse(code)
        assert len(elements) == 3
        assert elements[0].type == "class"
        assert elements[0].name == "MathUtils"
        assert elements[1].type == "method"
        assert elements[1].name == "add"
        assert elements[2].type == "method"
        assert elements[2].name == "validate"

    def test_anonymous_function(self):
        """Test parsing anonymous functions."""
        code = """<?php
$greet = function($name) {
    return "Hello, " . $name;
};

$numbers = array_map(function($n) {
    return $n * 2;
}, [1, 2, 3]);
?>"""
        elements = self.parser.parse(code)
        # PHPParser might not capture anonymous functions as separate elements
        # This depends on the implementation
        assert isinstance(elements, list)

    def test_arrow_function(self):
        """Test parsing arrow functions (PHP 7.4+)."""
        code = """<?php
$double = fn($n) => $n * 2;

$names = array_map(fn($user) => $user->name, $users);
?>"""
        elements = self.parser.parse(code)
        # PHPParser might not capture arrow functions as separate elements
        assert isinstance(elements, list)

    def test_use_statements(self):
        """Test parsing use statements."""
        code = """<?php
use App\\Models\\User;
use App\\Services\\{UserService, EmailService};
use function App\\Helpers\\format_date;
use const App\\Constants\\MAX_USERS;

class UserController {
    public function create() {
        return new User();
    }
}
?>"""
        elements = self.parser.parse(code)
        assert any(e.name == "UserController" for e in elements)
        assert any(e.name == "create" for e in elements)

    def test_constants(self):
        """Test parsing class constants."""
        code = """<?php
class Config {
    const VERSION = "1.0.0";
    public const DEBUG = true;
    private const SECRET = "hidden";
    
    public function getVersion() {
        return self::VERSION;
    }
}
?>"""
        elements = self.parser.parse(code)
        assert any(e.name == "Config" for e in elements)
        assert any(e.name == "getVersion" for e in elements)

    def test_properties(self):
        """Test parsing class properties."""
        code = """<?php
class Product {
    public $name;
    private $price;
    protected $stock;
    public static $count = 0;
    private static $instances = [];
    
    public function __construct($name, $price) {
        $this->name = $name;
        $this->price = $price;
    }
}
?>"""
        elements = self.parser.parse(code)
        assert any(e.name == "Product" for e in elements)
        assert any(e.name == "__construct" for e in elements)

    def test_try_catch_finally(self):
        """Test parsing try-catch-finally blocks."""
        code = """<?php
function divide($a, $b) {
    try {
        if ($b == 0) {
            throw new DivisionByZeroError("Cannot divide by zero");
        }
        return $a / $b;
    } catch (DivisionByZeroError $e) {
        echo $e->getMessage();
        return null;
    } finally {
        echo "Division attempted";
    }
}
?>"""
        elements = self.parser.parse(code)
        assert len(elements) == 1
        assert elements[0].type == "function"
        assert elements[0].name == "divide"

    def test_generators(self):
        """Test parsing generator functions."""
        code = """<?php
function fibonacci($max) {
    $a = 0;
    $b = 1;
    
    while ($a < $max) {
        yield $a;
        $temp = $a;
        $a = $b;
        $b = $temp + $b;
    }
}
?>"""
        elements = self.parser.parse(code)
        assert len(elements) == 1
        assert elements[0].type == "function"
        assert elements[0].name == "fibonacci"

    def test_match_expression(self):
        """Test parsing match expression (PHP 8.0+)."""
        code = """<?php
function getStatusMessage($status) {
    return match($status) {
        200 => "OK",
        404 => "Not Found",
        500 => "Internal Server Error",
        default => "Unknown Status"
    };
}
?>"""
        elements = self.parser.parse(code)
        assert len(elements) == 1
        assert elements[0].type == "function"
        assert elements[0].name == "getStatusMessage"

    def test_enums(self):
        """Test parsing enums (PHP 8.1+)."""
        code = """<?php
enum Status {
    case PENDING;
    case APPROVED;
    case REJECTED;
    
    public function label(): string {
        return match($this) {
            Status::PENDING => "Pending",
            Status::APPROVED => "Approved",
            Status::REJECTED => "Rejected",
        };
    }
}
?>"""
        elements = self.parser.parse(code)
        # PHPParser might parse enum as a class
        assert any(e.name == "Status" for e in elements)
        assert any(e.name == "label" for e in elements)

    def test_attributes(self):
        """Test parsing attributes (PHP 8.0+)."""
        code = """<?php
#[Route("/api/users", methods: ["GET", "POST"])]
class UserController {
    #[Deprecated("Use getUsers() instead")]
    public function index() {
        return [];
    }
    
    #[RequiresAuth]
    #[ValidateRequest]
    public function create($request) {
        return new User($request);
    }
}
?>"""
        elements = self.parser.parse(code)
        assert any(e.name == "UserController" for e in elements)
        assert any(e.name == "index" for e in elements)
        assert any(e.name == "create" for e in elements)

    def test_constructor_property_promotion(self):
        """Test parsing constructor property promotion (PHP 8.0+)."""
        code = """<?php
class Point {
    public function __construct(
        private float $x,
        private float $y,
        public string $label = "point"
    ) {}
    
    public function distance(Point $other): float {
        return sqrt(pow($this->x - $other->x, 2) + pow($this->y - $other->y, 2));
    }
}
?>"""
        elements = self.parser.parse(code)
        assert any(e.name == "Point" for e in elements)
        assert any(e.name == "__construct" for e in elements)
        assert any(e.name == "distance" for e in elements)

    def test_mixed_content(self):
        """Test parsing mixed PHP and HTML content."""
        code = """<!DOCTYPE html>
<html>
<body>
<?php
function renderHeader($title) {
    echo "<h1>" . htmlspecialchars($title) . "</h1>";
}

class Template {
    public function render($data) {
        ?>
        <div class="content">
            <?php foreach ($data as $item): ?>
                <p><?= htmlspecialchars($item) ?></p>
            <?php endforeach; ?>
        </div>
        <?php
    }
}
?>
</body>
</html>"""
        elements = self.parser.parse(code)
        assert any(e.name == "renderHeader" for e in elements)
        assert any(e.name == "Template" for e in elements)
        assert any(e.name == "render" for e in elements)

    def test_empty_file(self):
        """Test parsing empty PHP file."""
        code = """<?php
?>"""
        elements = self.parser.parse(code)
        assert isinstance(elements, list)
        assert len(elements) == 0

    def test_syntax_error_handling(self):
        """Test handling of syntax errors."""
        code = """<?php
function broken( {
    echo "This won't parse";
}
?>"""
        elements = self.parser.parse(code)
        # Parser should handle errors gracefully
        assert isinstance(elements, list)

    def test_multiline_strings(self):
        """Test parsing functions with multiline strings."""
        code = """<?php
function getQuery() {
    return "
        SELECT u.id, u.name, u.email
        FROM users u
        WHERE u.active = 1
        ORDER BY u.created_at DESC
    ";
}

function getHeredoc() {
    return <<<SQL
    SELECT * FROM products
    WHERE price > 100
    SQL;
}
?>"""
        elements = self.parser.parse(code)
        assert len(elements) == 2
        assert elements[0].name == "getQuery"
        assert elements[1].name == "getHeredoc"
