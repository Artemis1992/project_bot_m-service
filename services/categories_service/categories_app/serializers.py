from rest_framework import serializers

from .models import Warehouse, Category, Subcategory


class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = (
            "slug",
            "name",
            "requires_comment",
            "is_custom_input",
        )


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubcategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ("slug", "name", "subcategories")


class WarehouseSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = Warehouse
        fields = ("slug", "name", "categories")

