// Basic Go test file for parser validation.
//
// This file contains common Go constructs that should be properly parsed.

package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"time"
)

// Constants with documentation
const (
	// PI represents the mathematical constant pi.
	PI = 3.14159
	// MaxRetries defines the maximum number of retry attempts.
	MaxRetries = 3
)

// Global variables
var (
	DefaultTimeout = time.Second * 30
	AppName        = "TestApp"
)

// Person represents a human with name and age.
type Person struct {
	Name    string
	Age     int
	Address string
	private int // private field
}

// NewPerson creates a new Person instance.
// It initializes the person with the given name and age.
func NewPerson(name string, age int) *Person {
	return &Person{
		Name: name,
		Age:  age,
	}
}

// Greet returns a greeting message from the person.
// It includes the person's name in the message.
func (p *Person) Greet() string {
	return fmt.Sprintf("Hello, my name is %s and I am %d years old.", p.Name, p.Age)
}

// SetAddress updates the person's address.
func (p *Person) SetAddress(address string) {
	p.Address = address
}

// Employee extends Person with job-related fields.
type Employee struct {
	Person
	Title  string
	Salary float64
}

// NewEmployee creates a new Employee instance.
func NewEmployee(name string, age int, title string, salary float64) *Employee {
	return &Employee{
		Person: Person{
			Name: name,
			Age:  age,
		},
		Title:  title,
		Salary: salary,
	}
}

// GiveRaise increases the employee's salary by the given percentage.
func (e *Employee) GiveRaise(percentage float64) {
	e.Salary = e.Salary * (1 + percentage/100)
}

// WorkInfo returns information about the employee's job.
func (e *Employee) WorkInfo() string {
	return fmt.Sprintf("I work as a %s and earn %.2f per year.", e.Title, e.Salary)
}

// Stringer interface implementation
func (e Employee) String() string {
	return fmt.Sprintf("%s (%s, $%.2f)", e.Name, e.Title, e.Salary)
}

// Processor defines an interface for processing data.
type Processor interface {
	// Process performs data processing.
	Process(data []byte) ([]byte, error)
	
	// GetStats returns processing statistics.
	GetStats() map[string]int
}

// SimpleProcessor implements the Processor interface.
type SimpleProcessor struct {
	count int
}

// Process implements the Processor interface Process method.
func (p *SimpleProcessor) Process(data []byte) ([]byte, error) {
	if data == nil {
		return nil, fmt.Errorf("nil data")
	}
	p.count++
	return append([]byte("Processed: "), data...), nil
}

// GetStats implements the Processor interface GetStats method.
func (p *SimpleProcessor) GetStats() map[string]int {
	return map[string]int{
		"count": p.count,
	}
}

// Standalone function with multiple parameters
// and return values.
func calculateStats(numbers []int) (int, int, float64) {
	if len(numbers) == 0 {
		return 0, 0, 0
	}
	
	min, max, sum := numbers[0], numbers[0], 0
	
	for _, n := range numbers {
		if n < min {
			min = n
		}
		if n > max {
			max = n
		}
		sum += n
	}
	
	avg := float64(sum) / float64(len(numbers))
	return min, max, avg
}

// FileExists checks if a file exists at the given path.
func FileExists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

// Simple function to demonstrate error handling
func divide(a, b int) (result int, err error) {
	if b == 0 {
		return 0, fmt.Errorf("division by zero")
	}
	return a / b, nil
}

func main() {
	// Create a person
	p := NewPerson("John", 30)
	p.SetAddress("123 Main St")
	fmt.Println(p.Greet())
	
	// Create an employee
	e := NewEmployee("Jane", 28, "Software Engineer", 100000)
	e.GiveRaise(10)
	fmt.Println(e.WorkInfo())
	fmt.Println(e.Greet())
	
	// Use the processor
	proc := &SimpleProcessor{}
	data, err := proc.Process([]byte("test data"))
	if err != nil {
		fmt.Println("Error:", err)
	} else {
		fmt.Println(string(data))
	}
	
	// Use standalone functions
	numbers := []int{3, 7, 2, 9, 5}
	min, max, avg := calculateStats(numbers)
	fmt.Printf("Min: %d, Max: %d, Avg: %.2f\n", min, max, avg)
	
	result, err := divide(10, 2)
	if err != nil {
		fmt.Println("Error:", err)
	} else {
		fmt.Println("10 / 2 =", result)
	}
	
	// Use constants and variables
	fmt.Println("PI:", PI)
	fmt.Println("MaxRetries:", MaxRetries)
	fmt.Println("DefaultTimeout:", DefaultTimeout)
	fmt.Println("AppName:", AppName)
}
