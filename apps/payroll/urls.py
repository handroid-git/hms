from django.urls import path
from .views import (
    payroll_dashboard,
    payroll_detail,
    payroll_generate,
    payroll_list,
    salary_structure_create,
    salary_structure_list,
    salary_structure_update,
)

urlpatterns = [
    path("dashboard/", payroll_dashboard, name="payroll_dashboard"),
    path("", payroll_list, name="payroll_list"),
    path("generate/", payroll_generate, name="payroll_generate"),
    path("<uuid:pk>/", payroll_detail, name="payroll_detail"),
    path("salary-structures/", salary_structure_list, name="salary_structure_list"),
    path("salary-structures/create/", salary_structure_create, name="salary_structure_create"),
    path("salary-structures/<uuid:pk>/update/", salary_structure_update, name="salary_structure_update"),
]