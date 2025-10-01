# R S3/S4 OOP Test Fixture
# This file tests S3/S4 class detection in the R parser

# ===== S3 Methods with <- operator =====
#' Print method for my custom class
print.myclass <- function(x, ...) {
  cat("MyClass object\n")
}

# S3 method with = operator
summary.myclass = function(object, ...) {
  cat("Summary of MyClass\n")
}

# S3 method with operator/bracket generics
`[.myclass` <- function(x, i) {
  x[[i]]
}

`+.myclass` <- function(e1, e2) {
  e1$value + e2$value
}

# ===== S3 Generics with UseMethod() =====
#' Generic function for processing data
process <- function(x, ...) {
  UseMethod("process")
}

#' Another generic
transform <- function(x) UseMethod("transform")

# ===== S4 Class Definitions =====
# Simple S4 class
setClass("Person",
  slots = c(
    name = "character",
    age = "numeric"
  )
)

# S4 class with namespace
methods::setClass("Employee",
  slots = c(
    name = "character",
    salary = "numeric",
    department = "character"
  ),
  contains = "Person"
)

# ===== S4 Methods =====
setMethod("show", "Person",
  function(object) {
    cat("Person:", object@name, "\n")
  }
)

# S4 method with namespace
methods::setMethod("initialize", "Employee",
  function(.Object, name, salary, department) {
    .Object@name <- name
    .Object@salary <- salary
    .Object@department <- department
    .Object
  }
)

# ===== S4 Generics =====
setGeneric("getInfo", function(object) standardGeneric("getInfo"))

methods::setGeneric("updateSalary",
  function(object, amount) standardGeneric("updateSalary")
)

# ===== Mixed Patterns =====
# Regular function (not S3/S4)
calculate_sum <- function(a, b) {
  a + b
}

# Constant (not S3/S4)
MAX_ITERATIONS <- 1000

# S3 method that looks like regular function
data.frame.custom <- function() {
  # This should be detected as S3 method
}
