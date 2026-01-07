resource "azurerm_resource_group" "CSW_LiveStatusMonitor_RG" {
  name     = "CSW-LiveStatusMonitor-RG"
  location = var.resource_group_location
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
}

resource "azurerm_container_app" "CSW_LiveStatusMonitor_App" {
  name                = "CSW-LiveStatusMonitor-App"
  container_app_environment_id = azurerm_container_app_environment.CSW_LiveStatusMonitor_Env.id
  resource_group_name = azurerm_resource_group.CSW_LiveStatusMonitor_RG.name
  location            = azurerm_resource_group.CSW_LiveStatusMonitor_RG.location
  revision_mode = "Single"

  secret {
    name  = "ACR-Password"
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
    name  = "Authorization"
    value = var.Authorization
  }

  secret {
    name  = "CW_ClientID"
    value = var.CW_ClientID
  }

  secret {
    name  = "CLIENT_ID"
    value = var.CLIENT_ID
  }

  secret {
    name  = "CLIENT_SECRET"
    value = var.CLIENT_SECRET
  }

  secret {
    name  = "TEAM_ID"
    value = var.TEAM_ID
  }

  secret  {
    name  = "CHANNEL_ID"
    value = var.CHANNEL_ID
  }

  secret {
    name  = "CHAT_ID"
    value = var.CHAT_ID
  }

  secret {
    name  = "TENANT_ID"
    value = var.TENANT_ID
  }

  secret {
    name  = "SENDER_USER_ID"
    value = var.SENDER_USER_ID
  }

  secret {
    name  = "SENDER_DISPLAY_NAME"
    value = var.SENDER_DISPLAY_NAME
  }

  secret {
    name  = "SMTP_SERVER"
    value = var.SMTP_SERVER
  }

  secret {
    name  = "SMTP_PORT"
    value = var.SMTP_PORT
  }

  secret {
    name  = "SMTP_USER"
    value = var.SMTP_USER
  }

  secret {
    name  = "SMTP_AUTH_PASSWORD"
    value = var.SMTP_AUTH_PASSWORD
  }

  secret {
    name  = "RECIPIENT_EMAILS"
    value = var.recipient_emails
  }

  secret {
    name  = "QR_QUEUE"
    value = var.QR_QUEUE
  }

  secret {
    name  = "QR_START_HOUR"
    value = var.QR_START_HOUR
  }

  secret {
    name  = "QR_END_HOUR"
    value = var.QR_END_HOUR
  }

  secret {
    name  = "techs"
    value = var.techs
  }

  secret {
    name  = "TEAMS_WEBHOOK_URL"
    value = var.TEAMS_WEBHOOK_URL
  }

  secret {
    name  = "TEAMS_WEBHOOK2_URL"
    value = var.TEAMS_WEBHOOK2_URL
  }

  secret {
    name = "TEAMS_WEBHOOK3_URL"
    value = var.TEAMS_WEBHOOK3_URL
  }

  secret {
    name = "TEAMS_WEBHOOK4_URL"
    value = var.TEAMS_WEBHOOK4_URL
  }

  registry {
    server   = azurerm_container_registry.CSW_LiveStatusMonitor_ACR.login_server
    username = azurerm_container_registry.CSW_LiveStatusMonitor_ACR.admin_username
    password_secret_name = "ACR-Password"
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
        name  = "Authorization"
        secret_name = "Authorization"
    }
      env {
        name  = "CW_ClientID"
        secret_name = "CW_ClientID"
    }
      env {
        name  = "CLIENT_ID"
        secret_name = "CLIENT_ID"
    }
      env {
        name  = "CLIENT_SECRET"
        secret_name = "CLIENT_SECRET"
    }
      env {
        name  = "TENANT_ID"
        secret_name = "TENANT_ID"
    }
      env {
        name  = "TEAM_ID"
        secret_name = "TEAM_ID"
    }
      env {
        name  = "CHANNEL_ID"
        secret_name = "CHANNEL_ID"
    }
      env {
        name  = "CHAT_ID"
        secret_name = "CHAT_ID"
    }
      env {
        name  = "SENDER_USER_ID"
        secret_name = "SENDER_USER_ID"
    }
      env {
        name  = "SENDER_DISPLAY_NAME"
        secret_name = "SENDER_DISPLAY_NAME"
    }
      env {
        name  = "SMTP_SERVER"
        secret_name = "SMTP_SERVER"
    }
      env {
        name  = "SMTP_PORT"
        secret_name = "SMTP_PORT"
    }
      env {
        name  = "SMTP_USER"
        secret_name = "SMTP_USER"
    }
      env {
        name  = "SMTP_AUTH_PASSWORD"
        secret_name = "SMTP_AUTH_PASSWORD"
    }
      env {
        name  = "RECIPIENT_EMAILS"
        secret_name = "RECIPIENT_EMAILS"
    }
      env {
        name  = "QR_QUEUE"
        secret_name = "QR_QUEUE"
    }
      env {
        name  = "QR_START_HOUR"
        secret_name = "QR_START_HOUR"
    }
      env {
        name  = "QR_END_HOUR"
        secret_name = "QR_END_HOUR"
    }
      env {
        name  = "techs"
        secret_name = "techs"
    }
      env {
        name  = "TEAMS_WEBHOOK_URL"
        secret_name = "TEAMS_WEBHOOK_URL"
    }
      env {
        name  = "TEAMS_WEBHOOK2_URL"
        secret_name = "TEAMS_WEBHOOK2_URL"
    }
      env {
        name  = "TEAMS_WEBHOOK3_URL"
        secret_name = "TEAMS_WEBHOOK3_URL"
    }
      env {
        name  = "TEAMS_WEBHOOK4_URL"
        secret_name = "TEAMS_WEBHOOK4_URL"
    }
    }
  }
  ingress {
    external_enabled = true
    target_port      = 5000
    transport        = "Auto"
    traffic_weight {
      percentage = 100
      latest_revision = true
    }
  }
}


