output "queue_names" { value = { for key, queue in google_cloud_tasks_queue.queue : key => queue.name } }
