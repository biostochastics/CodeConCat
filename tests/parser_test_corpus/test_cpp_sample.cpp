#include <iostream>
#include <vector>
#include "myheader.h"

namespace MyNamespace {
    class MyClass {
    public:
        void myMethod();
    };

    struct MyStruct {
        int value;
    };

    enum MyEnum {
        VALUE1,
        VALUE2
    };

    union MyUnion {
        int intVal;
        float floatVal;
    };

    void myFunction(int param) {
        std::cout << "Hello" << std::endl;
    }
}
