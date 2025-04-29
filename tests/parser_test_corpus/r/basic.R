#' Basic R test file for parser validation.
#' 
#' This file contains common R constructs that should be properly parsed.

# Load libraries
library(stats)
library(utils)
require(graphics)

#' The mathematical constant pi, approximately.
PI <- 3.14159

#' Maximum number of retry attempts.
MAX_RETRIES <- 3

#' Person class for representing humans with name and age.
#' 
#' @field name Character string for person's name
#' @field age Numeric age in years
#' @field address Optional character string for address
Person <- R6::R6Class("Person",
  public = list(
    #' @field name Person's name
    name = NULL,
    
    #' @field age Person's age
    age = NULL,
    
    #' @field address Person's address (optional)
    address = NULL,
    
    #' @description
    #' Create a new person instance.
    #' 
    #' @param name The person's name
    #' @param age The person's age
    initialize = function(name, age) {
      self$name <- name
      self$age <- age
      self$address <- NULL
    },
    
    #' @description
    #' Get a greeting from the person.
    #' 
    #' @return A greeting string
    greet = function() {
      return(paste0("Hello, my name is ", self$name, " and I am ", self$age, " years old."))
    },
    
    #' @description
    #' Set the person's address.
    #' 
    #' @param address The address to set
    set_address = function(address) {
      self$address <- address
    },
    
    #' @description
    #' Get the person's address or a default message.
    #' 
    #' @return The address or a default message
    get_address = function() {
      return(if (is.null(self$address)) "Address not set" else self$address)
    }
  )
)

#' Employee class extending Person with job information.
#' 
#' @field title Employee's job title
#' @field salary Employee's annual salary
Employee <- R6::R6Class("Employee",
  inherit = Person,
  public = list(
    #' @field title Job title
    title = NULL,
    
    #' @field salary Annual salary
    salary = NULL,
    
    #' @description
    #' Create a new employee instance.
    #' 
    #' @param name The person's name
    #' @param age The person's age
    #' @param title The job title
    #' @param salary The annual salary
    initialize = function(name, age, title, salary) {
      super$initialize(name, age)
      self$title <- title
      self$salary <- salary
    },
    
    #' @description
    #' Give the employee a raise.
    #' 
    #' @param percentage The percentage to increase the salary
    give_raise = function(percentage) {
      self$salary <- self$salary * (1 + percentage / 100)
    },
    
    #' @description
    #' Get information about the employee's job.
    #' 
    #' @return A string with job information
    work_info = function() {
      return(paste0("I work as a ", self$title, " and earn $", self$salary, " per year."))
    },
    
    #' @description
    #' Override the parent's greet method.
    #' 
    #' @return An enhanced greeting string
    greet = function() {
      parent_greeting <- super$greet()
      return(paste0(parent_greeting, " I work as a ", self$title, "."))
    }
  )
)

#' Simple S3 class for data processing.
#' 
#' @param count Number of successful processing operations
#' @return A new SimpleProcessor object
new_simple_processor <- function() {
  structure(
    list(
      count = 0
    ),
    class = "SimpleProcessor"
  )
}

#' Process data with SimpleProcessor.
#' 
#' @param processor The SimpleProcessor object
#' @param data The data to process
#' @return The processed data
#' @export
process.SimpleProcessor <- function(processor, data) {
  if (length(data) == 0) {
    stop("Empty data")
  }
  
  processor$count <- processor$count + 1
  cat("Processing data:", substr(data, 1, min(20, nchar(data))), "...\n")
  
  return(paste0("Processed: ", data))
}

#' Get processing statistics.
#' 
#' @param processor The SimpleProcessor object
#' @return A list with statistics
#' @export
get_stats.SimpleProcessor <- function(processor) {
  return(list(count = processor$count))
}

#' Print method for SimpleProcessor.
#' 
#' @param x The SimpleProcessor object
#' @param ... Additional arguments
#' @export
print.SimpleProcessor <- function(x, ...) {
  cat("SimpleProcessor with count:", x$count, "\n")
}

#' Calculate statistics for a vector of numbers.
#' 
#' @param numbers Vector of numeric values
#' @return A list containing min, max, and average, or NULL if empty
#' @examples
#' calculateStats(c(3, 7, 2, 9, 5))
calculateStats <- function(numbers) {
  if (length(numbers) == 0) {
    return(NULL)
  }
  
  min_val <- min(numbers)
  max_val <- max(numbers)
  avg_val <- mean(numbers)
  
  return(list(min = min_val, max = max_val, avg = avg_val))
}

#' Divide two numbers and return the result.
#' 
#' @param a The dividend
#' @param b The divisor
#' @return The result of the division
#' @examples
#' divide(10, 2)
divide <- function(a, b) {
  if (b == 0) {
    stop("Division by zero")
  }
  
  return(a / b)
}

#' S4 class for advanced data processing.
#' 
#' @slot name Name of the processor
#' @slot count Number of operations performed
setClass("AdvancedProcessor",
  slots = c(
    name = "character",
    count = "numeric"
  ),
  prototype = list(
    name = "default",
    count = 0
  )
)

#' Initialize a new AdvancedProcessor
#' 
#' @param name Name for the processor
#' @return A new AdvancedProcessor object
#' @export
setMethod("initialize", "AdvancedProcessor",
  function(.Object, name = "default") {
    .Object@name <- name
    .Object@count <- 0
    return(.Object)
  }
)

#' Process data with an AdvancedProcessor
#' 
#' @param processor The AdvancedProcessor object
#' @param data The data to process
#' @return The processed data
#' @export
setGeneric("processData", function(processor, data) standardGeneric("processData"))

#' @describeIn processData Process data with AdvancedProcessor
setMethod("processData", "AdvancedProcessor",
  function(processor, data) {
    if (length(data) == 0) {
      stop("Empty data")
    }
    
    processor@count <- processor@count + 1
    return(paste0("[", processor@name, "] Processed: ", data))
  }
)

# Example usage in a script context
if (interactive()) {
  # Create a person
  person <- Person$new("John", 30)
  person$set_address("123 Main St")
  cat(person$greet(), "\n")
  
  # Create an employee
  employee <- Employee$new("Jane", 28, "Software Engineer", 100000)
  employee$give_raise(10)
  cat(employee$work_info(), "\n")
  cat(employee$greet(), "\n")
  
  # Use the S3 processor
  processor <- new_simple_processor()
  tryCatch({
    result <- process.SimpleProcessor(processor, "test data")
    cat(result, "\n")
  }, error = function(e) {
    cat("Error:", conditionMessage(e), "\n")
  })
  
  # Use the S4 processor
  advanced <- new("AdvancedProcessor", name = "advanced")
  tryCatch({
    result <- processData(advanced, "test data")
    cat(result, "\n")
  }, error = function(e) {
    cat("Error:", conditionMessage(e), "\n")
  })
  
  # Use standalone functions
  numbers <- c(3, 7, 2, 9, 5)
  stats <- calculateStats(numbers)
  if (!is.null(stats)) {
    cat("Min:", stats$min, ", Max:", stats$max, ", Avg:", stats$avg, "\n")
  }
  
  tryCatch({
    result <- divide(10, 2)
    cat("10 / 2 =", result, "\n")
  }, error = function(e) {
    cat("Error:", conditionMessage(e), "\n")
  })
  
  # Use constants
  cat("PI:", PI, "\n")
  cat("MAX_RETRIES:", MAX_RETRIES, "\n")
}
