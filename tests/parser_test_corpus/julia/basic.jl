#!/usr/bin/env julia

"""
Basic Julia test file for parser validation.

This file contains common Julia constructs that should be properly parsed.
"""

module TestModule

# Import standard libraries
using LinearAlgebra
using Statistics
import Base: show, +

export Person, Employee, greet, calculateStats

"""
    const PI = 3.14159

The mathematical constant pi, approximately.
"""
const PI = 3.14159

"""
    const MAX_RETRIES = 3

Maximum number of retry attempts.
"""
const MAX_RETRIES = 3

"""
    mutable struct Person
        name::String
        age::Int
        address::Union{String, Nothing}
    end

Represents a person with name, age, and optional address.
"""
mutable struct Person
    name::String
    age::Int
    address::Union{String, Nothing}
    
    """
        Person(name::String, age::Int)
    
    Create a new Person with the given name and age.
    """
    function Person(name::String, age::Int)
        new(name, age, nothing)
    end
end

"""
    greet(p::Person)

Return a greeting message from the person.
"""
function greet(p::Person)
    return "Hello, my name is $(p.name) and I am $(p.age) years old."
end

"""
    setAddress!(p::Person, address::String)

Set the person's address.
"""
function setAddress!(p::Person, address::String)
    p.address = address
end

"""
    getAddress(p::Person)

Get the person's address or a default message if not set.
"""
function getAddress(p::Person)
    return p.address === nothing ? "Address not set" : p.address
end

"""
    mutable struct Employee <: Person
        title::String
        salary::Float64
    end

Employee extends Person with job-related fields.
"""
mutable struct Employee <: Person
    name::String
    age::Int
    address::Union{String, Nothing}
    title::String
    salary::Float64
    
    """
        Employee(name::String, age::Int, title::String, salary::Float64)
    
    Create a new Employee with the given attributes.
    """
    function Employee(name::String, age::Int, title::String, salary::Float64)
        new(name, age, nothing, title, salary)
    end
end

"""
    giveRaise!(e::Employee, percentage::Float64)

Give a raise to the employee by the specified percentage.
"""
function giveRaise!(e::Employee, percentage::Float64)
    e.salary *= (1.0 + percentage / 100.0)
end

"""
    workInfo(e::Employee)

Return information about the employee's job.
"""
function workInfo(e::Employee)
    return "I work as a $(e.title) and earn \$$(e.salary) per year."
end

"""
    greet(e::Employee)

Override the greet method for Employee.
"""
function greet(e::Employee)
    return "$(greet(e)) I work as a $(e.title)."
end

"""
    abstract type Processor end

Abstract type for data processors.
"""
abstract type Processor end

"""
    process(p::Processor, data::Vector{UInt8})

Process the given data.
"""
function process(p::Processor, data::Vector{UInt8})
    error("Subclasses must implement process")
end

"""
    getStats(p::Processor)

Get processing statistics.
"""
function getStats(p::Processor)
    error("Subclasses must implement getStats")
end

"""
    mutable struct SimpleProcessor <: Processor
        count::Int
    end

Simple implementation of the Processor abstract type.
"""
mutable struct SimpleProcessor <: Processor
    count::Int
    
    SimpleProcessor() = new(0)
end

"""
    process(p::SimpleProcessor, data::Vector{UInt8})

Process the data by adding a prefix.
"""
function process(p::SimpleProcessor, data::Vector{UInt8})
    if isempty(data)
        throw(ArgumentError("Empty data"))
    end
    
    p.count += 1
    result = Vector{UInt8}("Processed: ")
    return vcat(result, data)
end

"""
    getStats(p::SimpleProcessor)

Return the count of successful processing operations.
"""
function getStats(p::SimpleProcessor)
    return Dict("count" => p.count)
end

"""
    calculateStats(numbers::Vector{Int})

Calculate statistics for a list of numbers.

# Arguments
- `numbers`: A vector of integers

# Returns
A tuple containing the minimum, maximum, and average values,
or nothing if the input is empty.
"""
function calculateStats(numbers::Vector{Int})
    if isempty(numbers)
        return nothing
    end
    
    min_val = minimum(numbers)
    max_val = maximum(numbers)
    avg_val = mean(numbers)
    
    return (min=min_val, max=max_val, avg=avg_val)
end

"""
    divide(a::Int, b::Int)

Divide two numbers and return the result.

# Arguments
- `a`: The dividend
- `b`: The divisor

# Returns
The result of dividing a by b,
or throws a DivideError if b is zero.
"""
function divide(a::Int, b::Int)
    if b == 0
        throw(DivideError())
    end
    
    return div(a, b)
end

"""
    macro twice(ex)

A macro that evaluates an expression twice.
"""
macro twice(ex)
    quote
        $(esc(ex))
        $(esc(ex))
    end
end

# Example usage when run as a script
if abspath(PROGRAM_FILE) == @__FILE__
    # Create a person
    person = Person("John", 30)
    setAddress!(person, "123 Main St")
    println(greet(person))
    
    # Create an employee
    employee = Employee("Jane", 28, "Software Engineer", 100000.0)
    giveRaise!(employee, 10.0)
    println(workInfo(employee))
    println(greet(employee))
    
    # Use the processor
    processor = SimpleProcessor()
    try
        result = process(processor, Vector{UInt8}("test data"))
        println(String(result))
    catch e
        println("Error: $(e)")
    end
    
    # Use standalone functions
    numbers = [3, 7, 2, 9, 5]
    stats = calculateStats(numbers)
    if stats !== nothing
        println("Min: $(stats.min), Max: $(stats.max), Avg: $(stats.avg)")
    end
    
    try
        result = divide(10, 2)
        println("10 / 2 = $(result)")
    catch e
        println("Error: $(e)")
    end
    
    # Use constants
    println("PI: $(PI)")
    println("MAX_RETRIES: $(MAX_RETRIES)")
    
    # Use the macro
    @twice println("This prints twice")
end

end # module TestModule
