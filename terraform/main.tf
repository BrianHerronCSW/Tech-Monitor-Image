resource "azurerm_resource_group" "CSW_LiveStatusMonitor_RG" {
  name     = "CSW-LiveStatusMonitor-RG"
  location = "East US"
}

resource "azurerm_container_registry" "CSW_LiveStatusMonitor_ACR" {
  name                = "cswlivestatusmonitoracr"
  resource_group_name = azurerm_resource_group.CSW_LiveStatusMonitor_RG.name
  location            = azurerm_resource_group.CSW_LiveStatusMonitor_RG.location
  sku                 = "Basic"
  admin_enabled       = true
}

resource "azurerm_log_analytics_workspace" "CSW_LiveStatusMonitor_LAW" {
  name                = "CSW-LiveStatusMonitor-LAW"
  location            = azurerm_resource_group.CSW_LiveStatusMonitor_RG.location
  resource_group_name = azurerm_resource_group.CSW_LiveStatusMonitor_RG.name
  sku                 = "PerGB2018"
  retention_in_days  = 30
}


resource "azurerm_container_app_environment" "CSW_LiveStatusMonitor_Env" {
  name                = "CSW-LiveStatusMonitor-Env"
  resource_group_name = azurerm_resource_group.CSW_LiveStatusMonitor_RG.name
  location            = azurerm_resource_group.CSW_LiveStatusMonitor_RG.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.CSW_LiveStatusMonitor_LAW.id
  infrastructure_subnet_id = azurerm_subnet.CSW_LiveStatusMonitor_Subnet.id

  workload_profile {
    name       = "d4"
    workload_profile_type = "D4"
    minimum_count = 1
    maximum_count = 5
  }

  lifecycle {
    ignore_changes = [workload_profile]
  }

  timeouts {
    create = "180m"
  }
}

resource "azurerm_virtual_network" "CSW_LiveStatusMonitor_VNet" {
  name                = "CSW-LiveStatusMonitor-VNet"
  address_space       = ["10.10.0.0/16"]
  location            = azurerm_resource_group.CSW_LiveStatusMonitor_RG.location
  resource_group_name = azurerm_resource_group.CSW_LiveStatusMonitor_RG.name
}

resource "azurerm_subnet" "CSW_LiveStatusMonitor_Subnet" {
  name                 = "CSW-LiveStatusMonitor-Subnet"
  resource_group_name  = azurerm_resource_group.CSW_LiveStatusMonitor_RG.name
  virtual_network_name = azurerm_virtual_network.CSW_LiveStatusMonitor_VNet.name
  address_prefixes     = ["10.10.1.0/24"]
  delegation {
    name = "delegation"
    service_delegation {
      name = "Microsoft.App/environments"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
        "Microsoft.Network/virtualNetworks/subnets/prepareNetworkPolicies/action",
      ]
    }
  }
}

resource "azurerm_subnet" "CSW_GatewaySubnet" {
  name                 = "GatewaySubnet"
  resource_group_name  = azurerm_resource_group.CSW_LiveStatusMonitor_RG.name
  virtual_network_name = azurerm_virtual_network.CSW_LiveStatusMonitor_VNet.name
  address_prefixes     = ["10.10.2.0/24"]
}

resource "azurerm_local_network_gateway" "CSW_OnPrem_LNG" {
  name                = "CSW-OnPrem-LNG"
  resource_group_name = azurerm_resource_group.CSW_LiveStatusMonitor_RG.name
  location            = azurerm_resource_group.CSW_LiveStatusMonitor_RG.location
  gateway_address     = var.ONPREM_GATEWAY_IP
  address_space       = [var.ONPREM_ADDRESS_SPACE]
}

resource "azurerm_public_ip" "CSW_VPNGW_PublicIP" {
  name                = "CSW-VPNGW-PublicIP"
  location            = azurerm_resource_group.CSW_LiveStatusMonitor_RG.location
  resource_group_name = azurerm_resource_group.CSW_LiveStatusMonitor_RG.name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_virtual_network_gateway" "CSW_VPNGW" {
  name                = "CSW-VPNGW"
  location            = azurerm_resource_group.CSW_LiveStatusMonitor_RG.location
  resource_group_name = azurerm_resource_group.CSW_LiveStatusMonitor_RG.name
  type                = "Vpn"
  vpn_type            = "RouteBased"
  active_active       = false
  enable_bgp         = false
  sku                 = "VpnGw1"
  ip_configuration {
    name                          = "vpngw-ipconfig"
    public_ip_address_id          = azurerm_public_ip.CSW_VPNGW_PublicIP.id
    subnet_id                     = azurerm_subnet.CSW_GatewaySubnet.id
  }

  timeouts {
    create = "180m"
  }
}

resource "azurerm_virtual_network_gateway_connection" "CSW_VPN_Connection" {
  name                           = "CSW-VPN-Connection"
  location                       = azurerm_resource_group.CSW_LiveStatusMonitor_RG.location
  resource_group_name            = azurerm_resource_group.CSW_LiveStatusMonitor_RG.name
  virtual_network_gateway_id     = azurerm_virtual_network_gateway.CSW_VPNGW.id
  local_network_gateway_id       = azurerm_local_network_gateway.CSW_OnPrem_LNG.id
  type                = "IPsec"
  routing_weight                 = 1
  shared_key                     = var.VPN_SHARED_KEY
}

resource "azurerm_container_app" "CSW_LiveStatusMonitor_App" {
  name                = "csw-livestatusmonitor-app"
  container_app_environment_id = azurerm_container_app_environment.CSW_LiveStatusMonitor_Env.id
  resource_group_name = azurerm_resource_group.CSW_LiveStatusMonitor_RG.name
  revision_mode = "Single"

  workload_profile_name = "d4"

  timeouts {
    create = "180m"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.CSW_LiveStatusMonitor_ACR.admin_password
  }

  secret {
    name  = "hostname"
    value = var.hostname
  }

  secret {
    name  = "username"
    value = var.username
  }

  secret {
    name  = "password"
    value = var.password
  }

  secret {
    name  = "cw-authorization"
    value = var.CW_Authorization
  }

  secret {
    name  = "cw-client-id"
    value = var.CW_ClientID
  }

  secret {
    name  = "client-id"
    value = var.CLIENT_ID
  }

  secret {
    name  = "client-secret"
    value = var.CLIENT_SECRET
  }

  secret {
    name  = "team-id"
    value = var.TEAM_ID
  }

  secret  {
    name  = "channel-id"
    value = var.CHANNEL_ID
  }

  secret {
    name  = "chat-id"
    value = var.CHAT_ID
  }

  secret {
    name  = "tenant-id"
    value = var.TENANT_ID
  }

  secret {
    name  = "sender-user-id"
    value = var.SENDER_USER_ID
  }

  secret {
    name  = "sender-display-name"
    value = var.SENDER_DISPLAY_NAME
  }

  secret {
    name  = "smtp-server"
    value = var.SMTP_SERVER
  }

  secret {
    name  = "smtp-port"
    value = var.SMTP_PORT
  }

  secret {
    name  = "smtp-user"
    value = var.SMTP_USER
  }

  secret {
    name  = "smtp-auth-password"
    value = var.SMTP_AUTH_PASSWORD
  }

  secret {
    name  = "recipient-emails"
    value = var.recipient_emails
  }

  secret {
    name  = "qr-queue"
    value = var.QR_QUEUE
  }

  secret {
    name  = "qr-start-hour"
    value = var.QR_START_HOUR
  }

  secret {
    name  = "qr-end-hour"
    value = var.QR_END_HOUR
  }

  secret {
    name  = "techs"
    value = var.techs
  }

  secret {
    name  = "teams-webhook-url"
    value = var.TEAMS_WEBHOOK_URL
  }

  secret {
    name  = "teams-webhook2-url"
    value = var.TEAMS_WEBHOOK2_URL
  }

  secret {
    name = "teams-webhook3-url"
    value = var.TEAMS_WEBHOOK3_URL
  }

  secret {
    name = "teams-webhook4-url"
    value = var.TEAMS_WEBHOOK4_URL
  }

  secret {
    name  = "ssl-pfx-base64"
    value = var.SSL_PFX_BASE64
  }

  secret {
    name  = "ssl-password"
    value = var.SSL_PASSWORD
  }

  secret {
    name  = "microsoft-auth-secret"
    value = var.MICROSOFT_CLIENT_SECRET
  }

  secret {
    name  = "microsoft-auth-id"
    value = var.MICROSOFT_CLIENT_ID
  }

  secret {
    name  = "azure-tenant-id"
    value = var.AZURE_TENANT_ID
  }

  registry {
    server   = azurerm_container_registry.CSW_LiveStatusMonitor_ACR.login_server
    username = azurerm_container_registry.CSW_LiveStatusMonitor_ACR.admin_username
    password_secret_name = "acr-password"
  }

  template{
    container {
      name   = "tech-status-monitor"
      image  = "${azurerm_container_registry.CSW_LiveStatusMonitor_ACR.login_server}/tech-status-monitor:${var.container_image_tag}"
      cpu    = "0.25"
      memory = "0.5Gi"
      env {
        name  = "hostname"
        secret_name = "hostname"
      }
      env {
        name  = "username"
        secret_name = "username"
      }
      env {
        name  = "password"
        secret_name = "password"
      }
      env {
        name  = "cw_authorization"
        secret_name = "cw-authorization"
      }
      env {
        name  = "cw-client-id"
        secret_name = "cw-client-id"
      }
      env {
        name  = "client-id"
        secret_name = "client-id"
      }
      env {
        name  = "client-secret"
        secret_name = "client-secret"
      }
      env {
        name  = "tenant-id"
        secret_name = "tenant-id"
      }
      env {
        name  = "team-id"
        secret_name = "team-id"
      }
      env {
        name  = "channel-id"
        secret_name = "channel-id"
      }
      env {
        name  = "chat-id"
        secret_name = "chat-id"
      }
      env {
        name  = "sender-user-id"
        secret_name = "sender-user-id"
      }
      env {
        name  = "sender-display-name"
        secret_name = "sender-display-name"
      }
      env {
        name  = "smtp-server"
        secret_name = "smtp-server"
      }
      env {
        name  = "smtp-port"
        secret_name = "smtp-port"
      }
      env {
        name  = "smtp-user"
        secret_name = "smtp-user"
      }
      env {
        name  = "smtp-auth-password"
        secret_name = "smtp-auth-password"
      }
      env {
        name  = "recipient-emails"
        secret_name = "recipient-emails"
      }
      env {
        name  = "qr-queue"
        secret_name = "qr-queue"
      }
      env {
        name  = "qr-start-hour"
        secret_name = "qr-start-hour"
      }
      env {
        name  = "qr-end-hour"
        secret_name = "qr-end-hour"
      }
      env {
        name  = "techs"
        secret_name = "techs"
      }
      env {
        name  = "teams-webhook-url"
        secret_name = "teams-webhook-url"
      }
      env {
        name  = "teams-webhook2-url"
        secret_name = "teams-webhook2-url"
      }
      env {
        name  = "teams-webhook3-url"
        secret_name = "teams-webhook3-url"
      }
      env {
        name  = "teams-webhook4-url"
        secret_name = "teams-webhook4-url"
      }
      env {
        name  = "ssl-pfx-base64"
        secret_name = "ssl-pfx-base64"
      }
      env {
        name  = "ssl-password"
        secret_name = "ssl-password"
      }
    }
    
  }
  ingress {
    external_enabled = true
    target_port      = 5000
    transport        = "auto"
    traffic_weight {
      percentage = 100
      latest_revision = true
    }
  }
}


resource "azurerm_container_app_environment_certificate" "csw_certificate" {
  name                = "csw-cert"
  container_app_environment_id = azurerm_container_app_environment.CSW_LiveStatusMonitor_Env.id
  certificate_blob_base64 = var.SSL_PFX_BASE64
  certificate_password   = var.SSL_PASSWORD
}

resource "azurerm_container_app_custom_domain" "csw_domain" {
  name                = "live.capstoneworks.com"
  container_app_id   = azurerm_container_app.CSW_LiveStatusMonitor_App.id
  certificate_binding_type = "SniEnabled"
  container_app_environment_certificate_id = azurerm_container_app_environment_certificate.csw_certificate.id

  depends_on = [ 
    azurerm_container_app.CSW_LiveStatusMonitor_App 
  ]
}

