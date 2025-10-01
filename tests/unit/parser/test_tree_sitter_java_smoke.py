#!/usr/bin/env python3
"""Comprehensive smoke tests for tree-sitter Java parser.

Tests basic functionality, import extraction, declaration extraction,
docstring handling, and error resilience for the Java parser.
"""

import pytest

from codeconcat.parser.language_parsers.tree_sitter_java_parser import TreeSitterJavaParser


class TestTreeSitterJavaSmoke:
    """Smoke tests for TreeSitterJavaParser."""

    @pytest.fixture
    def parser(self):
        """Fixture providing a Java parser instance."""
        return TreeSitterJavaParser()

    @pytest.fixture
    def java_sample(self):
        """Fixture providing sample Java code."""
        return '''package com.example.demo;

import java.util.List;
import java.util.ArrayList;
import java.io.IOException;

/**
 * Main application class.
 * Demonstrates various Java features.
 *
 * @author CodeConCat
 * @version 1.0
 */
public class Application {

    /** Maximum retry attempts */
    private static final int MAX_RETRIES = 3;

    private String name;
    private List<String> items;

    /**
     * Creates a new Application instance.
     *
     * @param name the application name
     */
    public Application(String name) {
        this.name = name;
        this.items = new ArrayList<>();
    }

    /**
     * Processes an item with retry logic.
     *
     * @param item the item to process
     * @return true if successful
     * @throws IOException if processing fails
     */
    public boolean processItem(String item) throws IOException {
        if (item == null || item.isEmpty()) {
            return false;
        }
        items.add(item);
        return true;
    }

    /**
     * Gets the application name.
     * @return the name
     */
    public String getName() {
        return name;
    }
}

/**
 * Helper utility class.
 */
class Helper {

    /**
     * Validates input string.
     * @param input the input to validate
     * @return true if valid
     */
    public static boolean validate(String input) {
        return input != null && !input.trim().isEmpty();
    }
}
'''

    def test_parser_initialization(self, parser):
        """Test parser initializes correctly."""
        assert parser is not None
        assert parser.language_name == "java"
        assert parser.ts_language is not None

    def test_basic_parsing(self, parser, java_sample):
        """Test basic parsing returns valid result."""
        result = parser.parse(java_sample, "Application.java")

        assert result is not None
        assert hasattr(result, "declarations")
        assert hasattr(result, "imports")
        assert result.error is None

    def test_import_extraction(self, parser, java_sample):
        """Test import statement extraction."""
        result = parser.parse(java_sample, "Application.java")

        imports = result.imports
        assert len(imports) == 3
        assert "java.util.List" in imports
        assert "java.util.ArrayList" in imports
        assert "java.io.IOException" in imports

    def test_class_extraction(self, parser, java_sample):
        """Test class declaration extraction."""
        result = parser.parse(java_sample, "Application.java")

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) == 2

        # Check main class
        app_class = next((c for c in classes if c.name == "Application"), None)
        assert app_class is not None
        assert "public" in app_class.modifiers
        assert app_class.docstring is not None
        assert "Main application class" in app_class.docstring

        # Check helper class
        helper_class = next((c for c in classes if c.name == "Helper"), None)
        assert helper_class is not None

    def test_method_extraction(self, parser, java_sample):
        """Test method declaration extraction."""
        result = parser.parse(java_sample, "Application.java")

        methods = [d for d in result.declarations if d.kind == "method"]
        assert len(methods) >= 3

        # Check processItem method
        process_method = next((m for m in methods if m.name == "processItem"), None)
        assert process_method is not None
        assert "public" in process_method.modifiers
        assert process_method.docstring is not None
        assert "Processes an item" in process_method.docstring

    def test_constructor_extraction(self, parser, java_sample):
        """Test constructor extraction."""
        result = parser.parse(java_sample, "Application.java")

        constructors = [d for d in result.declarations if d.kind == "constructor"]
        assert len(constructors) >= 1

        constructor = constructors[0]
        assert constructor.name == "Application"
        assert "public" in constructor.modifiers

    def test_field_extraction(self, parser, java_sample):
        """Test field declaration extraction."""
        result = parser.parse(java_sample, "Application.java")

        fields = [d for d in result.declarations if d.kind == "field"]
        assert len(fields) >= 3

        # Check for specific fields
        field_names = [f.name for f in fields]
        assert "MAX_RETRIES" in field_names
        assert "name" in field_names
        assert "items" in field_names

    def test_javadoc_extraction(self, parser, java_sample):
        """Test Javadoc comment extraction and cleaning."""
        result = parser.parse(java_sample, "Application.java")

        app_class = next((d for d in result.declarations
                         if d.kind == "class" and d.name == "Application"), None)

        assert app_class.docstring is not None
        docstring = app_class.docstring

        # Should not have comment markers
        assert "/**" not in docstring
        assert "*/" not in docstring

        # Should have cleaned content
        assert "Main application class" in docstring
        assert "Demonstrates various Java features" in docstring

    def test_line_numbers(self, parser, java_sample):
        """Test accurate line number tracking."""
        result = parser.parse(java_sample, "Application.java")

        app_class = next((d for d in result.declarations
                         if d.kind == "class" and d.name == "Application"), None)

        assert app_class.start_line > 0
        assert app_class.end_line > app_class.start_line

        # Helper class should come after Application
        helper_class = next((d for d in result.declarations
                           if d.kind == "class" and d.name == "Helper"), None)
        assert helper_class.start_line > app_class.end_line

    def test_empty_file(self, parser):
        """Test parser handles empty file gracefully."""
        result = parser.parse("", "Empty.java")

        assert result is not None
        assert len(result.declarations) == 0
        assert len(result.imports) == 0

    def test_malformed_syntax(self, parser):
        """Test parser handles syntax errors gracefully."""
        malformed = "public class Broken { public void test( { }"
        result = parser.parse(malformed, "Broken.java")

        # Parser should still return a result (tree-sitter is resilient)
        assert result is not None

    def test_generic_types(self, parser):
        """Test parsing generic type declarations."""
        generic_code = '''
import java.util.Map;
import java.util.HashMap;

public class Container<T> {
    private Map<String, T> items;

    public Container() {
        items = new HashMap<>();
    }

    public void add(String key, T value) {
        items.put(key, value);
    }
}
'''
        result = parser.parse(generic_code, "Container.java")

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) == 1
        assert classes[0].name == "Container"

        methods = [d for d in result.declarations if d.kind == "method"]
        assert any(m.name == "add" for m in methods)

    def test_interface_parsing(self, parser):
        """Test interface declaration parsing."""
        interface_code = '''
/**
 * Service interface.
 */
public interface Service {
    /**
     * Process a request.
     */
    void process(String request);

    String getStatus();
}
'''
        result = parser.parse(interface_code, "Service.java")

        interfaces = [d for d in result.declarations if d.kind == "interface"]
        assert len(interfaces) == 1
        assert interfaces[0].name == "Service"
        assert "Service interface" in interfaces[0].docstring

    def test_enum_parsing(self, parser):
        """Test enum declaration parsing."""
        enum_code = '''
/**
 * Status enumeration.
 */
public enum Status {
    ACTIVE,
    INACTIVE,
    PENDING
}
'''
        result = parser.parse(enum_code, "Status.java")

        enums = [d for d in result.declarations if d.kind == "enum"]
        assert len(enums) == 1
        assert enums[0].name == "Status"
        assert "Status enumeration" in enums[0].docstring

    def test_annotation_parsing(self, parser):
        """Test annotation parsing (should be in modifiers or handled)."""
        annotated_code = '''
import org.springframework.stereotype.Service;

@Service
public class MyService {

    @Override
    public String toString() {
        return "MyService";
    }
}
'''
        result = parser.parse(annotated_code, "MyService.java")

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) == 1
        assert classes[0].name == "MyService"
