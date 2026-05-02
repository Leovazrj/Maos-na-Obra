from django.urls import path

from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.FinancialTransactionListView.as_view(), name='transaction_list'),
    path('faturamentos/novo/', views.FinancialBillingCreateView.as_view(), name='billing_create'),
    path('contas-a-pagar/', views.AccountPayableListView.as_view(), name='payable_list'),
    path('contas-a-pagar/novo/', views.AccountPayableCreateView.as_view(), name='payable_create'),
    path('contas-a-pagar/<int:pk>/', views.AccountPayableDetailView.as_view(), name='payable_detail'),
    path('contas-a-pagar/<int:pk>/editar/', views.AccountPayableUpdateView.as_view(), name='payable_update'),
    path('contas-a-pagar/<int:pk>/excluir/', views.AccountPayableDeleteView.as_view(), name='payable_delete'),
    path('contas-a-pagar/<int:pk>/pagar/', views.AccountPayablePaymentView.as_view(), name='payable_pay'),
    path('contas-a-receber/', views.AccountReceivableListView.as_view(), name='receivable_list'),
    path('contas-a-receber/novo/', views.AccountReceivableCreateView.as_view(), name='receivable_create'),
    path('contas-a-receber/<int:pk>/', views.AccountReceivableDetailView.as_view(), name='receivable_detail'),
    path('contas-a-receber/<int:pk>/editar/', views.AccountReceivableUpdateView.as_view(), name='receivable_update'),
    path('contas-a-receber/<int:pk>/excluir/', views.AccountReceivableDeleteView.as_view(), name='receivable_delete'),
    path('contas-a-receber/<int:pk>/receber/', views.AccountReceivableReceiveView.as_view(), name='receivable_receive'),
    path('nfe/xml/upload/', views.InvoiceXmlUploadView.as_view(), name='invoice_xml_upload'),
    path('nfe/xml/<int:pk>/', views.InvoiceXmlDetailView.as_view(), name='invoice_xml_detail'),
    path('nfe/xml/<int:pk>/excluir/', views.InvoiceXmlDeleteView.as_view(), name='invoice_xml_delete'),
    path('nfe/xml/<int:pk>/apropriar/', views.FinancialAppropriationCreateView.as_view(), name='appropriation_create'),
    path('nfe/xml/apropriacao/<int:pk>/excluir/', views.FinancialAppropriationDeleteView.as_view(), name='appropriation_delete'),
    path('relatorios/obras/', views.ProjectFinancialReportView.as_view(), name='project_report'),
    path('relatorios/obras/pdf/', views.ProjectFinancialReportPdfView.as_view(), name='project_report_pdf'),
    path('relatorios/movimentacoes/pdf/', views.FinancialTransactionPdfView.as_view(), name='transaction_report_pdf'),
    path('movimentacoes/<int:pk>/excluir/', views.FinancialTransactionDeleteView.as_view(), name='transaction_delete'),
]
