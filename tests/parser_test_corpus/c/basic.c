/**
 * Example C file
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/**
 * A test struct
 */
typedef struct {
    int field1;
    char field2[100];
} TestStruct;

/**
 * Initialize a TestStruct
 */
void init_test_struct(TestStruct* ts, int field1, const char* field2) {
    ts->field1 = field1;
    strncpy(ts->field2, field2, 99);
    ts->field2[99] = '\0';
}

/**
 * A test function
 */
int test_function(int arg1, const char* arg2) {
    printf("%s: %d\n", arg2, arg1);
    return arg1;
}

/**
 * Main function
 */
int main(int argc, char** argv) {
    TestStruct ts;
    init_test_struct(&ts, 42, "Hello");
    test_function(ts.field1, ts.field2);
    return 0;
}
