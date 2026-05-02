from django.urls import path

from . import views

app_name = 'client_portal'

urlpatterns = [
    path('', views.ClientPortalHomeView.as_view(), name='home'),
    path('clientes/<int:customer_id>/', views.CustomerPortalDetailView.as_view(), name='customer_detail'),
    path('clientes/<int:customer_id>/obras/<int:pk>/', views.ProjectPortalDetailView.as_view(), name='project_detail'),
]
