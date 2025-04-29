#!/usr/bin/env julia

"""
Advanced Julia nested functions test file.

This file contains complex nested Julia constructs to test parser capabilities.
"""

module NestedFunctionsTest

using LinearAlgebra

export process_data, run_analysis

"""
    process_data(data::Vector{Float64})

Process a vector of data with multiple nested functions.

# Arguments
- `data`: Vector of floating point values to process

# Returns
A processed result with statistics
"""
function process_data(data::Vector{Float64})
    # Local nested function for normalization
    function normalize(values)
        """
        Normalize values to [0,1] range
        """
        min_val = minimum(values)
        max_val = maximum(values)
        return [(x - min_val) / (max_val - min_val) for x in values]
    end
    
    # Another nested function for filtering
    function filter_outliers(values; threshold=2.5)
        """
        Remove outliers beyond threshold standard deviations
        """
        μ = mean(values)
        σ = std(values)
        return filter(x -> abs(x - μ) <= threshold * σ, values)
    end
    
    # Multiple levels of nesting
    function calculate_stats(values)
        """
        Calculate statistics on the values
        """
        # Deepest level of nesting
        function weighted_average(xs, ws)
            """
            Calculate weighted average
            """
            @assert length(xs) == length(ws) "Lengths must match"
            return sum(xs .* ws) / sum(ws)
        end
        
        basic_stats = (
            min = minimum(values),
            max = maximum(values),
            mean = mean(values),
            median = median(values)
        )
        
        # Create some weights for demonstration
        weights = [i for i in 1:length(values)]
        basic_stats = merge(basic_stats, (weighted_avg = weighted_average(values, weights),))
        
        return basic_stats
    end
    
    # Process the data using the nested functions
    normalized = normalize(data)
    filtered = filter_outliers(normalized)
    stats = calculate_stats(filtered)
    
    return (
        original_length = length(data),
        filtered_length = length(filtered),
        stats = stats
    )
end

"""
    Module NestedModule

A module nested inside another module.
"""
module NestedModule
    export transform_data
    
    """
        transform_data(data::Vector{Float64})
    
    Transform data using matrix operations.
    """
    function transform_data(data::Vector{Float64})
        # Nested function inside a nested module
        function create_transform_matrix(dim)
            return rand(dim, dim)
        end
        
        dim = length(data)
        matrix = create_transform_matrix(dim)
        return matrix * data
    end
end # nested module

"""
    run_analysis(data::Vector{Float64})

Run a full analysis on the data.
"""
function run_analysis(data::Vector{Float64})
    processed = process_data(data)
    transformed = NestedModule.transform_data(data)
    
    return (processed = processed, transformed = transformed)
end

# Struct with nested methods
"""
    struct DataProcessor
        name::String
        options::Dict{Symbol, Any}
    end

Data processor with configurable options.
"""
struct DataProcessor
    name::String
    options::Dict{Symbol, Any}
    
    """
        DataProcessor(name::String)
    
    Create a new DataProcessor with default options.
    """
    function DataProcessor(name::String)
        default_options = Dict{Symbol, Any}(
            :normalize => true,
            :filter_outliers => true
        )
        new(name, default_options)
    end
    
    """
        DataProcessor(name::String, options::Dict{Symbol, Any})
    
    Create a new DataProcessor with custom options.
    """
    function DataProcessor(name::String, options::Dict{Symbol, Any})
        new(name, options)
    end
end

"""
    process(dp::DataProcessor, data::Vector{Float64})

Process data using the processor's configuration.
"""
function process(dp::DataProcessor, data::Vector{Float64})
    # Local function that uses object properties
    function apply_options(data)
        result = copy(data)
        
        if get(dp.options, :normalize, false)
            result = (result .- minimum(result)) ./ (maximum(result) - minimum(result))
        end
        
        if get(dp.options, :filter_outliers, false)
            # Nested function inside another nested function
            function is_outlier(x, values)
                μ = mean(values)
                σ = std(values)
                threshold = get(dp.options, :outlier_threshold, 2.5)
                return abs(x - μ) > threshold * σ
            end
            
            result = filter(x -> !is_outlier(x, result), result)
        end
        
        return result
    end
    
    return apply_options(data)
end

end # module NestedFunctionsTest
