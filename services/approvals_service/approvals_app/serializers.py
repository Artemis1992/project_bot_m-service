from __future__ import annotations

from typing import List

from rest_framework import serializers

from .models import (
    ApprovalChain,
    ApprovalStep,
    DEFAULT_APPROVAL_FLOW,
    StepStatus,
)


class ApprovalStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalStep
        fields = (
            "id",
            "order",
            "approver_name",
            "approver_role",
            "telegram_username",
            "status",
            "comment",
            "acted_at",
        )


class ApprovalChainSerializer(serializers.ModelSerializer):
    steps = ApprovalStepSerializer(many=True, read_only=True)

    class Meta:
        model = ApprovalChain
        fields = (
            "id",
            "request_id",
            "summary",
            "status",
            "current_step_order",
            "steps",
            "created_at",
            "updated_at",
        )


class StartApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalChain
        fields = ("request_id", "summary")

    def create(self, validated_data):
        chain = ApprovalChain.objects.create(**validated_data)
        steps = [
            ApprovalStep(
                chain=chain,
                order=approver.order,
                approver_name=approver.name,
                approver_role=approver.role,
                telegram_username=approver.telegram_username or "",
            )
            for approver in DEFAULT_APPROVAL_FLOW
        ]
        ApprovalStep.objects.bulk_create(steps)
        return chain


class ApprovalActionSerializer(serializers.Serializer):
    actor_username = serializers.CharField(max_length=100, allow_blank=True)
    comment = serializers.CharField(required=False, allow_blank=True)

