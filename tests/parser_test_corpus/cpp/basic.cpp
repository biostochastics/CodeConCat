/**
 * Example C++ file
 */
#include <iostream>
#include <string>
#include <vector>

/**
 * A test class
 */
class TestClass {
private:
    int value;
    
public:
    /**
     * Constructor
     */
    TestClass(int value = 0) : value(value) {}
    
    /**
     * Get the value
     */
    int getValue() const {
        return value;
    }
    
    /**
     * Set the value
     */
    void setValue(int newValue) {
        value = newValue;
    }
};

/**
 * A test function
 */
int testFunction(int arg1, const std::string& arg2) {
    std::cout << arg2 << ": " << arg1 << std::endl;
    return arg1;
}

/**
 * Main function
 */
int main() {
    TestClass tc(42);
    std::cout << "Value: " << tc.getValue() << std::endl;
    tc.setValue(100);
    std::cout << "New value: " << tc.getValue() << std::endl;
    
    testFunction(tc.getValue(), "Test");
    
    return 0;
}
