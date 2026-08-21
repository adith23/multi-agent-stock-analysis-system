from django.contrib import admin

from .models import AnalysisRun, PipelineStepResult

admin.site.register((AnalysisRun, PipelineStepResult))
