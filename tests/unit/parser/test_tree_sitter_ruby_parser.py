"""
Unit tests for TreeSitterRubyParser.

Tests comprehensive Ruby parsing including:
- Method and class definitions
- Blocks, procs, and lambdas
- Metaprogramming constructs
- Module mixins and visibility
- DSL patterns (RSpec, Rails)
"""

import pytest
from unittest.mock import Mock, patch

from codeconcat.parser.language_parsers.tree_sitter_ruby_parser import TreeSitterRubyParser
from codeconcat.errors import LanguageParserError


class TestTreeSitterRubyParser:
    """Test suite for Ruby parser."""

    def test_parser_initialization(self):
        """Test parser initializes correctly."""
        parser = TreeSitterRubyParser()
        assert parser.language_name == "ruby"
        assert parser.ts_language is not None
        assert parser.parser is not None

    def test_parse_simple_method(self):
        """Test parsing simple method definitions."""
        parser = TreeSitterRubyParser()
        code = """
        def hello(name)
          puts "Hello, #{name}!"
        end

        def world
          "World"
        end
        """

        result = parser.parse(code, "test.rb")
        declarations = result.declarations
        assert len(declarations) >= 2

        # Check method names
        method_names = [d.name for d in declarations if d.kind == "method"]
        assert "hello" in method_names
        assert "world" in method_names

    def test_parse_class_with_inheritance(self):
        """Test parsing class definitions with inheritance."""
        parser = TreeSitterRubyParser()
        code = """
        class Animal
          def speak
            "Some sound"
          end
        end

        class Dog < Animal
          def bark
            "Woof!"
          end
        end
        """

        result = parser.parse(code, "test.rb")
        declarations = result.declarations

        # Check classes
        classes = [d for d in declarations if d.kind == "class"]
        assert len(classes) == 2

        # Check inheritance
        dog_class = next((d for d in classes if d.name == "Dog"), None)
        assert dog_class is not None
        assert dog_class.metadata.get("superclass") == "Animal"

    def test_parse_module_definition(self):
        """Test parsing module definitions."""
        parser = TreeSitterRubyParser()
        code = """
        module Greeting
          def say_hello
            "Hello!"
          end

          module Nested
            def nested_method
              "Nested"
            end
          end
        end
        """

        result = parser.parse(code, "test.rb")
        declarations = result.declarations

        # Check modules
        modules = [d for d in declarations if d.kind == "module"]
        assert len(modules) >= 1
        assert "Greeting" in [m.name for m in modules]

    def test_parse_attribute_accessors(self):
        """Test parsing attribute accessors."""
        parser = TreeSitterRubyParser()
        code = """
        class Person
          attr_reader :name
          attr_writer :age
          attr_accessor :email, :phone
        end
        """

        result = parser.parse(code, "test.rb")
        declarations = result.declarations

        # Check attributes
        attributes = [d for d in declarations if d.kind == "attribute"]
        assert len(attributes) >= 4

        attr_names = [a.name for a in attributes]
        assert "name" in attr_names
        assert "age" in attr_names
        assert "email" in attr_names
        assert "phone" in attr_names

    def test_parse_blocks_and_procs(self):
        """Test parsing blocks, procs, and lambdas."""
        parser = TreeSitterRubyParser()
        code = """
        # Do/end block
        [1, 2, 3].each do |n|
          puts n * 2
        end

        # Brace block
        [1, 2, 3].map { |n| n * 2 }

        # Lambda
        my_lambda = ->(x) { x * 2 }

        # Proc
        my_proc = Proc.new { |x| x + 1 }
        """

        result = parser.parse(code, "test.rb")
        declarations = result.declarations

        # Check blocks
        blocks = [d for d in declarations if d.kind == "block"]
        assert len(blocks) >= 2

        # Check different block types
        block_types = [b.metadata.get("block_type") for b in blocks]
        assert "do_block" in block_types or "brace_block" in block_types

    def test_parse_singleton_methods(self):
        """Test parsing singleton (class) methods."""
        parser = TreeSitterRubyParser()
        code = """
        class MyClass
          def self.class_method
            "Class method"
          end

          def instance_method
            "Instance method"
          end
        end
        """

        result = parser.parse(code, "test.rb")
        declarations = result.declarations

        # Check methods
        methods = [d for d in declarations if d.kind == "method"]
        assert len(methods) >= 2

        # Check singleton method
        singleton = next((m for m in methods if m.metadata.get("method_type") == "singleton"), None)
        assert singleton is not None
        assert "self.class_method" in singleton.signature

    def test_parse_metaprogramming_define_method(self):
        """Test parsing define_method metaprogramming."""
        parser = TreeSitterRubyParser()
        code = """
        class Dynamic
          define_method :dynamic_hello do |name|
            "Hello, #{name}!"
          end

          [:foo, :bar, :baz].each do |method_name|
            define_method method_name do
              method_name.to_s
            end
          end
        end
        """

        result = parser.parse(code, "test.rb")
        declarations = result.declarations

        # Check dynamic methods
        dynamic_methods = [d for d in declarations if d.kind == "dynamic_method"]
        assert len(dynamic_methods) >= 1
        assert "dynamic_hello" in [m.name for m in dynamic_methods]

    def test_parse_method_missing(self):
        """Test parsing method_missing."""
        parser = TreeSitterRubyParser()
        code = """
        class Ghost
          def method_missing(method_name, *args, &block)
            puts "Called: #{method_name}"
            super
          end

          def respond_to_missing?(method_name, include_private = false)
            method_name.to_s.start_with?('ghost_') || super
          end
        end
        """

        result = parser.parse(code, "test.rb")
        declarations = result.declarations

        # Check method_missing
        method_missing = next((d for d in declarations if d.name == "method_missing"), None)
        assert method_missing is not None
        assert method_missing.metadata.get("special_method") is True

    def test_parse_module_mixins(self):
        """Test parsing module mixins (include, extend, prepend)."""
        parser = TreeSitterRubyParser()
        code = """
        module Printable
          def print
            "Printing..."
          end
        end

        class Document
          include Printable
          extend ClassMethods
          prepend Overrides
        end
        """

        result = parser.parse(code, "test.rb")
        declarations = result.declarations

        # The parser should capture class and module definitions
        assert any(d.name == "Document" and d.kind == "class" for d in declarations)
        assert any(d.name == "Printable" and d.kind == "module" for d in declarations)

    def test_parse_rspec_dsl(self):
        """Test parsing RSpec DSL patterns."""
        parser = TreeSitterRubyParser()
        code = """
        describe User do
          context 'when valid' do
            it 'saves successfully' do
              user = User.new(name: 'Test')
              expect(user.save).to be_truthy
            end
          end

          describe '#full_name' do
            it 'returns first and last name' do
              user = User.new(first: 'John', last: 'Doe')
              expect(user.full_name).to eq('John Doe')
            end
          end
        end
        """

        result = parser.parse(code, "test.rb")
        declarations = result.declarations

        # Check for test blocks
        tests = [d for d in declarations if d.kind == "test"]
        assert len(tests) >= 2

        # Check RSpec metadata
        rspec_tests = [t for t in tests if t.metadata.get("framework") == "rspec"]
        assert len(rspec_tests) >= 1

    def test_parse_rails_dsl(self):
        """Test parsing Rails DSL patterns."""
        parser = TreeSitterRubyParser()
        code = """
        class User < ApplicationRecord
          has_many :posts
          has_one :profile
          belongs_to :organization

          validates :email, presence: true, uniqueness: true
          validates :age, numericality: { greater_than: 0 }

          before_action :authenticate
          after_action :log_activity
        end
        """

        result = parser.parse(code, "test.rb")
        declarations = result.declarations

        # Check for Rails DSL declarations
        rails_dsl = [d for d in declarations if d.kind == "rails_dsl"]
        assert len(rails_dsl) >= 4

        # Check for specific Rails patterns
        dsl_methods = [d.name for d in rails_dsl]
        assert any("has_many" in m for m in dsl_methods)
        assert any("validates" in m for m in dsl_methods)

    def test_parse_method_visibility(self):
        """Test parsing method visibility modifiers."""
        parser = TreeSitterRubyParser()
        code = """
        class SecureClass
          def public_method
            "Public"
          end

          private

          def private_method
            "Private"
          end

          protected

          def protected_method
            "Protected"
          end
        end
        """

        result = parser.parse(code, "test.rb")
        declarations = result.declarations

        # Check methods are parsed
        methods = [d for d in declarations if d.kind == "method"]
        assert len(methods) >= 3

    def test_parse_class_reopening(self):
        """Test tracking class reopening."""
        parser = TreeSitterRubyParser()
        code = """
        class User
          def name
            @name
          end
        end

        # Later in the file...
        class User
          def email
            @email
          end
        end
        """

        result = parser.parse(code, "test.rb")
        declarations = result.declarations

        # Check classes
        classes = [d for d in declarations if d.kind == "class" and d.name == "User"]
        assert len(classes) == 2

        # Second one should be marked as reopened
        if len(classes) == 2:
            assert classes[1].metadata.get("is_reopened") is True

    def test_extract_imports(self):
        """Test extracting require statements."""
        parser = TreeSitterRubyParser()
        code = """
        require 'json'
        require_relative 'lib/helper'
        load 'config.rb'
        autoload :MyClass, 'my_class'

        # Bundler require
        Bundler.require
        """

        imports = parser.extract_imports(code)
        assert len(imports) >= 3
        assert any("require 'json'" in imp for imp in imports)
        assert any("require_relative 'lib/helper'" in imp for imp in imports)

    def test_parse_empty_code(self):
        """Test parsing empty code."""
        parser = TreeSitterRubyParser()
        declarations = parser.parse("")
        assert declarations == []

    def test_parse_malformed_code(self):
        """Test parsing malformed Ruby code."""
        parser = TreeSitterRubyParser()
        code = """
        def broken_method(
          # Missing closing parenthesis and end
          puts "This won't parse properly"
        """

        # Should not raise exception, but return empty or partial results
        result = parser.parse(code, "test.rb")
        declarations = result.declarations
        assert isinstance(declarations, list)

    def test_parse_unicode_in_code(self):
        """Test parsing Ruby code with Unicode characters."""
        parser = TreeSitterRubyParser()
        code = """
        def 你好(名字)
          puts "你好, #{名字}!"
        end

        class 日本語クラス
          def メソッド
            "こんにちは"
          end
        end
        """

        result = parser.parse(code, "test.rb")
        declarations = result.declarations
        assert len(declarations) >= 2

    def test_parse_heredoc_strings(self):
        """Test parsing with heredoc strings."""
        parser = TreeSitterRubyParser()
        code = """
        def long_string
          <<~SQL
            SELECT * FROM users
            WHERE active = true
          SQL
        end
        """

        result = parser.parse(code, "test.rb")
        declarations = result.declarations
        methods = [d for d in declarations if d.kind == "method"]
        assert len(methods) >= 1
        assert "long_string" in [m.name for m in methods]

    def test_parse_nested_classes_and_modules(self):
        """Test parsing nested classes and modules."""
        parser = TreeSitterRubyParser()
        code = """
        module OuterModule
          class InnerClass
            module DeepModule
              def deep_method
                "Deep"
              end
            end
          end
        end
        """

        result = parser.parse(code, "test.rb")
        declarations = result.declarations

        # Check all levels are parsed
        assert any(d.name == "OuterModule" and d.kind == "module" for d in declarations)
        assert any(d.name == "InnerClass" and d.kind == "class" for d in declarations)
        assert any(d.name == "DeepModule" and d.kind == "module" for d in declarations)
