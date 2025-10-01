"""Tests for the Tree-sitter HCL2/Terraform parser."""

from codeconcat.parser.language_parsers.tree_sitter_hcl_parser import (
    TreeSitterHclParser,
)


class TestTreeSitterHclParser:
    """Test suite for TreeSitterHclParser."""

    def test_parser_initialization(self):
        """Test that the parser initializes correctly."""
        parser = TreeSitterHclParser()
        assert parser is not None
        assert parser.language_name == "hcl"
        assert parser.ts_language is not None
        assert parser.parser is not None

    def test_parse_simple_resource(self):
        """Test parsing a simple Terraform resource block."""
        parser = TreeSitterHclParser()
        content = """
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
}
"""
        result = parser.parse(content, "test.tf")
        assert result is not None
        assert len(result.declarations) >= 1

        # Resources are mapped to 'function' kind
        resources = [d for d in result.declarations if d.kind == "function"]
        assert len(resources) == 1
        assert resources[0].name == "web"

    def test_parse_multiple_resources(self):
        """Test parsing multiple resource blocks."""
        parser = TreeSitterHclParser()
        content = """
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
}

resource "aws_s3_bucket" "data" {
  bucket = "my-terraform-state"
  acl    = "private"
}
"""
        result = parser.parse(content, "test.tf")
        assert result is not None

        # Resources are mapped to 'function' kind
        resources = [d for d in result.declarations if d.kind == "function"]
        assert len(resources) == 2
        assert "web" in [r.name for r in resources]
        assert "data" in [r.name for r in resources]

    def test_parse_module_block(self):
        """Test parsing a module block."""
        parser = TreeSitterHclParser()
        content = """
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "3.0.0"

  name = "my-vpc"
  cidr = "10.0.0.0/16"
}
"""
        result = parser.parse(content, "test.tf")
        assert result is not None

        # Modules are mapped to 'module' kind
        modules = [d for d in result.declarations if d.kind == "module"]
        assert len(modules) >= 1

    def test_parse_provider_block(self):
        """Test parsing a provider block."""
        parser = TreeSitterHclParser()
        content = """
provider "aws" {
  region = "us-west-2"
  profile = "default"
}
"""
        result = parser.parse(content, "test.tf")
        assert result is not None

        # Providers are mapped to 'class' kind
        providers = [d for d in result.declarations if d.kind == "class"]
        assert len(providers) >= 1

    def test_parse_variable_block(self):
        """Test parsing a variable block."""
        parser = TreeSitterHclParser()
        content = """
variable "instance_count" {
  description = "Number of instances to create"
  type        = number
  default     = 1
}
"""
        result = parser.parse(content, "test.tf")
        assert result is not None

        # Variables are mapped to 'property' kind
        variables = [d for d in result.declarations if d.kind == "property"]
        assert len(variables) >= 1

    def test_parse_data_block(self):
        """Test parsing a data source block."""
        parser = TreeSitterHclParser()
        content = """
data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }
}
"""
        result = parser.parse(content, "test.tf")
        assert result is not None

        # Data sources are mapped to 'function' kind
        data_sources = [d for d in result.declarations if d.kind == "function"]
        assert len(data_sources) >= 1

    def test_parse_output_block(self):
        """Test parsing an output block."""
        parser = TreeSitterHclParser()
        content = """
output "instance_ip_addr" {
  value       = aws_instance.web.public_ip
  description = "The public IP address of the web server"
}
"""
        result = parser.parse(content, "test.tf")
        assert result is not None

        # Outputs are mapped to 'property' kind
        outputs = [d for d in result.declarations if d.kind == "property"]
        assert len(outputs) >= 1

    def test_parse_locals_block(self):
        """Test parsing a locals block."""
        parser = TreeSitterHclParser()
        content = """
locals {
  service_name = "my-service"
  owner        = "DevOps Team"

  common_tags = {
    Service = local.service_name
    Owner   = local.owner
  }
}
"""
        result = parser.parse(content, "test.tf")
        assert result is not None

        # Locals are mapped to 'object' kind
        locals_blocks = [d for d in result.declarations if d.kind == "object"]
        assert len(locals_blocks) >= 1

    def test_parse_terraform_block(self):
        """Test parsing a terraform configuration block."""
        parser = TreeSitterHclParser()
        content = """
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}
"""
        result = parser.parse(content, "test.tf")
        assert result is not None
        # Terraform blocks captured in imports query

    def test_parse_with_variable_interpolation(self):
        """Test parsing with variable interpolation."""
        parser = TreeSitterHclParser()
        content = """
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type

  tags = {
    Name = "${var.project_name}-web-server"
  }
}
"""
        result = parser.parse(content, "test.tf")
        assert result is not None
        assert len(result.declarations) >= 1

    def test_parse_complex_terraform_file(self):
        """Test parsing a complex Terraform file with multiple block types."""
        parser = TreeSitterHclParser()
        content = """
terraform {
  required_version = ">= 1.0"
}

provider "aws" {
  region = var.aws_region
}

variable "instance_count" {
  type    = number
  default = 2
}

data "aws_ami" "ubuntu" {
  most_recent = true
}

resource "aws_instance" "web" {
  count         = var.instance_count
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t2.micro"
}

output "instance_ids" {
  value = aws_instance.web[*].id
}

locals {
  common_tags = {
    Environment = "production"
  }
}
"""
        result = parser.parse(content, "test.tf")
        assert result is not None
        # Should have: provider (class), variable (property), data (function), resource (function), output (property), locals (object)
        assert len(result.declarations) >= 5

    def test_parse_gcp_resource(self):
        """Test parsing GCP Terraform resources."""
        parser = TreeSitterHclParser()
        content = """
resource "google_compute_instance" "default" {
  name         = "test-instance"
  machine_type = "e2-medium"
  zone         = "us-central1-a"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }
}
"""
        result = parser.parse(content, "test.tf")
        assert result is not None

        # Resources are mapped to 'function' kind
        resources = [d for d in result.declarations if d.kind == "function"]
        assert len(resources) >= 1

    def test_parse_azure_resource(self):
        """Test parsing Azure Terraform resources."""
        parser = TreeSitterHclParser()
        content = """
resource "azurerm_virtual_machine" "main" {
  name                  = "test-vm"
  location              = "East US"
  resource_group_name   = azurerm_resource_group.main.name
  vm_size               = "Standard_DS1_v2"
}
"""
        result = parser.parse(content, "test.tf")
        assert result is not None

        # Resources are mapped to 'function' kind
        resources = [d for d in result.declarations if d.kind == "function"]
        assert len(resources) >= 1

    def test_parse_empty_file(self):
        """Test parsing an empty file."""
        parser = TreeSitterHclParser()
        content = ""
        result = parser.parse(content, "empty.tf")
        assert result is not None
        assert len(result.declarations) == 0

    def test_parse_comments_only(self):
        """Test parsing a file with only comments."""
        parser = TreeSitterHclParser()
        content = """
# This is a comment
// This is also a comment
/* Multi-line
   comment */
"""
        result = parser.parse(content, "comments.tf")
        assert result is not None
        # Comments should not create declarations

    def test_performance_large_file(self):
        """Test parser performance with a larger file."""
        parser = TreeSitterHclParser()
        # Generate a file with 50 resources
        resources = "\n\n".join([
            f'''resource "aws_instance" "server_{i}" {{
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  tags = {{
    Name = "Server-{i}"
  }}
}}''' for i in range(50)
        ])

        result = parser.parse(resources, "large.tf")
        assert result is not None
        # Should handle large files without errors

    def test_malformed_missing_closing_brace(self):
        """Test parser handles malformed HCL with missing closing brace."""
        parser = TreeSitterHclParser()
        content = """
resource "aws_instance" "web" {
  ami = "ami-123"
  # Missing closing brace
"""
        result = parser.parse(content, "malformed.tf")
        # Parser should handle errors gracefully
        assert result is not None
        # May have error flag set
        if result.error:
            assert "error" in result.error.lower() or "line" in result.error.lower()

    def test_malformed_invalid_block_syntax(self):
        """Test parser handles invalid block syntax."""
        parser = TreeSitterHclParser()
        content = """
resource aws_instance web {
  # Missing quotes around type and name
  ami = "ami-123"
}
"""
        result = parser.parse(content, "invalid.tf")
        assert result is not None
        # Should parse with errors or partial results

    def test_malformed_incomplete_variable(self):
        """Test parser handles incomplete variable block."""
        parser = TreeSitterHclParser()
        content = """
variable "instance_count" {
  type =
  # Incomplete type assignment
}
"""
        result = parser.parse(content, "incomplete.tf")
        assert result is not None

    def test_syntax_error_recovery(self):
        """Test parser can recover from syntax errors and continue."""
        parser = TreeSitterHclParser()
        content = """
resource "aws_instance" "web" {
  ami = "ami-123"
}

# Malformed block
resource "bad syntax here

resource "aws_s3_bucket" "data" {
  bucket = "my-bucket"
}
"""
        result = parser.parse(content, "recovery.tf")
        assert result is not None
        # Should still extract valid blocks
        resources = [d for d in result.declarations if d.kind == "function"]
        # At least the first valid resource should be parsed
        assert len(resources) >= 1
