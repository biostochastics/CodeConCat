/**
 * Basic JavaScript test file for parser validation.
 * 
 * This file contains common JavaScript constructs that should be properly parsed.
 */

// ES6 imports
import { Component } from 'react';
import React from 'react';
import * as utils from './utils';

// CommonJS require
const fs = require('fs');
const path = require('path');

/**
 * A simple JavaScript class with JSDoc documentation
 */
class SimpleClass {
  /**
   * The constructor for the class
   * @param {string} name - The name to use
   */
  constructor(name) {
    this.name = name;
    this._private = 42;
  }

  /**
   * A class method with documentation
   * @param {number} arg1 - First argument
   * @param {string} [arg2='default'] - Second argument with default
   * @returns {string} A formatted string
   */
  method(arg1, arg2 = 'default') {
    return `${this.name}: ${arg1} - ${arg2}`;
  }

  /**
   * A getter property
   * @returns {string} Uppercased name
   */
  get propertyExample() {
    return this.name.toUpperCase();
  }

  /**
   * A static method
   * @param {number} value - Value to double
   * @returns {number} Double the input value
   */
  static staticMethod(value) {
    return value * 2;
  }
}

/**
 * A standalone function with documentation
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} Sum of a and b
 */
function standaloneFunction(a, b) {
  return a + b;
}

// Arrow function with implicit return
/**
 * Arrow function example
 * @param {number} x - Value to square
 * @returns {number} Square of x
 */
const square = (x) => x * x;

// Arrow function with block body
/**
 * Complex arrow function
 * @param {Object} obj - Input object
 * @returns {Object} Transformed object
 */
const transformObject = (obj) => {
  const result = {};
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      result[key.toUpperCase()] = typeof obj[key] === 'string' 
        ? obj[key].toUpperCase() 
        : obj[key];
    }
  }
  return result;
};

/**
 * The mathematical constant pi, approximately.
 * @type {number}
 */
const PI = 3.14159;

/**
 * Higher-order function example
 * @param {number} x - Value to capture in closure
 * @returns {Function} A function that uses the captured value
 */
function outerFunction(x) {
  /**
   * Inner function with its own documentation
   * @param {number} y - Value to add to the captured x
   * @returns {number} Sum of x and y
   */
  function innerFunction(y) {
    return x + y;
  }
  
  return innerFunction;
}

/**
 * Class with inheritance
 * @extends SimpleClass
 */
class ChildClass extends SimpleClass {
  /**
   * Initialize with name and extra info
   * @param {string} name - The name to use
   * @param {string} extra - Extra information
   */
  constructor(name, extra) {
    super(name);
    this.extra = extra;
  }

  /**
   * Override parent method
   * @param {number} arg1 - First argument
   * @param {string} [arg2='child_default'] - Second argument with default
   * @returns {string} A modified string result
   * @override
   */
  method(arg1, arg2 = 'child_default') {
    const parentResult = super.method(arg1, arg2);
    return `${parentResult} (child: ${this.extra})`;
  }
}

// Example usage
if (typeof window !== 'undefined') {
  const simple = new SimpleClass('test');
  const child = new ChildClass('child', 'extra_info');
  console.log(simple.method(1, 'hello'));
  console.log(child.method(2, 'world'));
  console.log(standaloneFunction(5, 7));
}

// Export constructs
module.exports = {
  SimpleClass,
  ChildClass,
  standaloneFunction,
  square,
  transformObject,
  PI
};
