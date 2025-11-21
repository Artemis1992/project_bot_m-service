from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Warehouse
from .serializers import WarehouseSerializer
from .sheets_sync import CategoriesSheetSync


class CategoryTreeView(APIView):
    """
    Возвращает актуальную структуру расходов:
    Склад -> Категории -> Подкатегории.
    """

    def get(self, request, *args, **kwargs):
        queryset = Warehouse.objects.prefetch_related(
            "categories__subcategories"
        ).all()
        serializer = WarehouseSerializer(queryset, many=True)
        return Response(serializer.data)


class CategorySyncView(APIView):
    """
    Заглушка под синхронизацию с Google Sheets.
    В дальнейшем здесь будет логика загрузки данных и обновления БД.
    """

    def post(self, request, *args, **kwargs):
        # Use unified config
        sync = CategoriesSheetSync()  # Uses config/google_sheets.py
        if not sync.spreadsheet_key:
            return Response(
                {
                    "detail": "GOOGLE_SHEET_ID is not configured; sync skipped.",
                },
                status=status.HTTP_202_ACCEPTED,
            )
        result = sync.sync()
        return Response(
            {"detail": "Синхронизация выполнена.", **result},
            status=status.HTTP_200_OK,
        )
