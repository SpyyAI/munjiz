from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Branch, Staff, Counter, Kiosk, DigitalScreen
from .serializers import (
    BranchSerializer, StaffSerializer, CounterSerializer,
    KioskSerializer, DigitalScreenSerializer,
)


class BranchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer


class StaffViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer


class KioskViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Kiosk.objects.all()
    serializer_class = KioskSerializer


class CounterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Counter.objects.all()
    serializer_class = CounterSerializer


class ScreenViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DigitalScreen.objects.all()
    serializer_class = DigitalScreenSerializer


@api_view(['GET'])
def overview(request):
    """One-shot snapshot of branch + staff + kiosks for the dashboard."""
    branch = Branch.objects.first()
    if not branch:
        return Response({'error': 'no branch seeded'}, status=404)
    return Response({
        'branch': BranchSerializer(branch).data,
        'staff': StaffSerializer(branch.staff.all(), many=True).data,
        'kiosks': KioskSerializer(branch.kiosks.all(), many=True).data,
        'counters': CounterSerializer(branch.counters.all(), many=True).data,
        'screens': DigitalScreenSerializer(branch.screens.all(), many=True).data,
    })
