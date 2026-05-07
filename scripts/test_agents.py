"""Smoke test for the Munjiz agent pipeline.

Run inside the web container:
    docker-compose exec web python scripts/test_agents.py
"""
import os
import sys
import django

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.agents.models import Agent, Scenario, AgentMessage
from apps.agents.fallback import run_prescripted_scenario


def smoke_test():
    print('--- Munjiz smoke test ---')

    agents = Agent.objects.filter(is_active=True)
    print(f'Agents loaded: {agents.count()}')
    assert agents.count() == 5, f'Expected 5 agents, got {agents.count()}'

    scenarios = Scenario.objects.filter(is_active=True)
    print(f'Scenarios loaded: {scenarios.count()}')
    assert scenarios.count() == 7, f'Expected 7 scenarios, got {scenarios.count()}'

    target = scenarios.get(scenario_id='S-03')
    print(f'Running scripted playback of {target.scenario_id}: {target.name_ar}')

    before = AgentMessage.objects.filter(scenario=target).count()
    run_prescripted_scenario(target)
    after = AgentMessage.objects.filter(scenario=target).count()

    print(f'Messages before: {before}, after: {after}')
    assert after > before, 'Expected new messages to be created'

    print('✅ Smoke test passed.')


if __name__ == '__main__':
    smoke_test()
