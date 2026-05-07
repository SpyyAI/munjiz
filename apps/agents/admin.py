from django.contrib import admin
from .models import Agent, AgentMessage, Scenario, Decision


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'agent_type', 'status', 'current_task', 'is_active')
    list_filter = ('agent_type', 'status')
    search_fields = ('name_ar', 'name_en')


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ('scenario_id', 'name_ar', 'scenario_type', 'is_recommended', 'use_ai', 'is_active')
    list_filter = ('scenario_type', 'is_recommended', 'use_ai')
    search_fields = ('scenario_id', 'name_ar')


@admin.register(AgentMessage)
class AgentMessageAdmin(admin.ModelAdmin):
    list_display = ('order', 'from_agent', 'message_type', 'priority', 'is_ai_generated', 'created_at')
    list_filter = ('message_type', 'priority', 'is_ai_generated', 'from_agent')
    search_fields = ('content',)
    raw_id_fields = ('scenario', 'from_agent', 'to_agent')


@admin.register(Decision)
class DecisionAdmin(admin.ModelAdmin):
    list_display = ('decision_text', 'authority_level', 'was_escalated', 'financial_impact_sar', 'created_at')
    list_filter = ('authority_level', 'was_escalated')
