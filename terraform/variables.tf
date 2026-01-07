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
}

variable "TEAM_ID" {
  description = "Azure Subscription ID for ACR authentication."
  type        = string
  sensitive   = true
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
  description = "Sender email address for Email sending notifications."
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
}

variable "QR_START_HOUR" {
  description = "Start hour for QR code generation."
  type        = string
}

variable "QR_END_HOUR" {
  description = "End hour for QR code generation."
  type        = string
}

variable "techs" {
  description = "List of technician names."
  type        = string
  default     = "{\"100\": \"Front Conference\", \"101\": \"Conference Room Mobile\", \"102\": \"Chuck Adams\", \"103\": \"Easton\", \"104\": \"Cindy Adams\", \"105\": \"Dispatch Backup\", \"106\": \"Logan\", \"107\": \"Chuck (Line 2)\", \"108\": \"Clarissa\", \"109\": \"Alex Adams\", \"110\": \"Support Desk\", \"111\": \"open\", \"112\": \"Indusoft Support\", \"113\": \"Open\", \"114\": \"Capstone Support\", \"115\": \"Tim Home\", \"116\": \"Open\", \"117\": \"Vendors\", \"118\": \"Accounting\", \"120\": \"Open\", \"121\": \"Open\", \"122\": \"Daniel\", \"124\": \"Open Ext\", \"125\": \"Brian\", \"126\": \"Kalani\", \"127\": \"Derrick\", \"129\": \"John\", \"130\": \"Capstone Support\", \"140\": \"Test Extension\", \"150\": \"Cindy - Home\", \"151\": \"John Home\", \"152\": \"Brian - Home\", \"153\": \"IE2\", \"154\": \"C-Adams - Home\", \"155\": \"Sahil Home\", \"156\": \"Alex - Home\", \"158\": \"Clarissa - Home\", \"159\": \"Capstone Support\", \"160\": \"Kalani - Home\", \"161\": \"Logan Home\", \"162\": \"Daniel Home\", \"163\": \"Spare desk\", \"190\": \"ATA Test Extension\", \"198\": \"FH Support\", \"199\": \"Support\", \"200\": \"Conference\", \"202\": \"Kitchen\", \"203\": \"203\", \"210\": \"Mobile 1\", \"211\": \"Mobile 2\", \"212\": \"CTA Mobile\", \"213\": \"Mobile 3\", \"220\": \"Adams Home\", \"232\": \"Test Cisco SPA\", \"302\": \"302\", \"350\": \"QR Hotdesk\", \"400\": \"LOC Help Desk\", \"501\": \"CellPhone\", \"599\": \"Emergency Support\", \"700\": \"Main Conference Room\", \"701\": \"Small Conference Room\", \"1001\": \"OIB 4 Duneside ext1\", \"1002\": \"OIB 4 Duneside ext2\"}"
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