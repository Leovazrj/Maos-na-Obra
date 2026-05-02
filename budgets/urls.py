from django.urls import path

from . import views

app_name = 'budgets'

urlpatterns = [
    path('insumos/', views.InputItemListView.as_view(), name='input_item_list'),
    path('insumos/novo/', views.InputItemCreateView.as_view(), name='input_item_create'),
    path('insumos/<int:pk>/editar/', views.InputItemUpdateView.as_view(), name='input_item_update'),
    path('insumos/<int:pk>/excluir/', views.InputItemDeleteView.as_view(), name='input_item_delete'),
    path('', views.BudgetListView.as_view(), name='list'),
    path('novo/', views.BudgetCreateView.as_view(), name='create'),
    path('<int:pk>/', views.BudgetDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.BudgetUpdateView.as_view(), name='update'),
    path('<int:pk>/excluir/', views.BudgetDeleteView.as_view(), name='delete'),
    path('<int:budget_id>/item/', views.BudgetItemCreateView.as_view(), name='item_create'),
    path('<int:budget_id>/item/<int:pk>/editar/', views.BudgetItemUpdateView.as_view(), name='item_update'),
    path('<int:budget_id>/item/<int:pk>/excluir/', views.BudgetItemDeleteView.as_view(), name='item_delete'),
    path('<int:budget_id>/item/<int:item_id>/composicao/', views.BudgetCompositionItemCreateView.as_view(), name='composition_create'),
    path('<int:budget_id>/item/<int:item_id>/composicao/<int:pk>/remover/', views.BudgetCompositionItemDeleteView.as_view(), name='composition_delete'),
]
