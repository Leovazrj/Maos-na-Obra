from django.contrib import admin

from .models import DailyLog, PhysicalMeasurement, Project, ProjectTask


class DailyLogInline(admin.TabularInline):
    model = DailyLog
    extra = 0


class ProjectTaskInline(admin.TabularInline):
    model = ProjectTask
    extra = 0


class PhysicalMeasurementInline(admin.TabularInline):
    model = PhysicalMeasurement
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'customer', 'responsible', 'status', 'expected_start_date', 'expected_end_date', 'expected_value')
    list_filter = ('status', 'expected_start_date', 'expected_end_date')
    search_fields = ('name', 'customer__name', 'address')
    inlines = [ProjectTaskInline, DailyLogInline, PhysicalMeasurementInline]


@admin.register(DailyLog)
class DailyLogAdmin(admin.ModelAdmin):
    list_display = ('project', 'log_date', 'weather', 'created_at')
    list_filter = ('log_date', 'weather')
    search_fields = ('project__name', 'services_performed', 'occurrences')


@admin.register(ProjectTask)
class ProjectTaskAdmin(admin.ModelAdmin):
    list_display = ('project', 'name', 'planned_start_date', 'planned_end_date', 'planned_percentage', 'planned_cost')
    list_filter = ('planned_start_date', 'planned_end_date')
    search_fields = ('project__name', 'name')


@admin.register(PhysicalMeasurement)
class PhysicalMeasurementAdmin(admin.ModelAdmin):
    list_display = ('project', 'task', 'measurement_date', 'measured_percentage', 'measured_value', 'visible_in_portal')
    list_filter = ('measurement_date', 'visible_in_portal')
    search_fields = ('project__name', 'task__name')
