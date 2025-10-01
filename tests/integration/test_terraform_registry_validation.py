"""Integration tests for Terraform Registry module parsing validation.

Tests the HCL parser against real-world Terraform Registry modules to ensure:
- >99% parse accuracy (successful parsing of all module files)
- Performance <80ms for 10KB files
- Correct extraction of resources, variables, outputs, and other constructs
"""

import time
from pathlib import Path

from codeconcat.parser.language_parsers.tree_sitter_hcl_parser import (
    TreeSitterHclParser,
)


class TestTerraformRegistryValidation:
    """Test suite for validating parser against Terraform Registry modules."""

    def test_aws_vpc_module_parsing(self):
        """Test parsing AWS VPC module from registry (terraform-aws-modules/vpc)."""
        parser = TreeSitterHclParser()
        fixture_path = Path(__file__).parent / "fixtures/terraform/registry/aws/vpc-complete.tf"

        content = fixture_path.read_text()
        file_size = len(content.encode("utf-8"))

        # Benchmark parsing time
        start_time = time.perf_counter()
        result = parser.parse(content, str(fixture_path))
        parse_time_ms = (time.perf_counter() - start_time) * 1000

        # Validate parsing succeeded
        assert result is not None
        assert result.error is None or "error" not in result.error.lower()

        # Count declarations by type
        resources = [d for d in result.declarations if d.kind == "function"]
        properties = [d for d in result.declarations if d.kind == "property"]
        providers = [d for d in result.declarations if d.kind == "class"]

        # AWS VPC module should have:
        # - ~13 resources (vpc, igw, subnets, route tables, nat gateways, etc.)
        # - ~16 properties (variables + outputs)
        # - 1 provider
        # - 1 locals block
        assert len(resources) >= 10, f"Expected >=10 resources, got {len(resources)}"
        assert len(properties) >= 15, f"Expected >=15 properties (vars+outputs), got {len(properties)}"
        assert len(providers) == 1, f"Expected 1 provider, got {len(providers)}"

        # Performance requirement: <80ms for 10KB file
        if file_size <= 10240:  # 10KB
            assert parse_time_ms < 80, f"Parsing took {parse_time_ms:.2f}ms, expected <80ms"

        print(f"\n✓ AWS VPC Module:")
        print(f"  File size: {file_size / 1024:.1f}KB")
        print(f"  Parse time: {parse_time_ms:.2f}ms")
        print(f"  Resources: {len(resources)}")
        print(f"  Properties: {len(properties)}")
        print(f"  Providers: {len(providers)}")
        print(f"  Total declarations: {len(result.declarations)}")

    def test_gcp_compute_module_parsing(self):
        """Test parsing GCP Compute module from registry (terraform-google-modules/vm)."""
        parser = TreeSitterHclParser()
        fixture_path = Path(__file__).parent / "fixtures/terraform/registry/gcp/compute-instance.tf"

        content = fixture_path.read_text()
        file_size = len(content.encode("utf-8"))

        # Benchmark parsing time
        start_time = time.perf_counter()
        result = parser.parse(content, str(fixture_path))
        parse_time_ms = (time.perf_counter() - start_time) * 1000

        # Validate parsing succeeded
        assert result is not None
        assert result.error is None or "error" not in result.error.lower()

        # Count declarations by type
        resources = [d for d in result.declarations if d.kind == "function"]
        properties = [d for d in result.declarations if d.kind == "property"]
        providers = [d for d in result.declarations if d.kind == "class"]

        # GCP Compute module should have:
        # - ~8 resources (instance, service account, iam members, firewall rules, data sources)
        # - ~17 properties (variables + outputs)
        # - 1 provider
        assert len(resources) >= 6, f"Expected >=6 resources, got {len(resources)}"
        assert len(properties) >= 15, f"Expected >=15 properties (vars+outputs), got {len(properties)}"
        assert len(providers) == 1, f"Expected 1 provider, got {len(providers)}"

        # Performance requirement
        if file_size <= 10240:
            assert parse_time_ms < 80, f"Parsing took {parse_time_ms:.2f}ms, expected <80ms"

        print(f"\n✓ GCP Compute Module:")
        print(f"  File size: {file_size / 1024:.1f}KB")
        print(f"  Parse time: {parse_time_ms:.2f}ms")
        print(f"  Resources: {len(resources)}")
        print(f"  Properties: {len(properties)}")
        print(f"  Providers: {len(providers)}")
        print(f"  Total declarations: {len(result.declarations)}")

    def test_azure_vnet_module_parsing(self):
        """Test parsing Azure VNet module from registry (Azure/vnet/azurerm)."""
        parser = TreeSitterHclParser()
        fixture_path = Path(__file__).parent / "fixtures/terraform/registry/azure/virtual-network.tf"

        content = fixture_path.read_text()
        file_size = len(content.encode("utf-8"))

        # Benchmark parsing time
        start_time = time.perf_counter()
        result = parser.parse(content, str(fixture_path))
        parse_time_ms = (time.perf_counter() - start_time) * 1000

        # Validate parsing succeeded
        assert result is not None
        assert result.error is None or "error" not in result.error.lower()

        # Count declarations by type
        resources = [d for d in result.declarations if d.kind == "function"]
        properties = [d for d in result.declarations if d.kind == "property"]
        providers = [d for d in result.declarations if d.kind == "class"]

        # Azure VNet module should have:
        # - ~15 resources (rg, vnet, subnets, nsg, routes, nat gateway, etc.)
        # - ~20 properties (variables + outputs)
        # - 1 provider
        # - 1 locals block
        assert len(resources) >= 12, f"Expected >=12 resources, got {len(resources)}"
        assert len(properties) >= 18, f"Expected >=18 properties (vars+outputs), got {len(properties)}"
        assert len(providers) == 1, f"Expected 1 provider, got {len(providers)}"

        # Performance requirement
        if file_size <= 10240:
            assert parse_time_ms < 80, f"Parsing took {parse_time_ms:.2f}ms, expected <80ms"

        print(f"\n✓ Azure VNet Module:")
        print(f"  File size: {file_size / 1024:.1f}KB")
        print(f"  Parse time: {parse_time_ms:.2f}ms")
        print(f"  Resources: {len(resources)}")
        print(f"  Properties: {len(properties)}")
        print(f"  Providers: {len(providers)}")
        print(f"  Total declarations: {len(result.declarations)}")

    def test_registry_modules_parse_success_rate(self):
        """Test that all registry modules parse successfully (>99% accuracy)."""
        parser = TreeSitterHclParser()
        fixtures_dir = Path(__file__).parent / "fixtures/terraform/registry"

        # Find all .tf files in registry fixtures
        tf_files = list(fixtures_dir.rglob("*.tf"))
        assert len(tf_files) > 0, "No Terraform files found in registry fixtures"

        successful_parses = 0
        total_files = len(tf_files)
        failed_files = []

        for tf_file in tf_files:
            content = tf_file.read_text()
            result = parser.parse(content, str(tf_file))

            if result is not None and (result.error is None or "error" not in result.error.lower()):
                successful_parses += 1
            else:
                failed_files.append(tf_file.name)

        success_rate = (successful_parses / total_files) * 100

        print(f"\n✓ Registry Module Parse Success Rate:")
        print(f"  Total files: {total_files}")
        print(f"  Successful: {successful_parses}")
        print(f"  Failed: {total_files - successful_parses}")
        print(f"  Success rate: {success_rate:.1f}%")

        if failed_files:
            print(f"  Failed files: {', '.join(failed_files)}")

        # Require >99% success rate (task requirement)
        assert success_rate > 99.0, f"Parse success rate {success_rate:.1f}% is below 99% threshold"

    def test_performance_benchmark_10kb_file(self):
        """Benchmark parser performance with 10KB file (<80ms requirement)."""
        parser = TreeSitterHclParser()

        # Use AWS VPC module (largest fixture, ~7KB)
        fixture_path = Path(__file__).parent / "fixtures/terraform/registry/aws/vpc-complete.tf"
        content = fixture_path.read_text()
        file_size = len(content.encode("utf-8"))

        # Run multiple iterations for accurate benchmark
        iterations = 10
        total_time = 0

        for _ in range(iterations):
            start_time = time.perf_counter()
            result = parser.parse(content, str(fixture_path))
            total_time += (time.perf_counter() - start_time) * 1000

            assert result is not None

        avg_time_ms = total_time / iterations

        print(f"\n✓ Performance Benchmark:")
        print(f"  File size: {file_size / 1024:.2f}KB")
        print(f"  Iterations: {iterations}")
        print(f"  Average parse time: {avg_time_ms:.2f}ms")
        print(f"  Min target: <80ms for 10KB")

        # If file is <=10KB, must be <80ms
        if file_size <= 10240:
            assert avg_time_ms < 80, f"Average parsing time {avg_time_ms:.2f}ms exceeds 80ms threshold"

    def test_complex_hcl_constructs_coverage(self):
        """Test that parser handles all HCL constructs in registry modules."""
        parser = TreeSitterHclParser()
        fixtures_dir = Path(__file__).parent / "fixtures/terraform/registry"

        # Collect all declarations from all registry modules
        all_declarations = []
        for tf_file in fixtures_dir.rglob("*.tf"):
            content = tf_file.read_text()
            result = parser.parse(content, str(tf_file))
            if result:
                all_declarations.extend(result.declarations)

        # Verify we extracted all major HCL construct types
        declaration_kinds = {d.kind for d in all_declarations}

        print(f"\n✓ HCL Construct Coverage:")
        print(f"  Total declarations: {len(all_declarations)}")
        print(f"  Declaration kinds found: {sorted(declaration_kinds)}")

        # Should have extracted: resources (function), variables (property),
        # outputs (property), providers (class), modules (module), locals (object)
        assert "function" in declaration_kinds, "No resources/data sources extracted"
        assert "property" in declaration_kinds, "No variables/outputs extracted"
        assert "class" in declaration_kinds, "No providers extracted"

        # Verify substantial number of declarations (3 registry modules with ~30 declarations each)
        assert len(all_declarations) >= 90, f"Only extracted {len(all_declarations)} declarations, expected >=90"
