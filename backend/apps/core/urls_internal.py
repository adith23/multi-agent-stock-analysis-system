"""Routes that are reachable only by trusted GCP service identities."""

from django.urls import path

from apps.core.views.internal import SchedulerDispatchView, WorkerExecuteView

app_name = "internal"

urlpatterns = [
    path("worker/execute/", WorkerExecuteView.as_view(), name="worker-execute"),
    path(
        "scheduler/<str:schedule_name>/",
        SchedulerDispatchView.as_view(),
        name="scheduler-dispatch",
    ),
]
