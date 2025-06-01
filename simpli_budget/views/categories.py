from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View


class Categories(LoginRequiredMixin, View):
    def get(self, request):
        context = {
            "title": "Categories",
        }
        return render(request, template_name="categories/index.html", context=context)


class Category(LoginRequiredMixin, View):
    def get(self, request):
        context = {
            "title": "Category",
        }
        return render(request, template_name="transaction/index.html", context=context)