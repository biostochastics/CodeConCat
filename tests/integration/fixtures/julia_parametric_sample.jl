# Julia Parametric Types Test Fixture
# This file tests parametric type detection in the Julia parser

# ===== Parametric Struct Definitions =====
"""
A point in 2D space with parametric type
"""
struct Point{T}
    x::T
    y::T
end

# Parametric struct with constraints
struct BoundedValue{T<:Real}
    value::T
    min::T
    max::T
end

# Multi-parameter struct
struct Pair{T, S}
    first::T
    second::S
end

# Nested parametric types
struct Container{T}
    data::Vector{T}
    metadata::Dict{String, Any}
end

# ===== Parametric Abstract Types =====
"""
Abstract numeric type with parameter
"""
abstract type Number{T} end

abstract type Pointy{T<:Real} end

# ===== Parametric Functions with where Clauses =====
"""
Identity function with type parameter
"""
function identity(x::T) where T
    return x
end

# Multiple type parameters
function process(a::T, b::S) where {T, S}
    (a, b)
end

# Type constraints in where clause
function clamp_value(x::T, min::T, max::T) where T<:Real
    return min < x < max ? x : (x < min ? min : max)
end

# Nested where clauses
function complex_func(x::T, y::S) where {T<:Number, S<:Number}
    x + y
end

# ===== Short-form Parametric Functions =====
square(x::T) where T<:Number = x * x

add(a::T, b::T) where T = a + b

# ===== Return Type Annotations with Parameters =====
function get_vector(n::Int)::Vector{Float64}
    zeros(n)
end

function make_pair(a::T, b::S)::Pair{T,S} where {T,S}
    Pair(a, b)
end

# ===== Complex Nested Parametric Types =====
struct Graph{V, E}
    vertices::Vector{V}
    edges::Vector{Tuple{Int, Int, E}}
end

function build_graph(vertices::Vector{T}) where T
    Graph{T, Float64}(vertices, Tuple{Int,Int,Float64}[])
end

# Deeply nested parametric type
struct NestedContainer{T}
    data::Dict{String, Vector{Tuple{Int, T}}}
end

# ===== Regular (Non-parametric) Definitions for Comparison =====
# Simple struct without parameters
struct SimplePoint
    x::Float64
    y::Float64
end

# Simple abstract type
abstract type Shape end

# Regular function without parameters
function simple_add(a, b)
    a + b
end

# ===== Mutable Parametric Structs =====
mutable struct MutablePoint{T<:Real}
    x::T
    y::T
end

# ===== Parametric Type Aliases =====
const StringDict{T} = Dict{String, T}
const NumberPair{T<:Number} = Tuple{T, T}
