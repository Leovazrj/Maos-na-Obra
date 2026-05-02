from datetime import date
from decimal import Decimal
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from PIL import Image, ImageDraw

from accounts.models import User
from budgets.models import Budget, BudgetCompositionItem, BudgetItem, InputItem
from client_portal.models import ClientPortalAccess
from customers.models import Customer, CustomerDocument, CustomerInteraction, CustomerPhoto
from finance.models import AccountPayable, AccountReceivable, FinancialAppropriation, FinancialTransaction, InvoiceXml
from projects.models import DailyLog, PhysicalMeasurement, Project, ProjectTask
from purchases.models import PurchaseOrder, PurchaseOrderItem, PurchaseRequest, PurchaseRequestItem, Quotation, QuotationItemPrice, QuotationSupplier
from suppliers.models import Supplier, SupplierCategory


class Command(BaseCommand):
    help = 'Popula dados de demonstração para apresentação do aplicativo.'

    def handle(self, *args, **options):
        summary = self.seed()

        self.stdout.write(self.style.SUCCESS('Dados de demonstração preparados com sucesso.'))
        for label, value in summary.items():
            self.stdout.write(f'{label}: {value}')

    def seed(self):
        admin = self.ensure_user(
            email='apresentacao@maosnaobra.com',
            name='Admin Apresentação',
            password='apresentacao123',
            is_staff=True,
            is_superuser=True,
        )
        manager = self.ensure_user(
            email='gestor.operacional@maosnaobra.com',
            name='Gestor Operacional',
            password='gestor123',
            is_staff=True,
        )
        client_user = self.ensure_user(
            email='cliente.atlas@maosnaobra.com',
            name='Cliente Atlas Portal',
            password='cliente123',
        )
        client_user_horizonte = self.ensure_user(
            email='cliente.horizonte@maosnaobra.com',
            name='Cliente Horizonte Portal',
            password='cliente123',
        )
        client_user_litoral = self.ensure_user(
            email='cliente.litoral@maosnaobra.com',
            name='Cliente Litoral Portal',
            password='cliente123',
        )

        customer_atlas = Customer.objects.get_or_create(
            name='Residencial Atlas LTDA',
            defaults={
                'person_type': 'J',
                'document_number': '12.345.678/0001-90',
                'email': 'contato@atlas.com.br',
                'phone': '(11) 3333-4444',
                'address': 'Av. das Nações, 1200 - Centro - São Paulo/SP',
                'status': 'active',
            },
        )[0]
        customer_horizonte = Customer.objects.get_or_create(
            name='Grupo Horizonte Engenharia',
            defaults={
                'person_type': 'J',
                'document_number': '98.765.432/0001-10',
                'email': 'engenharia@horizonte.com.br',
                'phone': '(11) 2222-5555',
                'address': 'Rua Projetada, 450 - Moema - São Paulo/SP',
                'status': 'active',
            },
        )[0]
        customer_litoral = Customer.objects.get_or_create(
            name='Incorporadora Litoral SA',
            defaults={
                'person_type': 'J',
                'document_number': '44.555.666/0001-77',
                'email': 'obras@litoral.com.br',
                'phone': '(13) 3444-8899',
                'address': 'Av. Beira Mar, 1500 - Santos/SP',
                'status': 'active',
            },
        )[0]

        self.ensure_portal_access(customer_atlas, client_user)
        self.ensure_portal_access(customer_horizonte, client_user_horizonte)
        self.ensure_portal_access(customer_litoral, client_user_litoral)

        categories = {
            'Materiais básicos': SupplierCategory.objects.get_or_create(
                name='Materiais básicos',
                defaults={'description': 'Cimento, areia, brita e blocos.'},
            )[0],
            'Acabamentos': SupplierCategory.objects.get_or_create(
                name='Acabamentos',
                defaults={'description': 'Revestimentos, tintas e louças.'},
            )[0],
            'Estrutural': SupplierCategory.objects.get_or_create(
                name='Estrutural',
                defaults={'description': 'Concreto, aço e forma.'},
            )[0],
        }

        suppliers = {
            'concremax': self.ensure_supplier(
                legal_name='ConcreMax Distribuidora LTDA',
                trade_name='ConcreMax',
                email='compras@concremax.com.br',
                categories=[categories['Materiais básicos'], categories['Estrutural']],
                notes='Fornecedor recorrente para concreto e aço.',
            ),
            'acabamentos': self.ensure_supplier(
                legal_name='Acabamentos Pro Comércio Ltda',
                trade_name='Acabamentos Pro',
                email='vendas@acabamentospro.com.br',
                categories=[categories['Acabamentos']],
                notes='Linha premium para acabamento fino.',
            ),
            'servicos': self.ensure_supplier(
                legal_name='Serra Serviços Técnicos ME',
                trade_name='Serra Serviços',
                email='contato@serraservicos.com.br',
                categories=[categories['Estrutural']],
                notes='Equipe de montagem e apoio técnico.',
            ),
            'inativo': self.ensure_supplier(
                legal_name='Fornecedor Reserva Sem Email',
                trade_name='Reserva Obra',
                email=None,
                status='inactive',
                categories=[],
                notes='Cadastro inativo para histórico.',
            ),
            'eletrica': self.ensure_supplier(
                legal_name='Prime Elétrica LTDA',
                trade_name='Prime Elétrica',
                email='vendas@primeeletrica.com.br',
                categories=[categories['Materiais básicos']],
                notes='Infraestrutura elétrica e automação.',
            ),
            'madeira': self.ensure_supplier(
                legal_name='Madeireira São Paulo Comércio LTDA',
                trade_name='Madeireira São Paulo',
                email='comercial@madeireirasp.com.br',
                categories=[categories['Estrutural']],
                notes='Formas, escoramentos e madeira de apoio.',
            ),
        }

        project_atlas = self.ensure_project(
            name='Residencial Atlas - Torre A',
            customer=customer_atlas,
            responsible=manager,
            address='Rua das Palmeiras, 250 - Pinheiros - São Paulo/SP',
            expected_start_date=date(2026, 2, 10),
            expected_end_date=date(2026, 9, 30),
            expected_value=Decimal('1250000.00'),
            description='Obra residencial com 18 pavimentos e áreas comuns.',
        )
        project_horizonte = self.ensure_project(
            name='Clínica Horizonte - Reforma',
            customer=customer_horizonte,
            responsible=manager,
            address='Av. Brigadeiro Faria Lima, 900 - São Paulo/SP',
            expected_start_date=date(2026, 3, 1),
            expected_end_date=date(2026, 7, 15),
            status='active',
            expected_value=Decimal('420000.00'),
            description='Reforma completa com adequação de layout e instalações.',
        )
        project_backoffice = self.ensure_project(
            name='Escritório Mão na Obra - Ampliação',
            customer=customer_atlas,
            responsible=admin,
            address='Rua Interna, 100 - São Paulo/SP',
            expected_start_date=date(2026, 1, 5),
            expected_end_date=date(2026, 4, 30),
            status='closed',
            expected_value=Decimal('180000.00'),
            description='Projeto interno usado para acompanhamento financeiro.',
        )
        project_litoral = self.ensure_project(
            name='Condomínio Litoral - Bloco B',
            customer=customer_litoral,
            responsible=manager,
            address='Av. Beira Mar, 1520 - Santos/SP',
            expected_start_date=date(2026, 4, 5),
            expected_end_date=date(2026, 11, 20),
            expected_value=Decimal('2180000.00'),
            description='Empreendimento residencial com frentes de estrutura, elétrica e acabamento.',
        )

        self.ensure_customer_assets(customer_atlas, project_atlas)
        self.ensure_customer_assets(customer_horizonte, project_horizonte)
        self.ensure_customer_assets(customer_litoral, project_litoral)

        tasks_atlas = [
            self.ensure_project_task(project_atlas, 'Mobilização e canteiro', date(2026, 2, 10), date(2026, 2, 20), Decimal('8.00'), Decimal('32000.00')),
            self.ensure_project_task(project_atlas, 'Estrutura e concretagem', date(2026, 2, 21), date(2026, 4, 5), Decimal('28.00'), Decimal('220000.00')),
            self.ensure_project_task(project_atlas, 'Alvenaria e vedação', date(2026, 4, 6), date(2026, 5, 20), Decimal('24.00'), Decimal('180000.00')),
            self.ensure_project_task(project_atlas, 'Acabamentos', date(2026, 5, 21), date(2026, 8, 30), Decimal('30.00'), Decimal('310000.00')),
            self.ensure_project_task(project_atlas, 'Entrega técnica', date(2026, 9, 1), date(2026, 9, 30), Decimal('10.00'), Decimal('60000.00')),
        ]
        tasks_horizonte = [
            self.ensure_project_task(project_horizonte, 'Demolição controlada', date(2026, 3, 1), date(2026, 3, 12), Decimal('15.00'), Decimal('30000.00')),
            self.ensure_project_task(project_horizonte, 'Infraestrutura elétrica', date(2026, 3, 13), date(2026, 4, 20), Decimal('35.00'), Decimal('110000.00')),
            self.ensure_project_task(project_horizonte, 'Revestimentos e pintura', date(2026, 4, 21), date(2026, 6, 10), Decimal('30.00'), Decimal('95000.00')),
        ]

        self.ensure_daily_log(
            project_atlas,
            log_date=date(2026, 4, 28),
            weather='Parcialmente nublado',
            team_present='01 engenheiro, 02 mestres, 12 operários',
            services_performed='Montagem de formas e armação de vigas do 8o pavimento.',
            occurrences='Entrega parcial de aço atrasada em 2 horas.',
            notes='Produção normal após ajuste no cronograma.',
        )
        self.ensure_daily_log(
            project_atlas,
            log_date=date(2026, 4, 29),
            weather='Sol forte',
            team_present='01 engenheiro, 02 mestres, 14 operários',
            services_performed='Concretagem de laje e início da cura úmida.',
            occurrences='Nenhuma ocorrência relevante.',
            notes='Frente de concretagem acompanhada pelo responsável.',
        )
        self.ensure_physical_measurement(
            project_atlas,
            tasks_atlas[0],
            measurement_date=date(2026, 4, 29),
            measured_percentage=Decimal('100.00'),
            measured_value=Decimal('32000.00'),
            visible_in_portal=True,
            notes='Mobilização concluída e liberada ao cliente.',
        )
        self.ensure_physical_measurement(
            project_atlas,
            tasks_atlas[1],
            measurement_date=date(2026, 4, 29),
            measured_percentage=Decimal('46.00'),
            measured_value=Decimal('101200.00'),
            visible_in_portal=True,
            notes='Etapa estrutural com medição parcial.',
        )
        self.ensure_physical_measurement(
            project_atlas,
            tasks_atlas[2],
            measurement_date=date(2026, 4, 30),
            measured_percentage=Decimal('18.00'),
            measured_value=Decimal('32400.00'),
            visible_in_portal=True,
            notes='Avanço inicial em alvenaria.',
        )
        self.ensure_physical_measurement(
            project_horizonte,
            tasks_horizonte[1],
            measurement_date=date(2026, 4, 27),
            measured_percentage=Decimal('28.00'),
            measured_value=Decimal('30800.00'),
            visible_in_portal=True,
            notes='Serviço liberado para o portal do cliente.',
        )

        input_items = {
            'cimento': self.ensure_input_item('Cimento CP II', 'sc', Decimal('42.50'), 'Saco de cimento para concretagem.'),
            'areia': self.ensure_input_item('Areia média lavada', 'm3', Decimal('118.00'), 'Agregado para argamassa e concreto.'),
            'brita': self.ensure_input_item('Brita 1', 'm3', Decimal('126.00'), 'Agregado graúdo para concreto estrutural.'),
            'tinta': self.ensure_input_item('Tinta acrílica fosca', 'l', Decimal('31.90'), 'Acabamento interno de paredes.'),
            'porcelanato': self.ensure_input_item('Porcelanato acetinado', 'm2', Decimal('96.00'), 'Revestimento de áreas nobres.'),
            'eletroduto': self.ensure_input_item('Eletroduto corrugado', 'm', Decimal('4.20'), 'Infraestrutura elétrica embutida.'),
        }

        budget_atlas = self.ensure_budget(
            project_atlas,
            name='Orçamento base - Atlas Torre A',
            budget_type='cost',
            margin_percentage=Decimal('18.00'),
            status='approved',
            notes='Orçamento consolidado para apresentação.',
        )
        budget_horizonte = self.ensure_budget(
            project_horizonte,
            name='Orçamento executivo - Clínica Horizonte',
            budget_type='sale',
            margin_percentage=Decimal('22.00'),
            status='draft',
            notes='Base de venda para negociação com o cliente.',
        )

        budget_item_structure = self.ensure_budget_item(
            budget_atlas,
            'Estrutura de concreto',
            'm2',
            Decimal('1.00'),
            'Lote principal da estrutura.',
        )
        budget_item_finish = self.ensure_budget_item(
            budget_atlas,
            'Acabamento interno',
            'm2',
            Decimal('1.00'),
            'Pacote de acabamento dos apartamentos.',
        )
        budget_item_clinic = self.ensure_budget_item(
            budget_horizonte,
            'Adequação elétrica',
            'm2',
            Decimal('1.00'),
            'Melhorias de infraestrutura da clínica.',
        )

        self.ensure_budget_composition_item(budget_item_structure, input_items['cimento'], 'sc', Decimal('240.00'), Decimal('42.50'))
        self.ensure_budget_composition_item(budget_item_structure, input_items['brita'], 'm3', Decimal('65.00'), Decimal('126.00'))
        self.ensure_budget_composition_item(budget_item_structure, input_items['areia'], 'm3', Decimal('52.00'), Decimal('118.00'))

        self.ensure_budget_composition_item(budget_item_finish, input_items['tinta'], 'l', Decimal('180.00'), Decimal('31.90'))
        self.ensure_budget_composition_item(budget_item_finish, input_items['porcelanato'], 'm2', Decimal('420.00'), Decimal('96.00'))

        self.ensure_budget_composition_item(budget_item_clinic, input_items['eletroduto'], 'm', Decimal('380.00'), Decimal('4.20'))
        self.ensure_budget_composition_item(budget_item_clinic, input_items['tinta'], 'l', Decimal('90.00'), Decimal('31.90'))

        request_atlas = self.ensure_purchase_request(
            project_atlas,
            title='Solicitação de compra - Torre A, lote estrutural',
            status='ordered',
            notes='Itens críticos para a etapa estrutural.',
        )
        request_horizonte = self.ensure_purchase_request(
            project_horizonte,
            title='Solicitação de compra - Clínica Horizonte',
            status='open',
            notes='Cotação aberta para comparação comercial.',
        )

        self.ensure_purchase_request_item(request_atlas, input_items['cimento'], 'Cimento CP II', 'sc', Decimal('220.00'), 'Entrega fracionada em 2 lotes.')
        self.ensure_purchase_request_item(request_atlas, input_items['brita'], 'Brita 1', 'm3', Decimal('58.00'), 'Material para concretagem da laje.')
        self.ensure_purchase_request_item(request_atlas, input_items['areia'], 'Areia média lavada', 'm3', Decimal('46.00'), 'Mistura para argamassa.')

        self.ensure_purchase_request_item(request_horizonte, input_items['eletroduto'], 'Eletroduto corrugado', 'm', Decimal('400.00'), 'Reforço da infraestrutura elétrica.')
        self.ensure_purchase_request_item(request_horizonte, input_items['tinta'], 'Tinta acrílica fosca', 'l', Decimal('120.00'), 'Pintura interna dos consultórios.')
        self.ensure_purchase_request_item(request_horizonte, input_items['porcelanato'], 'Porcelanato acetinado', 'm2', Decimal('165.00'), 'Piso das áreas de circulação.')

        quotation_atlas = self.ensure_quotation(request_atlas, 'Cotação estrutural - Atlas', status='finished', notes='Cotações comparadas e fornecedor definido.')
        quotation_horizonte = self.ensure_quotation(request_horizonte, 'Cotação clínica - Horizonte', status='open', notes='Ainda aguardando propostas.')

        quote_suppliers_atlas = [
            self.ensure_quotation_supplier(quotation_atlas, suppliers['concremax'], status='responded', notes='Fornecedor vencedor pela melhor composição de preços.'),
            self.ensure_quotation_supplier(quotation_atlas, suppliers['servicos'], status='responded', notes='Fornecedor alternativo para comparação.'),
        ]
        quote_suppliers_horizonte = [
            self.ensure_quotation_supplier(quotation_horizonte, suppliers['acabamentos'], status='invited', notes='Convite enviado ao comercial.'),
            self.ensure_quotation_supplier(quotation_horizonte, suppliers['concremax'], status='invited', notes='Fornecedor de apoio para materiais básicos.'),
        ]

        self.ensure_quotation_item_price(quote_suppliers_atlas[0], request_atlas.items.get(description='Cimento CP II'), Decimal('39.80'))
        self.ensure_quotation_item_price(quote_suppliers_atlas[0], request_atlas.items.get(description='Brita 1'), Decimal('121.00'))
        self.ensure_quotation_item_price(quote_suppliers_atlas[0], request_atlas.items.get(description='Areia média lavada'), Decimal('112.00'))

        self.ensure_quotation_item_price(quote_suppliers_atlas[1], request_atlas.items.get(description='Cimento CP II'), Decimal('41.20'))
        self.ensure_quotation_item_price(quote_suppliers_atlas[1], request_atlas.items.get(description='Brita 1'), Decimal('125.00'))
        self.ensure_quotation_item_price(quote_suppliers_atlas[1], request_atlas.items.get(description='Areia média lavada'), Decimal('117.50'))

        purchase_order = self.ensure_purchase_order_from_quotation(quotation_atlas)
        purchase_order.approve()

        payable_manual = self.ensure_account_payable(
            project_atlas,
            suppliers['acabamentos'],
            title='Pagamento pendente - louças e metais',
            due_date=date(2026, 5, 18),
            amount=Decimal('18420.00'),
            source_label='Lançamento manual para apresentação',
            notes='Compra complementar de acabamento.',
        )
        payable_from_order = purchase_order.account_payable
        payable_from_order.register_payment(notes='Pagamento agendado e conciliado para apresentação.')

        receivable_admin = self.ensure_account_receivable(
            project_atlas,
            customer_atlas,
            title='Medição administrativa - abril',
            due_date=date(2026, 5, 10),
            amount=Decimal('28500.00'),
            billing_type='admin',
            source_label='Administração de obra',
            notes='Taxa administrativa mensal.',
        )
        receivable_progress = self.ensure_account_receivable(
            project_atlas,
            customer_atlas,
            title='Taxa por avanço físico - Atlas',
            due_date=date(2026, 5, 22),
            amount=Decimal('12500.00'),
            billing_type='progress_fee',
            source_label='Taxa por avanço físico',
            notes='Lançamento para o fluxo financeiro.',
        )
        receivable_measurement = self.ensure_account_receivable(
            project_horizonte,
            customer_horizonte,
            title='Faturamento por medição - Clínica Horizonte',
            due_date=date(2026, 5, 25),
            amount=Decimal('17600.00'),
            billing_type='measurement',
            source_label='Medição física',
            notes='Medição vinculada ao avanço da obra.',
        )
        receivable_admin.register_receipt(notes='Recebimento parcial via banco para apresentação.')

        invoice = self.ensure_invoice_xml(
            project_atlas,
            access_key='35123456789012345678901234567890123456789012',
            issuer_name='Fornecedor XML Demo LTDA',
            total_amount=Decimal('7823.45'),
        )
        self.ensure_appropriation(
            project_atlas,
            invoice,
            service_name='Concretagem estrutural',
            amount=Decimal('4120.00'),
            percentage=Decimal('52.65'),
            notes='Apropriação sobre NFe XML da concretagem.',
        )
        self.ensure_appropriation(
            project_atlas,
            invoice,
            service_name='Materiais de acabamento',
            amount=Decimal('3703.45'),
            percentage=Decimal('47.35'),
            notes='Saldo apropriado em materiais.',
        )

        self.ensure_financial_transaction(
            project_atlas,
            transaction_type='inflow',
            transaction_date=date(2026, 5, 1),
            amount=Decimal('68000.00'),
            description='Entrada contratual inicial',
            notes='Lançamento manual para demonstrar saldo.',
        )
        self.ensure_financial_transaction(
            project_atlas,
            transaction_type='outflow',
            transaction_date=date(2026, 5, 2),
            amount=Decimal('24500.00'),
            description='Saída operacional de canteiro',
            notes='Pagamento de fretes e insumos.',
        )
        self.ensure_financial_transaction(
            project_horizonte,
            transaction_type='inflow',
            transaction_date=date(2026, 5, 2),
            amount=Decimal('17600.00'),
            description='Recebimento por medição clínica',
            notes='Receita vinculada à obra da clínica.',
        )

        extra_customers = {
            'aurora': self.ensure_customer(
                name='Construtora Aurora Participações',
                document_number='55.666.777/0001-88',
                email='contato@aurora.com.br',
                phone='(11) 3444-1010',
                address='Av. Paulista, 2100 - Bela Vista - São Paulo/SP',
            ),
            'delta': self.ensure_customer(
                name='Shopping Delta Empreendimentos',
                document_number='22.333.444/0001-55',
                email='engenharia@shoppingdelta.com.br',
                phone='(11) 3888-2020',
                address='Rua do Comércio, 120 - Centro - São Paulo/SP',
            ),
            'porto': self.ensure_customer(
                name='Residencial Porto Azul SPE',
                document_number='11.222.333/0001-44',
                email='obras@portoazul.com.br',
                phone='(13) 3999-3030',
                address='Av. Atlântica, 500 - Santos/SP',
            ),
            'industrial': self.ensure_customer(
                name='Complexo Industrial Norte Ltda',
                document_number='66.777.888/0001-99',
                email='suprimentos@industrialnorte.com.br',
                phone='(19) 3555-4040',
                address='Rodovia SP-75, Km 12 - Campinas/SP',
            ),
        }
        extra_users = {
            'aurora': self.ensure_user(
                email='cliente.aurora@maosnaobra.com',
                name='Cliente Aurora Portal',
                password='cliente123',
            ),
            'delta': self.ensure_user(
                email='cliente.delta@maosnaobra.com',
                name='Cliente Delta Portal',
                password='cliente123',
            ),
            'porto': self.ensure_user(
                email='cliente.porto@maosnaobra.com',
                name='Cliente Porto Azul Portal',
                password='cliente123',
            ),
            'industrial': self.ensure_user(
                email='cliente.industrial@maosnaobra.com',
                name='Cliente Industrial Portal',
                password='cliente123',
            ),
        }

        for key, customer in extra_customers.items():
            self.ensure_portal_access(customer, extra_users[key])

        extra_suppliers = {
            'hidraulica': self.ensure_supplier(
                legal_name='HidraTech Materiais Hidráulicos LTDA',
                trade_name='HidraTech',
                email='vendas@hidratech.com.br',
                categories=[categories['Materiais básicos']],
                notes='Tubos, conexões e bombas para abastecimento.',
            ),
            'acustica': self.ensure_supplier(
                legal_name='Acústica Pro Soluções Ltda',
                trade_name='Acústica Pro',
                email='comercial@acusticapro.com.br',
                categories=[categories['Acabamentos']],
                notes='Revestimentos acústicos e forros.',
            ),
            'metais': self.ensure_supplier(
                legal_name='Metais Urbanos Comércio LTDA',
                trade_name='Metais Urbanos',
                email='vendas@metaisurbanos.com.br',
                categories=[categories['Acabamentos']],
                notes='Louças, metais e acessórios de banheiro.',
            ),
            'estrutura2': self.ensure_supplier(
                legal_name='Estrutura Forte Industrial LTDA',
                trade_name='Estrutura Forte',
                email='compras@estruturaforte.com.br',
                categories=[categories['Estrutural']],
                notes='Aço, concreto e montagem industrial.',
            ),
        }

        extra_input_items = {
            'aco': self.ensure_input_item('Aço CA-50', 'kg', Decimal('8.90'), 'Vergalhão para estrutura de concreto armado.'),
            'tijolo': self.ensure_input_item('Tijolo cerâmico', 'un', Decimal('1.32'), 'Bloco para alvenaria de vedação.'),
            'gesso': self.ensure_input_item('Gesso acartonado', 'm2', Decimal('41.80'), 'Sistema de divisórias e forros.'),
            'pvc': self.ensure_input_item('Tubo PVC soldável', 'm', Decimal('6.75'), 'Linha hidráulica de água fria.'),
            'argamassa': self.ensure_input_item('Argamassa colante ACII', 'sc', Decimal('34.60'), 'Assentamento de revestimentos.'),
            'vidro': self.ensure_input_item('Vidro temperado', 'm2', Decimal('215.00'), 'Fechamento e esquadrias de vidro.'),
        }

        project_aurora = self.ensure_project(
            name='Residencial Aurora - Fase 1',
            customer=extra_customers['aurora'],
            responsible=manager,
            address='Av. Paulista, 2150 - Bela Vista - São Paulo/SP',
            expected_start_date=date(2026, 2, 1),
            expected_end_date=date(2026, 12, 20),
            expected_value=Decimal('2480000.00'),
            description='Residencial de alto padrão com frentes simultâneas de estrutura e acabamento.',
        )
        project_delta = self.ensure_project(
            name='Shopping Delta - Retrofit',
            customer=extra_customers['delta'],
            responsible=admin,
            address='Rua do Comércio, 150 - Centro - São Paulo/SP',
            expected_start_date=date(2026, 3, 10),
            expected_end_date=date(2026, 10, 15),
            expected_value=Decimal('930000.00'),
            description='Retrofit com adequação de áreas comuns e instalações.',
        )
        project_porto = self.ensure_project(
            name='Residencial Porto Azul - Torre 2',
            customer=extra_customers['porto'],
            responsible=manager,
            address='Av. Atlântica, 620 - Santos/SP',
            expected_start_date=date(2026, 4, 2),
            expected_end_date=date(2026, 11, 28),
            expected_value=Decimal('1710000.00'),
            description='Torre residencial com etapas de estrutura, hidráulica e acabamentos.',
        )
        project_industrial = self.ensure_project(
            name='Complexo Industrial Norte - Expansão',
            customer=extra_customers['industrial'],
            responsible=admin,
            address='Rodovia SP-75, Km 14 - Campinas/SP',
            expected_start_date=date(2026, 1, 20),
            expected_end_date=date(2026, 9, 12),
            expected_value=Decimal('3110000.00'),
            description='Ampliação industrial para área produtiva e administrativa.',
        )

        for customer, project in (
            (extra_customers['aurora'], project_aurora),
            (extra_customers['delta'], project_delta),
            (extra_customers['porto'], project_porto),
            (extra_customers['industrial'], project_industrial),
        ):
            self.ensure_customer_assets(customer, project)

        aurora_tasks = [
            self.ensure_project_task(project_aurora, 'Fundação e contenção', date(2026, 2, 1), date(2026, 3, 10), Decimal('12.00'), Decimal('180000.00')),
            self.ensure_project_task(project_aurora, 'Estrutura principal', date(2026, 3, 11), date(2026, 6, 15), Decimal('33.00'), Decimal('720000.00')),
            self.ensure_project_task(project_aurora, 'Alvenaria e fechamento', date(2026, 6, 16), date(2026, 8, 20), Decimal('22.00'), Decimal('430000.00')),
            self.ensure_project_task(project_aurora, 'Acabamentos finos', date(2026, 8, 21), date(2026, 11, 20), Decimal('25.00'), Decimal('640000.00')),
        ]
        delta_tasks = [
            self.ensure_project_task(project_delta, 'Demolição seletiva', date(2026, 3, 10), date(2026, 3, 25), Decimal('10.00'), Decimal('64000.00')),
            self.ensure_project_task(project_delta, 'Infraestrutura predial', date(2026, 3, 26), date(2026, 6, 1), Decimal('36.00'), Decimal('290000.00')),
            self.ensure_project_task(project_delta, 'Pisos e revestimentos', date(2026, 6, 2), date(2026, 8, 15), Decimal('28.00'), Decimal('262000.00')),
        ]
        porto_tasks = [
            self.ensure_project_task(project_porto, 'Estacas e blocos', date(2026, 4, 2), date(2026, 5, 20), Decimal('16.00'), Decimal('210000.00')),
            self.ensure_project_task(project_porto, 'Hidráulica e elétrica', date(2026, 5, 21), date(2026, 8, 5), Decimal('29.00'), Decimal('338000.00')),
            self.ensure_project_task(project_porto, 'Acabamento e áreas comuns', date(2026, 8, 6), date(2026, 11, 28), Decimal('33.00'), Decimal('511000.00')),
        ]
        industrial_tasks = [
            self.ensure_project_task(project_industrial, 'Terraplenagem', date(2026, 1, 20), date(2026, 2, 28), Decimal('9.00'), Decimal('120000.00')),
            self.ensure_project_task(project_industrial, 'Estrutura metálica', date(2026, 3, 1), date(2026, 5, 18), Decimal('31.00'), Decimal('890000.00')),
            self.ensure_project_task(project_industrial, 'Instalações especiais', date(2026, 5, 19), date(2026, 7, 30), Decimal('24.00'), Decimal('640000.00')),
            self.ensure_project_task(project_industrial, 'Comissionamento', date(2026, 8, 1), date(2026, 9, 12), Decimal('18.00'), Decimal('210000.00')),
        ]

        self.ensure_daily_log(
            project_aurora,
            log_date=date(2026, 5, 3),
            weather='Nublado com períodos de sol',
            team_present='01 engenheiro, 03 encarregados, 18 operários',
            services_performed='Concretagem do bloco de fundação e liberação da armação do 1o subsolo.',
            occurrences='Ajuste de bomba de concreto durante a manhã.',
            notes='Frente com avanço acima do planejado.',
        )
        self.ensure_daily_log(
            project_delta,
            log_date=date(2026, 5, 3),
            weather='Chuva leve',
            team_present='01 engenheiro, 02 encarregados, 10 operários',
            services_performed='Remoção de revestimentos antigos e limpeza técnica das áreas comuns.',
            occurrences='Interrupção pontual por chuva.',
            notes='Produção retomada após o almoço.',
        )
        self.ensure_daily_log(
            project_porto,
            log_date=date(2026, 5, 4),
            weather='Sol forte',
            team_present='01 engenheiro, 02 encarregados, 16 operários',
            services_performed='Instalação hidráulica do 2o pavimento e montagem de shafts.',
            occurrences='Nenhuma ocorrência relevante.',
            notes='Frente acompanhada pelo cliente no portal.',
        )
        self.ensure_daily_log(
            project_industrial,
            log_date=date(2026, 5, 4),
            weather='Parcialmente nublado',
            team_present='01 engenheiro, 04 encarregados, 22 operários',
            services_performed='Montagem da estrutura metálica principal do galpão.',
            occurrences='Entrega de peças metálicas antecipada.',
            notes='Produção intensificada para cumprir cronograma.',
        )

        self.ensure_physical_measurement(project_aurora, aurora_tasks[0], date(2026, 5, 3), Decimal('100.00'), Decimal('180000.00'), True, 'Fundação concluída e liberada ao cliente.')
        self.ensure_physical_measurement(project_aurora, aurora_tasks[1], date(2026, 5, 3), Decimal('34.00'), Decimal('244800.00'), True, 'Estrutura principal em avanço contínuo.')
        self.ensure_physical_measurement(project_delta, delta_tasks[0], date(2026, 5, 3), Decimal('100.00'), Decimal('64000.00'), True, 'Demolição seletiva concluída.')
        self.ensure_physical_measurement(project_porto, porto_tasks[1], date(2026, 5, 4), Decimal('21.00'), Decimal('70980.00'), True, 'Hidráulica e elétrica em andamento.')
        self.ensure_physical_measurement(project_industrial, industrial_tasks[1], date(2026, 5, 4), Decimal('18.00'), Decimal('160200.00'), True, 'Estrutura metálica com medição parcial.')

        budget_aurora = self.ensure_budget(
            project_aurora,
            name='Orçamento executivo - Aurora Fase 1',
            budget_type='cost',
            margin_percentage=Decimal('19.00'),
            status='approved',
            notes='Base consolidada para execução da torre.',
        )
        budget_aurora_structure = self.ensure_budget_item(
            budget_aurora,
            'Estrutura e fundação',
            'm2',
            Decimal('1.00'),
            'Conjunto executivo da estrutura principal.',
        )
        budget_aurora_finish = self.ensure_budget_item(
            budget_aurora,
            'Acabamentos premium',
            'm2',
            Decimal('1.00'),
            'Pacote de acabamento de alto padrão.',
        )
        self.ensure_budget_composition_item(budget_aurora_structure, extra_input_items['aco'], 'kg', Decimal('15800.00'), Decimal('8.90'))
        self.ensure_budget_composition_item(budget_aurora_structure, input_items['cimento'], 'sc', Decimal('540.00'), Decimal('42.50'))
        self.ensure_budget_composition_item(budget_aurora_finish, extra_input_items['vidro'], 'm2', Decimal('620.00'), Decimal('215.00'))
        self.ensure_budget_composition_item(budget_aurora_finish, extra_input_items['argamassa'], 'sc', Decimal('240.00'), Decimal('34.60'))

        request_aurora = self.ensure_purchase_request(
            project_aurora,
            title='Solicitação de compra - Aurora Fase 1',
            status='quoted',
            notes='Volume elevado de materiais para estrutura e acabamento.',
        )
        self.ensure_purchase_request_item(request_aurora, extra_input_items['aco'], 'Aço CA-50', 'kg', Decimal('12600.00'), 'Compra em múltiplos lotes para a estrutura.')
        self.ensure_purchase_request_item(request_aurora, input_items['cimento'], 'Cimento CP II', 'sc', Decimal('620.00'), 'Reposição para concretagem.')
        self.ensure_purchase_request_item(request_aurora, extra_input_items['vidro'], 'Vidro temperado', 'm2', Decimal('210.00'), 'Esquadrias e fechamento de varanda.')

        quotation_aurora = self.ensure_quotation(request_aurora, 'Cotação executiva - Aurora', status='finished', notes='Processo concluído com múltiplos fornecedores.')
        qsup_aurora_1 = self.ensure_quotation_supplier(quotation_aurora, suppliers['concremax'], status='responded', notes='Proposta base de estrutura.')
        qsup_aurora_2 = self.ensure_quotation_supplier(quotation_aurora, extra_suppliers['estrutura2'], status='responded', notes='Proposta competitiva para aço e concreto.')
        self.ensure_quotation_item_price(qsup_aurora_1, request_aurora.items.get(description='Aço CA-50'), Decimal('8.75'))
        self.ensure_quotation_item_price(qsup_aurora_1, request_aurora.items.get(description='Cimento CP II'), Decimal('41.20'))
        self.ensure_quotation_item_price(qsup_aurora_1, request_aurora.items.get(description='Vidro temperado'), Decimal('214.00'))
        self.ensure_quotation_item_price(qsup_aurora_2, request_aurora.items.get(description='Aço CA-50'), Decimal('8.48'))
        self.ensure_quotation_item_price(qsup_aurora_2, request_aurora.items.get(description='Cimento CP II'), Decimal('40.70'))
        self.ensure_quotation_item_price(qsup_aurora_2, request_aurora.items.get(description='Vidro temperado'), Decimal('211.50'))

        order_aurora = self.ensure_purchase_order_from_quotation(quotation_aurora)
        order_aurora.approve()

        self.ensure_account_payable(
            project_aurora,
            extra_suppliers['estrutura2'],
            title='Conta a pagar - OC - Cotação executiva - Aurora',
            due_date=date(2026, 5, 28),
            amount=Decimal('118500.00'),
            source_label='Ordem de compra de grande volume',
            notes='Lançamento de apresentação com volume industrial.',
        )
        self.ensure_account_receivable(
            project_aurora,
            extra_customers['aurora'],
            title='Medição executiva - Aurora',
            due_date=date(2026, 5, 30),
            amount=Decimal('94200.00'),
            billing_type='measurement',
            source_label='Medição executiva',
            notes='Faturamento por avanço físico da torre.',
        )

        self.ensure_invoice_xml(
            project_aurora,
            access_key='35123456789012345678901234567890123456789111',
            issuer_name='Estrutura Forte Industrial LTDA',
            total_amount=Decimal('15890.20'),
        )
        self.ensure_invoice_xml(
            project_porto,
            access_key='35123456789012345678901234567890123456789222',
            issuer_name='HidraTech Materiais Hidráulicos LTDA',
            total_amount=Decimal('6842.10'),
        )
        self.ensure_appropriation(
            project_aurora,
            InvoiceXml.objects.get(project=project_aurora, access_key='35123456789012345678901234567890123456789111'),
            service_name='Estrutura metálica pesada',
            amount=Decimal('9800.00'),
            percentage=Decimal('61.65'),
            notes='Apropriação de NFe do lote estrutural.',
        )
        self.ensure_appropriation(
            project_porto,
            InvoiceXml.objects.get(project=project_porto, access_key='35123456789012345678901234567890123456789222'),
            service_name='Instalação hidráulica',
            amount=Decimal('4100.00'),
            percentage=Decimal('60.00'),
            notes='Apropriação para obra residencial.',
        )

        for project, items in (
            (project_aurora, [
                ('Entrada contratual Aurora', 'inflow', date(2026, 5, 3), Decimal('120000.00'), 'Entrada inicial do contrato', 'Receita de apresentação em volume alto.'),
                ('Saída operacional Aurora', 'outflow', date(2026, 5, 4), Decimal('38500.00'), 'Compras de estrutura', 'Pagamentos de insumos e fretes.'),
            ]),
            (project_delta, [
                ('Entrada contratual Delta', 'inflow', date(2026, 5, 3), Decimal('54000.00'), 'Entrada do retrofit', 'Receita contratual inicial.'),
                ('Saída operacional Delta', 'outflow', date(2026, 5, 4), Decimal('18250.00'), 'Desmobilização e limpeza', 'Custos operacionais do retrofit.'),
            ]),
            (project_porto, [
                ('Entrada contratual Porto Azul', 'inflow', date(2026, 5, 4), Decimal('78000.00'), 'Entrada inicial da torre', 'Fluxo financeiro da torre residencial.'),
                ('Saída operacional Porto Azul', 'outflow', date(2026, 5, 5), Decimal('26500.00'), 'Materiais hidráulicos', 'Compra de tubulação e conexões.'),
            ]),
            (project_industrial, [
                ('Entrada contratual Industrial Norte', 'inflow', date(2026, 5, 4), Decimal('160000.00'), 'Entrada da expansão', 'Captação inicial da expansão industrial.'),
                ('Saída operacional Industrial Norte', 'outflow', date(2026, 5, 5), Decimal('49250.00'), 'Estrutura metálica', 'Pagamento de fabricação e montagem.'),
            ]),
        ):
            for description, transaction_type, transaction_date, amount, source_label, notes in items:
                self.ensure_financial_transaction(
                    project,
                    transaction_type=transaction_type,
                    transaction_date=transaction_date,
                    amount=amount,
                    description=description,
                    notes=notes,
                )

        summary = {
            'Usuários de apresentação': User.objects.filter(email__in=[
                'apresentacao@maosnaobra.com',
                'gestor.operacional@maosnaobra.com',
                'cliente.atlas@maosnaobra.com',
                'cliente.horizonte@maosnaobra.com',
                'cliente.litoral@maosnaobra.com',
                'cliente.aurora@maosnaobra.com',
                'cliente.delta@maosnaobra.com',
                'cliente.porto@maosnaobra.com',
                'cliente.industrial@maosnaobra.com',
            ]).count(),
            'Clientes': Customer.objects.filter(name__in=[
                'Residencial Atlas LTDA',
                'Grupo Horizonte Engenharia',
                'Incorporadora Litoral SA',
                'Construtora Aurora Participações',
                'Shopping Delta Empreendimentos',
                'Residencial Porto Azul SPE',
                'Complexo Industrial Norte Ltda',
            ]).count(),
            'Fornecedores': Supplier.objects.filter(legal_name__in=[
                'ConcreMax Distribuidora LTDA',
                'Acabamentos Pro Comércio Ltda',
                'Serra Serviços Técnicos ME',
                'Fornecedor Reserva Sem Email',
                'Prime Elétrica LTDA',
                'Madeireira São Paulo Comércio LTDA',
                'HidraTech Materiais Hidráulicos LTDA',
                'Acústica Pro Soluções Ltda',
                'Metais Urbanos Comércio LTDA',
                'Estrutura Forte Industrial LTDA',
            ]).count(),
            'Obras': Project.objects.filter(name__in=[
                'Residencial Atlas - Torre A',
                'Clínica Horizonte - Reforma',
                'Escritório Mão na Obra - Ampliação',
                'Condomínio Litoral - Bloco B',
                'Residencial Aurora - Fase 1',
                'Shopping Delta - Retrofit',
                'Residencial Porto Azul - Torre 2',
                'Complexo Industrial Norte - Expansão',
            ]).count(),
            'Solicitações de compra': PurchaseRequest.objects.filter(title__in=[
                'Solicitação de compra - Torre A, lote estrutural',
                'Solicitação de compra - Clínica Horizonte',
                'Solicitação de compra - Aurora Fase 1',
            ]).count(),
            'Contas a pagar': AccountPayable.objects.filter(title__in=[
                'Conta a pagar - OC - Cotação estrutural - Atlas',
                'Pagamento pendente - louças e metais',
                'Conta a pagar - OC - Cotação executiva - Aurora',
            ]).count(),
            'Contas a receber': AccountReceivable.objects.filter(title__in=[
                'Medição administrativa - abril',
                'Taxa por avanço físico - Atlas',
                'Faturamento por medição - Clínica Horizonte',
                'Medição executiva - Aurora',
            ]).count(),
            'Movimentações financeiras': FinancialTransaction.objects.filter(description__in=[
                'Entrada contratual inicial',
                'Saída operacional de canteiro',
                'Recebimento por medição clínica',
                'Conta a pagar - OC - Cotação estrutural - Atlas',
                'Medição administrativa - abril',
                'Entrada contratual Aurora',
                'Saída operacional Aurora',
                'Entrada contratual Delta',
                'Saída operacional Delta',
                'Entrada contratual Porto Azul',
                'Saída operacional Porto Azul',
                'Entrada contratual Industrial Norte',
                'Saída operacional Industrial Norte',
            ]).count(),
        }
        return summary

    def ensure_user(self, *, email, name, password, is_staff=False, is_superuser=False):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'name': name,
                'is_active': True,
                'is_staff': is_staff,
                'is_superuser': is_superuser,
            },
        )
        updated = False
        if user.name != name:
            user.name = name
            updated = True
        if user.is_active is not True:
            user.is_active = True
            updated = True
        if user.is_staff != is_staff:
            user.is_staff = is_staff
            updated = True
        if user.is_superuser != is_superuser:
            user.is_superuser = is_superuser
            updated = True
        if created or updated or not user.check_password(password):
            user.set_password(password)
            updated = True
        if updated:
            user.save()
        return user

    def ensure_portal_access(self, customer, user):
        ClientPortalAccess.objects.get_or_create(
            customer=customer,
            user=user,
            defaults={'is_active': True, 'notes': 'Acesso liberado para apresentação.'},
        )

    def ensure_customer(self, *, name, document_number, email, phone, address, status='active'):
        customer, created = Customer.objects.get_or_create(
            name=name,
            defaults={
                'person_type': 'J',
                'document_number': document_number,
                'email': email,
                'phone': phone,
                'address': address,
                'status': status,
            },
        )
        changed = False
        fields = {
            'person_type': 'J',
            'document_number': document_number,
            'email': email,
            'phone': phone,
            'address': address,
            'status': status,
        }
        for field, value in fields.items():
            if getattr(customer, field) != value:
                setattr(customer, field, value)
                changed = True
        if created or changed:
            customer.save()
        return customer

    def ensure_supplier(self, *, legal_name, trade_name=None, email=None, categories=None, status='active', notes=''):
        supplier, created = Supplier.objects.get_or_create(
            legal_name=legal_name,
            defaults={
                'trade_name': trade_name,
                'document_number': None,
                'email': email,
                'phone': None,
                'address': None,
                'status': status,
                'notes': notes,
            },
        )
        changed = False
        fields = {
            'trade_name': trade_name,
            'email': email,
            'status': status,
            'notes': notes,
        }
        for field, value in fields.items():
            if getattr(supplier, field) != value:
                setattr(supplier, field, value)
                changed = True
        if created or changed:
            supplier.save()
        if categories is not None:
            supplier.categories.set(categories)
        return supplier

    def ensure_project(self, *, name, customer, responsible, address, expected_start_date, expected_end_date, expected_value, description, status='active'):
        project, created = Project.objects.get_or_create(
            name=name,
            defaults={
                'customer': customer,
                'responsible': responsible,
                'address': address,
                'expected_start_date': expected_start_date,
                'expected_end_date': expected_end_date,
                'expected_value': expected_value,
                'description': description,
                'status': status,
            },
        )
        changed = False
        fields = {
            'customer': customer,
            'responsible': responsible,
            'address': address,
            'expected_start_date': expected_start_date,
            'expected_end_date': expected_end_date,
            'expected_value': expected_value,
            'description': description,
            'status': status,
        }
        for field, value in fields.items():
            if getattr(project, field) != value:
                setattr(project, field, value)
                changed = True
        if created or changed:
            project.save()
        return project

    def ensure_customer_assets(self, customer, project):
        document, created = CustomerDocument.objects.get_or_create(
            customer=customer,
            title=f'Dossiê comercial - {customer.name}',
            defaults={'visible_in_portal': True},
        )
        if created or not document.file:
            document.file.save(
                f'dossie-{customer.pk}.txt',
                ContentFile(
                    (
                        f'Dossiê comercial de {customer.name}\n'
                        f'Obra vinculada: {project.name}\n'
                        'Informações de apresentação e histórico operacional.'
                    ).encode('utf-8')
                ),
                save=True,
            )
        elif document.visible_in_portal is not True:
            document.visible_in_portal = True
            document.save(update_fields=['visible_in_portal', 'updated_at'])

        photo, created = CustomerPhoto.objects.get_or_create(
            customer=customer,
            title=f'Foto institucional - {customer.name}',
            defaults={'visible_in_portal': True},
        )
        if created or not photo.image:
            photo.image.save(
                f'foto-{customer.pk}.jpg',
                ContentFile(self.build_demo_image_bytes(customer.name, project.name)),
                save=True,
            )
        elif photo.visible_in_portal is not True:
            photo.visible_in_portal = True
            photo.save(update_fields=['visible_in_portal', 'updated_at'])

    def build_demo_image_bytes(self, customer_name, project_name):
        image = Image.new('RGB', (1280, 720), color='#183153')
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 470, 1280, 720), fill='#f59e0b')
        draw.rectangle((70, 90, 1210, 600), outline='#ffffff', width=8)
        draw.text((110, 160), 'Mao na Obra', fill='white')
        draw.text((110, 240), customer_name, fill='white')
        draw.text((110, 310), project_name, fill='white')
        draw.text((110, 400), 'Imagem gerada para apresentacao comercial.', fill='white')
        buffer = BytesIO()
        image.save(buffer, format='JPEG', quality=88)
        return buffer.getvalue()

    def ensure_project_task(self, project, name, planned_start_date, planned_end_date, planned_percentage, planned_cost):
        task, created = ProjectTask.objects.get_or_create(
            project=project,
            name=name,
            defaults={
                'planned_start_date': planned_start_date,
                'planned_end_date': planned_end_date,
                'planned_percentage': planned_percentage,
                'planned_cost': planned_cost,
                'description': f'{name} - etapa de apresentação.',
            },
        )
        changed = False
        fields = {
            'planned_start_date': planned_start_date,
            'planned_end_date': planned_end_date,
            'planned_percentage': planned_percentage,
            'planned_cost': planned_cost,
            'description': f'{name} - etapa de apresentação.',
        }
        for field, value in fields.items():
            if getattr(task, field) != value:
                setattr(task, field, value)
                changed = True
        if created or changed:
            task.save()
        return task

    def ensure_daily_log(self, project, **kwargs):
        log, created = DailyLog.objects.get_or_create(project=project, log_date=kwargs['log_date'], defaults=kwargs)
        changed = False
        for field, value in kwargs.items():
            if getattr(log, field) != value:
                setattr(log, field, value)
                changed = True
        if created or changed:
            log.save()
        return log

    def ensure_physical_measurement(
        self,
        project,
        task,
        measurement_date,
        measured_percentage,
        measured_value,
        visible_in_portal,
        notes,
    ):
        measurement, created = PhysicalMeasurement.objects.get_or_create(
            project=project,
            task=task,
            measurement_date=measurement_date,
            defaults={
                'measured_percentage': measured_percentage,
                'measured_value': measured_value,
                'visible_in_portal': visible_in_portal,
                'notes': notes,
            },
        )
        changed = False
        for field, value in {
            'measured_percentage': measured_percentage,
            'measured_value': measured_value,
            'visible_in_portal': visible_in_portal,
            'notes': notes,
        }.items():
            if getattr(measurement, field) != value:
                setattr(measurement, field, value)
                changed = True
        if created or changed:
            measurement.save()
        return measurement

    def ensure_input_item(self, name, unit, unit_cost, description):
        item, created = InputItem.objects.get_or_create(
            name=name,
            defaults={
                'unit': unit,
                'unit_cost': unit_cost,
                'description': description,
                'is_active': True,
            },
        )
        changed = False
        fields = {
            'unit': unit,
            'unit_cost': unit_cost,
            'description': description,
            'is_active': True,
        }
        for field, value in fields.items():
            if getattr(item, field) != value:
                setattr(item, field, value)
                changed = True
        if created or changed:
            item.save()
        return item

    def ensure_budget(self, project, **kwargs):
        budget, created = Budget.objects.get_or_create(project=project, name=kwargs['name'], defaults=kwargs)
        changed = False
        for field, value in kwargs.items():
            if getattr(budget, field) != value:
                setattr(budget, field, value)
                changed = True
        if created or changed:
            budget.save()
        return budget

    def ensure_budget_item(self, budget, name, unit, quantity, description):
        item, created = BudgetItem.objects.get_or_create(
            budget=budget,
            name=name,
            defaults={
                'unit': unit,
                'quantity': quantity,
                'description': description,
            },
        )
        changed = False
        fields = {
            'unit': unit,
            'quantity': quantity,
            'description': description,
        }
        for field, value in fields.items():
            if getattr(item, field) != value:
                setattr(item, field, value)
                changed = True
        if created or changed:
            item.save()
        return item

    def ensure_budget_composition_item(self, budget_item, input_item, unit, quantity, unit_cost):
        composition, created = BudgetCompositionItem.objects.get_or_create(
            budget_item=budget_item,
            input_item=input_item,
            defaults={
                'unit': unit,
                'quantity': quantity,
                'unit_cost': unit_cost,
            },
        )
        changed = False
        fields = {'unit': unit, 'quantity': quantity, 'unit_cost': unit_cost}
        for field, value in fields.items():
            if getattr(composition, field) != value:
                setattr(composition, field, value)
                changed = True
        if created or changed:
            composition.save()
        return composition

    def ensure_purchase_request(self, project, title, status, notes):
        request, created = PurchaseRequest.objects.get_or_create(
            project=project,
            title=title,
            defaults={'status': status, 'notes': notes},
        )
        changed = False
        for field, value in {'status': status, 'notes': notes}.items():
            if getattr(request, field) != value:
                setattr(request, field, value)
                changed = True
        if created or changed:
            request.save()
        return request

    def ensure_purchase_request_item(self, purchase_request, input_item, description, unit, quantity, notes):
        item, created = PurchaseRequestItem.objects.get_or_create(
            purchase_request=purchase_request,
            description=description,
            defaults={
                'input_item': input_item,
                'unit': unit,
                'quantity': quantity,
                'notes': notes,
            },
        )
        changed = False
        fields = {'input_item': input_item, 'unit': unit, 'quantity': quantity, 'notes': notes}
        for field, value in fields.items():
            if getattr(item, field) != value:
                setattr(item, field, value)
                changed = True
        if created or changed:
            item.save()
        return item

    def ensure_quotation(self, purchase_request, title, status, notes):
        quotation, created = Quotation.objects.get_or_create(
            purchase_request=purchase_request,
            title=title,
            defaults={'status': status, 'notes': notes},
        )
        changed = False
        for field, value in {'status': status, 'notes': notes}.items():
            if getattr(quotation, field) != value:
                setattr(quotation, field, value)
                changed = True
        if created or changed:
            quotation.save()
        return quotation

    def ensure_quotation_supplier(self, quotation, supplier, status, notes):
        quotation_supplier, created = QuotationSupplier.objects.get_or_create(
            quotation=quotation,
            supplier=supplier,
            defaults={'status': status, 'notes': notes},
        )
        changed = False
        for field, value in {'status': status, 'notes': notes}.items():
            if getattr(quotation_supplier, field) != value:
                setattr(quotation_supplier, field, value)
                changed = True
        if created or changed:
            quotation_supplier.save()
        return quotation_supplier

    def ensure_quotation_item_price(self, quotation_supplier, purchase_request_item, unit_price):
        price, created = QuotationItemPrice.objects.get_or_create(
            quotation_supplier=quotation_supplier,
            purchase_request_item=purchase_request_item,
            defaults={'unit_price': unit_price, 'notes': ''},
        )
        changed = False
        if price.unit_price != unit_price:
            price.unit_price = unit_price
            changed = True
        if created or changed:
            price.save()
        return price

    def ensure_purchase_order_from_quotation(self, quotation):
        order_title = f'OC - {quotation.title}'
        order, created = PurchaseOrder.objects.get_or_create(
            quotation=quotation,
            defaults={
                'purchase_request': quotation.purchase_request,
                'supplier': quotation.best_supplier.supplier,
                'title': order_title,
                'status': 'draft',
                'notes': 'Ordem gerada a partir da cotação vencedora.',
            },
        )
        changed = False
        fields = {
            'purchase_request': quotation.purchase_request,
            'supplier': quotation.best_supplier.supplier,
            'title': order_title,
            'notes': 'Ordem gerada a partir da cotação vencedora.',
        }
        for field, value in fields.items():
            if getattr(order, field) != value:
                setattr(order, field, value)
                changed = True
        if created or changed:
            order.save()

        for request_item in quotation.purchase_request.items.all():
            price = quotation.best_supplier.item_prices.filter(purchase_request_item=request_item).first()
            if price:
                poi, poi_created = PurchaseOrderItem.objects.get_or_create(
                    purchase_order=order,
                    purchase_request_item=request_item,
                    defaults={
                        'description': request_item.description,
                        'unit': request_item.unit,
                        'quantity': request_item.quantity,
                        'unit_price': price.unit_price,
                    },
                )
                poi_changed = False
                for field, value in {
                    'description': request_item.description,
                    'unit': request_item.unit,
                    'quantity': request_item.quantity,
                    'unit_price': price.unit_price,
                }.items():
                    if getattr(poi, field) != value:
                        setattr(poi, field, value)
                        poi_changed = True
                if poi_created or poi_changed:
                    poi.save()
        return order

    def ensure_account_payable(self, project, supplier, title, due_date, amount, source_label, notes):
        payable, created = AccountPayable.objects.get_or_create(
            project=project,
            supplier=supplier,
            title=title,
            defaults={
                'due_date': due_date,
                'amount': amount,
                'status': 'open',
                'source_label': source_label,
                'notes': notes,
            },
        )
        changed = False
        for field, value in {
            'due_date': due_date,
            'amount': amount,
            'source_label': source_label,
            'notes': notes,
        }.items():
            if getattr(payable, field) != value:
                setattr(payable, field, value)
                changed = True
        if created or changed:
            payable.save()
        return payable

    def ensure_account_receivable(self, project, customer, title, due_date, amount, billing_type, source_label, notes):
        receivable, created = AccountReceivable.objects.get_or_create(
            project=project,
            customer=customer,
            title=title,
            defaults={
                'due_date': due_date,
                'amount': amount,
                'billing_type': billing_type,
                'status': 'open',
                'source_label': source_label,
                'notes': notes,
            },
        )
        changed = False
        for field, value in {
            'due_date': due_date,
            'amount': amount,
            'billing_type': billing_type,
            'source_label': source_label,
            'notes': notes,
        }.items():
            if getattr(receivable, field) != value:
                setattr(receivable, field, value)
                changed = True
        if created or changed:
            receivable.save()
        return receivable

    def ensure_invoice_xml(self, project, access_key, issuer_name, total_amount):
        invoice, created = InvoiceXml.objects.get_or_create(
            project=project,
            access_key=access_key,
            defaults={'issuer_name': issuer_name, 'total_amount': total_amount},
        )
        changed = False
        for field, value in {'issuer_name': issuer_name, 'total_amount': total_amount}.items():
            if getattr(invoice, field) != value:
                setattr(invoice, field, value)
                changed = True
        if created or not invoice.xml_file:
            invoice.xml_file.save(
                f'nfe-{project.pk}.xml',
                ContentFile(self.build_invoice_xml(access_key, issuer_name, total_amount).encode('utf-8')),
                save=True,
            )
        elif changed:
            invoice.save()
        return invoice

    def build_invoice_xml(self, access_key, issuer_name, total_amount):
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<nfeProc>\n'
            f'  <NFe Id="NFe{access_key}">\n'
            '    <infNFe>\n'
            '      <emit>\n'
            f'        <xNome>{issuer_name}</xNome>\n'
            '      </emit>\n'
            '      <total>\n'
            '        <ICMSTot>\n'
            f'          <vNF>{total_amount}</vNF>\n'
            '        </ICMSTot>\n'
            '      </total>\n'
            '    </infNFe>\n'
            '  </NFe>\n'
            '</nfeProc>\n'
        )

    def ensure_appropriation(self, project, invoice, service_name, amount, percentage, notes):
        appropriation, created = FinancialAppropriation.objects.get_or_create(
            project=project,
            invoice_xml=invoice,
            service_name=service_name,
            defaults={'amount': amount, 'percentage': percentage, 'notes': notes},
        )
        changed = False
        for field, value in {'amount': amount, 'percentage': percentage, 'notes': notes}.items():
            if getattr(appropriation, field) != value:
                setattr(appropriation, field, value)
                changed = True
        if created or changed:
            appropriation.save()
        return appropriation

    def ensure_financial_transaction(self, project, transaction_type, transaction_date, amount, description, notes):
        transaction, created = FinancialTransaction.objects.get_or_create(
            project=project,
            transaction_type=transaction_type,
            transaction_date=transaction_date,
            amount=amount,
            description=description,
            defaults={'notes': notes},
        )
        changed = False
        if transaction.notes != notes:
            transaction.notes = notes
            changed = True
        if created or changed:
            transaction.save()
        return transaction
