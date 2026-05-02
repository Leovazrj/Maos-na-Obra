from datetime import timedelta
from decimal import Decimal
from xml.etree import ElementTree as ET

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone


def create_payable_from_purchase_order(purchase_order):
    from .models import AccountPayable

    defaults = {
        'project': purchase_order.purchase_request.project,
        'supplier': purchase_order.supplier,
        'title': f'Conta a pagar - {purchase_order.title}',
        'due_date': timezone.localdate() + timedelta(days=30),
        'amount': purchase_order.total_value,
        'source_label': f'Ordem de compra {purchase_order.title}',
    }

    with transaction.atomic():
        payable, created = AccountPayable.objects.get_or_create(
            purchase_order=purchase_order,
            defaults=defaults,
        )
        if not created and payable.status == 'open':
            payable.project = defaults['project']
            payable.supplier = defaults['supplier']
            payable.title = defaults['title']
            payable.due_date = defaults['due_date']
            payable.amount = defaults['amount']
            payable.source_label = defaults['source_label']
            payable.save(update_fields=['project', 'supplier', 'title', 'due_date', 'amount', 'source_label', 'updated_at'])
    return payable


def summarize_transaction_totals(transactions):
    totals = {
        'inflow': Decimal('0.00'),
        'outflow': Decimal('0.00'),
    }
    for transaction in transactions:
        totals[transaction.transaction_type] += transaction.amount
    return {
        'inflow': totals['inflow'].quantize(Decimal('0.01')),
        'outflow': totals['outflow'].quantize(Decimal('0.01')),
        'balance': (totals['inflow'] - totals['outflow']).quantize(Decimal('0.01')),
    }


def create_receivable_from_billing(*, project, billing_type, title, amount=None, measurement=None, progress_percentage=None, notes=''):
    from .models import AccountReceivable

    if project.customer_id is None:
        raise ValueError('Selecione uma obra com cliente vinculado.')

    billing_sources = {
        'admin': 'Administração de obra',
        'measurement': 'Medição física',
        'progress_fee': 'Taxa por avanço físico',
    }
    if billing_type not in billing_sources and billing_type != 'manual':
        raise ValueError('Tipo de faturamento inválido.')

    if billing_type == 'measurement':
        if not measurement:
            raise ValueError('Selecione uma medição física.')
        amount = measurement.measured_value
        title = title or f'Faturamento - {measurement.task.name}'
        if measurement.project_id != project.pk:
            raise ValueError('A medição precisa pertencer à obra selecionada.')
    elif billing_type == 'progress_fee':
        if progress_percentage is None:
            raise ValueError('Informe o percentual de taxa por avanço físico.')
        amount = (project.expected_value * (Decimal(progress_percentage) / Decimal('100.00'))).quantize(Decimal('0.01'))
        title = title or f'Taxa por avanço físico - {project.name}'
    else:
        amount = Decimal(amount or '0.00')

    source_label = billing_sources.get(billing_type, 'Faturamento manual')

    receivable = AccountReceivable.objects.create(
        project=project,
        customer=project.customer,
        title=title,
        due_date=timezone.localdate() + timedelta(days=30),
        amount=amount,
        billing_type=billing_type,
        source_label=source_label,
        notes=notes,
    )
    return receivable


def parse_invoice_xml(uploaded_file):
    raw = uploaded_file.read()
    if hasattr(uploaded_file, 'seek'):
        uploaded_file.seek(0)

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError('XML inválido.') from exc

    access_key = ''
    for element in root.iter():
        identifier = element.attrib.get('Id', '')
        if identifier.startswith('NFe') and len(identifier) >= 47:
            access_key = identifier[3:47]
            break
        for value in element.attrib.values():
            if isinstance(value, str) and len(value) == 44 and value.isdigit():
                access_key = value
                break
        if access_key:
            break

    issuer_name = ''
    total_amount = Decimal('0.00')

    for tag in ('./emit/xNome', './/emit/xNome', './/xNome'):
        node = root.find(tag)
        if node is not None and node.text:
            issuer_name = node.text.strip()
            break

    for tag in ('.//ICMSTot/vNF', './/vNF'):
        node = root.find(tag)
        if node is not None and node.text:
            total_amount = Decimal(node.text.replace(',', '.')).quantize(Decimal('0.01'))
            break

    return {
        'access_key': access_key or None,
        'issuer_name': issuer_name or None,
        'total_amount': total_amount,
    }


def summarize_project_financials(project):
    from budgets.models import Budget
    from .models import AccountPayable, AccountReceivable, FinancialAppropriation, FinancialTransaction

    budget_total = Budget.objects.filter(project=project).aggregate(total=Sum('cost_total'))['total'] or Decimal('0.00')
    realized_cost = FinancialTransaction.objects.filter(project=project, transaction_type='outflow').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    realized_income = FinancialTransaction.objects.filter(project=project, transaction_type='inflow').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    open_payables = AccountPayable.objects.filter(project=project, status='open').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    open_receivables = AccountReceivable.objects.filter(project=project, status='open').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    appropriations = FinancialAppropriation.objects.filter(project=project).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    return {
        'budget_total': budget_total.quantize(Decimal('0.01')),
        'realized_cost': realized_cost.quantize(Decimal('0.01')),
        'realized_income': realized_income.quantize(Decimal('0.01')),
        'open_payables': open_payables.quantize(Decimal('0.01')),
        'open_receivables': open_receivables.quantize(Decimal('0.01')),
        'appropriations': appropriations.quantize(Decimal('0.01')),
        'balance': (realized_income - realized_cost).quantize(Decimal('0.01')),
    }
