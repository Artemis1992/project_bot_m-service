from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ApprovalChain, StepStatus
from .serializers import (
    ApprovalActionSerializer,
    ApprovalChainSerializer,
    StartApprovalSerializer,
)


class ApprovalChainViewSet(viewsets.GenericViewSet):
    queryset = ApprovalChain.objects.prefetch_related("steps")
    serializer_class = ApprovalChainSerializer
    lookup_field = "request_id"

    def retrieve(self, request, *args, **kwargs):
        chain = self.get_object()
        serializer = self.get_serializer(chain)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="start")
    def start_flow(self, request, *args, **kwargs):
        serializer = StartApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        chain = serializer.save()
        return Response(
            ApprovalChainSerializer(chain).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, *args, **kwargs):
        chain = self.get_object()
        action_serializer = ApprovalActionSerializer(data=request.data)
        action_serializer.is_valid(raise_exception=True)
        current_step = chain.steps.filter(order=chain.current_step_order).first()
        if not current_step:
            return Response(
                {"detail": "Текущий шаг не найден."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if current_step.status != StepStatus.WAITING:
            return Response(
                {"detail": "Этот шаг уже обработан."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        chain.mark_approved(current_step)
        return Response(ApprovalChainSerializer(chain).data)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, *args, **kwargs):
        chain = self.get_object()
        action_serializer = ApprovalActionSerializer(data=request.data)
        action_serializer.is_valid(raise_exception=True)
        current_step = chain.steps.filter(order=chain.current_step_order).first()
        if not current_step:
            return Response(
                {"detail": "Текущий шаг не найден."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if current_step.status != StepStatus.WAITING:
            return Response(
                {"detail": "Этот шаг уже обработан."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        chain.mark_rejected(
            current_step,
            comment=action_serializer.validated_data.get("comment"),
        )
        return Response(ApprovalChainSerializer(chain).data)

