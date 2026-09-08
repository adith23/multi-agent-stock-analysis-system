output "service_account_emails" {
  value = {
    for key, service_account in google_service_account.service_account :
    key => service_account.email
  }
}
