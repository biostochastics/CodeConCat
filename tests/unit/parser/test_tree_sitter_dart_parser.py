"""Comprehensive tests for the Tree-sitter Dart parser.

Tests cover Dart 3.x features including:
- Flutter widgets (StatelessWidget, StatefulWidget, State)
- Lifecycle methods (initState, dispose, build)
- Null safety (late, required, ?, !)
- Mixins and extensions
- Async patterns (async/await, Future, Stream)
- Modern class modifiers (base, sealed, final)
- Imports with combinators (show, hide, as)
"""

from codeconcat.parser.language_parsers.tree_sitter_dart_parser import (
    TreeSitterDartParser,
)


class TestTreeSitterDartParser:
    """Test suite for TreeSitterDartParser."""

    # ========== BASIC TESTS ==========

    def test_parser_initialization(self):
        """Test that the parser initializes correctly."""
        parser = TreeSitterDartParser()
        assert parser is not None
        assert parser.language_name == "dart"
        assert parser.ts_language is not None
        assert parser.parser is not None
        assert parser.check_language_availability()

    def test_parse_simple_function(self):
        """Test parsing a simple Dart function."""
        parser = TreeSitterDartParser()
        content = """
void greet(String name) {
  print('Hello, \$name!');
}
"""
        result = parser.parse(content, "test.dart")
        assert result is not None
        assert len(result.declarations) >= 1

        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) == 1
        assert functions[0].name == "greet"

    def test_parse_simple_class(self):
        """Test parsing a simple Dart class."""
        parser = TreeSitterDartParser()
        content = """
class Person {
  String name;
  int age;

  Person(this.name, this.age);

  void sayHello() {
    print('Hello, I am \$name');
  }
}
"""
        result = parser.parse(content, "test.dart")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) == 1
        assert classes[0].name == "Person"

        # Methods should be captured as functions
        functions = [d for d in result.declarations if d.kind == "function"]
        assert any(f.name == "sayHello" for f in functions)

    def test_parse_imports(self):
        """Test parsing import statements with various forms."""
        parser = TreeSitterDartParser()
        content = """
import 'dart:async';
import 'dart:core' as core;
import 'package:flutter/material.dart';
import 'package:http/http.dart' show Client, Response;
import 'dart:io' hide File;

void main() {}
"""
        result = parser.parse(content, "test.dart")
        assert result is not None
        assert len(result.imports) >= 3

        # Check that various import forms are captured
        imports_text = '\n'.join(result.imports)
        assert 'dart:async' in imports_text
        assert 'package:flutter/material.dart' in imports_text

    # ========== FLUTTER WIDGET TESTS ==========

    def test_parse_stateless_widget(self):
        """Test parsing a StatelessWidget."""
        parser = TreeSitterDartParser()
        content = """
import 'package:flutter/material.dart';

class MyWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      child: Text('Hello'),
    );
  }
}
"""
        result = parser.parse(content, "test.dart")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) == 1
        assert classes[0].name == "MyWidget"

        # build() method should be captured
        functions = [d for d in result.declarations if d.kind == "function"]
        assert any(f.name == "build" for f in functions)

    def test_parse_stateful_widget(self):
        """Test parsing a StatefulWidget with State class."""
        parser = TreeSitterDartParser()
        content = """
import 'package:flutter/material.dart';

class CounterWidget extends StatefulWidget {
  @override
  State<CounterWidget> createState() => _CounterWidgetState();
}

class _CounterWidgetState extends State<CounterWidget> {
  int _counter = 0;

  @override
  void initState() {
    super.initState();
    _counter = 0;
  }

  @override
  void dispose() {
    super.dispose();
  }

  void _increment() {
    setState(() {
      _counter++;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text('\$_counter'),
        ElevatedButton(onPressed: _increment, child: Text('+')),
      ],
    );
  }
}
"""
        result = parser.parse(content, "test.dart")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) >= 2
        class_names = {c.name for c in classes}
        assert "CounterWidget" in class_names
        assert "_CounterWidgetState" in class_names

        # Lifecycle methods should be captured
        functions = [d for d in result.declarations if d.kind == "function"]
        function_names = {f.name for f in functions}
        assert "initState" in function_names
        assert "dispose" in function_names
        assert "build" in function_names
        assert "createState" in function_names

    def test_parse_widget_composition(self):
        """Test parsing complex widget trees."""
        parser = TreeSitterDartParser()
        content = """
class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        appBar: AppBar(title: Text('My App')),
        body: Center(
          child: Column(
            children: [
              Text('Line 1'),
              Text('Line 2'),
              ElevatedButton(onPressed: () {}, child: Text('Click')),
            ],
          ),
        ),
      ),
    );
  }
}
"""
        result = parser.parse(content, "test.dart")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) >= 1
        assert any(c.name == "MyApp" for c in classes)

    # ========== MIXIN TESTS ==========

    def test_parse_mixin_declaration(self):
        """Test parsing mixin declarations."""
        parser = TreeSitterDartParser()
        content = """
mixin LoggerMixin {
  void log(String message) {
    print('[LOG] \$message');
  }
}

mixin ValidationMixin on StatefulWidget {
  bool validate() => true;
}

class MyWidget with LoggerMixin {
  void doSomething() {
    log('Doing something');
  }
}
"""
        result = parser.parse(content, "test.dart")
        assert result is not None

        # Mixins might be captured as classes or have dedicated mixin nodes
        declarations = result.declarations
        assert len(declarations) >= 3

    def test_parse_class_with_mixins(self):
        """Test parsing classes that use mixins."""
        parser = TreeSitterDartParser()
        content = """
mixin A {
  void methodA() {}
}

mixin B {
  void methodB() {}
}

class MyClass with A, B {
  void myMethod() {}
}

abstract class BaseClass {}

class DerivedClass extends BaseClass with A, B {
  void derivedMethod() {}
}
"""
        result = parser.parse(content, "test.dart")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) >= 3
        class_names = {c.name for c in classes}
        assert "MyClass" in class_names
        assert "BaseClass" in class_names
        assert "DerivedClass" in class_names

    # ========== EXTENSION TESTS ==========

    def test_parse_extension_methods(self):
        """Test parsing extension methods."""
        parser = TreeSitterDartParser()
        content = """
extension StringExtensions on String {
  bool get isBlank => trim().isEmpty;

  String capitalize() {
    if (isEmpty) return this;
    return '\${this[0].toUpperCase()}\${substring(1)}';
  }
}

extension<T> ListExtensions<T> on List<T> {
  T? get secondOrNull {
    return length >= 2 ? this[1] : null;
  }
}

extension NumberParsing on String {
  int? toIntOrNull() => int.tryParse(this);
}
"""
        result = parser.parse(content, "test.dart")
        assert result is not None

        # Extensions should be captured
        declarations = result.declarations
        assert len(declarations) >= 3

    # ========== NULL SAFETY TESTS ==========

    def test_parse_null_safety_features(self):
        """Test parsing null safety annotations."""
        parser = TreeSitterDartParser()
        content = """
class NullSafetyDemo {
  // Nullable types
  String? nullableString;
  int? nullableInt;

  // Non-nullable types
  String nonNullableString = 'value';
  int nonNullableInt = 42;

  // Late variables
  late String lateString;
  late final int lateFinalInt;

  // Required parameters
  NullSafetyDemo({
    required this.nonNullableString,
    required this.nonNullableInt,
    this.nullableString,
  });

  // Null-aware operators
  void demo() {
    String? maybeNull;
    var length = maybeNull?.length ?? 0;
    maybeNull ??= 'default';
    var nonNull = maybeNull!;
  }
}
"""
        result = parser.parse(content, "test.dart")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) >= 1
        assert any(c.name == "NullSafetyDemo" for c in classes)

    # ========== ASYNC TESTS ==========

    def test_parse_async_functions(self):
        """Test parsing async/await patterns."""
        parser = TreeSitterDartParser()
        content = """
Future<String> fetchData() async {
  await Future.delayed(Duration(seconds: 1));
  return 'data';
}

Future<void> processData() async {
  var data = await fetchData();
  print(data);
}

Stream<int> countStream() async* {
  for (int i = 0; i < 10; i++) {
    await Future.delayed(Duration(milliseconds: 100));
    yield i;
  }
}

Stream<String> transformStream() async* {
  await for (var value in countStream()) {
    yield 'Value: \$value';
  }
}
"""
        result = parser.parse(content, "test.dart")
        assert result is not None

        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) >= 4
        function_names = {f.name for f in functions}
        assert "fetchData" in function_names
        assert "processData" in function_names
        assert "countStream" in function_names
        assert "transformStream" in function_names

    # ========== ENUM TESTS ==========

    def test_parse_simple_enum(self):
        """Test parsing simple enums."""
        parser = TreeSitterDartParser()
        content = """
enum Status {
  pending,
  active,
  completed,
  cancelled
}

enum Priority { low, medium, high }
"""
        result = parser.parse(content, "test.dart")
        assert result is not None

        enums = [d for d in result.declarations if d.kind == "enum"]
        assert len(enums) >= 2
        enum_names = {e.name for e in enums}
        assert "Status" in enum_names
        assert "Priority" in enum_names

    def test_parse_enhanced_enum(self):
        """Test parsing enhanced enums with members and methods."""
        parser = TreeSitterDartParser()
        content = """
enum Planet {
  mercury(3.7),
  venus(8.87),
  earth(9.81),
  mars(3.71);

  const Planet(this.surfaceGravity);

  final double surfaceGravity;

  double get weight => surfaceGravity * 70;

  bool isHabitable() {
    return this == Planet.earth;
  }
}
"""
        result = parser.parse(content, "test.dart")
        assert result is not None

        enums = [d for d in result.declarations if d.kind == "enum"]
        assert len(enums) >= 1
        assert any(e.name == "Planet" for e in enums)

    # ========== CLASS MODIFIER TESTS ==========

    def test_parse_class_modifiers(self):
        """Test parsing modern class modifiers (base, sealed, final, abstract)."""
        parser = TreeSitterDartParser()
        content = """
abstract class AbstractBase {
  void abstractMethod();
}

base class BaseClass {
  void baseMethod() {}
}

sealed class SealedResult {}

class Success extends SealedResult {
  final String data;
  Success(this.data);
}

class Error extends SealedResult {
  final String message;
  Error(this.message);
}

final class FinalClass {
  const FinalClass();
}
"""
        result = parser.parse(content, "test.dart")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) >= 4
        class_names = {c.name for c in classes}
        assert "AbstractBase" in class_names
        assert "BaseClass" in class_names
        assert "SealedResult" in class_names

    # ========== GENERICS TESTS ==========

    def test_parse_generic_classes(self):
        """Test parsing generic classes and methods."""
        parser = TreeSitterDartParser()
        content = """
class Box<T> {
  T value;
  Box(this.value);

  T getValue() => value;
  void setValue(T newValue) {
    value = newValue;
  }
}

class Pair<K, V> {
  final K key;
  final V value;

  Pair(this.key, this.value);
}

T identity<T>(T value) => value;

List<T> filter<T>(List<T> items, bool Function(T) predicate) {
  return items.where(predicate).toList();
}
"""
        result = parser.parse(content, "test.dart")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) >= 2
        class_names = {c.name for c in classes}
        assert "Box" in class_names
        assert "Pair" in class_names

        functions = [d for d in result.declarations if d.kind == "function"]
        function_names = {f.name for f in functions}
        assert "identity" in function_names
        assert "filter" in function_names

    # ========== ANNOTATION TESTS ==========

    def test_parse_annotations(self):
        """Test parsing annotated declarations."""
        parser = TreeSitterDartParser()
        content = """
@deprecated
class OldClass {
  void oldMethod() {}
}

class MyWidget {
  @override
  void build() {}

  @protected
  void protectedMethod() {}

  @visibleForTesting
  void testMethod() {}
}

@JsonSerializable()
class User {
  final String name;
  final int age;

  User(this.name, this.age);
}
"""
        result = parser.parse(content, "test.dart")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) >= 3

    # ========== EDGE CASE TESTS ==========

    def test_parse_empty_file(self):
        """Test parsing an empty file."""
        parser = TreeSitterDartParser()
        content = ""
        result = parser.parse(content, "empty.dart")
        assert result is not None
        assert len(result.declarations) == 0
        assert len(result.imports) == 0

    def test_parse_comment_only_file(self):
        """Test parsing a file with only comments."""
        parser = TreeSitterDartParser()
        content = """
// This is a single-line comment

/* This is a
   multi-line comment */

/// This is a documentation comment
/// It can span multiple lines
"""
        result = parser.parse(content, "comments.dart")
        assert result is not None
        assert len(result.declarations) == 0
        assert len(result.imports) == 0

    def test_parse_whitespace_only(self):
        """Test parsing a file with only whitespace."""
        parser = TreeSitterDartParser()
        content = "   \n\n  \t\n   "
        result = parser.parse(content, "whitespace.dart")
        assert result is not None
        assert len(result.declarations) == 0

    def test_parse_malformed_syntax_missing_brace(self):
        """Test parsing code with missing closing brace."""
        parser = TreeSitterDartParser()
        content = """
class Broken {
  void method() {
    print('Missing closing brace');
"""
        # Parser should not crash
        result = parser.parse(content, "malformed.dart")
        assert result is not None
        # May or may not find declarations depending on error recovery

    def test_parse_malformed_syntax_invalid_token(self):
        """Test parsing code with invalid tokens."""
        parser = TreeSitterDartParser()
        content = """
void validFunction() {}

@@@ invalid syntax @@@

void anotherValidFunction() {}
"""
        # Parser should not crash
        result = parser.parse(content, "malformed2.dart")
        assert result is not None
        # Should still find at least one valid function
        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) >= 1

    def test_parse_unicode_identifiers(self):
        """Test parsing Unicode identifiers (if supported by grammar)."""
        parser = TreeSitterDartParser()
        content = """
// Note: Dart allows Unicode in identifiers
class Café {
  void método() {}
}

var переменная = 42;
const 变量 = 'value';
"""
        result = parser.parse(content, "unicode.dart")
        assert result is not None
        # Should parse without errors even if not all identifiers captured

    def test_parse_mixed_declarations(self):
        """Test parsing a file with mixed declaration types."""
        parser = TreeSitterDartParser()
        content = """
import 'dart:async';
import 'package:flutter/material.dart';

const int MAX_SIZE = 100;
final String appName = 'MyApp';

enum Status { active, inactive }

mixin LogMixin {
  void log(String msg) => print(msg);
}

abstract class Repository {
  Future<List<String>> fetch();
}

class UserRepository implements Repository with LogMixin {
  @override
  Future<List<String>> fetch() async {
    log('Fetching users...');
    return ['Alice', 'Bob'];
  }
}

extension StringUtils on String {
  String get reversed => split('').reversed.join();
}

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(home: Container());
  }
}
"""
        result = parser.parse(content, "mixed.dart")
        assert result is not None

        # Should find multiple declaration types
        assert len(result.declarations) >= 5
        assert len(result.imports) >= 2

        # Verify various kinds are present
        kinds = {d.kind for d in result.declarations}
        assert "class" in kinds
        assert "function" in kinds or "enum" in kinds

    # ========== CONSTRUCTOR TESTS ==========

    def test_parse_constructors(self):
        """Test parsing various constructor forms."""
        parser = TreeSitterDartParser()
        content = """
class Person {
  final String name;
  final int age;

  // Default constructor
  Person(this.name, this.age);

  // Named constructor
  Person.guest() : name = 'Guest', age = 0;

  // Const constructor
  const Person.defaultPerson() : name = 'Default', age = 18;

  // Factory constructor
  factory Person.fromJson(Map<String, dynamic> json) {
    return Person(json['name'], json['age']);
  }
}
"""
        result = parser.parse(content, "test.dart")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) >= 1
        assert any(c.name == "Person" for c in classes)

    # ========== TYPEDEF TESTS ==========

    def test_parse_typedefs(self):
        """Test parsing type aliases."""
        parser = TreeSitterDartParser()
        content = """
typedef IntList = List<int>;
typedef StringToInt = int Function(String);
typedef Compare<T> = int Function(T a, T b);

void useTypedefs() {
  IntList numbers = [1, 2, 3];
  StringToInt parser = int.parse;
  Compare<String> comparator = (a, b) => a.compareTo(b);
}
"""
        result = parser.parse(content, "test.dart")
        assert result is not None
        # Typedefs may or may not be captured depending on grammar

    # ========== GETTER/SETTER TESTS ==========

    def test_parse_getters_setters(self):
        """Test parsing getters and setters."""
        parser = TreeSitterDartParser()
        content = """
class Rectangle {
  double width;
  double height;

  Rectangle(this.width, this.height);

  // Getter
  double get area => width * height;

  // Getter with block
  double get perimeter {
    return 2 * (width + height);
  }

  // Setter
  set dimensions(List<double> dims) {
    width = dims[0];
    height = dims[1];
  }
}

// Top-level getter
String get appVersion => '1.0.0';

// Top-level setter
int _count = 0;
set count(int value) {
  _count = value.clamp(0, 100);
}
"""
        result = parser.parse(content, "test.dart")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) >= 1

    # ========== RECORD TESTS (Dart 3.x) ==========

    def test_parse_records(self):
        """Test parsing record types (Dart 3.x feature)."""
        parser = TreeSitterDartParser()
        content = """
// Records (Dart 3.0+)
(int, String) getUserInfo() {
  return (42, 'Alice');
}

({String name, int age}) getNamedRecord() {
  return (name: 'Bob', age: 30);
}

void useRecords() {
  var info = getUserInfo();
  var (id, name) = info;

  var named = getNamedRecord();
  print(named.name);
}
"""
        result = parser.parse(content, "test.dart")
        assert result is not None
        # Records may not be fully supported by grammar yet
        # At minimum, file should parse without crashing

    # ========== PERFORMANCE TESTS ==========

    def test_performance_10kb_file(self):
        """Test parsing performance on a 10KB file (~300 lines).

        Target: Parse time < 100ms for 10KB file
        """
        import time

        parser = TreeSitterDartParser()

        # Generate a realistic 10KB Dart file with Flutter widgets
        # Approximately 300 lines of code
        content = '''
import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';

/// Performance test widget demonstrating complex Flutter patterns
class PerformanceTestApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Performance Test',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _counter = 0;
  List<String> _items = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  @override
  void dispose() {
    _items.clear();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      await Future.delayed(Duration(seconds: 1));
      final data = List.generate(100, (i) => 'Item $i');
      if (mounted) {
        setState(() {
          _items = data;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  void _incrementCounter() {
    setState(() => _counter++);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Performance Test Screen'),
        actions: [
          IconButton(icon: Icon(Icons.refresh), onPressed: _loadData),
          IconButton(icon: Icon(Icons.settings), onPressed: () {}),
        ],
      ),
      body: _isLoading
          ? Center(child: CircularProgressIndicator())
          : Column(
              children: [
                CounterDisplay(count: _counter),
                Expanded(child: ItemList(items: _items)),
                ActionButtons(onIncrement: _incrementCounter),
              ],
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: _incrementCounter,
        child: Icon(Icons.add),
      ),
    );
  }
}

class CounterDisplay extends StatelessWidget {
  final int count;

  const CounterDisplay({Key? key, required this.count}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16),
      color: Colors.blue.shade50,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.counter, size: 32),
          SizedBox(width: 16),
          Text(
            'Count: $count',
            style: Theme.of(context).textTheme.headlineMedium,
          ),
        ],
      ),
    );
  }
}

class ItemList extends StatelessWidget {
  final List<String> items;

  const ItemList({Key? key, required this.items}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return Center(child: Text('No items'));
    }

    return ListView.builder(
      itemCount: items.length,
      itemBuilder: (context, index) {
        return ListTile(
          leading: CircleAvatar(child: Text('${index + 1}')),
          title: Text(items[index]),
          subtitle: Text('Details for item ${index + 1}'),
          trailing: Icon(Icons.chevron_right),
          onTap: () => _showItemDetails(context, items[index]),
        );
      },
    );
  }

  void _showItemDetails(BuildContext context, String item) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(item),
        content: Text('Item details would go here'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Close'),
          ),
        ],
      ),
    );
  }
}

class ActionButtons extends StatelessWidget {
  final VoidCallback onIncrement;

  const ActionButtons({Key? key, required this.onIncrement}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          ElevatedButton.icon(
            onPressed: onIncrement,
            icon: Icon(Icons.add),
            label: Text('Increment'),
          ),
          ElevatedButton.icon(
            onPressed: () => _showSnackBar(context),
            icon: Icon(Icons.info),
            label: Text('Info'),
          ),
          ElevatedButton.icon(
            onPressed: () => _navigateToSettings(context),
            icon: Icon(Icons.settings),
            label: Text('Settings'),
          ),
        ],
      ),
    );
  }

  void _showSnackBar(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Information displayed')),
    );
  }

  void _navigateToSettings(BuildContext context) {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => SettingsScreen()),
    );
  }
}

class SettingsScreen extends StatefulWidget {
  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _notifications = true;
  bool _darkMode = false;
  double _volume = 50.0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Settings')),
      body: ListView(
        children: [
          SwitchListTile(
            title: Text('Enable Notifications'),
            value: _notifications,
            onChanged: (value) => setState(() => _notifications = value),
          ),
          SwitchListTile(
            title: Text('Dark Mode'),
            value: _darkMode,
            onChanged: (value) => setState(() => _darkMode = value),
          ),
          ListTile(
            title: Text('Volume'),
            subtitle: Slider(
              value: _volume,
              min: 0,
              max: 100,
              onChanged: (value) => setState(() => _volume = value),
            ),
          ),
        ],
      ),
    );
  }
}
'''

        # Verify file size is approximately 10KB
        file_size_kb = len(content.encode('utf-8')) / 1024
        print(f"\nGenerated file size: {file_size_kb:.2f} KB")

        # Warmup parse
        parser.parse(content, "warmup.dart")

        # Measure parse time over multiple runs
        num_runs = 10
        times = []

        for _ in range(num_runs):
            start = time.perf_counter()
            result = parser.parse(content, "performance_test.dart")
            end = time.perf_counter()

            duration_ms = (end - start) * 1000
            times.append(duration_ms)

            # Verify parse succeeded
            assert result is not None
            assert result.error is None or 'partial' in result.parser_quality

        # Calculate statistics
        avg_time_ms = sum(times) / len(times)
        min_time_ms = min(times)
        max_time_ms = max(times)
        median_time_ms = sorted(times)[len(times) // 2]

        print(f"\nPerformance statistics over {num_runs} runs:")
        print(f"  Average: {avg_time_ms:.2f}ms")
        print(f"  Median:  {median_time_ms:.2f}ms")
        print(f"  Min:     {min_time_ms:.2f}ms")
        print(f"  Max:     {max_time_ms:.2f}ms")

        # Assert performance target: average < 100ms
        assert avg_time_ms < 100, f"Average parse time {avg_time_ms:.2f}ms exceeds 100ms target"

        # Also check p95 (95th percentile)
        p95_time_ms = sorted(times)[int(0.95 * len(times))]
        print(f"  P95:     {p95_time_ms:.2f}ms")
        assert p95_time_ms < 150, f"P95 parse time {p95_time_ms:.2f}ms exceeds 150ms threshold"
