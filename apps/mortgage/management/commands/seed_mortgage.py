"""Seed demo applicants and refresh Agent rows for the mortgage credit-risk demo."""
from django.core.management.base import BaseCommand
from apps.agents.models import Agent
from apps.agents.prompts import PROMPTS
from apps.mortgage.models import Applicant


AGENT_CONFIG = {
    'analytics': {
        'name_ar': 'سارة',
        'name_en': 'Sara',
        'role_ar': 'الجدارة الائتمانية / SIMAH',
        'color': '#FF1744',
        'model_name': 'deepseek/deepseek-v3.2',
        'temperature': 0.3,
    },
    'operations': {
        'name_ar': 'فهد',
        'name_en': 'Fahad',
        'role_ar': 'الهوية والقانوني / SDAIA + employer',
        'color': '#FF6D00',
        'model_name': 'openai/gpt-4o-mini',
        'temperature': 0.3,
    },
    'customer': {
        'name_ar': 'خالد',
        'name_en': 'Khalid',
        'role_ar': 'قدرة العميل والدعم / ABD',
        'color': '#2979FF',
        'model_name': 'anthropic/claude-sonnet-4.5',
        'temperature': 0.4,
    },
    'queue': {
        'name_ar': 'نورة',
        'name_en': 'Nora',
        'role_ar': 'تقييم العقار / Sakani · البورصة العقارية',
        'color': '#AA00FF',
        'model_name': 'qwen/qwen3-next-80b-a3b-instruct',
        'temperature': 0.4,
    },
    'orchestrator': {
        'name_ar': 'المنسّق',
        'name_en': 'Orchestrator',
        'role_ar': 'التوصية النهائية',
        'color': '#00C853',
        'model_name': 'anthropic/claude-opus-4',
        'temperature': 0.2,
    },
}


APPLICANTS = [
    {
        'applicant_id': 'DEMO-A-001',
        'name_ar': 'سلمان عبدالعزيز القحطاني',
        'nationality': 'saudi',
        'age': 32,
        'monthly_salary_sar': 22000,
        'existing_monthly_obligations_sar': 1200,
        'employer_name': 'أرامكو السعودية',
        'employer_sector': 'semi_government',
        'employment_duration_months': 72,
        'notes': 'ملف منخفض المخاطر — مهندس بسجل وظيفي ثابت.',
    },
    {
        'applicant_id': 'DEMO-A-002',
        'name_ar': 'منيرة فهد الدوسري',
        'nationality': 'saudi',
        'age': 41,
        'monthly_salary_sar': 16500,
        'existing_monthly_obligations_sar': 4200,
        'employer_name': 'وزارة التعليم',
        'employer_sector': 'government',
        'employment_duration_months': 144,
        'notes': 'ملف متوسط — موظفة حكومية ولديها قرض شخصي قائم.',
    },
    {
        'applicant_id': 'DEMO-A-003',
        'name_ar': 'تركي ناصر الشمري',
        'nationality': 'saudi',
        'age': 36,
        'monthly_salary_sar': 14000,
        'existing_monthly_obligations_sar': 5800,
        'employer_name': 'مؤسسة فردية للتجارة',
        'employer_sector': 'self_employed',
        'employment_duration_months': 18,
        'notes': 'ملف حدّي — عمل حر بمدّة قصيرة و DBR قريب من حدّ ساما.',
    },
]


class Command(BaseCommand):
    help = "Seed mortgage demo applicants and refresh Agent rows."

    def handle(self, *args, **opts):
        for atype, cfg in AGENT_CONFIG.items():
            agent, created = Agent.objects.update_or_create(
                agent_type=atype,
                defaults={
                    **cfg,
                    'system_prompt': PROMPTS[atype],
                    'is_active': True,
                    'status': 'idle',
                    'current_task': '',
                },
            )
            self.stdout.write(
                f"  {'+' if created else '~'} agent {atype} → {agent.name_ar} ({cfg['model_name']})"
            )

        for a in APPLICANTS:
            applicant, created = Applicant.objects.update_or_create(
                applicant_id=a['applicant_id'],
                defaults=a,
            )
            self.stdout.write(
                f"  {'+' if created else '~'} applicant {applicant.applicant_id} · {applicant.name_ar}"
            )

        self.stdout.write(self.style.SUCCESS("Mortgage demo seed complete."))
