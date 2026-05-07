from django.shortcuts import render
from django.views.decorators.cache import never_cache
from apps.agents.models import Agent, Scenario


# Pretty short labels for the heterogeneous model architecture
MODEL_LABELS = {
    'deepseek/deepseek-r1': 'DeepSeek R1',
    'deepseek/deepseek-v3.2': 'DeepSeek V3.2',
    'openai/gpt-4o-mini': 'GPT-4o mini',
    'qwen/qwen3-next-80b-a3b-instruct': 'Qwen3 80B',
    'qwen/qwen3-next-80b-a3b-instruct:free': 'Qwen3 80B',
    'anthropic/claude-sonnet-4.5': 'Claude Sonnet 4.5',
    'anthropic/claude-opus-4.7': 'Claude Opus 4.7',
}

MODEL_RATIONALES = {
    'analytics':    'نموذج استدلال متخصص للأرقام و حساب ROI',
    'operations':   'سريع ودقيق في تطبيق قواعد SLA',
    'customer':     'أقوى نموذج عربي — يتقن اللهجة السعودية',
    'queue':        'تخطيط استراتيجي إبداعي ومنظّم',
    'orchestrator': 'استدلال متقدم لاتخاذ القرار النهائي',
}


@never_cache
def index(request):
    agents = list(Agent.objects.filter(is_active=True).order_by('agent_type'))
    for a in agents:
        a.model_label = MODEL_LABELS.get(a.model_name, a.model_name.split('/')[-1])
        a.model_rationale = MODEL_RATIONALES.get(a.agent_type, '')
    scenarios = list(Scenario.objects.filter(is_active=True).order_by('scenario_id'))
    return render(request, 'dashboard/index.html', {
        'agents': agents,
        'scenarios': scenarios,
    })
