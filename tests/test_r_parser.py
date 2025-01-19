import unittest
from codeconcat.parser.language_parsers.r_parser import RParser, parse_r


class TestRParser(unittest.TestCase):
    def setUp(self):
        self.parser = RParser()

    def test_function_declarations(self):
        r_code = """
        # Different assignment styles
        func1 <- function(x) { x + 1 }
        func2 = function(x) { x + 1 }
        function(x) -> func3
        
        # Function with comments and spaces
        complex_func <- # comment
          function(x) {
            x + 1
        }
        """
        declarations = self.parser.parse(r_code)
        func_names = {d.name for d in declarations if d.kind == "function"}
        self.assertEqual(func_names, {"func1", "func2", "func3", "complex_func"})

    def test_class_declarations(self):
        r_code = """
        # S4 class
        setClass("MyS4Class", slots = list(x = "numeric"))
        
        # S3 class
        MyS3Class <- function(x) {
            obj <- list(x = x)
            class(obj) <- "MyS3Class"
            obj
        }
        
        # S4 method
        setGeneric("myMethod", function(x) standardGeneric("myMethod"))
        setMethod("myMethod", "MyS4Class", function(x) x@x)
        """
        declarations = self.parser.parse(r_code)
        class_names = {d.name for d in declarations if d.kind == "class"}
        method_names = {d.name for d in declarations if d.kind == "method"}
        self.assertEqual(class_names, {"MyS4Class", "MyS3Class"})
        self.assertEqual(method_names, {"myMethod"})

    def test_package_imports(self):
        r_code = """
        library(dplyr)
        library("tidyr")
        require(ggplot2)
        require("data.table")
        
        # Namespace operators
        dplyr::select
        data.table:::fread
        """
        declarations = self.parser.parse(r_code)
        package_names = {d.name for d in declarations if d.kind == "package"}
        self.assertEqual(package_names, {"dplyr", "tidyr", "ggplot2", "data.table"})

    def test_nested_functions(self):
        r_code = """
        outer <- function() {
            inner1 <- function() {
                inner2 <- function() {
                    x + 1
                }
                inner2
            }
            inner1
        }
        """
        declarations = self.parser.parse(r_code)
        func_names = {d.name for d in declarations if d.kind == "function"}
        self.assertEqual(func_names, {"outer", "inner1", "inner2"})

    def test_r6_class(self):
        r_code = """
        # R6 class with methods
        Calculator <- R6Class("Calculator",
            public = list(
                value = 0,
                add = function(x) {
                    self$value <- self$value + x
                },
                subtract = function(x) {
                    self$value <- self$value - x
                }
            )
        )
        """
        declarations = self.parser.parse(r_code)
        class_decls = [d for d in declarations if d.kind == "class"]
        method_decls = [d for d in declarations if d.kind == "method"]

        self.assertEqual(len(class_decls), 1)
        self.assertEqual(class_decls[0].name, "Calculator")
        self.assertEqual({m.name for m in method_decls}, {"Calculator.add", "Calculator.subtract"})

    def test_reference_class(self):
        r_code = """
        # Reference class with methods
        setRefClass("Employee",
            fields = list(
                name = "character",
                salary = "numeric"
            ),
            methods = list(
                raise = function(amount) {
                    salary <<- salary + amount
                },
                get_info = function() {
                    paste(name, salary)
                }
            )
        )
        """
        declarations = self.parser.parse(r_code)
        class_decls = [d for d in declarations if d.kind == "class"]
        method_decls = [d for d in declarations if d.kind == "method"]

        self.assertEqual(len(class_decls), 1)
        self.assertEqual(class_decls[0].name, "Employee")
        self.assertEqual({m.name for m in method_decls}, {"Employee.raise", "Employee.get_info"})

    def test_modifiers(self):
        r_code = """
        #' @export
        #' @internal
        process_data <- function(data) {
            data
        }
        
        #' @export
        MyClass <- R6Class("MyClass")
        """
        declarations = self.parser.parse(r_code)

        process_data = next(d for d in declarations if d.name == "process_data")
        my_class = next(d for d in declarations if d.name == "MyClass")

        self.assertEqual(process_data.modifiers, {"export", "internal"})
        self.assertEqual(my_class.modifiers, {"export"})

    def test_s3_methods(self):
        r_code = """
        # S3 class methods
        print.myclass <- function(x) {
            cat("MyClass object\\n")
        }
        
        plot.myclass = function(x, y, ...) {
            plot(x$data)
        }
        
        summary.myclass -> function(object) {
            list(object)
        }
        """
        declarations = self.parser.parse(r_code)
        method_names = {d.name for d in declarations if d.kind == "method"}

        expected_methods = {"print.myclass", "plot.myclass", "summary.myclass"}
        self.assertEqual(method_names, expected_methods)

    def test_complex_assignments(self):
        r_code = """
        # Various assignment operators
        func1 <- function(x) x
        func2 = function(x) x
        func3 <<- function(x) x
        function(x) -> func4
        function(x) ->> func5
        func6 := function(x) x
        """
        declarations = self.parser.parse(r_code)
        func_names = {d.name for d in declarations if d.kind == "function"}

        expected_funcs = {"func1", "func2", "func3", "func4", "func5", "func6"}
        self.assertEqual(func_names, expected_funcs)

    def test_dollar_notation_methods(self):
        r_code = """
        # Methods using $ notation
        Employee$get_salary <- function(x) {
            x$salary
        }
        
        Employee$set_salary <- function(x, value) {
            x$salary <- value
        }
        
        # Mixed dot and $ notation
        Employee.Department$get_manager <- function(x) {
            x$manager
        }
        """
        declarations = self.parser.parse(r_code)
        method_names = {d.name for d in declarations if d.kind == "method"}

        expected_methods = {
            "Employee$get_salary",
            "Employee$set_salary",
            "Employee.Department$get_manager",
        }
        self.assertEqual(method_names, expected_methods)

    def test_object_methods_with_dots(self):
        r_code = """
        # Object methods using dot notation
        Employee.new <- function(name, salary) {
            list(name = name, salary = salary)
        }
        
        Employee.get_info <- function(self) {
            paste(self$name, self$salary)
        }
        
        # Nested object methods
        Department.Employee.create <- function(dept, name) {
            list(department = dept, name = name)
        }
        """
        declarations = self.parser.parse(r_code)
        method_names = {d.name for d in declarations if d.kind == "method"}

        expected_methods = {"Employee.new", "Employee.get_info", "Department.Employee.create"}
        self.assertEqual(method_names, expected_methods)


if __name__ == "__main__":
    unittest.main()
