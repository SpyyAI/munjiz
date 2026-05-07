from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import QueueSnapshot, SLAConfig
from .serializers import QueueSnapshotSerializer, SLAConfigSerializer
from .predictor import predict_next_hour


@api_view(['GET'])
def snapshot(request):
    snap = QueueSnapshot.objects.order_by('-timestamp').first()
    if not snap:
        return Response({'error': 'no snapshots yet'}, status=404)
    return Response(QueueSnapshotSerializer(snap).data)


@api_view(['GET'])
def predictions(request):
    snap = QueueSnapshot.objects.order_by('-timestamp').first()
    waiting = snap.total_waiting if snap else 20
    return Response(predict_next_hour(waiting))


@api_view(['GET'])
def sla(request):
    return Response(SLAConfigSerializer(SLAConfig.objects.all(), many=True).data)
