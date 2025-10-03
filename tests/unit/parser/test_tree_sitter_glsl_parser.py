"""
Unit tests for TreeSitterGlslParser.

Tests comprehensive GLSL parsing including:
- Uniforms and uniform blocks
- Input/output variables with layout qualifiers
- Texture samplers and images
- Shader storage buffers (SSBOs)
- Vertex, fragment, and compute shaders
- Preprocessor directives
"""

import pytest
from unittest.mock import Mock, patch

from codeconcat.parser.language_parsers.tree_sitter_glsl_parser import TreeSitterGlslParser
from codeconcat.errors import LanguageParserError


class TestTreeSitterGlslParser:
    """Test suite for GLSL parser."""

    def test_parser_initialization(self):
        """Test parser initializes correctly."""
        parser = TreeSitterGlslParser()
        assert parser.language_name == "glsl"
        assert parser.ts_language is not None
        assert parser.parser is not None

    def test_parse_simple_vertex_shader(self):
        """Test parsing a simple vertex shader."""
        parser = TreeSitterGlslParser()
        code = """
        #version 330 core

        layout(location = 0) in vec3 aPos;
        layout(location = 1) in vec2 aTexCoord;

        out vec2 TexCoord;

        uniform mat4 model;
        uniform mat4 view;
        uniform mat4 projection;

        void main()
        {
            gl_Position = projection * view * model * vec4(aPos, 1.0);
            TexCoord = aTexCoord;
        }
        """

        result = parser.parse(code, "vertex.glsl")
        declarations = result.declarations

        # Check for uniforms
        uniforms = [d for d in declarations if d.kind == "uniform"]
        assert len(uniforms) == 3
        uniform_names = [u.name for u in uniforms]
        assert "model" in uniform_names
        assert "view" in uniform_names
        assert "projection" in uniform_names

        # Check for input variables
        inputs = [d for d in declarations if "in_variable" in d.kind]
        assert len(inputs) == 2
        input_names = [i.name for i in inputs]
        assert "aPos" in input_names
        assert "aTexCoord" in input_names

        # Check for output variables
        outputs = [d for d in declarations if "out_variable" in d.kind]
        assert len(outputs) == 1
        assert outputs[0].name == "TexCoord"

        # Check for main function
        functions = [d for d in declarations if d.kind in ["function", "entry_point"]]
        assert len(functions) == 1
        assert functions[0].name == "main"

    def test_parse_fragment_shader_with_samplers(self):
        """Test parsing fragment shader with texture samplers."""
        parser = TreeSitterGlslParser()
        code = """
        #version 330 core

        in vec2 TexCoord;
        in vec3 Normal;

        out vec4 FragColor;

        uniform sampler2D texture1;
        uniform sampler2D texture2;
        uniform vec3 lightColor;

        void main()
        {
            vec4 tex1 = texture(texture1, TexCoord);
            vec4 tex2 = texture(texture2, TexCoord);
            FragColor = mix(tex1, tex2, 0.5) * vec4(lightColor, 1.0);
        }
        """

        result = parser.parse(code, "fragment.glsl")
        declarations = result.declarations

        # Check for samplers
        samplers = [d for d in declarations if d.kind == "sampler"]
        assert len(samplers) == 2
        sampler_names = [s.name for s in samplers]
        assert "texture1" in sampler_names
        assert "texture2" in sampler_names

        # Check for uniforms
        uniforms = [d for d in declarations if d.kind == "uniform"]
        assert len(uniforms) >= 1
        assert any(u.name == "lightColor" for u in uniforms)

    def test_parse_compute_shader(self):
        """Test parsing compute shader with local size."""
        parser = TreeSitterGlslParser()
        code = """
        #version 430 core

        layout(local_size_x = 16, local_size_y = 16, local_size_z = 1) in;

        layout(binding = 0, rgba32f) uniform image2D inputImage;
        layout(binding = 1, rgba32f) uniform image2D outputImage;

        void main()
        {
            ivec2 pixel = ivec2(gl_GlobalInvocationID.xy);
            vec4 color = imageLoad(inputImage, pixel);
            color = vec4(1.0) - color;  // Invert colors
            imageStore(outputImage, pixel, color);
        }
        """

        result = parser.parse(code, "compute.glsl")
        declarations = result.declarations

        # Check for images
        images = [d for d in declarations if d.kind == "image"]
        assert len(images) == 2
        image_names = [i.name for i in images]
        assert "inputImage" in image_names
        assert "outputImage" in image_names

        # Check that shader stage is detected as compute
        assert parser.shader_stage == "compute"

    def test_parse_uniform_blocks(self):
        """Test parsing uniform blocks."""
        parser = TreeSitterGlslParser()
        code = """
        #version 330 core

        uniform Matrices {
            mat4 model;
            mat4 view;
            mat4 projection;
        } matrices;

        uniform LightData {
            vec3 position;
            vec3 color;
            float intensity;
        };

        void main()
        {
            // Shader code
        }
        """

        result = parser.parse(code, "test.glsl")
        declarations = result.declarations

        # Check for uniform blocks
        uniform_blocks = [d for d in declarations if d.kind == "uniform_block"]
        assert len(uniform_blocks) >= 1

    def test_parse_shader_storage_blocks(self):
        """Test parsing shader storage buffer objects (SSBOs)."""
        parser = TreeSitterGlslParser()
        code = """
        #version 430 core

        layout(std430, binding = 0) buffer ParticleData {
            vec4 position[];
        } particles;

        layout(std430, binding = 1) buffer VelocityData {
            vec4 velocity[];
        } velocities;

        void main()
        {
            uint index = gl_GlobalInvocationID.x;
            particles.position[index] += velocities.velocity[index];
        }
        """

        result = parser.parse(code, "ssbo.glsl")
        declarations = result.declarations

        # Check for storage buffers
        buffers = [d for d in declarations if d.kind == "storage_buffer"]
        assert len(buffers) == 2

    def test_parse_struct_definitions(self):
        """Test parsing struct definitions."""
        parser = TreeSitterGlslParser()
        code = """
        #version 330 core

        struct Material {
            vec3 ambient;
            vec3 diffuse;
            vec3 specular;
            float shininess;
        };

        struct Light {
            vec3 position;
            vec3 color;
            float intensity;
        };

        uniform Material material;
        uniform Light light;

        void main()
        {
            // Shader code
        }
        """

        result = parser.parse(code, "structs.glsl")
        declarations = result.declarations

        # Check for structs
        structs = [d for d in declarations if d.kind == "struct"]
        assert len(structs) == 2
        struct_names = [s.name for s in structs]
        assert "Material" in struct_names
        assert "Light" in struct_names

    def test_parse_preprocessor_directives(self):
        """Test parsing preprocessor directives."""
        parser = TreeSitterGlslParser()
        code = """
        #version 330 core
        #extension GL_ARB_shading_language_420pack : require

        #define MAX_LIGHTS 32
        #define EPSILON 0.0001

        #include "common/utils.glsl"

        void main()
        {
            // Shader code
        }
        """

        result = parser.parse(code, "preprocessor.glsl")
        imports = result.imports

        # Check for includes
        assert len(imports) >= 1
        assert "common/utils.glsl" in imports

    def test_parse_array_declarations(self):
        """Test parsing array declarations."""
        parser = TreeSitterGlslParser()
        code = """
        #version 330 core

        uniform vec3 lightPositions[16];
        uniform float shadowMaps[4];

        in vec2 texCoords[3];
        out vec4 fragColors[2];

        void main()
        {
            // Shader code
        }
        """

        result = parser.parse(code, "arrays.glsl")
        declarations = result.declarations

        # Check for array uniforms
        uniforms = [d for d in declarations if d.kind == "uniform"]
        assert len(uniforms) >= 2

        # Check for array I/O
        ios = [d for d in declarations if "variable" in d.kind]
        assert len(ios) >= 2

    def test_parse_multiple_shaders_in_file(self):
        """Test parsing multiple shader functions."""
        parser = TreeSitterGlslParser()
        code = """
        #version 330 core

        vec3 calculateDiffuse(vec3 normal, vec3 lightDir, vec3 color)
        {
            float diff = max(dot(normal, lightDir), 0.0);
            return diff * color;
        }

        vec3 calculateSpecular(vec3 normal, vec3 lightDir, vec3 viewDir, float shininess)
        {
            vec3 reflectDir = reflect(-lightDir, normal);
            float spec = pow(max(dot(viewDir, reflectDir), 0.0), shininess);
            return spec * vec3(1.0);
        }

        void main()
        {
            // Main shader code
        }
        """

        result = parser.parse(code, "functions.glsl")
        declarations = result.declarations

        # Check for functions
        functions = [d for d in declarations if d.kind in ["function", "entry_point"]]
        assert len(functions) == 3
        function_names = [f.name for f in functions]
        assert "calculateDiffuse" in function_names
        assert "calculateSpecular" in function_names
        assert "main" in function_names

    def test_empty_shader(self):
        """Test parsing empty shader file."""
        parser = TreeSitterGlslParser()
        code = ""

        result = parser.parse(code, "empty.glsl")
        assert result.declarations == []
        assert result.imports == []

    def test_malformed_shader_recovery(self):
        """Test parser recovery from malformed shader code."""
        parser = TreeSitterGlslParser()
        code = """
        #version 330 core

        uniform mat4 model;
        uniform mat4;  // Missing name

        void main() {
            // Some code
        """  # Missing closing brace

        # Should not raise an exception
        result = parser.parse(code, "malformed.glsl")

        # Should still extract what it can
        declarations = result.declarations
        uniforms = [d for d in declarations if d.kind == "uniform"]
        assert len(uniforms) >= 1  # At least the valid uniform

    def test_geometry_shader_specifics(self):
        """Test parsing geometry shader specific constructs."""
        parser = TreeSitterGlslParser()
        code = """
        #version 330 core

        layout(triangles) in;
        layout(triangle_strip, max_vertices = 6) out;

        in vec3 vNormal[];
        out vec3 gNormal;

        void main()
        {
            for(int i = 0; i < 3; i++)
            {
                gl_Position = gl_in[i].gl_Position;
                gNormal = vNormal[i];
                EmitVertex();
            }
            EndPrimitive();
        }
        """

        result = parser.parse(code, "geometry.glsl")
        declarations = result.declarations

        # Check for array I/O variables
        inputs = [d for d in declarations if "in_variable" in d.kind]
        outputs = [d for d in declarations if "out_variable" in d.kind]
        assert len(inputs) >= 1
        assert len(outputs) >= 1
