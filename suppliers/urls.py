from django.urls import path

from . import views

app_name = 'suppliers'

urlpatterns = [
    path('', views.SupplierListView.as_view(), name='list'),
    path('novo/', views.SupplierCreateView.as_view(), name='create'),
    path('<int:pk>/', views.SupplierDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.SupplierUpdateView.as_view(), name='update'),
    path('<int:pk>/excluir/', views.SupplierDeleteView.as_view(), name='delete'),
    path('<int:pk>/inativar/', views.SupplierInactivateView.as_view(), name='inactivate'),
]
