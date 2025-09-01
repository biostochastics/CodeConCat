// Basic Rust test file for parser validation.
//
// This file contains common Rust constructs that should be properly parsed.

use std::collections::HashMap;
use std::fmt::{self, Display, Formatter};
use std::error::Error;

/// The mathematical constant pi, approximately.
const PI: f64 = 3.14159;

/// Maximum number of retry attempts.
const MAX_RETRIES: u32 = 3;

/// Application settings
struct AppSettings {
    /// The name of the application
    name: String,
    /// Maximum timeout in seconds
    timeout_seconds: u32,
    /// Debug mode flag
    debug: bool,
}

/// Represents a person with name and age.
pub struct Person {
    /// Person's name
    name: String,
    /// Person's age in years
    age: u32,
    /// Optional address
    address: Option<String>,
}

impl Person {
    /// Creates a new Person instance.
    ///
    /// # Arguments
    ///
    /// * `name` - The person's name
    /// * `age` - The person's age in years
    ///
    /// # Returns
    ///
    /// A new Person instance with the given name and age.
    pub fn new(name: String, age: u32) -> Self {
        Person {
            name,
            age,
            address: None,
        }
    }

    /// Returns a greeting message from the person.
    pub fn greet(&self) -> String {
        format!("Hello, my name is {} and I am {} years old.", self.name, self.age)
    }

    /// Sets the person's address.
    pub fn set_address(&mut self, address: String) {
        self.address = Some(address);
    }

    /// Gets the person's address or a default message if none is set.
    pub fn get_address(&self) -> String {
        match &self.address {
            Some(addr) => addr.clone(),
            None => "Address not set".to_string(),
        }
    }
}

/// Employee extends Person with job-related fields.
pub struct Employee {
    /// Base person information
    person: Person,
    /// Job title
    title: String,
    /// Annual salary
    salary: f64,
}

impl Employee {
    /// Creates a new Employee instance.
    pub fn new(name: String, age: u32, title: String, salary: f64) -> Self {
        Employee {
            person: Person::new(name, age),
            title,
            salary,
        }
    }

    /// Gives a raise to the employee by the specified percentage.
    pub fn give_raise(&mut self, percentage: f64) {
        self.salary *= 1.0 + percentage / 100.0;
    }

    /// Returns information about the employee's job.
    pub fn work_info(&self) -> String {
        format!("I work as a {} and earn ${:.2} per year.", self.title, self.salary)
    }
}

impl Display for Employee {
    /// Formats the Employee for display
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        write!(f, "{} ({}, ${:.2})", self.person.name, self.title, self.salary)
    }
}

/// Custom error type for our application
#[derive(Debug)]
pub enum AppError {
    /// Division by zero error
    DivisionByZero,
    /// Invalid input data
    InvalidInput(String),
    /// I/O error wrapping std::io::Error
    IoError(std::io::Error),
}

impl Display for AppError {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        match self {
            AppError::DivisionByZero => write!(f, "Division by zero"),
            AppError::InvalidInput(msg) => write!(f, "Invalid input: {}", msg),
            AppError::IoError(err) => write!(f, "I/O error: {}", err),
        }
    }
}

impl Error for AppError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            AppError::IoError(err) => Some(err),
            _ => None,
        }
    }
}

/// Defines a trait for data processing.
pub trait Processor {
    /// Processes the given data.
    fn process(&mut self, data: &[u8]) -> Result<Vec<u8>, AppError>;

    /// Returns processing statistics.
    fn get_stats(&self) -> HashMap<String, u32>;
}

/// Simple implementation of the Processor trait.
pub struct SimpleProcessor {
    /// Number of successful processing operations
    count: u32,
}

impl SimpleProcessor {
    /// Creates a new SimpleProcessor.
    pub fn new() -> Self {
        SimpleProcessor { count: 0 }
    }
}

impl Processor for SimpleProcessor {
    /// Processes the data by adding a prefix.
    fn process(&mut self, data: &[u8]) -> Result<Vec<u8>, AppError> {
        if data.is_empty() {
            return Err(AppError::InvalidInput("Empty data".to_string()));
        }

        self.count += 1;
        let mut result = "Processed: ".as_bytes().to_vec();
        result.extend_from_slice(data);

        Ok(result)
    }

    /// Returns the count of successful processing operations.
    fn get_stats(&self) -> HashMap<String, u32> {
        let mut stats = HashMap::new();
        stats.insert("count".to_string(), self.count);
        stats
    }
}

/// Calculates statistics for a list of numbers.
///
/// # Arguments
///
/// * `numbers` - A slice of integers
///
/// # Returns
///
/// A tuple containing the minimum, maximum, and average values.
pub fn calculate_stats(numbers: &[i32]) -> Option<(i32, i32, f64)> {
    if numbers.is_empty() {
        return None;
    }

    let mut min = numbers[0];
    let mut max = numbers[0];
    let mut sum = 0;

    for &n in numbers {
        if n < min {
            min = n;
        }
        if n > max {
            max = n;
        }
        sum += n;
    }

    let avg = sum as f64 / numbers.len() as f64;
    Some((min, max, avg))
}

/// Divides two numbers and returns the result.
///
/// # Arguments
///
/// * `a` - The dividend
/// * `b` - The divisor
///
/// # Returns
///
/// The result of dividing a by b, or an error if b is zero.
pub fn divide(a: i32, b: i32) -> Result<i32, AppError> {
    if b == 0 {
        Err(AppError::DivisionByZero)
    } else {
        Ok(a / b)
    }
}

/// Generic function to swap two values.
pub fn swap<T>(a: &mut T, b: &mut T) {
    std::mem::swap(a, b);
}

/// Main function demonstrating the use of the defined types and functions.
fn main() -> Result<(), Box<dyn Error>> {
    // Create a person
    let mut person = Person::new("John".to_string(), 30);
    person.set_address("123 Main St".to_string());
    println!("{}", person.greet());

    // Create an employee
    let mut employee = Employee::new("Jane".to_string(), 28, "Software Engineer".to_string(), 100000.0);
    employee.give_raise(10.0);
    println!("{}", employee.work_info());

    // Use the processor
    let mut processor = SimpleProcessor::new();
    match processor.process(b"test data") {
        Ok(data) => println!("{}", String::from_utf8_lossy(&data)),
        Err(e) => println!("Error: {}", e),
    }

    // Use standalone functions
    let numbers = vec![3, 7, 2, 9, 5];
    if let Some((min, max, avg)) = calculate_stats(&numbers) {
        println!("Min: {}, Max: {}, Avg: {:.2}", min, max, avg);
    }

    match divide(10, 2) {
        Ok(result) => println!("10 / 2 = {}", result),
        Err(e) => println!("Error: {}", e),
    }

    // Use constants
    println!("PI: {}", PI);
    println!("MAX_RETRIES: {}", MAX_RETRIES);

    Ok(())
}
