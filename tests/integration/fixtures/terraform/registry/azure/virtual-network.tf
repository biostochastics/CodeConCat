# Azure Virtual Network Module - Based on Azure/vnet/azurerm
# https://registry.terraform.io/modules/Azure/vnet/azurerm/latest

terraform {
  required_version = ">= 1.0"
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

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "my-resource-group"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "East US"
}

variable "vnet_name" {
  description = "Name of the virtual network"
  type        = string
  default     = "my-vnet"
}

variable "address_space" {
  description = "Address space for the virtual network"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "subnet_prefixes" {
  description = "Subnet CIDR prefixes"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "subnet_names" {
  description = "Subnet names"
  type        = list(string)
  default     = ["subnet-1", "subnet-2", "subnet-3"]
}

variable "dns_servers" {
  description = "DNS servers"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default = {
    Environment = "Production"
    ManagedBy   = "Terraform"
  }
}

variable "nsg_ids" {
  description = "Network Security Group IDs"
  type        = map(string)
  default     = {}
}

variable "route_tables_ids" {
  description = "Route table IDs"
  type        = map(string)
  default     = {}
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

# Virtual Network
resource "azurerm_virtual_network" "main" {
  name                = var.vnet_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  address_space       = var.address_space
  dns_servers         = var.dns_servers

  tags = var.tags
}

# Subnets
resource "azurerm_subnet" "subnet" {
  count                = length(var.subnet_names)
  name                 = var.subnet_names[count.index]
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = [var.subnet_prefixes[count.index]]
}

# Network Security Group
resource "azurerm_network_security_group" "main" {
  name                = "${var.vnet_name}-nsg"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = var.tags
}

# NSG Rules
resource "azurerm_network_security_rule" "allow_ssh" {
  name                        = "AllowSSH"
  priority                    = 100
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "22"
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.main.name
  network_security_group_name = azurerm_network_security_group.main.name
}

resource "azurerm_network_security_rule" "allow_http" {
  name                        = "AllowHTTP"
  priority                    = 110
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "80"
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.main.name
  network_security_group_name = azurerm_network_security_group.main.name
}

resource "azurerm_network_security_rule" "allow_https" {
  name                        = "AllowHTTPS"
  priority                    = 120
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "443"
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.main.name
  network_security_group_name = azurerm_network_security_group.main.name
}

# NSG Association
resource "azurerm_subnet_network_security_group_association" "main" {
  count                     = length(var.subnet_names)
  subnet_id                 = azurerm_subnet.subnet[count.index].id
  network_security_group_id = azurerm_network_security_group.main.id
}

# Route Table
resource "azurerm_route_table" "main" {
  name                = "${var.vnet_name}-rt"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = var.tags
}

# Route Table Association
resource "azurerm_subnet_route_table_association" "main" {
  count          = length(var.subnet_names)
  subnet_id      = azurerm_subnet.subnet[count.index].id
  route_table_id = azurerm_route_table.main.id
}

# Public IP
resource "azurerm_public_ip" "main" {
  name                = "${var.vnet_name}-pip"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = var.tags
}

# NAT Gateway
resource "azurerm_nat_gateway" "main" {
  name                = "${var.vnet_name}-nat"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku_name            = "Standard"

  tags = var.tags
}

# NAT Gateway Public IP Association
resource "azurerm_nat_gateway_public_ip_association" "main" {
  nat_gateway_id       = azurerm_nat_gateway.main.id
  public_ip_address_id = azurerm_public_ip.main.id
}

# NAT Gateway Subnet Association
resource "azurerm_subnet_nat_gateway_association" "main" {
  count          = length(var.subnet_names)
  subnet_id      = azurerm_subnet.subnet[count.index].id
  nat_gateway_id = azurerm_nat_gateway.main.id
}

# Outputs
output "resource_group_name" {
  description = "The name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "resource_group_id" {
  description = "The ID of the resource group"
  value       = azurerm_resource_group.main.id
}

output "vnet_name" {
  description = "The name of the virtual network"
  value       = azurerm_virtual_network.main.name
}

output "vnet_id" {
  description = "The ID of the virtual network"
  value       = azurerm_virtual_network.main.id
}

output "vnet_address_space" {
  description = "The address space of the virtual network"
  value       = azurerm_virtual_network.main.address_space
}

output "subnet_ids" {
  description = "The IDs of the subnets"
  value       = azurerm_subnet.subnet[*].id
}

output "subnet_names" {
  description = "The names of the subnets"
  value       = azurerm_subnet.subnet[*].name
}

output "nsg_id" {
  description = "The ID of the network security group"
  value       = azurerm_network_security_group.main.id
}

output "route_table_id" {
  description = "The ID of the route table"
  value       = azurerm_route_table.main.id
}

output "nat_gateway_id" {
  description = "The ID of the NAT gateway"
  value       = azurerm_nat_gateway.main.id
}

locals {
  subnet_map = zipmap(var.subnet_names, azurerm_subnet.subnet[*].id)

  resource_tags = merge(
    var.tags,
    {
      Resource  = var.vnet_name
      Location  = var.location
      CreatedBy = "Terraform"
    }
  )
}

data "azurerm_subscription" "current" {}
