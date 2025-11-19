from django.urls import path

from .views import CategoryTreeView, CategorySyncView

urlpatterns = [
    path("categories/tree", CategoryTreeView.as_view(), name="categories-tree"),
    path("categories/sync", CategorySyncView.as_view(), name="categories-sync"),
]

