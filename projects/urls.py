from django.urls import path

from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='list'),
    path('novo/', views.ProjectCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.ProjectUpdateView.as_view(), name='update'),
    path('<int:pk>/encerrar/', views.ProjectCloseView.as_view(), name='close'),
    path('<int:project_id>/diario/', views.DailyLogCreateView.as_view(), name='daily_log_create'),
    path('<int:project_id>/diario/<int:pk>/editar/', views.DailyLogUpdateView.as_view(), name='daily_log_update'),
    path('<int:project_id>/tarefa/', views.ProjectTaskCreateView.as_view(), name='task_create'),
    path('<int:project_id>/tarefa/<int:pk>/editar/', views.ProjectTaskUpdateView.as_view(), name='task_update'),
    path('<int:project_id>/medicao/', views.PhysicalMeasurementCreateView.as_view(), name='measurement_create'),
    path('<int:project_id>/medicao/<int:pk>/editar/', views.PhysicalMeasurementUpdateView.as_view(), name='measurement_update'),
]
