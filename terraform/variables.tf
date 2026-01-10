variable "resource_group_location" {
  description = "The location where the resource group will be created."
  type        = string
  default     = "East US"
}

variable "container_image_tag" {
  description = "The tag of the container image to deploy."
  type        = string
  default     = "latest"
}

variable "hostname" {
  description = "The IP address of the Asterisk server."
  type        = string
  sensitive   = true
}

variable "username" {
  description = "The admin username for the Asterisk container registry."
  type        = string
  sensitive   = true
}

variable "password" {
  description = "The admin password for the Asterisk container registry."
  type        = string
  sensitive   = true
}

variable "CW_Authorization" {
  description = "ConnectWise API Authorization header value."
  type        = string
  sensitive   = true
}

variable "CW_ClientID" {
  description = "ConnectWise API Client ID."
  type        = string
  sensitive   = true
}

variable "TENANT_ID" {
  description = "Azure Tenant ID for ACR authentication."
  type        = string
  sensitive   = true
  default     = ""
}

variable "CLIENT_ID" {
  description = "Azure Client ID for ACR authentication."
  type        = string
  sensitive   = true
  default     = ""
}

variable "CLIENT_SECRET" {
  description = "Azure Client Secret for ACR authentication."
  type        = string
  sensitive   = true
  default     = ""
}

variable "TEAM_ID" {
  description = "Azure Subscription ID for ACR authentication."
  type        = string
  sensitive   = true
  default     = ""
}

variable "CHANNEL_ID" {
  description = "Microsoft Teams Channel ID for notifications."
  type        = string
  sensitive   = true
  default     = ""

}

variable "CHAT_ID" {
  description = "Microsoft Teams Chat ID for notifications."
  type        = string
  sensitive   = true
  default     = ""
}

variable "SENDER_USER_ID" {
  description = "Email address of the sender user for Email sending notifications."
  type        = string
  sensitive   = true
  default     = ""
}

variable "SENDER_DISPLAY_NAME" {
  description = "Display name of the sender for Email sending notifications."
  type        = string
  sensitive   = true
  default     = ""
}

variable "SMTP_SERVER" {
  description = "SMTP server address for Email sending notifications."
  type        = string
  sensitive   = true
  default     = ""
}

variable "SMTP_PORT" {
  description = "SMTP server port for Email sending notifications."
  type        = number
  sensitive   = true
  default     = 587
}

variable "SMTP_SENDER_EMAIL" {
  description = "Sender email address for Email sending notifications"
  type        = string
  sensitive   = true
  default     = ""
}

variable "SMTP_USER" {
  description = "Username for SMTP authentication for Email sending notifications."
  type        = string
  sensitive   = true
  default     = ""
}

variable "SMTP_AUTH_PASSWORD" {
  description = "Password for SMTP authentication for Email sending notifications."
  type        = string
  sensitive   = true
  default     = ""
}

variable "recipient_emails" {
  description = "Recipient email address for Email sending notifications."
  type        = string
  sensitive   = true
  default     = ""
}

variable "QR_QUEUE" {
  description = "Queue name for QR code generation."
  type        = string
  default     = "15"
}

variable "QR_START_HOUR" {
  description = "Start hour for QR code generation."
  type        = string
  default     = "6"
}

variable "QR_END_HOUR" {
  description = "End hour for QR code generation."
  type        = string
  default     = "7"
}

variable "techs" {
  description = "List of technician names."
  type        = string
}

variable "TEAMS_WEBHOOK_URL" {
  description = "Microsoft Teams Webhook URL for notifications."
  type        = string
  sensitive   = true
}

variable "TEAMS_WEBHOOK2_URL" {
  description = "Secondary Microsoft Teams Webhook URL for notifications."
  type        = string
  sensitive   = true
}

variable "TEAMS_WEBHOOK3_URL" {
  description = "Tertiary Microsoft Teams Webhook URL for notifications."
  type        = string
  sensitive   = true
}

variable "TEAMS_WEBHOOK4_URL" {
  description = "Quaternary Microsoft Teams Webhook URL for notifications."
  type        = string
  sensitive   = true
}

variable "SSL_PFX_BASE64" {
  description = "Base64 encoded SSL PFX certificate."
  type        = string
  sensitive   = true
}

variable "SSL_PASSWORD" {
  description = "Password for the SSL PFX certificate."
  type        = string
  sensitive   = true
}

variable "MICROSOFT_CLIENT_ID" {
  description = "Microsoft client ID"
  type = string
  sensitive = true
}

variable "AZURE_TENANT_ID" {
  description = "Azure tenant ID"
  type = string
  sensitive = true
}

variable "MICROSOFT_CLIENT_SECRET" {
  description = "Microsoft client secret"
  type = string
  sensitive = true
}

variable "ONPREM_GATEWAY_IP" {
  description = "onprem ip for vpn gateway"
  type = string
  sensitive = true
}

variable "ONPREM_ADDRESS_SPACE" {
  description = "onprem address space for vpn gateway"
  type = string
  sensitive = true
}

variable "VPN_SHARED_KEY" {
  description = "vpn shared key for vpn gateway"
  type = string
  sensitive = true
}