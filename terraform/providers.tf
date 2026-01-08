terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~>3.0"
    }
    azapi = {
      source  = "azure/azapi"
      version = "~>1.0"
    }
  }
  backend "azurerm" {
    resource_group_name = "CSW-TFSTATE-RG"
    storage_account_name = "cswtfstatesa"
    container_name       = "tfstate"
    key                  = "terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
}

resource "azapi_resource" "container_app_auth" {
  type      = "Microsoft.App/containerApps/authConfigs@2024-03-01"
  name      = "current"
  parent_id = azurerm_container_app.CSW_LiveStatusMonitor_App.id

  body = jsonencode({
    properties = {
      platform = {
        enabled = true # Activates the authentication layer
      }
      globalValidation = {
        # Forces the login screen for anyone visiting live.capstoneworks.com
        unauthenticatedClientAction = "RedirectToLoginPage"
        redirectToProvider          = "azureactivedirectory"
      }
      identityProviders = {
        azureActiveDirectory = {
          enabled = true
          registration = {
            clientId                = var.MICROSOFT_CLIENT_ID
            clientSecretSettingName = "microsoft-auth-secret" # Refers to the secret name in your Container App
            openIdIssuer           = "https://sts.windows.net/${var.AZURE_TENANT_ID}/v2.0"
          }
          validation = {
            allowedAudiences = ["api://${var.MICROSOFT_CLIENT_ID}"]
          }
        }
      }
    }
  })
}