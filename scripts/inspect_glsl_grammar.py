#!/usr/bin/env python3
"""
Script to inspect GLSL grammar structure by parsing sample code and printing the AST.
"""

import tree_sitter_glsl
from tree_sitter import Language, Parser


def print_tree(node, source_code, indent=0):
    """Recursively print the syntax tree."""
    node_text = source_code[node.start_byte : node.end_byte]
    # Limit text display for readability
    if len(node_text) > 50:
        node_text = node_text[:50] + "..."
    node_text = node_text.replace("\n", "\\n")

    print(
        "  " * indent
        + f"{node.type} [{node.start_point[0]}:{node.start_point[1]} - {node.end_point[0]}:{node.end_point[1]}]",
        end="",
    )
    if not node.children:
        print(f" = '{node_text}'")
    else:
        print()

    for child in node.children:
        print_tree(child, source_code, indent + 1)


def main():
    # Load the language
    lang_ptr = tree_sitter_glsl.language()
    language = Language(lang_ptr)

    # Create parser
    parser = Parser(language)

    # Test various GLSL constructs
    test_cases = {
        "Simple uniform": """
uniform mat4 model;
""",
        "Uniform with layout": """
layout(binding = 0) uniform sampler2D texSampler;
""",
        "In/out variables": """
in vec3 position;
out vec4 color;
""",
        "Function definition": """
void main() {
    gl_Position = vec4(1.0);
}
""",
        "Struct definition": """
struct Light {
    vec3 position;
    vec3 color;
    float intensity;
};
""",
        "Sampler declaration": """
uniform sampler2D diffuseMap;
uniform sampler2DShadow shadowMap;
""",
        "Buffer declaration": """
buffer ParticleBuffer {
    vec4 positions[];
    vec4 velocities[];
};
""",
        "Preprocessor": """
#version 330 core
#extension GL_ARB_explicit_uniform_location : enable
#define PI 3.14159
""",
        "Complete shader": """
#version 330 core

layout(location = 0) in vec3 aPos;
layout(location = 1) in vec2 aTexCoord;

out vec2 TexCoord;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main() {
    gl_Position = projection * view * model * vec4(aPos, 1.0);
    TexCoord = aTexCoord;
}
""",
    }

    for name, code in test_cases.items():
        print(f"\n{'=' * 80}")
        print(f"Test Case: {name}")
        print(f"{'=' * 80}")
        print("Code:")
        print(code)
        print("\nAST:")
        tree = parser.parse(bytes(code, "utf8"))
        print_tree(tree.root_node, code)


if __name__ == "__main__":
    main()
