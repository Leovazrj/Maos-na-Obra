from django.urls import path

from . import views

app_name = 'purchases'

urlpatterns = [
    path('', views.PurchaseRequestListView.as_view(), name='request_list'),
    path('solicitacoes/novo/', views.PurchaseRequestCreateView.as_view(), name='request_create'),
    path('solicitacoes/<int:pk>/', views.PurchaseRequestDetailView.as_view(), name='request_detail'),
    path('solicitacoes/<int:pk>/editar/', views.PurchaseRequestUpdateView.as_view(), name='request_update'),
    path('solicitacoes/<int:pk>/excluir/', views.PurchaseRequestDeleteView.as_view(), name='request_delete'),
    path('solicitacoes/<int:request_id>/item/', views.PurchaseRequestItemCreateView.as_view(), name='request_item_create'),
    path('solicitacoes/<int:request_id>/item/<int:pk>/remover/', views.PurchaseRequestItemDeleteView.as_view(), name='request_item_delete'),
    path('solicitacoes/<int:pk>/cotacao/gerar/', views.QuotationGenerateView.as_view(), name='quotation_generate'),
    path('cotacoes/<int:pk>/', views.QuotationDetailView.as_view(), name='quotation_detail'),
    path('cotacoes/<int:pk>/finalizar/', views.QuotationFinalizeView.as_view(), name='quotation_finalize'),
    path('cotacoes/<int:pk>/vencedor/', views.QuotationSelectWinnerView.as_view(), name='quotation_select_winner'),
    path('cotacoes/<int:pk>/excluir/', views.QuotationDeleteView.as_view(), name='quotation_delete'),
    path('cotacoes/<int:quotation_id>/fornecedor/', views.QuotationSupplierCreateView.as_view(), name='quotation_supplier_create'),
    path('cotacoes/<int:quotation_id>/preco/', views.QuotationItemPriceCreateView.as_view(), name='quotation_item_price_create'),
    path('cotacoes/<int:quotation_id>/fornecedor/<int:pk>/preco/', views.QuotationItemPriceBySupplierCreateView.as_view(), name='quotation_item_price_by_supplier_create'),
    path('cotacoes/<int:pk>/ordem/gerar/', views.PurchaseOrderGenerateView.as_view(), name='purchase_order_generate'),
    path('ordens/<int:pk>/', views.PurchaseOrderDetailView.as_view(), name='order_detail'),
    path('ordens/<int:pk>/aprovar/', views.PurchaseOrderApproveView.as_view(), name='order_approve'),
    path('ordens/<int:pk>/excluir/', views.PurchaseOrderDeleteView.as_view(), name='order_delete'),
]
