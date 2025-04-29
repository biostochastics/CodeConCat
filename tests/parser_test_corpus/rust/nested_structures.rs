// Advanced Rust test file with nested structures
// 
// This file tests complex nested declarations in Rust

use std::collections::HashMap;

/// A struct with a nested impl that contains nested functions
pub struct NestedExample {
    counter: u32,
    data: HashMap<String, String>,
}

impl NestedExample {
    /// Creates a new NestedExample
    pub fn new() -> Self {
        // Nested closure within function
        let init_counter = || {
            let base = 10;
            base * 2
        };
        
        Self {
            counter: init_counter(),
            data: HashMap::new(),
        }
    }
    
    /// Process data with nested functions and closures
    pub fn process_data(&mut self, input: &str) -> String {
        // Inner function inside another function
        fn tokenize(s: &str) -> Vec<&str> {
            s.split_whitespace().collect()
        }
        
        // Another nested function
        fn calculate_score(tokens: &[&str]) -> u32 {
            // Third level of nesting
            fn word_value(word: &str) -> u32 {
                word.chars().map(|c| c as u32).sum::<u32>() % 100
            }
            
            tokens.iter().map(|t| word_value(t)).sum()
        }
        
        let tokens = tokenize(input);
        self.counter += calculate_score(&tokens);
        
        // Nested closure with captured variables
        let formatter = |tokens: &[&str], counter: u32| {
            let mut result = String::new();
            for t in tokens {
                result.push_str(&format!("{}:{}, ", t, counter));
            }
            result
        };
        
        formatter(&tokens, self.counter)
    }
    
    /// Method with nested trait implementation
    pub fn create_processor(&self) -> impl FnMut(&str) -> String {
        let counter = self.counter;
        
        // Return a closure that processes strings
        move |input: &str| {
            // Nested function inside closure
            fn sanitize(s: &str) -> String {
                s.chars()
                 .filter(|c| c.is_alphanumeric() || c.is_whitespace())
                 .collect()
            }
            
            let clean_input = sanitize(input);
            format!("Processed [{}]: {}", counter, clean_input)
        }
    }
}

/// A trait with default implementations that contain nested functions
pub trait ComplexProcessor {
    fn process(&self, data: &[u8]) -> Vec<u8>;
    
    fn analyze(&self, data: &[u8]) -> HashMap<String, u32> {
        // Default implementation with nested function
        fn count_occurrences(bytes: &[u8]) -> HashMap<u8, u32> {
            let mut counts = HashMap::new();
            for &b in bytes {
                *counts.entry(b).or_insert(0) += 1;
            }
            counts
        }
        
        let byte_counts = count_occurrences(data);
        
        // Nested closure
        let summarize = |counts: HashMap<u8, u32>| {
            let mut result = HashMap::new();
            result.insert("total_bytes".to_string(), data.len() as u32);
            result.insert("unique_bytes".to_string(), counts.len() as u32);
            
            // Find most common byte
            if !counts.is_empty() {
                let most_common = counts.iter()
                    .max_by_key(|&(_, count)| count)
                    .map(|(&byte, &count)| (byte, count))
                    .unwrap();
                    
                result.insert("most_common_byte".to_string(), most_common.0 as u32);
                result.insert("most_common_count".to_string(), most_common.1);
            }
            
            result
        };
        
        summarize(byte_counts)
    }
}

/// Implementation of ComplexProcessor
pub struct AdvancedProcessor {
    name: String,
}

impl AdvancedProcessor {
    pub fn new(name: String) -> Self {
        Self { name }
    }
}

impl ComplexProcessor for AdvancedProcessor {
    fn process(&self, data: &[u8]) -> Vec<u8> {
        // Nested closures and blocks
        let transformer = |chunk: &[u8]| {
            // Nested function in implementation
            fn transform_byte(b: u8) -> u8 {
                if b.is_ascii_alphabetic() {
                    // Nested block with its own variables
                    {
                        let offset = if b.is_ascii_lowercase() { b'a' } else { b'A' };
                        let position = (b - offset + 1) % 26;
                        offset + position
                    }
                } else {
                    b
                }
            }
            
            chunk.iter().map(|&b| transform_byte(b)).collect::<Vec<_>>()
        };
        
        // Process in chunks
        let chunk_size = 8;
        let mut result = Vec::with_capacity(data.len());
        
        for chunk in data.chunks(chunk_size) {
            result.extend_from_slice(&transformer(chunk));
        }
        
        result
    }
}

/// Function with nested functions and closures
pub fn advanced_processing(data: &str) -> Result<String, String> {
    // Nested validation function
    fn validate(input: &str) -> bool {
        !input.is_empty() && input.chars().any(|c| c.is_alphabetic())
    }
    
    if !validate(data) {
        return Err("Invalid input data".to_string());
    }
    
    // Nested data processing function with further nesting
    fn process_text(text: &str) -> String {
        // Another level of nesting
        fn capitalize(s: &str) -> String {
            let mut c = s.chars();
            match c.next() {
                None => String::new(),
                Some(f) => f.to_uppercase().collect::<String>() + c.as_str(),
            }
        }
        
        // Nested closure
        let join_words = |words: Vec<String>| -> String {
            words.join("-")
        };
        
        let words: Vec<String> = text
            .split_whitespace()
            .map(capitalize)
            .collect();
            
        join_words(words)
    }
    
    Ok(process_text(data))
}
