# requests_app/views.py
import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Request, RequestStatus
from .approvals_client import get_approvals_client
from .reporting_client import get_reporting_client
from .serializers import (
    RequestCreateSerializer,
    RequestDetailSerializer,
    RequestUpdateSerializer,
    AttachmentCreateSerializer,
)

logger = logging.getLogger(__name__)


class RequestViewSet(viewsets.GenericViewSet):
    """
    ViewSet для работы с заявками.
    Здесь:
    - POST /requests/             -> создать заявку
    - GET /requests/{id}/         -> получить заявку
    - PATCH /requests/{id}/       -> частично обновить (пока статус NEW)
    - POST /requests/{id}/attach/ -> привязать файл
    """

    queryset = Request.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return RequestCreateSerializer
        elif self.action in ("retrieve", "list"):
            return RequestDetailSerializer
        elif self.action == "partial_update":
            return RequestUpdateSerializer
        elif self.action == "attach":
            return AttachmentCreateSerializer
        return RequestDetailSerializer

    def create(self, request, *args, **kwargs):
        """
        Создание новой заявки (бот вызывает этот endpoint после того,
        как пользователь прошёл все шаги).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_obj = serializer.save()

        # Запускаем цепочку согласования
        try:
            approvals_client = get_approvals_client()
            summary = request_obj.build_summary_text()
            approvals_client.start_approval_chain_sync(request_obj.id, summary)
            # Обновляем статус заявки на "в согласовании"
            request_obj.status = RequestStatus.IN_PROGRESS
            request_obj.current_level = 1
            request_obj.save(update_fields=["status", "current_level"])
        except Exception as exc:
            logger.error(f"Failed to start approval chain for request {request_obj.id}: {exc}")

        # Отправляем в reporting_service (асинхронно, не блокируем ответ)
        try:
            reporting_client = get_reporting_client()
            reporting_client.report_request_sync(request_obj)
        except Exception as exc:
            logger.error(f"Failed to report request {request_obj.id} to reporting_service: {exc}")

        # Возвращаем подробную информацию для бота
        detail_data = RequestDetailSerializer(request_obj).data
        return Response(detail_data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        """
        Получить список заявок пользователя.
        Фильтрация по tg_user_id через параметр запроса.
        """
        tg_user_id = request.query_params.get("tg_user_id")
        queryset = self.queryset
        
        if tg_user_id:
            try:
                tg_user_id = int(tg_user_id)
                queryset = queryset.filter(tg_user_id=tg_user_id)
            except (ValueError, TypeError):
                return Response(
                    {"detail": "Неверный формат tg_user_id."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        """
        Получить заявку по ID.
        Можно использовать для проверки статуса или отображения истории.
        """
        request_obj = self.get_object()
        serializer = self.get_serializer(request_obj)
        return Response(serializer.data)

    def partial_update(self, request, pk=None, *args, **kwargs):
        """
        Обновление заявки автором до того, как она ушла на согласование.
        Позже добавим проверку "кто автор" и статус.
        """
        request_obj = self.get_object()

        if not request_obj.is_editable_by_author:
            return Response(
                {"detail": "Заявку нельзя редактировать после начала согласования."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(
            request_obj,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Обновляем отчет в reporting_service при изменении заявки
        try:
            reporting_client = get_reporting_client()
            reporting_client.report_request_sync(request_obj)
        except Exception as exc:
            logger.error(f"Failed to update report for request {request_obj.id}: {exc}")
        
        detail_data = RequestDetailSerializer(request_obj).data
        return Response(detail_data)

    @action(detail=True, methods=["post"], url_path="attach")
    def attach(self, request, pk=None, *args, **kwargs):
        """
        Привязать файл к заявке.
        Предполагается, что файл уже загружен файловым сервисом в облако,
        и сюда приходят только ссылки/пути.
        """
        request_obj = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        attachment = serializer.save(request=request_obj)
        return Response(
            {
                "detail": "Файл успешно привязан к заявке.",
                "attachment_id": attachment.id,
            },
            status=status.HTTP_201_CREATED,
        )
