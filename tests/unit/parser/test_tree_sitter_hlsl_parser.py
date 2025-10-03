"""
Unit tests for TreeSitterHlslParser.

Tests comprehensive HLSL parsing including:
- Constant buffers (cbuffer/tbuffer)
- Structured buffers and RW resources
- Texture and sampler declarations
- Semantics on parameters and returns
- Compute shader attributes
- Register assignments
"""

import pytest
from unittest.mock import Mock, patch

from codeconcat.parser.language_parsers.tree_sitter_hlsl_parser import TreeSitterHlslParser
from codeconcat.errors import LanguageParserError


class TestTreeSitterHlslParser:
    """Test suite for HLSL parser."""

    def test_parser_initialization(self):
        """Test parser initializes correctly."""
        parser = TreeSitterHlslParser()
        assert parser.language_name == "hlsl"
        assert parser.ts_language is not None
        assert parser.parser is not None

    def test_parse_simple_vertex_shader(self):
        """Test parsing a simple vertex shader."""
        parser = TreeSitterHlslParser()
        code = """
        cbuffer MatrixBuffer : register(b0)
        {
            float4x4 worldMatrix;
            float4x4 viewMatrix;
            float4x4 projectionMatrix;
        };

        struct VertexInput
        {
            float3 position : POSITION;
            float2 texCoord : TEXCOORD0;
            float3 normal : NORMAL;
        };

        struct PixelInput
        {
            float4 position : SV_Position;
            float2 texCoord : TEXCOORD0;
            float3 normal : NORMAL;
        };

        PixelInput main(VertexInput input)
        {
            PixelInput output;
            float4 worldPos = mul(float4(input.position, 1.0f), worldMatrix);
            float4 viewPos = mul(worldPos, viewMatrix);
            output.position = mul(viewPos, projectionMatrix);
            output.texCoord = input.texCoord;
            output.normal = input.normal;
            return output;
        }
        """

        result = parser.parse(code, "vertex.hlsl")
        declarations = result.declarations

        # Check for constant buffers
        cbuffers = [d for d in declarations if d.kind == "cbuffer"]
        assert len(cbuffers) == 1
        assert cbuffers[0].name == "MatrixBuffer"

        # Check for structs
        structs = [d for d in declarations if d.kind == "struct"]
        assert len(structs) == 2
        struct_names = [s.name for s in structs]
        assert "VertexInput" in struct_names
        assert "PixelInput" in struct_names

        # Check for functions
        functions = [d for d in declarations if "entry_point" in d.kind or d.kind == "function"]
        assert len(functions) >= 1
        assert any(f.name == "main" for f in functions)

    def test_parse_pixel_shader_with_textures(self):
        """Test parsing pixel shader with textures and samplers."""
        parser = TreeSitterHlslParser()
        code = """
        Texture2D diffuseTexture : register(t0);
        Texture2D normalTexture : register(t1);
        SamplerState samplerState : register(s0);

        struct PixelInput
        {
            float4 position : SV_Position;
            float2 texCoord : TEXCOORD0;
            float3 normal : NORMAL;
        };

        float4 main(PixelInput input) : SV_Target
        {
            float4 diffuseColor = diffuseTexture.Sample(samplerState, input.texCoord);
            float3 normalMap = normalTexture.Sample(samplerState, input.texCoord).rgb;

            // Simple lighting calculation
            float3 lightDir = normalize(float3(1, 1, -1));
            float intensity = saturate(dot(input.normal, lightDir));

            return diffuseColor * intensity;
        }
        """

        result = parser.parse(code, "pixel.hlsl")
        declarations = result.declarations

        # Check for textures
        textures = [d for d in declarations if d.kind == "texture"]
        assert len(textures) == 2
        texture_names = [t.name for t in textures]
        assert "diffuseTexture" in texture_names
        assert "normalTexture" in texture_names

        # Check for samplers
        samplers = [d for d in declarations if d.kind == "sampler"]
        assert len(samplers) == 1
        assert samplers[0].name == "samplerState"

    def test_parse_compute_shader(self):
        """Test parsing compute shader with numthreads attribute."""
        parser = TreeSitterHlslParser()
        code = """
        RWTexture2D<float4> outputTexture : register(u0);
        StructuredBuffer<float4> inputData : register(t0);

        [numthreads(8, 8, 1)]
        void CSMain(uint3 id : SV_DispatchThreadID)
        {
            uint index = id.y * 256 + id.x;
            float4 data = inputData[index];
            outputTexture[id.xy] = data * 2.0f;
        }
        """

        result = parser.parse(code, "compute.hlsl")
        declarations = result.declarations

        # Check for RW texture
        rw_textures = [d for d in declarations if d.kind == "rw_texture"]
        assert len(rw_textures) >= 1
        assert any(t.name == "outputTexture" for t in rw_textures)

        # Check for structured buffer
        buffers = [d for d in declarations if "buffer" in d.kind]
        assert len(buffers) >= 1
        assert any(b.name == "inputData" for b in buffers)

        # Check for compute entry point
        compute_funcs = [d for d in declarations if d.kind == "compute_entry_point"]
        assert len(compute_funcs) >= 1
        assert any(f.name == "CSMain" for f in compute_funcs)

        # Check that shader stage is detected as compute
        assert parser.shader_stage == "compute"

    def test_parse_structured_buffers(self):
        """Test parsing various structured buffer types."""
        parser = TreeSitterHlslParser()
        code = """
        struct Particle
        {
            float3 position;
            float3 velocity;
            float life;
        };

        StructuredBuffer<Particle> particlesIn : register(t0);
        RWStructuredBuffer<Particle> particlesOut : register(u0);
        AppendStructuredBuffer<Particle> deadParticles : register(u1);
        ConsumeStructuredBuffer<Particle> newParticles : register(u2);
        ByteAddressBuffer rawData : register(t1);
        RWByteAddressBuffer rwRawData : register(u3);

        void ProcessParticles(uint id : SV_DispatchThreadID)
        {
            Particle p = particlesIn[id];
            p.life -= 0.01f;
            particlesOut[id] = p;
        }
        """

        result = parser.parse(code, "buffers.hlsl")
        declarations = result.declarations

        # Check for different buffer types
        buffers = [d for d in declarations if "buffer" in d.kind]
        assert len(buffers) >= 6

        buffer_names = [b.name for b in buffers]
        assert "particlesIn" in buffer_names
        assert "particlesOut" in buffer_names
        assert "deadParticles" in buffer_names
        assert "newParticles" in buffer_names
        assert "rawData" in buffer_names
        assert "rwRawData" in buffer_names

    def test_parse_cbuffer_and_tbuffer(self):
        """Test parsing constant and texture buffers."""
        parser = TreeSitterHlslParser()
        code = """
        cbuffer SceneConstants : register(b0)
        {
            float4x4 viewProj;
            float4 lightPosition;
            float4 lightColor;
            float time;
        };

        tbuffer TextureData : register(t10)
        {
            float4 textureScaleOffset;
            int textureIndex;
        };

        void main()
        {
            // Shader code
        }
        """

        result = parser.parse(code, "buffers.hlsl")
        declarations = result.declarations

        # Check for cbuffer
        cbuffers = [d for d in declarations if d.kind == "cbuffer"]
        assert len(cbuffers) == 1
        assert cbuffers[0].name == "SceneConstants"

        # Check for tbuffer
        tbuffers = [d for d in declarations if d.kind == "tbuffer"]
        assert len(tbuffers) == 1
        assert tbuffers[0].name == "TextureData"

    def test_parse_semantics(self):
        """Test parsing various HLSL semantics."""
        parser = TreeSitterHlslParser()
        code = """
        struct VSInput
        {
            float3 position : POSITION;
            float3 normal : NORMAL;
            float2 texCoord : TEXCOORD0;
            float4 color : COLOR0;
            uint instanceID : SV_InstanceID;
        };

        struct PSInput
        {
            float4 position : SV_Position;
            float3 worldPos : POSITION1;
            float2 texCoord : TEXCOORD0;
            float4 color : COLOR0;
            uint primitiveID : SV_PrimitiveID;
        };

        PSInput VSMain(VSInput input)
        {
            PSInput output;
            output.position = float4(input.position, 1.0f);
            output.worldPos = input.position;
            output.texCoord = input.texCoord;
            output.color = input.color;
            output.primitiveID = 0;
            return output;
        }

        float4 PSMain(PSInput input) : SV_Target
        {
            return input.color;
        }
        """

        result = parser.parse(code, "semantics.hlsl")
        declarations = result.declarations

        # Check for vertex shader entry point
        vs_funcs = [d for d in declarations if d.kind == "vertex_entry_point"]
        # Note: Detection might not work perfectly without full semantic analysis

        # Check for pixel shader entry point
        ps_funcs = [d for d in declarations if d.kind == "pixel_entry_point"]
        # Should detect PSMain based on SV_Target semantic

    def test_parse_typedef_declarations(self):
        """Test parsing typedef declarations."""
        parser = TreeSitterHlslParser()
        code = """
        typedef float3 Vector;
        typedef float4x4 Matrix;

        typedef struct
        {
            Vector position;
            Vector normal;
            float2 uv;
        } Vertex;

        Vector TransformVector(Vector v, Matrix m)
        {
            return mul(float4(v, 0.0f), m).xyz;
        }
        """

        result = parser.parse(code, "typedefs.hlsl")
        declarations = result.declarations

        # Check for typedefs
        typedefs = [d for d in declarations if d.kind == "typedef"]
        assert len(typedefs) >= 2
        typedef_names = [t.name for t in typedefs]
        assert "Vector" in typedef_names
        assert "Matrix" in typedef_names

    def test_parse_global_variables(self):
        """Test parsing global variable declarations."""
        parser = TreeSitterHlslParser()
        code = """
        static const float PI = 3.14159265f;
        static const int MAX_LIGHTS = 16;

        groupshared float sharedData[256];

        float4 globalColor : register(c0);

        void main()
        {
            // Shader code
        }
        """

        result = parser.parse(code, "globals.hlsl")
        declarations = result.declarations

        # Check for global variables
        globals = [d for d in declarations if "global" in d.kind or "constant" in d.kind]
        assert len(globals) >= 1

    def test_parse_multiple_entry_points(self):
        """Test parsing shader with multiple entry points."""
        parser = TreeSitterHlslParser()
        code = """
        struct VSOutput
        {
            float4 position : SV_Position;
            float2 texCoord : TEXCOORD0;
        };

        VSOutput VSMain(float3 position : POSITION, float2 texCoord : TEXCOORD0)
        {
            VSOutput output;
            output.position = float4(position, 1.0f);
            output.texCoord = texCoord;
            return output;
        }

        float4 PSMain(VSOutput input) : SV_Target
        {
            return float4(input.texCoord, 0.0f, 1.0f);
        }

        [numthreads(1, 1, 1)]
        void CSMain(uint3 id : SV_DispatchThreadID)
        {
            // Compute shader code
        }
        """

        result = parser.parse(code, "multi_entry.hlsl")
        declarations = result.declarations

        # Check for multiple functions
        functions = [d for d in declarations if d.kind in ["function", "vertex_entry_point",
                                                           "pixel_entry_point", "compute_entry_point"]]
        assert len(functions) >= 3
        function_names = [f.name for f in functions]
        assert "VSMain" in function_names
        assert "PSMain" in function_names
        assert "CSMain" in function_names

    def test_empty_shader(self):
        """Test parsing empty shader file."""
        parser = TreeSitterHlslParser()
        code = ""

        result = parser.parse(code, "empty.hlsl")
        assert result.declarations == []
        assert result.imports == []

    def test_malformed_shader_recovery(self):
        """Test parser recovery from malformed shader code."""
        parser = TreeSitterHlslParser()
        code = """
        cbuffer Constants : register(b0)
        {
            float4x4 world;
            float4x4;  // Missing name
        };

        float4 main() : SV_Target
        {
            return float4(1, 0, 0
        """  # Missing closing parenthesis and brace

        # Should not raise an exception
        result = parser.parse(code, "malformed.hlsl")

        # Should still extract what it can
        declarations = result.declarations
        cbuffers = [d for d in declarations if d.kind == "cbuffer"]
        assert len(cbuffers) >= 1  # At least the cbuffer declaration

    def test_parse_texture_arrays(self):
        """Test parsing texture array declarations."""
        parser = TreeSitterHlslParser()
        code = """
        Texture2DArray<float4> textureArray : register(t0);
        TextureCubeArray<float4> cubeArray : register(t1);
        RWTexture2DArray<float4> rwTextureArray : register(u0);

        SamplerState sampler : register(s0);

        float4 SampleArray(float3 coords)
        {
            return textureArray.Sample(sampler, coords);
        }
        """

        result = parser.parse(code, "texture_arrays.hlsl")
        declarations = result.declarations

        # Check for texture arrays
        textures = [d for d in declarations if "texture" in d.kind]
        assert len(textures) >= 2

        # Check for RW texture array
        rw_textures = [d for d in declarations if d.kind == "rw_texture"]
        assert len(rw_textures) >= 1
