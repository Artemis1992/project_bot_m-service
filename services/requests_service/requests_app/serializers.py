# requests_app/serializers.py
from rest_framework import serializers

from .choices import RequestStatus
from .models import Request, Attachment


class AttachmentSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения файла в составе заявки."""

    class Meta:
        model = Attachment
        fields = ("id", "file_url", "storage_path", "file_name", "created_at")


class RequestCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания заявки из бота.

    Здесь мы принимаем сырые данные:
    - tg_user_id, author_username, author_full_name
    - warehouse, category, subcategory, subsubcategory
    - extra_value, goal, item_name, quantity
    - amount, comment
    """

    class Meta:
        model = Request
        fields = (
            "tg_user_id",
            "author_username",
            "author_full_name",
            "warehouse",
            "category",
            "subcategory",
            "subsubcategory",
            "extra_value",
            "goal",
            "item_name",
            "quantity",
            "amount",
            "comment",
        )

    def validate_amount(self, value):
        """Проверяем, что сумма > 0."""
        if value <= 0:
            raise serializers.ValidationError("Сумма должна быть больше нуля.")
        return value

    def create(self, validated_data):
        """
        На этапе создания статус всегда 'new', current_level = 0.
        Всё остальное — из validated_data.
        """
        request_obj = Request.objects.create(**validated_data)
        return request_obj


class RequestDetailSerializer(serializers.ModelSerializer):
    """
    Подробный сериализатор для чтения заявки.
    Используется для:
    - отображения после создания
    - получения состояния заявки
    """

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    summary_text = serializers.SerializerMethodField()
    attachments = AttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Request
        fields = (
            "id",
            "tg_user_id",
            "author_username",
            "author_full_name",
            "warehouse",
            "category",
            "subcategory",
            "subsubcategory",
            "extra_value",
            "goal",
            "item_name",
            "quantity",
            "amount",
            "comment",
            "status",
            "status_display",
            "current_level",
            "google_row_id",
            "created_at",
            "updated_at",
            "summary_text",
            "attachments",
        )

    def get_summary_text(self, obj: Request) -> str:
        """Готовый текст для Telegram (подтверждение/показ пользователю)."""
        return obj.build_summary_text()


class RequestUpdateSerializer(serializers.ModelSerializer):
    """
    Обновление заявки автором до старта согласования.
    Логика проверки (можно ли редактировать) будет во view.
    """

    class Meta:
        model = Request
        fields = (
            "goal",
            "item_name",
            "quantity",
            "amount",
            "comment",
            "extra_value",
        )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Сумма должна быть больше нуля.")
        return value


class AttachmentCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для привязки файла к заявке после загрузки в файловый сервис.
    """

    class Meta:
        model = Attachment
        fields = ("file_url", "storage_path", "file_name")
