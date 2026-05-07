"""Seed the Munjiz database with demo data.

Usage:
    python manage.py seed_data                # Insert all (errors if exists)
    python manage.py seed_data --skip-existing  # Idempotent
    python manage.py seed_data --reset         # Wipe + reseed
"""
import json
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.agents.models import Agent, Scenario
from apps.agents.prompts import get_agent_prompt
from apps.branch.models import Branch, Staff, Counter, Kiosk, DigitalScreen
from apps.customers.models import Customer
from apps.queue_system.models import SLAConfig, QueueSnapshot


FIXTURES = Path(settings.BASE_DIR) / 'fixtures'


class Command(BaseCommand):
    help = 'Seed the Munjiz database with demo data.'

    def add_arguments(self, parser):
        parser.add_argument('--skip-existing', action='store_true', help='Idempotent: skip rows that already exist.')
        parser.add_argument('--reset', action='store_true', help='Wipe seed tables before reseeding.')

    @transaction.atomic
    def handle(self, *args, **opts):
        skip = opts['skip_existing']
        if opts['reset']:
            self.stdout.write(self.style.WARNING('Wiping seed tables...'))
            QueueSnapshot.objects.all().delete()
            SLAConfig.objects.all().delete()
            DigitalScreen.objects.all().delete()
            Kiosk.objects.all().delete()
            Counter.objects.all().delete()
            Staff.objects.all().delete()
            Customer.objects.all().delete()
            Branch.objects.all().delete()
            Scenario.objects.all().delete()
            Agent.objects.all().delete()

        self.stdout.write(self.style.HTTP_INFO('Seeding agents...'))
        self._seed_agents(skip)

        self.stdout.write(self.style.HTTP_INFO('Seeding branch + counters + kiosks + screens + SLA...'))
        branch = self._seed_branch(skip)

        self.stdout.write(self.style.HTTP_INFO('Seeding staff...'))
        self._seed_staff(branch, skip)

        self.stdout.write(self.style.HTTP_INFO('Seeding customers...'))
        self._seed_customers(skip)

        self.stdout.write(self.style.HTTP_INFO('Seeding scenarios...'))
        self._seed_scenarios(skip)

        self.stdout.write(self.style.HTTP_INFO('Creating initial queue snapshot...'))
        self._seed_initial_snapshot(branch)

        self.stdout.write(self.style.SUCCESS('✅ Seed complete.'))

    def _seed_agents(self, skip):
        with open(FIXTURES / 'agents_data.json', encoding='utf-8') as f:
            agents = json.load(f)
        for a in agents:
            if skip and Agent.objects.filter(agent_type=a['agent_type']).exists():
                continue
            Agent.objects.update_or_create(
                agent_type=a['agent_type'],
                defaults={
                    'name_ar': a['name_ar'],
                    'name_en': a['name_en'],
                    'role_ar': a['role_ar'],
                    'color': a['color'],
                    'temperature': a['temperature'],
                    'system_prompt': get_agent_prompt(a['agent_type']),
                    'model_name': settings.LLM_MODEL_DEFAULT,
                    'status': 'idle',
                    'is_active': True,
                },
            )

    def _seed_branch(self, skip):
        with open(FIXTURES / 'branch_data.json', encoding='utf-8') as f:
            data = json.load(f)
        b = data['branch']
        branch, _ = Branch.objects.update_or_create(
            branch_id=b['branch_id'],
            defaults={
                'name_ar': b['name_ar'],
                'city': b['city'],
                'address': b['address'],
                'counters_total': b['counters_total'],
                'kiosks_total': b['kiosks_total'],
                'screens_total': b['screens_total'],
                'waiting_capacity': b['waiting_capacity'],
                'opening_time': datetime.strptime(b['opening_time'], '%H:%M').time(),
                'closing_time': datetime.strptime(b['closing_time'], '%H:%M').time(),
            },
        )
        for c in data['counters']:
            Counter.objects.update_or_create(
                branch=branch, number=c['number'],
                defaults={'counter_type': c['counter_type'], 'is_active': True},
            )
        for k in data['kiosks']:
            Kiosk.objects.update_or_create(
                branch=branch, kiosk_id=k['kiosk_id'],
                defaults={
                    'location_ar': k['location_ar'],
                    'status': k['status'],
                    'services_supported': k['services_supported'],
                    'usage_today': k['usage_today'],
                },
            )
        for s in data['screens']:
            DigitalScreen.objects.update_or_create(
                branch=branch, screen_id=s['screen_id'],
                defaults={
                    'location_ar': s['location_ar'],
                    'current_content': s['current_content'],
                    'content_options': s['content_options'],
                },
            )
        for sla in data['sla_configs']:
            SLAConfig.objects.update_or_create(
                branch=branch, segment=sla['segment'],
                defaults={
                    'max_wait_minutes': sla['max_wait_minutes'],
                    'penalty_sar': sla['penalty_sar'],
                    'satisfaction_target': sla['satisfaction_target'],
                },
            )
        return branch

    def _seed_staff(self, branch, skip):
        with open(FIXTURES / 'staff_data.json', encoding='utf-8') as f:
            staff_list = json.load(f)
        for s in staff_list:
            if skip and Staff.objects.filter(employee_id=s['employee_id']).exists():
                continue
            staff, _ = Staff.objects.update_or_create(
                employee_id=s['employee_id'],
                defaults={
                    'branch': branch,
                    'name_ar': s['name_ar'],
                    'role': s['role'],
                    'counter': s['counter'],
                    'status': s['status'],
                    'avg_service_time_min': s['avg_service_time_min'],
                    'performance_score': s['performance_score'],
                    'customers_served_today': s['customers_served_today'],
                    'experience_years': s['experience_years'],
                },
            )
            # Wire staff to their counter
            if s['counter']:
                Counter.objects.filter(branch=branch, number=s['counter']).update(assigned_staff=staff)

    def _seed_customers(self, skip):
        with open(FIXTURES / 'customer_data.json', encoding='utf-8') as f:
            customers = json.load(f)
        for c in customers:
            if skip and Customer.objects.filter(customer_id=c['customer_id']).exists():
                continue
            Customer.objects.update_or_create(
                customer_id=c['customer_id'],
                defaults={
                    'name_ar': c['name_ar'],
                    'alias': c['alias'],
                    'segment': c['segment'],
                    'phone': c['phone'],
                    'annual_value_sar': c['annual_value_sar'],
                    'avg_monthly_transactions': c['avg_monthly_transactions'],
                    'preferred_services': c['preferred_services'],
                    'visits_last_6m': c['visits_last_6m'],
                    'wait_tolerance_min': c['wait_tolerance_min'],
                    'satisfaction_score': c['satisfaction_score'],
                    'nps_score': c['nps_score'],
                    'churn_risk': c['churn_risk'],
                    'preferred_channel': c['preferred_channel'],
                    'customer_since': c['customer_since'],
                    'notes': c['notes'],
                },
            )

    def _seed_scenarios(self, skip):
        with open(FIXTURES / 'scenario_scripts.json', encoding='utf-8') as f:
            scenarios = json.load(f)
        for s in scenarios:
            if skip and Scenario.objects.filter(scenario_id=s['scenario_id']).exists():
                continue
            Scenario.objects.update_or_create(
                scenario_id=s['scenario_id'],
                defaults={
                    'name_ar': s['name_ar'],
                    'name_en': s['name_en'],
                    'scenario_type': s['scenario_type'],
                    'time': s['time'],
                    'description': s['description'],
                    'icon': s['icon'],
                    'is_recommended': s['is_recommended'],
                    'tension_level': s['tension_level'],
                    'use_ai': s.get('use_ai', True),
                    'is_active': True,
                },
            )

    def _seed_initial_snapshot(self, branch):
        with open(FIXTURES / 'branch_data.json', encoding='utf-8') as f:
            snap = json.load(f)['initial_snapshot']
        QueueSnapshot.objects.create(
            branch=branch,
            total_waiting=snap['total_waiting'],
            total_serving=snap['total_serving'],
            avg_wait_minutes=snap['avg_wait_minutes'],
            max_wait_minutes=snap['max_wait_minutes'],
            sla_compliance_percent=snap['sla_compliance_percent'],
            kiosk_usage_percent=snap['kiosk_usage_percent'],
            staff_utilization_percent=snap['staff_utilization_percent'],
        )
