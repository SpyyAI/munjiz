from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Agent, Scenario, AgentMessage
from .serializers import AgentSerializer, ScenarioSerializer, AgentMessageSerializer
from .tasks import run_scenario_task, run_scenario_with_custom_data_task


class AgentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Agent.objects.filter(is_active=True)
    serializer_class = AgentSerializer
    lookup_field = 'agent_type'


class ScenarioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Scenario.objects.filter(is_active=True)
    serializer_class = ScenarioSerializer
    lookup_field = 'scenario_id'

    @action(detail=True, methods=['post'])
    def trigger(self, request, scenario_id=None):
        scenario = self.get_object()
        custom_data = request.data.get('custom_data')
        if custom_data:
            run_scenario_with_custom_data_task.delay(scenario.scenario_id, custom_data)
        else:
            run_scenario_task.delay(scenario.scenario_id)
        return Response(
            {'status': 'queued', 'scenario_id': scenario.scenario_id},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=['get'])
    def messages(self, request, scenario_id=None):
        scenario = self.get_object()
        msgs = AgentMessage.objects.filter(scenario=scenario).select_related('from_agent')
        return Response(AgentMessageSerializer(msgs, many=True).data)
