/**
 * Example Java file
 */
package com.example.test;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.HashMap;

/**
 * A test class
 */
public class TestClass {
    private int value;

    /**
     * Constructor
     */
    public TestClass(int value) {
        this.value = value;
    }

    /**
     * Get the value
     */
    public int getValue() {
        return value;
    }

    /**
     * Set the value
     */
    public void setValue(int newValue) {
        this.value = newValue;
    }

    /**
     * A nested class
     */
    public static class NestedClass {
        private String name;

        public NestedClass(String name) {
            this.name = name;
        }

        public String getName() {
            return name;
        }
    }

    /**
     * Main method
     */
    public static void main(String[] args) {
        TestClass tc = new TestClass(42);
        System.out.println("Value: " + tc.getValue());
        tc.setValue(100);
        System.out.println("New value: " + tc.getValue());
    }
}
