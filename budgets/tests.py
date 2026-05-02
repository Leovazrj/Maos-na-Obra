from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from budgets.forms import BudgetCompositionItemForm, BudgetForm, BudgetItemForm, InputItemForm
from budgets.models import Budget, BudgetCompositionItem, BudgetItem, InputItem
from core.models import TimeStampedModel
from customers.models import Customer
from projects.models import Project


class BudgetModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='orcamentista@example.com',
            password='segura123',
            name='Orçamentista',
        )
        self.customer = Customer.objects.create(name='Cliente Orçamento')
        self.project = Project.objects.create(name='Obra Orçada', customer=self.customer, responsible=self.user)

    def test_budget_models_are_timestamped_and_calculate_totals(self):
        concrete = InputItem.objects.create(name='Concreto usinado', unit='m³', unit_cost=Decimal('450.00'))
        steel = InputItem.objects.create(name='Aço CA-50', unit='kg', unit_cost=Decimal('8.50'))
        budget = Budget.objects.create(
            project=self.project,
            name='Orçamento executivo',
            budget_type='sale',
            margin_percentage=Decimal('20.00'),
        )
        item = BudgetItem.objects.create(budget=budget, name='Fundação', unit='vb', quantity=Decimal('1.00'))
        BudgetCompositionItem.objects.create(
            budget_item=item,
            input_item=concrete,
            unit='m³',
            quantity=Decimal('10.00'),
            unit_cost=Decimal('450.00'),
        )
        BudgetCompositionItem.objects.create(
            budget_item=item,
            input_item=steel,
            unit='kg',
            quantity=Decimal('100.00'),
            unit_cost=Decimal('8.50'),
        )

        item.refresh_from_db()
        budget.refresh_from_db()

        self.assertIsInstance(concrete, TimeStampedModel)
        self.assertIsInstance(budget, TimeStampedModel)
        self.assertIsInstance(item, TimeStampedModel)
        self.assertEqual(item.cost_total, Decimal('5350.00'))
        self.assertEqual(item.sale_total, Decimal('6420.00'))
        self.assertEqual(budget.cost_total, Decimal('5350.00'))
        self.assertEqual(budget.sale_total, Decimal('6420.00'))

    def test_forms_expose_sprint_fields(self):
        self.assertIn('unit_cost', InputItemForm.base_fields)
        self.assertIn('project', BudgetForm.base_fields)
        self.assertIn('quantity', BudgetItemForm.base_fields)
        self.assertIn('input_item', BudgetCompositionItemForm.base_fields)


class BudgetViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='gestor@example.com',
            password='segura123',
            name='Gestor',
        )
        self.customer = Customer.objects.create(name='Cliente Vista')
        self.project = Project.objects.create(name='Casa Vista', customer=self.customer, responsible=self.user)
        self.client.force_login(self.user)
        self.input_item = InputItem.objects.create(name='Cimento CP II', unit='sc', unit_cost=Decimal('38.00'))
        self.budget = Budget.objects.create(project=self.project, name='Orçamento inicial', budget_type='cost')
        self.budget_item = BudgetItem.objects.create(
            budget=self.budget,
            name='Alvenaria',
            unit='m²',
            quantity=Decimal('20.00'),
        )
        BudgetCompositionItem.objects.create(
            budget_item=self.budget_item,
            input_item=self.input_item,
            unit='sc',
            quantity=Decimal('5.00'),
            unit_cost=Decimal('38.00'),
        )
        self.budget_item.refresh_from_db()
        self.budget.refresh_from_db()

    def test_input_item_list_is_available(self):
        response = self.client.get(reverse('budgets:input_item_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cimento CP II')
        self.assertContains(response, 'Novo Insumo')

    def test_budget_detail_shows_items_composition_and_totals(self):
        response = self.client.get(reverse('budgets:detail', args=[self.budget.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Orçamento inicial')
        self.assertContains(response, 'Alvenaria')
        self.assertContains(response, 'Cimento CP II')
        self.assertContains(response, 'Total de custo')
        self.assertContains(response, '190,00')

    def test_add_composition_recalculates_item_and_budget(self):
        sand = InputItem.objects.create(name='Areia média', unit='m³', unit_cost=Decimal('120.00'))

        response = self.client.post(reverse('budgets:composition_create', args=[self.budget.pk, self.budget_item.pk]), {
            'input_item': sand.pk,
            'unit': 'm³',
            'quantity': '2.00',
            'unit_cost': '120.00',
        })

        self.assertRedirects(response, reverse('budgets:detail', args=[self.budget.pk]))
        self.budget_item.refresh_from_db()
        self.budget.refresh_from_db()
        self.assertEqual(self.budget_item.cost_total, Decimal('430.00'))
        self.assertEqual(self.budget.cost_total, Decimal('430.00'))

    def test_remove_composition_recalculates_item_and_budget(self):
        composition = self.budget_item.composition_items.first()

        response = self.client.post(reverse('budgets:composition_delete', args=[self.budget.pk, self.budget_item.pk, composition.pk]))

        self.assertRedirects(response, reverse('budgets:detail', args=[self.budget.pk]))
        self.budget_item.refresh_from_db()
        self.budget.refresh_from_db()
        self.assertEqual(self.budget_item.cost_total, Decimal('0.00'))
        self.assertEqual(self.budget.cost_total, Decimal('0.00'))
