from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import TimeStampedModel
from customers.models import Customer
from projects.forms import DailyLogForm, PhysicalMeasurementForm, ProjectForm, ProjectTaskForm
from projects.models import DailyLog, PhysicalMeasurement, Project, ProjectTask


class ProjectModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='responsavel@example.com',
            password='segura123',
            name='Responsável Técnico',
        )
        self.customer = Customer.objects.create(name='Cliente Obra', email='cliente@example.com')

    def test_project_is_timestamped_and_linked_to_customer_and_responsible(self):
        project = Project.objects.create(
            name='Residência Jardim',
            customer=self.customer,
            responsible=self.user,
            address='Rua das Obras, 10',
            expected_start_date=date(2026, 5, 10),
            expected_end_date=date(2026, 8, 10),
            expected_value=Decimal('150000.00'),
        )

        self.assertIsInstance(project, TimeStampedModel)
        self.assertEqual(str(project), 'Residência Jardim')
        self.assertEqual(project.customer, self.customer)
        self.assertEqual(project.responsible, self.user)

    def test_project_physical_progress_uses_weighted_latest_measurements(self):
        project = Project.objects.create(name='Obra com medição', customer=self.customer, responsible=self.user)
        structure = ProjectTask.objects.create(
            project=project,
            name='Estrutura',
            planned_start_date=date(2026, 5, 1),
            planned_end_date=date(2026, 5, 30),
            planned_percentage=Decimal('60.00'),
            planned_cost=Decimal('60000.00'),
        )
        finishes = ProjectTask.objects.create(
            project=project,
            name='Acabamentos',
            planned_start_date=date(2026, 6, 1),
            planned_end_date=date(2026, 6, 30),
            planned_percentage=Decimal('40.00'),
            planned_cost=Decimal('40000.00'),
        )
        PhysicalMeasurement.objects.create(
            project=project,
            task=structure,
            measurement_date=date(2026, 5, 15),
            measured_percentage=Decimal('50.00'),
            measured_value=Decimal('30000.00'),
        )
        PhysicalMeasurement.objects.create(
            project=project,
            task=finishes,
            measurement_date=date(2026, 6, 15),
            measured_percentage=Decimal('25.00'),
            measured_value=Decimal('10000.00'),
        )

        self.assertEqual(project.physical_progress_percent, Decimal('40.00'))

    def test_forms_expose_sprint_fields(self):
        self.assertIn('customer', ProjectForm.base_fields)
        self.assertIn('weather', DailyLogForm.base_fields)
        self.assertIn('planned_percentage', ProjectTaskForm.base_fields)
        self.assertIn('visible_in_portal', PhysicalMeasurementForm.base_fields)


class ProjectViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='gestor@example.com',
            password='segura123',
            name='Gestor da Obra',
        )
        self.customer = Customer.objects.create(name='Cliente Vista', email='vista@example.com')
        self.client.force_login(self.user)
        self.project = Project.objects.create(
            name='Edifício Vista',
            customer=self.customer,
            responsible=self.user,
            address='Avenida Central, 500',
            status='active',
        )
        self.task = ProjectTask.objects.create(
            project=self.project,
            name='Fundação',
            planned_start_date=date(2026, 5, 1),
            planned_end_date=date(2026, 5, 20),
            planned_percentage=Decimal('100.00'),
            planned_cost=Decimal('25000.00'),
        )
        self.log = DailyLog.objects.create(
            project=self.project,
            log_date=date(2026, 5, 2),
            weather='Ensolarado',
            team_present='Equipe A',
            services_performed='Escavação',
            occurrences='Sem ocorrências',
            notes='Dia produtivo',
        )
        self.measurement = PhysicalMeasurement.objects.create(
            project=self.project,
            task=self.task,
            measurement_date=date(2026, 5, 3),
            measured_percentage=Decimal('20.00'),
            measured_value=Decimal('5000.00'),
            visible_in_portal=True,
        )

    def test_project_list_shows_active_projects(self):
        Project.objects.create(name='Obra encerrada', customer=self.customer, responsible=self.user, status='closed')

        response = self.client.get(reverse('projects:list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edifício Vista')
        self.assertNotContains(response, 'Obra encerrada')

    def test_project_detail_shows_daily_logs_tasks_measurements_and_gantt_data(self):
        response = self.client.get(reverse('projects:detail', args=[self.project.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Escavação')
        self.assertContains(response, 'Fundação')
        self.assertContains(response, '20,00%')
        self.assertContains(response, 'ganttData')
        self.assertContains(response, 'Avanço físico consolidado')

    def test_project_detail_uses_horizontal_action_row(self):
        response = self.client.get(reverse('projects:detail', args=[self.project.pk]))

        self.assertContains(response, 'app-action-row')
        self.assertContains(response, 'btn-light-brand')
        self.assertNotContains(response, 'btn-danger')

    def test_daily_log_filter_by_date(self):
        DailyLog.objects.create(
            project=self.project,
            log_date=date(2026, 5, 4),
            weather='Chuvoso',
            team_present='Equipe B',
            services_performed='Drenagem',
        )

        response = self.client.get(reverse('projects:detail', args=[self.project.pk]), {'log_date': '2026-05-04'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Drenagem')
        self.assertNotContains(response, 'Escavação')

    def test_close_action_changes_project_status(self):
        response = self.client.post(reverse('projects:close', args=[self.project.pk]))

        self.assertRedirects(response, reverse('projects:detail', args=[self.project.pk]))
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, 'closed')

    def test_project_create_view_persists_project_and_redirects(self):
        response = self.client.post(reverse('projects:create'), {
            'name': 'Condomínio Novo',
            'customer': self.customer.pk,
            'address': 'Rua Nova, 123',
            'expected_start_date': '2026-06-01',
            'expected_end_date': '2026-12-01',
            'status': 'active',
            'expected_value': '250000.00',
            'responsible': self.user.pk,
            'description': 'Projeto teste',
        })

        project = Project.objects.get(name='Condomínio Novo')
        self.assertRedirects(response, reverse('projects:list'))
        self.assertEqual(project.responsible, self.user)
