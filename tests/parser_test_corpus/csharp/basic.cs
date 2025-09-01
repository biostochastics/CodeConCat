using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using System.Threading.Tasks;

namespace TestNamespace
{
    /// <summary>
    /// Basic C# test file for parser validation.
    ///
    /// This file contains common C# constructs that should be properly parsed.
    /// </summary>

    /// <summary>
    /// Constants class with documentation.
    /// </summary>
    public static class Constants
    {
        /// <summary>
        /// The mathematical constant pi, approximately.
        /// </summary>
        public const double PI = 3.14159;

        /// <summary>
        /// Maximum number of retry attempts.
        /// </summary>
        public const int MAX_RETRIES = 3;
    }

    /// <summary>
    /// Represents a person with name, age, and optional address.
    /// </summary>
    public class Person
    {
        /// <summary>
        /// The person's name
        /// </summary>
        protected string Name { get; set; }

        /// <summary>
        /// The person's age
        /// </summary>
        protected int Age { get; set; }

        /// <summary>
        /// The person's address (optional)
        /// </summary>
        protected string Address { get; set; }

        /// <summary>
        /// Create a new person instance.
        /// </summary>
        /// <param name="name">The person's name</param>
        /// <param name="age">The person's age</param>
        public Person(string name, int age)
        {
            Name = name;
            Age = age;
            Address = null;
        }

        /// <summary>
        /// Get a greeting from the person.
        /// </summary>
        /// <returns>A greeting string</returns>
        public virtual string Greet()
        {
            return $"Hello, my name is {Name} and I am {Age} years old.";
        }

        /// <summary>
        /// Set the person's address.
        /// </summary>
        /// <param name="address">The address to set</param>
        public void SetAddress(string address)
        {
            Address = address;
        }

        /// <summary>
        /// Get the person's address or a default message.
        /// </summary>
        /// <returns>The address or a default message</returns>
        public string GetAddress()
        {
            return Address ?? "Address not set";
        }
    }

    /// <summary>
    /// Employee class extending Person with job information.
    /// </summary>
    public class Employee : Person
    {
        /// <summary>
        /// The employee's job title
        /// </summary>
        private string Title { get; set; }

        /// <summary>
        /// The employee's annual salary
        /// </summary>
        private double Salary { get; set; }

        /// <summary>
        /// Create a new employee instance.
        /// </summary>
        /// <param name="name">The person's name</param>
        /// <param name="age">The person's age</param>
        /// <param name="title">The job title</param>
        /// <param name="salary">The annual salary</param>
        public Employee(string name, int age, string title, double salary)
            : base(name, age)
        {
            Title = title;
            Salary = salary;
        }

        /// <summary>
        /// Give the employee a raise.
        /// </summary>
        /// <param name="percentage">The percentage to increase the salary</param>
        public void GiveRaise(double percentage)
        {
            Salary *= (1 + percentage / 100);
        }

        /// <summary>
        /// Get information about the employee's job.
        /// </summary>
        /// <returns>A string with job information</returns>
        public string GetWorkInfo()
        {
            return $"I work as a {Title} and earn ${Salary} per year.";
        }

        /// <summary>
        /// Override the parent's greet method.
        /// </summary>
        /// <returns>An enhanced greeting string</returns>
        public override string Greet()
        {
            string parentGreeting = base.Greet();
            return $"{parentGreeting} I work as a {Title}.";
        }
    }

    /// <summary>
    /// Interface for data processors.
    /// </summary>
    public interface IProcessor
    {
        /// <summary>
        /// Process the given data.
        /// </summary>
        /// <param name="data">The data to process</param>
        /// <returns>The processed data</returns>
        string Process(string data);

        /// <summary>
        /// Get processing statistics.
        /// </summary>
        /// <returns>A dictionary of statistics</returns>
        Dictionary<string, int> GetStats();
    }

    /// <summary>
    /// Simple implementation of the IProcessor interface.
    /// </summary>
    public class SimpleProcessor : IProcessor
    {
        /// <summary>
        /// Number of successful processing operations
        /// </summary>
        private int _count = 0;

        /// <summary>
        /// Process the data by adding a prefix.
        /// </summary>
        /// <param name="data">The data to process</param>
        /// <returns>The processed data</returns>
        /// <exception cref="ArgumentException">Thrown if data is empty</exception>
        public string Process(string data)
        {
            if (string.IsNullOrEmpty(data))
            {
                throw new ArgumentException("Empty data");
            }

            _count++;
            Console.WriteLine($"Processing data: {data.Substring(0, Math.Min(20, data.Length))}...");

            return $"Processed: {data}";
        }

        /// <summary>
        /// Get the count of successful processing operations.
        /// </summary>
        /// <returns>A dictionary with statistics</returns>
        public Dictionary<string, int> GetStats()
        {
            return new Dictionary<string, int>
            {
                { "count", _count }
            };
        }
    }

    /// <summary>
    /// Enumeration of status codes.
    /// </summary>
    public enum StatusCode
    {
        /// <summary>Success status</summary>
        Success = 0,

        /// <summary>Warning status</summary>
        Warning = 1,

        /// <summary>Error status</summary>
        Error = 2,

        /// <summary>Fatal error status</summary>
        Fatal = 3
    }

    /// <summary>
    /// Static utility class with helper methods.
    /// </summary>
    public static class Utils
    {
        /// <summary>
        /// Calculate statistics for an array of numbers.
        /// </summary>
        /// <param name="numbers">Array of integers</param>
        /// <returns>A tuple containing min, max, and average, or null if empty</returns>
        public static (int Min, int Max, double Avg)? CalculateStats(int[] numbers)
        {
            if (numbers == null || numbers.Length == 0)
            {
                return null;
            }

            int min = numbers.Min();
            int max = numbers.Max();
            double avg = numbers.Average();

            return (min, max, avg);
        }

        /// <summary>
        /// Divide two numbers and return the result.
        /// </summary>
        /// <param name="a">The dividend</param>
        /// <param name="b">The divisor</param>
        /// <returns>The result of the division</returns>
        /// <exception cref="DivideByZeroException">Thrown if divisor is zero</exception>
        public static int Divide(int a, int b)
        {
            if (b == 0)
            {
                throw new DivideByZeroException("Division by zero");
            }

            return a / b;
        }

        /// <summary>
        /// Asynchronously read a file.
        /// </summary>
        /// <param name="path">Path to the file</param>
        /// <returns>A task that resolves to the file contents</returns>
        public static async Task<string> ReadFileAsync(string path)
        {
            if (!File.Exists(path))
            {
                throw new FileNotFoundException("File not found", path);
            }

            return await File.ReadAllTextAsync(path);
        }
    }

    /// <summary>
    /// Main program class with entry point.
    /// </summary>
    public class Program
    {
        /// <summary>
        /// Main entry point for the application.
        /// </summary>
        /// <param name="args">Command line arguments</param>
        public static void Main(string[] args)
        {
            // Create a person
            Person person = new Person("John", 30);
            person.SetAddress("123 Main St");
            Console.WriteLine(person.Greet());

            // Create an employee
            Employee employee = new Employee("Jane", 28, "Software Engineer", 100000);
            employee.GiveRaise(10);
            Console.WriteLine(employee.GetWorkInfo());
            Console.WriteLine(employee.Greet());

            // Use the processor
            IProcessor processor = new SimpleProcessor();
            try
            {
                string result = processor.Process("test data");
                Console.WriteLine(result);
            }
            catch (Exception e)
            {
                Console.WriteLine($"Error: {e.Message}");
            }

            // Use standalone functions
            int[] numbers = { 3, 7, 2, 9, 5 };
            var stats = Utils.CalculateStats(numbers);
            if (stats.HasValue)
            {
                Console.WriteLine($"Min: {stats.Value.Min}, Max: {stats.Value.Max}, Avg: {stats.Value.Avg}");
            }

            try
            {
                int result = Utils.Divide(10, 2);
                Console.WriteLine($"10 / 2 = {result}");
            }
            catch (Exception e)
            {
                Console.WriteLine($"Error: {e.Message}");
            }

            // Use constants
            Console.WriteLine($"PI: {Constants.PI}");
            Console.WriteLine($"MAX_RETRIES: {Constants.MAX_RETRIES}");

            // Use enum
            StatusCode status = StatusCode.Success;
            Console.WriteLine($"Status: {status}");
        }
    }
}
