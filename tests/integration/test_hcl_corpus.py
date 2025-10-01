"""Integration tests for HCL2/Terraform parser with real-world examples."""

import pytest

from codeconcat.parser.language_parsers.tree_sitter_hcl_parser import (
    TreeSitterHclParser,
)


class TestHclCorpus:
    """Integration test suite for HCL2/Terraform parser with real-world examples."""

    def test_aws_ec2_vpc_configuration(self):
        """Test parsing a complete AWS EC2 + VPC configuration."""
        parser = TreeSitterHclParser()
        content = """
# AWS Provider Configuration
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "instance_count" {
  description = "Number of EC2 instances"
  type        = number
  default     = 2
}

# Data Sources
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

# VPC Resources
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "main-vpc"
    Environment = "production"
  }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "public-subnet-${count.index + 1}"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "main-igw"
  }
}

# EC2 Instances
resource "aws_instance" "web" {
  count         = var.instance_count
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t2.micro"
  subnet_id     = aws_subnet.public[count.index % 2].id

  tags = {
    Name        = "web-server-${count.index + 1}"
    Environment = "production"
  }
}

# Security Group
resource "aws_security_group" "web" {
  name        = "web-sg"
  description = "Security group for web servers"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "web-security-group"
  }
}

# Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "instance_ids" {
  description = "IDs of EC2 instances"
  value       = aws_instance.web[*].id
}

output "public_ips" {
  description = "Public IPs of EC2 instances"
  value       = aws_instance.web[*].public_ip
}

# Locals
locals {
  common_tags = {
    Project     = "terraform-test"
    Environment = "production"
    ManagedBy   = "Terraform"
  }
}
"""
        result = parser.parse(content, "aws_example.tf")

        # Verify parsing was successful
        assert result is not None
        assert result.error is None
        assert result.engine_used == "tree_sitter"

        # Verify we extracted multiple block types
        assert len(result.declarations) >= 10

        # Check for specific block types
        functions = [d for d in result.declarations if d.kind == "function"]  # resources + data
        properties = [d for d in result.declarations if d.kind == "property"]  # variables + outputs
        classes = [d for d in result.declarations if d.kind == "class"]  # providers
        objects = [d for d in result.declarations if d.kind == "object"]  # locals

        # Should have multiple resources and data sources (vpc, subnets, igw, instances, sg + 2 data sources)
        assert len(functions) >= 7, f"Expected at least 7 resources/data, got {len(functions)}"
        # Should have variables and outputs
        assert len(properties) >= 6, f"Expected at least 6 variables/outputs, got {len(properties)}"
        # Should have provider
        assert len(classes) >= 1, f"Expected at least 1 provider, got {len(classes)}"
        # Should have locals
        assert len(objects) >= 1, f"Expected at least 1 locals block, got {len(objects)}"

    def test_gcp_compute_network_configuration(self):
        """Test parsing a GCP compute and network configuration."""
        parser = TreeSitterHclParser()
        content = """
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "us-central1-a"
}

resource "google_compute_network" "vpc_network" {
  name                    = "terraform-network"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "terraform-subnet"
  ip_cidr_range = "10.2.0.0/16"
  region        = var.region
  network       = google_compute_network.vpc_network.id
}

resource "google_compute_instance" "vm_instance" {
  name         = "terraform-instance"
  machine_type = "e2-medium"
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.subnet.id

    access_config {
      // Ephemeral public IP
    }
  }

  metadata_startup_script = "echo 'Hello, World' > /tmp/hello.txt"

  tags = ["web", "dev"]
}

resource "google_compute_firewall" "allow_http" {
  name    = "allow-http"
  network = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["web"]
}

output "instance_ip" {
  description = "Public IP of the instance"
  value       = google_compute_instance.vm_instance.network_interface[0].access_config[0].nat_ip
}

output "network_name" {
  description = "Name of the VPC network"
  value       = google_compute_network.vpc_network.name
}
"""
        result = parser.parse(content, "gcp_example.tf")

        assert result is not None
        assert result.error is None
        assert len(result.declarations) >= 8

        # Verify GCP resource parsing
        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) >= 4, "Should have at least 4 GCP resources"

    def test_azure_resource_group_vm_configuration(self):
        """Test parsing an Azure resource group and VM configuration."""
        parser = TreeSitterHclParser()
        content = """
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "resource_group_location" {
  default     = "eastus"
  description = "Location of the resource group."
}

variable "resource_group_name" {
  default     = "rg-terraform-example"
  description = "Name of the resource group."
}

resource "azurerm_resource_group" "rg" {
  location = var.resource_group_location
  name     = var.resource_group_name
}

resource "azurerm_virtual_network" "vnet" {
  name                = "vnet-terraform"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
}

resource "azurerm_subnet" "subnet" {
  name                 = "subnet-terraform"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_public_ip" "public_ip" {
  name                = "pip-terraform"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  allocation_method   = "Dynamic"
}

resource "azurerm_network_interface" "nic" {
  name                = "nic-terraform"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.public_ip.id
  }
}

resource "azurerm_linux_virtual_machine" "vm" {
  name                = "vm-terraform"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  size                = "Standard_B1s"
  admin_username      = "azureuser"
  network_interface_ids = [
    azurerm_network_interface.nic.id,
  ]

  admin_ssh_key {
    username   = "azureuser"
    public_key = file("~/.ssh/id_rsa.pub")
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "UbuntuServer"
    sku       = "18.04-LTS"
    version   = "latest"
  }
}

output "resource_group_name" {
  value = azurerm_resource_group.rg.name
}

output "public_ip_address" {
  value = azurerm_linux_virtual_machine.vm.public_ip_address
}
"""
        result = parser.parse(content, "azure_example.tf")

        assert result is not None
        assert result.error is None
        assert len(result.declarations) >= 8

        # Verify Azure resource parsing
        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) >= 6, "Should have at least 6 Azure resources"

    def test_module_usage_configuration(self):
        """Test parsing Terraform configuration with module usage."""
        parser = TreeSitterHclParser()
        content = """
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.0.0"

  name = "my-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-west-2a", "us-west-2b", "us-west-2c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  enable_vpn_gateway = false

  tags = {
    Terraform   = "true"
    Environment = "dev"
  }
}

module "ec2_cluster" {
  source  = "terraform-aws-modules/ec2-instance/aws"
  version = "~> 3.0"

  name           = "my-cluster"
  instance_count = 3

  ami                    = "ami-0c55b159cbfafe1f0"
  instance_type          = "t2.micro"
  key_name               = "user-key"
  monitoring             = true
  vpc_security_group_ids = ["sg-12345678"]
  subnet_id              = module.vpc.private_subnets[0]

  tags = {
    Name = "EC2-Cluster"
  }
}

output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.vpc.vpc_id
}

output "ec2_instance_ids" {
  description = "List of IDs of instances"
  value       = module.ec2_cluster.id
}
"""
        result = parser.parse(content, "modules_example.tf")

        assert result is not None
        assert result.error is None

        # Should have module declarations
        modules = [d for d in result.declarations if d.kind == "module"]
        assert len(modules) >= 2, f"Expected at least 2 modules, got {len(modules)}"

        # Should have output declarations
        outputs = [d for d in result.declarations if d.kind == "property"]
        assert len(outputs) >= 2, f"Expected at least 2 outputs, got {len(outputs)}"

    def test_complex_variable_types(self):
        """Test parsing complex variable types (lists, maps, objects)."""
        parser = TreeSitterHclParser()
        content = """
variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b"]
}

variable "instance_tags" {
  description = "Map of tags for instances"
  type        = map(string)
  default = {
    Environment = "dev"
    Project     = "test"
  }
}

variable "instance_config" {
  description = "Complex instance configuration"
  type = object({
    instance_type = string
    disk_size     = number
    monitoring    = bool
    tags          = map(string)
  })
  default = {
    instance_type = "t2.micro"
    disk_size     = 20
    monitoring    = true
    tags = {
      Name = "default-instance"
    }
  }
}

variable "subnet_configurations" {
  description = "List of subnet configurations"
  type = list(object({
    name              = string
    cidr_block        = string
    availability_zone = string
  }))
  default = [
    {
      name              = "subnet-1"
      cidr_block        = "10.0.1.0/24"
      availability_zone = "us-west-2a"
    },
    {
      name              = "subnet-2"
      cidr_block        = "10.0.2.0/24"
      availability_zone = "us-west-2b"
    }
  ]
}
"""
        result = parser.parse(content, "complex_variables.tf")

        assert result is not None
        assert result.error is None

        # Should parse all variable declarations
        variables = [d for d in result.declarations if d.kind == "property"]
        assert len(variables) >= 4, f"Expected at least 4 variables, got {len(variables)}"

    def test_backends_and_remote_state(self):
        """Test parsing backend configuration and remote state."""
        parser = TreeSitterHclParser()
        content = """
terraform {
  required_version = ">= 1.0"

  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

data "terraform_remote_state" "vpc" {
  backend = "s3"

  config = {
    bucket = "shared-terraform-state"
    key    = "vpc/terraform.tfstate"
    region = "us-west-2"
  }
}

data "terraform_remote_state" "network" {
  backend = "s3"

  config = {
    bucket = "shared-terraform-state"
    key    = "network/terraform.tfstate"
    region = "us-west-2"
  }
}

resource "aws_instance" "app" {
  ami           = "ami-12345678"
  instance_type = "t2.micro"
  subnet_id     = data.terraform_remote_state.vpc.outputs.subnet_id
}
"""
        result = parser.parse(content, "backend_example.tf")

        assert result is not None
        assert result.error is None
        assert len(result.declarations) >= 3

    def test_parse_success_rate(self):
        """Test that parser achieves 100% parse success on various files."""
        parser = TreeSitterHclParser()

        test_files = [
            # Simple resource
            'resource "aws_instance" "web" { ami = "ami-123" }',

            # Module
            'module "vpc" { source = "terraform-aws-modules/vpc/aws" }',

            # Provider with complex config
            '''provider "aws" {
              region = "us-west-2"
              assume_role {
                role_arn = "arn:aws:iam::123456789012:role/TerraformRole"
              }
            }''',

            # Data source
            'data "aws_ami" "ubuntu" { most_recent = true }',

            # Output
            'output "instance_id" { value = aws_instance.web.id }',

            # Variable
            'variable "region" { type = string default = "us-west-2" }',

            # Locals
            'locals { common_tags = { Environment = "prod" } }',
        ]

        success_count = 0
        total_count = len(test_files)

        for i, content in enumerate(test_files):
            result = parser.parse(content, f"test_{i}.tf")
            if result.error is None:
                success_count += 1

        success_rate = (success_count / total_count) * 100
        assert success_rate == 100.0, f"Parse success rate: {success_rate}% (expected 100%)"
