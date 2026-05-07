from rest_framework import serializers
from .models import Agent, Scenario, AgentMessage, Decision


class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = ['id', 'agent_type', 'name_ar', 'name_en', 'role_ar', 'color',
                  'status', 'current_task', 'model_name', 'temperature', 'is_active']


class ScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields = ['id', 'scenario_id', 'name_ar', 'name_en', 'scenario_type', 'time',
                  'description', 'icon', 'is_recommended', 'tension_level', 'use_ai', 'is_active']


class AgentMessageSerializer(serializers.ModelSerializer):
    from_name = serializers.CharField(source='from_agent.name_ar', read_only=True)
    from_color = serializers.CharField(source='from_agent.color', read_only=True)
    from_type = serializers.CharField(source='from_agent.agent_type', read_only=True)

    class Meta:
        model = AgentMessage
        fields = ['id', 'order', 'from_type', 'from_name', 'from_color', 'content',
                  'message_type', 'priority', 'is_ai_generated', 'delay_ms', 'created_at']


class DecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Decision
        fields = ['id', 'decision_text', 'reasoning', 'authority_level',
                  'was_escalated', 'financial_impact_sar', 'created_at']
