#!/usr/bin/env python3
"""
Comprehensive test script for all tree-sitter parsers in CodeConCat.
Tests each parser's ability to parse sample code and extract declarations.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Test samples for each language
LANGUAGE_SAMPLES = {
    "python": {
        "extension": ".py",
        "code": '''
"""Module docstring for testing."""

import os
import sys
from typing import List, Dict
from collections import defaultdict

class TestClass:
    """A test class with methods."""

    def __init__(self, name: str):
        """Initialize the test class."""
        self.name = name

    def method_one(self, value: int) -> int:
        """Test method one."""
        return value * 2

    @staticmethod
    def static_method():
        """A static method."""
        pass

def function_one(arg1: str, arg2: int = 10) -> str:
    """Test function with type hints."""
    return f"{arg1}: {arg2}"

async def async_function():
    """An async function."""
    pass

lambda_func = lambda x: x * 2
''',
        "expected": {
            "classes": ["TestClass"],
            "functions": [
                "__init__",
                "method_one",
                "static_method",
                "function_one",
                "async_function",
            ],
            "imports": 4,  # import os, import sys, from typing..., from collections...
        },
    },
    "javascript": {
        "extension": ".js",
        "code": """
// JavaScript test file
import React from 'react';
import { useState, useEffect } from 'react';
const utils = require('./utils');

class MyComponent extends React.Component {
    constructor(props) {
        super(props);
        this.state = { count: 0 };
    }

    handleClick() {
        this.setState({ count: this.state.count + 1 });
    }

    render() {
        return null;
    }
}

function regularFunction(param1, param2) {
    return param1 + param2;
}

const arrowFunction = (x, y) => x * y;

async function asyncFunc() {
    await somePromise();
}

export default MyComponent;
export { regularFunction, arrowFunction };
""",
        "expected": {
            "classes": ["MyComponent"],
            "functions": [
                "constructor",
                "handleClick",
                "render",
                "regularFunction",
                "arrowFunction",
                "asyncFunc",
            ],
            "imports": 3,
        },
    },
    "typescript": {
        "extension": ".ts",
        "code": """
// TypeScript test file
import { Component } from '@angular/core';
import * as moment from 'moment';
import type { Config } from './types';

interface Person {
    name: string;
    age: number;
}

type Status = 'active' | 'inactive';

class UserService {
    private users: Person[] = [];

    constructor(private config: Config) {}

    addUser(user: Person): void {
        this.users.push(user);
    }

    getUsers(): Person[] {
        return this.users;
    }
}

function processData<T>(data: T[]): T[] {
    return data.filter(Boolean);
}

const fetchData = async (): Promise<void> => {
    console.log('Fetching...');
};

enum Color {
    Red = 'RED',
    Green = 'GREEN',
    Blue = 'BLUE'
}

export { UserService, processData };
""",
        "expected": {
            "classes": ["UserService"],
            "functions": ["constructor", "addUser", "getUsers", "processData", "fetchData"],
            "imports": 3,
            "types": ["Person", "Status", "Color"],
        },
    },
    "go": {
        "extension": ".go",
        "code": """
package main

import (
    "fmt"
    "os"
    "sync"
)

type Person struct {
    Name string
    Age  int
}

type Employee struct {
    Person
    ID     string
    Salary float64
}

func (p *Person) GetName() string {
    return p.Name
}

func (e *Employee) GetDetails() string {
    return fmt.Sprintf("%s: %s", e.ID, e.Name)
}

func ProcessData(data []string) []string {
    result := make([]string, len(data))
    for i, v := range data {
        result[i] = v
    }
    return result
}

func main() {
    fmt.Println("Hello, World!")
}

type DataProcessor interface {
    Process([]byte) error
    Validate() bool
}
""",
        "expected": {
            "structs": ["Person", "Employee"],
            "functions": ["GetName", "GetDetails", "ProcessData", "main"],
            "interfaces": ["DataProcessor"],
            "imports": 3,
        },
    },
    "rust": {
        "extension": ".rs",
        "code": """
use std::collections::HashMap;
use std::io::{self, Read};
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone)]
struct Person {
    name: String,
    age: u32,
}

impl Person {
    fn new(name: String, age: u32) -> Self {
        Person { name, age }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

trait Printable {
    fn print(&self);
    fn format(&self) -> String;
}

impl Printable for Person {
    fn print(&self) {
        println!("{}", self.format());
    }

    fn format(&self) -> String {
        format!("{}: {}", self.name, self.age)
    }
}

pub fn process_data(input: Vec<String>) -> Vec<String> {
    input.iter().map(|s| s.to_uppercase()).collect()
}

enum Status {
    Active,
    Inactive,
    Pending(String),
}

fn main() {
    let person = Person::new("Alice".to_string(), 30);
    person.print();
}
""",
        "expected": {
            "structs": ["Person"],
            "functions": ["new", "get_name", "print", "format", "process_data", "main"],
            "traits": ["Printable"],
            "enums": ["Status"],
            "imports": 3,
        },
    },
    "java": {
        "extension": ".java",
        "code": """
package com.example.test;

import java.util.List;
import java.util.ArrayList;
import java.util.stream.Collectors;

public class TestClass {
    private String name;
    private int value;

    public TestClass(String name, int value) {
        this.name = name;
        this.value = value;
    }

    public String getName() {
        return name;
    }

    public void setValue(int value) {
        this.value = value;
    }

    private static void helperMethod() {
        System.out.println("Helper");
    }
}

interface DataProcessor {
    void process(String data);
    boolean validate();
}

class DataHandler implements DataProcessor {
    @Override
    public void process(String data) {
        System.out.println("Processing: " + data);
    }

    @Override
    public boolean validate() {
        return true;
    }
}

enum Status {
    ACTIVE,
    INACTIVE,
    PENDING
}
""",
        "expected": {
            "classes": ["TestClass", "DataHandler"],
            "functions": [
                "TestClass",
                "getName",
                "setValue",
                "helperMethod",
                "process",
                "validate",
            ],
            "interfaces": ["DataProcessor"],
            "enums": ["Status"],
            "imports": 3,
        },
    },
    "csharp": {
        "extension": ".cs",
        "code": """
using System;
using System.Collections.Generic;
using System.Linq;

namespace TestNamespace
{
    public class Person
    {
        public string Name { get; set; }
        public int Age { get; set; }

        public Person(string name, int age)
        {
            Name = name;
            Age = age;
        }

        public string GetInfo()
        {
            return $"{Name}: {Age}";
        }
    }

    public interface IDataService
    {
        void SaveData(string data);
        string LoadData();
    }

    public class DataService : IDataService
    {
        public void SaveData(string data)
        {
            Console.WriteLine($"Saving: {data}");
        }

        public string LoadData()
        {
            return "Loaded data";
        }
    }

    public enum Status
    {
        Active,
        Inactive,
        Pending
    }

    public static class Utils
    {
        public static string ProcessString(string input)
        {
            return input.ToUpper();
        }
    }
}
""",
        "expected": {
            "classes": ["Person", "DataService", "Utils"],
            "functions": ["Person", "GetInfo", "SaveData", "LoadData", "ProcessString"],
            "interfaces": ["IDataService"],
            "enums": ["Status"],
            "imports": 3,
        },
    },
    "cpp": {
        "extension": ".cpp",
        "code": """
#include <iostream>
#include <vector>
#include <string>

class Person {
private:
    std::string name;
    int age;

public:
    Person(const std::string& n, int a) : name(n), age(a) {}

    std::string getName() const {
        return name;
    }

    void setAge(int a) {
        age = a;
    }
};

template<typename T>
class Container {
private:
    std::vector<T> items;

public:
    void add(const T& item) {
        items.push_back(item);
    }

    size_t size() const {
        return items.size();
    }
};

void processData(std::vector<int>& data) {
    for (auto& val : data) {
        val *= 2;
    }
}

int main() {
    Person p("Alice", 30);
    std::cout << p.getName() << std::endl;
    return 0;
}

namespace Utils {
    void helperFunction() {
        std::cout << "Helper" << std::endl;
    }
}
""",
        "expected": {
            "classes": ["Person", "Container"],
            "functions": [
                "Person",
                "getName",
                "setAge",
                "add",
                "size",
                "processData",
                "main",
                "helperFunction",
            ],
            "imports": 3,
        },
    },
    "php": {
        "extension": ".php",
        "code": """<?php

namespace App\\Controllers;

use App\\Models\\User;
use App\\Services\\DataService;
use Illuminate\\Http\\Request;

class UserController {
    private $dataService;

    public function __construct(DataService $service) {
        $this->dataService = $service;
    }

    public function index() {
        return view('users.index');
    }

    public function store(Request $request) {
        $user = new User($request->all());
        $user->save();
        return redirect()->route('users.index');
    }

    private function validateData($data) {
        return !empty($data);
    }
}

interface DataInterface {
    public function getData();
    public function setData($data);
}

trait LoggerTrait {
    public function log($message) {
        echo "Log: " . $message;
    }
}

function helperFunction($param) {
    return strtoupper($param);
}

class DataHandler implements DataInterface {
    use LoggerTrait;

    public function getData() {
        return "data";
    }

    public function setData($data) {
        $this->log("Setting data");
    }
}
""",
        "expected": {
            "classes": ["UserController", "DataHandler"],
            "functions": [
                "__construct",
                "index",
                "store",
                "validateData",
                "getData",
                "setData",
                "log",
                "helperFunction",
            ],
            "interfaces": ["DataInterface"],
            "traits": ["LoggerTrait"],
            "imports": 3,
        },
    },
    "julia": {
        "extension": ".jl",
        "code": r"""
using LinearAlgebra
using Statistics
import Base: +, -, *

struct Person
    name::String
    age::Int
end

mutable struct Employee
    person::Person
    id::String
    salary::Float64
end

function process_data(data::Vector{Float64})
    return mean(data)
end

function calculate_sum(a::Int, b::Int)::Int
    return a + b
end

macro timeit(expr)
    quote
        t0 = time()
        result = \$(esc(expr))
        elapsed = time() - t0
        println("Elapsed time: ", elapsed)
        result
    end
end

abstract type Shape end

struct Circle <: Shape
    radius::Float64
end

function area(c::Circle)
    return π * c.radius^2
end

module Utils
    export helper_func

    function helper_func(x)
        return x * 2
    end
end
""",
        "expected": {
            "structs": ["Person", "Employee", "Circle"],
            "functions": ["process_data", "calculate_sum", "area", "helper_func"],
            "macros": ["timeit"],
            "modules": ["Utils"],
            "imports": 3,
        },
    },
    "r": {
        "extension": ".R",
        "code": """
library(ggplot2)
library(dplyr)
require(tidyr)

# Function to process data
process_data <- function(data, threshold = 0.5) {
  result <- data %>%
    filter(value > threshold) %>%
    mutate(processed = TRUE)
  return(result)
}

# Another function
calculate_mean <- function(x) {
  if (length(x) == 0) {
    return(NA)
  }
  mean(x, na.rm = TRUE)
}

# S3 class definition
Person <- function(name, age) {
  obj <- list(name = name, age = age)
  class(obj) <- "Person"
  return(obj)
}

print.Person <- function(x) {
  cat("Person:", x$name, "Age:", x$age, "\\n")
}

# Generic function
get_info <- function(obj) {
  UseMethod("get_info")
}

get_info.Person <- function(obj) {
  paste(obj$name, "is", obj$age, "years old")
}

# R6 class example
if (require(R6)) {
  DataProcessor <- R6Class("DataProcessor",
    public = list(
      data = NULL,
      initialize = function(data = NULL) {
        self$data <- data
      },
      process = function() {
        # Process data
        self$data
      }
    )
  )
}
""",
        "expected": {
            "functions": [
                "process_data",
                "calculate_mean",
                "Person",
                "print.Person",
                "get_info",
                "get_info.Person",
            ],
            "imports": 3,
        },
    },
    "sql": {
        "extension": ".sql",
        "code": """
-- PostgreSQL SQL test file
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE posts (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    published BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE VIEW active_users AS
SELECT id, username, email
FROM users
WHERE created_at > NOW() - INTERVAL '30 days';

CREATE MATERIALIZED VIEW user_stats AS
SELECT u.id, u.username, COUNT(p.id) as post_count
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
GROUP BY u.id, u.username;

CREATE FUNCTION calculate_user_score(user_id INT) RETURNS INT AS $$
BEGIN
    RETURN (SELECT COUNT(*) FROM posts WHERE posts.user_id = user_id);
END;
$$ LANGUAGE plpgsql;
""",
        "expected": {
            "tables": ["users", "posts"],
            "views": ["active_users", "user_stats"],
            "procedures": ["calculate_user_score"],
        },
    },
    "graphql": {
        "extension": ".graphql",
        "code": """
# GraphQL Schema test file
scalar DateTime

enum UserRole {
  ADMIN
  USER
  GUEST
}

interface Node {
  id: ID!
  createdAt: DateTime!
}

type User implements Node {
  id: ID!
  createdAt: DateTime!
  username: String!
  email: String!
  role: UserRole!
  posts: [Post!]!
}

type Post implements Node {
  id: ID!
  createdAt: DateTime!
  title: String!
  content: String!
  author: User!
  comments: [Comment!]!
}

type Comment {
  id: ID!
  text: String!
  author: User!
  post: Post!
}

input CreatePostInput {
  title: String!
  content: String!
}

type Query {
  user(id: ID!): User
  posts(limit: Int): [Post!]!
}

type Mutation {
  createPost(input: CreatePostInput!): Post!
}

union SearchResult = User | Post | Comment

directive @auth(requires: UserRole = ADMIN) on FIELD_DEFINITION
""",
        "expected": {
            "types": ["User", "Post", "Comment", "Query", "Mutation"],
            "interfaces": ["Node"],
            "enums": ["UserRole"],
            "inputs": ["CreatePostInput"],
        },
    },
    "kotlin": {
        "extension": ".kt",
        "code": """
package com.example.app

import kotlin.collections.List
import kotlin.collections.Map
import java.util.Date

data class Person(
    val name: String,
    val age: Int,
    val email: String
)

sealed class Result<out T> {
    data class Success<T>(val value: T) : Result<T>()
    data class Error(val message: String) : Result<Nothing>()
    object Loading : Result<Nothing>()
}

interface DataRepository {
    fun fetchData(): List<Person>
    fun saveData(person: Person): Boolean
}

class UserService(private val repository: DataRepository) {
    private val cache = mutableMapOf<String, Person>()

    fun getUser(id: String): Person? {
        return cache[id] ?: repository.fetchData().find { it.name == id }
    }

    fun saveUser(person: Person): Boolean {
        cache[person.name] = person
        return repository.saveData(person)
    }

    companion object {
        const val MAX_CACHE_SIZE = 100

        fun create(repo: DataRepository): UserService {
            return UserService(repo)
        }
    }
}

fun processData(data: List<Person>): Map<Int, List<Person>> {
    return data.groupBy { it.age }
}

suspend fun fetchRemoteData(url: String): Result<String> {
    return try {
        Result.Success("data")
    } catch (e: Exception) {
        Result.Error(e.message ?: "Unknown error")
    }
}

object AppConfig {
    const val API_VERSION = "v1"
    const val BASE_URL = "https://api.example.com"

    fun getEndpoint(path: String): String {
        return "$BASE_URL/$API_VERSION/$path"
    }
}

enum class UserRole {
    ADMIN, MODERATOR, USER, GUEST
}
""",
        "expected": {
            "classes": ["Person", "Result", "UserService", "AppConfig"],
            "functions": [
                "fetchData",
                "saveData",
                "getUser",
                "saveUser",
                "create",
                "processData",
                "fetchRemoteData",
                "getEndpoint",
            ],
            "interfaces": ["DataRepository"],
            "enums": ["UserRole"],
            "imports": 3,
        },
    },
    "dart": {
        "extension": ".dart",
        "code": """
import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';

class Person {
  final String name;
  final int age;
  final String? email;

  Person({
    required this.name,
    required this.age,
    this.email,
  });

  factory Person.fromJson(Map<String, dynamic> json) {
    return Person(
      name: json['name'] as String,
      age: json['age'] as int,
      email: json['email'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'age': age,
      'email': email,
    };
  }
}

abstract class DataRepository {
  Future<List<Person>> fetchData();
  Future<bool> saveData(Person person);
}

class UserService extends ChangeNotifier {
  final DataRepository _repository;
  final Map<String, Person> _cache = {};

  UserService(this._repository);

  Future<Person?> getUser(String id) async {
    if (_cache.containsKey(id)) {
      return _cache[id];
    }

    final users = await _repository.fetchData();
    return users.firstWhere(
      (user) => user.name == id,
      orElse: () => throw Exception('User not found'),
    );
  }

  Future<bool> saveUser(Person person) async {
    _cache[person.name] = person;
    notifyListeners();
    return await _repository.saveData(person);
  }

  static UserService create(DataRepository repo) {
    return UserService(repo);
  }
}

mixin LoggerMixin {
  void log(String message) {
    print('[${DateTime.now()}] $message');
  }
}

class DataHandler with LoggerMixin {
  void processData(String data) {
    log('Processing: $data');
  }
}

enum UserRole {
  admin,
  moderator,
  user,
  guest;

  bool get isAdmin => this == UserRole.admin;
}

extension StringExtensions on String {
  String capitalize() {
    return '${this[0].toUpperCase()}${substring(1)}';
  }
}

Future<List<T>> processItems<T>(List<T> items, Future<T> Function(T) processor) async {
  final results = <T>[];
  for (final item in items) {
    results.add(await processor(item));
  }
  return results;
}
""",
        "expected": {
            "classes": ["Person", "UserService", "DataHandler"],
            "functions": [
                "fromJson",
                "toJson",
                "fetchData",
                "saveData",
                "getUser",
                "saveUser",
                "create",
                "log",
                "processData",
                "isAdmin",
                "capitalize",
                "processItems",
            ],
            "interfaces": ["DataRepository"],
            "enums": ["UserRole"],
            "imports": 3,
        },
    },
}


def check_parser(language: str, sample: Dict) -> Tuple[bool, str, Dict]:
    """Test a specific language parser."""
    results = {
        "language": language,
        "parser_loaded": False,
        "parse_successful": False,
        "declarations_found": 0,
        "imports_found": 0,
        "errors": [],
        "parser_quality": None,
        "missed_features": [],
    }

    try:
        # Import the parser dynamically
        if language == "typescript":
            # TypeScript uses the same parser as JavaScript
            from codeconcat.parser.language_parsers.tree_sitter_js_ts_parser import (
                TreeSitterJsTsParser,
            )

            parser = TreeSitterJsTsParser(language="typescript")
        elif language == "javascript":
            from codeconcat.parser.language_parsers.tree_sitter_js_ts_parser import (
                TreeSitterJsTsParser,
            )

            parser = TreeSitterJsTsParser(language="javascript")
        elif language == "python":
            from codeconcat.parser.language_parsers.tree_sitter_python_parser import (
                TreeSitterPythonParser,
            )

            parser = TreeSitterPythonParser()
        elif language == "go":
            from codeconcat.parser.language_parsers.tree_sitter_go_parser import TreeSitterGoParser

            parser = TreeSitterGoParser()
        elif language == "rust":
            from codeconcat.parser.language_parsers.tree_sitter_rust_parser import (
                TreeSitterRustParser,
            )

            parser = TreeSitterRustParser()
        elif language == "java":
            from codeconcat.parser.language_parsers.tree_sitter_java_parser import (
                TreeSitterJavaParser,
            )

            parser = TreeSitterJavaParser()
        elif language == "csharp":
            from codeconcat.parser.language_parsers.tree_sitter_csharp_parser import (
                TreeSitterCSharpParser,
            )

            parser = TreeSitterCSharpParser()
        elif language == "cpp":
            from codeconcat.parser.language_parsers.tree_sitter_cpp_parser import (
                TreeSitterCppParser,
            )

            parser = TreeSitterCppParser()
        elif language == "php":
            from codeconcat.parser.language_parsers.tree_sitter_php_parser import (
                TreeSitterPhpParser,
            )

            parser = TreeSitterPhpParser()
        elif language == "julia":
            from codeconcat.parser.language_parsers.tree_sitter_julia_parser import (
                TreeSitterJuliaParser,
            )

            parser = TreeSitterJuliaParser()
        elif language == "r":
            from codeconcat.parser.language_parsers.tree_sitter_r_parser import TreeSitterRParser

            parser = TreeSitterRParser()
        elif language == "sql":
            from codeconcat.parser.language_parsers.tree_sitter_sql_parser import (
                TreeSitterSqlParser,
            )

            parser = TreeSitterSqlParser()
        elif language == "kotlin":
            from codeconcat.parser.language_parsers.tree_sitter_kotlin_parser import (
                TreeSitterKotlinParser,
            )

            parser = TreeSitterKotlinParser()
        elif language == "dart":
            from codeconcat.parser.language_parsers.tree_sitter_dart_parser import (
                TreeSitterDartParser,
            )

            parser = TreeSitterDartParser()
        elif language == "graphql":
            from codeconcat.parser.language_parsers.tree_sitter_graphql_parser import (
                TreeSitterGraphqlParser,
            )

            parser = TreeSitterGraphqlParser()
        else:
            results["errors"].append(f"No parser found for {language}")
            return False, f"No parser for {language}", results

        results["parser_loaded"] = True

        # Create a temporary file with the sample code
        with tempfile.NamedTemporaryFile(mode="w", suffix=sample["extension"], delete=False) as f:
            f.write(sample["code"])
            temp_file = f.name

        try:
            # Parse the code
            parse_result = parser.parse(sample["code"], temp_file)
            results["parse_successful"] = True
            results["declarations_found"] = len(parse_result.declarations)
            results["imports_found"] = len(parse_result.imports)

            # Check parser quality if available
            if hasattr(parse_result, "parser_quality"):
                results["parser_quality"] = parse_result.parser_quality
            if hasattr(parse_result, "missed_features"):
                results["missed_features"] = parse_result.missed_features

            # Extract declaration names and types
            found_classes = []
            found_functions = []
            found_other = {}

            # Special handling for SQL parser
            if language == "sql":
                # SQL parser uses specialized extraction methods
                byte_content = sample["code"].encode('utf-8')
                from codeconcat.parser.language_parsers.tree_sitter_sql_parser import (
                    TreeSitterSqlParser,
                )
                sql_parser = parser  # type: TreeSitterSqlParser

                tables = sql_parser.extract_tables(byte_content)
                views = sql_parser.extract_views(byte_content)
                procedures = sql_parser.extract_stored_procedures(byte_content)

                found_other['table'] = [t['name'] for t in tables]
                found_other['view'] = [v['name'] for v in views]
                found_other['procedure'] = [p['name'] for p in procedures]
            elif language == "graphql":
                # GraphQL parser uses specialized extraction methods
                byte_content = sample["code"].encode('utf-8')
                from codeconcat.parser.language_parsers.tree_sitter_graphql_parser import (
                    TreeSitterGraphqlParser,
                )
                graphql_parser = parser  # type: TreeSitterGraphqlParser

                types = graphql_parser.extract_type_definitions(byte_content)

                # Categorize types by kind
                found_other['type'] = [t['name'] for t in types if t['kind'] == 'object_type']
                found_other['interface'] = [t['name'] for t in types if t['kind'] == 'interface']
                found_other['enum'] = [t['name'] for t in types if t['kind'] == 'enum']
                found_other['input'] = [t['name'] for t in types if t['kind'] == 'input']
            else:
                for decl in parse_result.declarations:
                    if decl.kind == "class":
                        found_classes.append(decl.name)
                    elif decl.kind in ["function", "method"]:
                        found_functions.append(decl.name)
                    else:
                        if decl.kind not in found_other:
                            found_other[decl.kind] = []
                        found_other[decl.kind].append(decl.name)

            # Store what was found
            results["found"] = {
                "classes": found_classes,
                "functions": found_functions,
                "imports": parse_result.imports,
                "other": found_other,
            }

            # Basic validation against expected
            expected = sample.get("expected", {})
            validation_issues = []

            # SQL-specific validation
            if language == "sql":
                if "tables" in expected:
                    found_tables = set(found_other.get('table', []))
                    expected_tables = set(expected["tables"])
                    missing_tables = expected_tables - found_tables
                    if missing_tables:
                        validation_issues.append(f"Missing tables: {missing_tables}")

                if "views" in expected:
                    found_views = set(found_other.get('view', []))
                    expected_views = set(expected["views"])
                    missing_views = expected_views - found_views
                    if missing_views:
                        validation_issues.append(f"Missing views: {missing_views}")

                if "procedures" in expected:
                    found_procs = set(found_other.get('procedure', []))
                    expected_procs = set(expected["procedures"])
                    missing_procs = expected_procs - found_procs
                    if missing_procs:
                        validation_issues.append(f"Missing procedures: {missing_procs}")
            elif language == "graphql":
                # GraphQL-specific validation
                if "types" in expected:
                    found_types = set(found_other.get('type', []))
                    expected_types = set(expected["types"])
                    missing_types = expected_types - found_types
                    if missing_types:
                        validation_issues.append(f"Missing types: {missing_types}")

                if "interfaces" in expected:
                    found_interfaces = set(found_other.get('interface', []))
                    expected_interfaces = set(expected["interfaces"])
                    missing_interfaces = expected_interfaces - found_interfaces
                    if missing_interfaces:
                        validation_issues.append(f"Missing interfaces: {missing_interfaces}")

                if "enums" in expected:
                    found_enums = set(found_other.get('enum', []))
                    expected_enums = set(expected["enums"])
                    missing_enums = expected_enums - found_enums
                    if missing_enums:
                        validation_issues.append(f"Missing enums: {missing_enums}")

                if "inputs" in expected:
                    found_inputs = set(found_other.get('input', []))
                    expected_inputs = set(expected["inputs"])
                    missing_inputs = expected_inputs - found_inputs
                    if missing_inputs:
                        validation_issues.append(f"Missing inputs: {missing_inputs}")
            else:
                # Standard validation for other languages
                if "classes" in expected:
                    missing_classes = set(expected["classes"]) - set(found_classes)
                    if missing_classes:
                        validation_issues.append(f"Missing classes: {missing_classes}")

                if "functions" in expected:
                    missing_funcs = set(expected["functions"]) - set(found_functions)
                    if missing_funcs and len(missing_funcs) > len(expected["functions"]) * 0.5:
                        validation_issues.append(f"Missing many functions: {missing_funcs}")

            if validation_issues:
                results["validation_issues"] = validation_issues

            # Check for parse errors
            if parse_result.error:
                results["errors"].append(f"Parse error: {parse_result.error}")
                return False, f"Parse error: {parse_result.error}", results

            return True, "Success", results

        finally:
            # Clean up temp file
            os.unlink(temp_file)

    except ImportError as e:
        results["errors"].append(f"Failed to import parser: {e}")
        return False, f"Import error: {e}", results
    except Exception as e:
        results["errors"].append(f"Unexpected error: {e}")
        return False, f"Error: {e}", results


def test_all_tree_sitter_parsers_comprehensive():
    print("=" * 80)
    print("Testing All Tree-Sitter Parsers in CodeConCat")
    print("=" * 80)

    # Check if tree-sitter is available
    try:
        import tree_sitter

        print(
            f"✓ tree-sitter version: {tree_sitter.__version__ if hasattr(tree_sitter, '__version__') else 'unknown'}"
        )
    except ImportError:
        print("✗ tree-sitter not installed")
        print("Install with: pip install tree-sitter tree-sitter-language-pack")
        return

    # Check if tree-sitter language modules are available
    import importlib.util

    tree_sitter_languages_available = importlib.util.find_spec("tree_sitter_languages") is not None
    tree_sitter_language_pack_available = (
        importlib.util.find_spec("tree_sitter_language_pack") is not None
    )

    if tree_sitter_languages_available:
        print("✓ tree-sitter-languages available")
    elif tree_sitter_language_pack_available:
        print("✓ tree-sitter-language-pack available")
    else:
        print("✗ tree-sitter language module not installed")
        print("Install with: pip install tree-sitter-languages")

    print("\n" + "=" * 80)

    # Test each language
    all_results = []
    languages_to_test = list(LANGUAGE_SAMPLES.keys())

    for language in languages_to_test:
        sample = LANGUAGE_SAMPLES[language]
        print(f"\nTesting {language.upper()} parser...")
        print("-" * 40)

        success, message, results = check_parser(language, sample)
        all_results.append(results)

        # Print results
        if success:
            print(f"✓ Parser loaded: {results['parser_loaded']}")
            print(f"✓ Parse successful: {results['parse_successful']}")
            print(f"  - Declarations found: {results['declarations_found']}")
            print(f"  - Imports found: {results['imports_found']}")
            if results.get("parser_quality"):
                print(f"  - Parser quality: {results['parser_quality']}")
            if results.get("validation_issues"):
                print(f"  ⚠ Validation issues: {', '.join(results['validation_issues'])}")
        else:
            print(f"✗ Test failed: {message}")
            if results["errors"]:
                for error in results["errors"]:
                    print(f"  - {error}")

        # Show what was found if available
        if results.get("found"):
            found = results["found"]
            if found.get("classes"):
                print(f"  - Classes: {', '.join(found['classes'])}")
            if found.get("functions"):
                print(
                    f"  - Functions: {', '.join(found['functions'][:5])}"
                    + (
                        f"... (+{len(found['functions']) - 5} more)"
                        if len(found["functions"]) > 5
                        else ""
                    )
                )
            if found.get("other"):
                for kind, items in found["other"].items():
                    print(
                        f"  - {kind.capitalize()}s: {', '.join(items[:3])}"
                        + (f"... (+{len(items) - 3} more)" if len(items) > 3 else "")
                    )

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    successful = sum(1 for r in all_results if r["parse_successful"])
    total = len(all_results)

    print(f"\nParsers tested: {total}")
    print(f"Successful: {successful}/{total}")
    print(f"Failed: {total - successful}/{total}")

    if total - successful > 0:
        print("\nFailed parsers:")
        for r in all_results:
            if not r["parse_successful"]:
                print(
                    f"  - {r['language']}: {', '.join(r['errors']) if r['errors'] else 'Unknown error'}"
                )

    # Quality summary
    quality_stats = {}
    for r in all_results:
        if r.get("parser_quality"):
            quality = r["parser_quality"]
            quality_stats[quality] = quality_stats.get(quality, 0) + 1

    if quality_stats:
        print("\nParser quality distribution:")
        for quality, count in quality_stats.items():
            print(f"  - {quality}: {count}")

    # Save detailed results to JSON
    output_file = "tree_sitter_parser_test_results.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    test_all_tree_sitter_parsers_comprehensive()
