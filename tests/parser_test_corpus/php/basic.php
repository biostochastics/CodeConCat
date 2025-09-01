<?php
/**
 * Basic PHP test file for parser validation.
 *
 * This file contains common PHP constructs that should be properly parsed.
 */

namespace App\Example;

// Imports (use statements)
use PDO;
use App\Models\User;
use App\Services\{
    AuthService,
    LogService as Logger
};

/**
 * A constant with documentation.
 *
 * @var float
 */
const PI = 3.14159;

/**
 * Maximum number of retry attempts.
 *
 * @var int
 */
define('MAX_RETRIES', 3);

/**
 * A simple class with documentation.
 */
class Person {
    /**
     * The person's name
     *
     * @var string
     */
    protected $name;

    /**
     * The person's age
     *
     * @var int
     */
    protected $age;

    /**
     * The person's address (optional)
     *
     * @var string|null
     */
    protected $address = null;

    /**
     * Create a new person instance.
     *
     * @param string $name  The person's name
     * @param int    $age   The person's age
     */
    public function __construct(string $name, int $age) {
        $this->name = $name;
        $this->age = $age;
    }

    /**
     * Get a greeting from the person.
     *
     * @return string
     */
    public function greet(): string {
        return "Hello, my name is {$this->name} and I am {$this->age} years old.";
    }

    /**
     * Set the person's address.
     *
     * @param string $address  The address to set
     * @return void
     */
    public function setAddress(string $address): void {
        $this->address = $address;
    }

    /**
     * Get the person's address or a default message.
     *
     * @return string
     */
    public function getAddress(): string {
        return $this->address ?? 'Address not set';
    }
}

/**
 * Employee class extending Person with job information.
 */
class Employee extends Person {
    /**
     * The employee's job title
     *
     * @var string
     */
    private $title;

    /**
     * The employee's annual salary
     *
     * @var float
     */
    private $salary;

    /**
     * Create a new employee instance.
     *
     * @param string $name    The person's name
     * @param int    $age     The person's age
     * @param string $title   The job title
     * @param float  $salary  The annual salary
     */
    public function __construct(string $name, int $age, string $title, float $salary) {
        parent::__construct($name, $age);
        $this->title = $title;
        $this->salary = $salary;
    }

    /**
     * Give the employee a raise.
     *
     * @param float $percentage  The percentage to increase the salary
     * @return void
     */
    public function giveRaise(float $percentage): void {
        $this->salary *= (1 + $percentage / 100);
    }

    /**
     * Get information about the employee's job.
     *
     * @return string
     */
    public function getWorkInfo(): string {
        return "I work as a {$this->title} and earn \${$this->salary} per year.";
    }

    /**
     * Override the parent's greet method.
     *
     * @return string
     */
    public function greet(): string {
        $parentGreeting = parent::greet();
        return "{$parentGreeting} I work as a {$this->title}.";
    }
}

/**
 * An interface for data processors.
 */
interface Processor {
    /**
     * Process the given data.
     *
     * @param string $data  The data to process
     * @return string
     */
    public function process(string $data): string;

    /**
     * Get processing statistics.
     *
     * @return array
     */
    public function getStats(): array;
}

/**
 * A trait for logging functionality.
 */
trait Logger {
    /**
     * Log a message.
     *
     * @param string $message  The message to log
     * @return void
     */
    public function log(string $message): void {
        echo "[LOG] " . date('Y-m-d H:i:s') . " - {$message}\n";
    }
}

/**
 * Simple implementation of the Processor interface.
 */
class SimpleProcessor implements Processor {
    use Logger;

    /**
     * Number of successful processing operations
     *
     * @var int
     */
    private $count = 0;

    /**
     * Process the data by adding a prefix.
     *
     * @param string $data  The data to process
     * @return string
     * @throws \InvalidArgumentException  If data is empty
     */
    public function process(string $data): string {
        if (empty($data)) {
            throw new \InvalidArgumentException("Empty data");
        }

        $this->count++;
        $this->log("Processing data: " . substr($data, 0, 20) . "...");

        return "Processed: {$data}";
    }

    /**
     * Get the count of successful processing operations.
     *
     * @return array
     */
    public function getStats(): array {
        return [
            'count' => $this->count
        ];
    }
}

/**
 * Calculate statistics for an array of numbers.
 *
 * @param array $numbers  Array of integers
 * @return array|null  Array containing min, max, and average, or null if empty
 */
function calculateStats(array $numbers): ?array {
    if (empty($numbers)) {
        return null;
    }

    $min = min($numbers);
    $max = max($numbers);
    $avg = array_sum($numbers) / count($numbers);

    return [
        'min' => $min,
        'max' => $max,
        'avg' => $avg
    ];
}

/**
 * Divide two numbers and return the result.
 *
 * @param int $a  The dividend
 * @param int $b  The divisor
 * @return int  The result of the division
 * @throws \DivisionByZeroError  If divisor is zero
 */
function divide(int $a, int $b): int {
    if ($b === 0) {
        throw new \DivisionByZeroError("Division by zero");
    }

    return intdiv($a, $b);
}

// Example usage
if (PHP_SAPI === 'cli') {
    // Create a person
    $person = new Person("John", 30);
    $person->setAddress("123 Main St");
    echo $person->greet() . "\n";

    // Create an employee
    $employee = new Employee("Jane", 28, "Software Engineer", 100000);
    $employee->giveRaise(10);
    echo $employee->getWorkInfo() . "\n";
    echo $employee->greet() . "\n";

    // Use the processor
    $processor = new SimpleProcessor();
    try {
        $result = $processor->process("test data");
        echo $result . "\n";
    } catch (\Exception $e) {
        echo "Error: " . $e->getMessage() . "\n";
    }

    // Use standalone functions
    $numbers = [3, 7, 2, 9, 5];
    $stats = calculateStats($numbers);
    if ($stats) {
        echo "Min: {$stats['min']}, Max: {$stats['max']}, Avg: {$stats['avg']}\n";
    }

    try {
        $result = divide(10, 2);
        echo "10 / 2 = {$result}\n";
    } catch (\Exception $e) {
        echo "Error: " . $e->getMessage() . "\n";
    }

    // Use constants
    echo "PI: " . PI . "\n";
    echo "MAX_RETRIES: " . MAX_RETRIES . "\n";
}
