output "job_ids" { value = { for key, job in google_cloud_scheduler_job.job : key => job.id } }
