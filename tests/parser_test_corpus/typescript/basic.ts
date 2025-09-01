/**
 * Basic TypeScript test file for parser validation.
 *
 * This file contains common TypeScript constructs that should be properly parsed.
 */

// TypeScript imports
import { Component } from 'react';
import React from 'react';
import * as utils from './utils';

// Interfaces
/**
 * Person interface representing a human with name and age
 */
interface Person {
  name: string;
  age: number;
  /** Optional address property */
  address?: string;
  /** Greeting method */
  greet(): string;
}

/**
 * Interface with inheritance
 */
interface Employee extends Person {
  /** Employee's job title */
  title: string;
  /** Employee's salary */
  salary: number;
}

// Type aliases
/** Type for coordinates */
type Point = {
  x: number;
  y: number;
};

/** Union type example */
type Result<T> =
  | { success: true; value: T }
  | { success: false; error: Error };

/**
 * A simple TypeScript class with documentation
 */
class SimpleClass {
  /** Public class property */
  public name: string;
  /** Private class property */
  private _private: number;

  /**
   * The constructor for the class
   * @param name - The name to use
   */
  constructor(name: string) {
    this.name = name;
    this._private = 42;
  }

  /**
   * A class method with documentation
   * @param arg1 - First argument
   * @param arg2 - Second argument with default
   * @returns A formatted string
   */
  method(arg1: number, arg2: string = 'default'): string {
    return `${this.name}: ${arg1} - ${arg2}`;
  }

  /**
   * A getter property
   * @returns Uppercased name
   */
  get propertyExample(): string {
    return this.name.toUpperCase();
  }

  /**
   * A static method
   * @param value - Value to double
   * @returns Double the input value
   */
  static staticMethod(value: number): number {
    return value * 2;
  }
}

/**
 * A function implementing Person interface
 * @param person - Person object
 * @returns A greeting string
 */
function greetPerson(person: Person): string {
  return `Hello, ${person.name}! You are ${person.age} years old.`;
}

/**
 * A standalone function with documentation
 * @param a - First number
 * @param b - Second number
 * @returns Sum of a and b
 */
function standaloneFunction(a: number, b: number): number {
  return a + b;
}

// Generic function
/**
 * Identity function for any type
 * @param arg - Any input
 * @returns Same as input
 */
function identity<T>(arg: T): T {
  return arg;
}

// Arrow function with explicit type
/**
 * Arrow function example
 * @param x - Value to square
 * @returns Square of x
 */
const square = (x: number): number => x * x;

/**
 * The mathematical constant pi, approximately.
 */
const PI: number = 3.14159;

/**
 * Class with inheritance implementing an interface
 */
class Employee implements Person {
  name: string;
  age: number;
  title: string;

  /**
   * Initialize an employee
   * @param name - Employee name
   * @param age - Employee age
   * @param title - Job title
   */
  constructor(name: string, age: number, title: string) {
    this.name = name;
    this.age = age;
    this.title = title;
  }

  /**
   * Implement the greet method from Person interface
   * @returns Greeting including job title
   */
  greet(): string {
    return `Hello, I'm ${this.name}, ${this.age} years old, and I work as a ${this.title}.`;
  }
}

// Enum example
/**
 * Direction enum for movement
 */
enum Direction {
  Up = "UP",
  Down = "DOWN",
  Left = "LEFT",
  Right = "RIGHT"
}

// Namespace example
/**
 * Utilities namespace
 */
namespace Utils {
  /**
   * Format a date
   * @param date - Date to format
   * @returns Formatted date string
   */
  export function formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  /**
   * Format a currency amount
   * @param amount - Amount to format
   * @param currency - Currency code
   * @returns Formatted currency string
   */
  export function formatCurrency(amount: number, currency: string = 'USD'): string {
    return `${currency} ${amount.toFixed(2)}`;
  }
}

// Example usage
if (typeof window !== 'undefined') {
  const person: Person = {
    name: 'John',
    age: 30,
    greet: function() { return `Hello, I'm ${this.name}!`; }
  };

  const employee = new Employee('Jane', 28, 'Developer');

  console.log(person.greet());
  console.log(employee.greet());
  console.log(Utils.formatDate(new Date()));
}

// Export constructs
export {
  Person,
  Employee,
  Point,
  Result,
  Direction,
  SimpleClass,
  greetPerson,
  standaloneFunction,
  identity,
  square,
  PI,
  Utils
};
