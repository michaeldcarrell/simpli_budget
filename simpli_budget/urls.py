from django.contrib import admin
from django.urls import path, include
from simpli_budget import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", views.Index.as_view(), name="index"),
    path("categories", views.Categories.as_view(), name="categories"),
    path("categories/<str:category_id>", views.Category.as_view(), name="category"),
    path("transaction/<str:transaction_id>", views.Transaction.as_view(), name="transaction"),
    path("budget/category/<int:category_id>", views.BudgetCategory.as_view(), name="budget"),
    path("logout", views.Logout.as_view(), name="logout"),
]
