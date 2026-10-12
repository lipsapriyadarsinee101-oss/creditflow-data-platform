terraform {
  required_version = ">= 1.6, < 2.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}
provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}
variable "subscription_id" {
  type = string
}
variable "prefix" {
  type    = string
  default = "creditflowdemo"
  validation {
    condition     = can(regex("^[a-z][a-z0-9]{5,17}$", var.prefix))
    error_message = "Use 6-18 lowercase alphanumeric characters."
  }
}
variable "location" {
  type    = string
  default = "germanywestcentral"
}
resource "azurerm_resource_group" "platform" {
  name     = "${var.prefix}-rg"
  location = var.location
  tags     = { purpose = "portfolio", environment = "demo" }
}
resource "azurerm_storage_account" "lake" {
  name                            = "${var.prefix}lake"
  resource_group_name             = azurerm_resource_group.platform.name
  location                        = var.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  is_hns_enabled                  = true
  min_tls_version                 = "TLS1_2"
  shared_access_key_enabled       = false
  allow_nested_items_to_be_public  = false
  public_network_access_enabled   = false
}
resource "azurerm_databricks_workspace" "workspace" {
  name                        = "${var.prefix}-dbw"
  resource_group_name         = azurerm_resource_group.platform.name
  location                    = var.location
  sku                         = "premium"
  managed_resource_group_name = "${var.prefix}-managed-rg"
}
resource "azurerm_data_factory" "factory" {
  name                = "${var.prefix}-adf"
  resource_group_name = azurerm_resource_group.platform.name
  location            = var.location
  identity { type = "SystemAssigned" }
}
output "workspace_url" {
  value = azurerm_databricks_workspace.workspace.workspace_url
}
output "storage_account" {
  value = azurerm_storage_account.lake.name
}
