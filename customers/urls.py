from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.CustomerListView.as_view(), name='list'),
    path('novo/', views.CustomerCreateView.as_view(), name='create'),
    path('<int:pk>/', views.CustomerDetailView.as_view(), name='detail'),
    path('<int:pk>/relatorio/pdf/', views.CustomerReportPdfView.as_view(), name='report_pdf'),
    path('<int:pk>/editar/', views.CustomerUpdateView.as_view(), name='update'),
    path('<int:pk>/excluir/', views.CustomerDeleteView.as_view(), name='delete'),
    path('<int:customer_id>/interacao/', views.CustomerInteractionCreateView.as_view(), name='interaction_create'),
    path('<int:customer_id>/interacao/<int:pk>/excluir/', views.CustomerInteractionDeleteView.as_view(), name='interaction_delete'),
    path('<int:customer_id>/documento/', views.CustomerDocumentCreateView.as_view(), name='document_create'),
    path('<int:customer_id>/documento/<int:pk>/excluir/', views.CustomerDocumentDeleteView.as_view(), name='document_delete'),
    path('<int:customer_id>/foto/', views.CustomerPhotoCreateView.as_view(), name='photo_create'),
    path('<int:customer_id>/foto/<int:pk>/excluir/', views.CustomerPhotoDeleteView.as_view(), name='photo_delete'),
]
