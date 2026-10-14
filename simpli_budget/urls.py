from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from simpli_budget import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("api/", include("api.urls")),
    path("", views.Landing.as_view(), name="index"),
    path("budget", views.MonthBudget.as_view(), name="budget"),
    path("categories", views.Categories.as_view(), name="categories"),
    path("categories/<str:category_id>", views.Category.as_view(), name="category"),
    path(
        "transaction/<str:transaction_id>",
        views.Transaction.as_view(),
        name="transaction",
    ),
    path(
      "transactions/search",
        views.TransactionSearch.as_view(),
        name="transaction_search"
    ),
    path(
        "budget/category/<int:category_id>",
        views.BudgetCategory.as_view(),
        name="budget",
    ),
    path("accounts", views.AccountsView.as_view(), name="accounts"),
    path("accounts/<str:account_id>", views.Account.as_view(), name="account"),
    path("rules", views.Rules.as_view(), name="rules"),
    path("rules/<int:rule_set_id>", views.RuleView.as_view(), name="rule"),
    path("tags", views.Tags.as_view(), name="tags"),
    path("notifications", views.Notifications.as_view(), name="notifications"),
    path("settings", RedirectView.as_view(url="/notifications")),  # old name, kept for bookmarks
    path("logout", views.Logout.as_view(), name="logout"),
    path("demo", views.Demo.as_view(), name="demo"),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
