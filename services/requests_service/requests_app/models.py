# requests_app/models.py
from django.db import models

from .choices import RequestStatus


class Request(models.Model):
    """
    Заявка / служебка на закуп.
    Здесь мы храним базовую информацию без логики согласования.
    """

    tg_user_id = models.BigIntegerField(
        help_text="Telegram ID автора заявки (user.id)"
    )
    author_username = models.CharField(
        max_length=150,
        blank=True,
        help_text="Telegram username автора (@username), если есть",
    )
    author_full_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Отображаемое имя автора в Telegram",
    )

    # Логика складов / категорий:
    warehouse = models.CharField(
        max_length=50,
        help_text="Склад: например, 'Алматы' или 'Капчагай'",
    )
    category = models.CharField(
        max_length=100,
        help_text="Категория расходов: 'Авто', 'Аренда', ...",
    )
    subcategory = models.CharField(
        max_length=150,
        help_text="Подкатегория / статья расходов: 'Ремонт авто', 'ГСМ', ...",
    )
    subsubcategory = models.CharField(
        max_length=150,
        blank=True,
        help_text="Подподкатегория: 'Газели', '5 тонник', 'Фавы', 'Другое' и т.п.",
    )

    # Дополнительное поле (номер авто, что покупаем и для чего и т.д.)
    extra_value = models.CharField(
        max_length=255,
        blank=True,
        help_text="Доп. значение: номер авто, что и для чего приобретается и т.п.",
    )

    # Цель / что / количество — под будущие отчёты
    goal = models.CharField(
        max_length=255,
        blank=True,
        help_text="Цель закупа: 'Пополнение ГСМ', 'Оплата аренды' и т.п.",
    )
    item_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Что закупается: 'АЙ-92', 'услуги охраны', 'пакеты' и т.д.",
    )
    quantity = models.CharField(
        max_length=100,
        blank=True,
        help_text="Количество (можно хранить строкой: '1', '50 шт', 'по 3 шт' и т.п.)",
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="Сумма закупа",
    )

    comment = models.TextField(
        blank=True,
        help_text="Комментарий автора (может быть обязателен для некоторых статей)",
    )

    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.NEW,
        help_text="Текущий статус заявки",
    )

    current_level = models.PositiveSmallIntegerField(
        default=0,
        help_text="Текущий уровень согласования (0 - ещё не отправлено на согласование)",
    )

    google_row_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Идентификатор строки в Google Sheets (если нужно)",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Дата и время создания заявки",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Дата и время последнего обновления заявки",
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"

    def __str__(self) -> str:
        return f"Request #{self.id} ({self.warehouse} / {self.category})"

    @property
    def is_editable_by_author(self) -> bool:
        """
        Логика: автор может редактировать/отменять заявку,
        только пока она в статусе NEW (ещё не ушла в согласование).
        """
        return self.status == RequestStatus.NEW

    def build_summary_text(self) -> str:
        """
        Человеческий текст заявки для отправки в Telegram.
        Это будет использоваться ботом на этапе подтверждения.
        """
        lines = [
            f"Служебка #{self.id}",
            f"Склад: {self.warehouse}",
            f"Категория: {self.category}",
        ]

        if self.subcategory:
            lines.append(f"Подкатегория: {self.subcategory}")

        if self.subsubcategory:
            lines.append(f"Статья: {self.subsubcategory}")

        if self.extra_value:
            lines.append(f"Дополнительно: {self.extra_value}")

        if self.goal:
            lines.append(f"Цель: {self.goal}")

        if self.item_name:
            lines.append(f"Что: {self.item_name}")

        if self.quantity:
            lines.append(f"Количество: {self.quantity}")

        lines.append(f"Сумма: {self.amount} тг")

        if self.comment:
            lines.append(f"Комментарий: {self.comment}")

        lines.append(f"Статус: {self.get_status_display()}")

        return "\n".join(lines)


class Attachment(models.Model):
    """
    Привязанный файл к заявке (ссылка на файл в облачном хранилище).
    """

    request = models.ForeignKey(
        Request,
        on_delete=models.CASCADE,
        related_name="attachments",
        help_text="Заявка, к которой относится файл",
    )
    file_url = models.URLField(
        help_text="Публичный или полу-публичный URL файла (Google Drive / S3 и т.п.)",
    )
    storage_path = models.CharField(
        max_length=255,
        help_text="Путь в хранилище: /Категория/Подкатегория/Год-Месяц/Файл_№ID.pdf",
    )
    file_name = models.CharField(
        max_length=255,
        help_text="Имя файла",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Когда файл был загружен",
    )

    class Meta:
        verbose_name = "Файл заявки"
        verbose_name_plural = "Файлы заявок"

    def __str__(self) -> str:
        return f"Файл {self.file_name} для заявки #{self.request_id}"


