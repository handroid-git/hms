from django.urls import path

from .views import (
    clinical_workflow_report,
    export_clinical_workflow_report_pdf,
    export_clinical_workflow_report_xlsx,
    export_financial_report_pdf,
    export_financial_report_xlsx,
    export_lab_pharmacy_report_pdf,
    export_lab_pharmacy_report_xlsx,
    export_staff_performance_report_pdf,
    export_staff_performance_report_xlsx,
    financial_report,
    lab_pharmacy_report,
    reports_home,
    staff_performance_report,
)

urlpatterns = [
    path("", reports_home, name="reports_home"),
    path("financial/", financial_report, name="financial_report"),
    path("financial/export/xlsx/", export_financial_report_xlsx, name="export_financial_report_xlsx"),
    path("financial/export/pdf/", export_financial_report_pdf, name="export_financial_report_pdf"),

    path("clinical-workflow/", clinical_workflow_report, name="clinical_workflow_report"),
    path(
        "clinical-workflow/export/xlsx/",
        export_clinical_workflow_report_xlsx,
        name="export_clinical_workflow_report_xlsx",
    ),
    path(
        "clinical-workflow/export/pdf/",
        export_clinical_workflow_report_pdf,
        name="export_clinical_workflow_report_pdf",
    ),

    path("lab-pharmacy/", lab_pharmacy_report, name="lab_pharmacy_report"),
    path("lab-pharmacy/export/xlsx/", export_lab_pharmacy_report_xlsx, name="export_lab_pharmacy_report_xlsx"),
    path("lab-pharmacy/export/pdf/", export_lab_pharmacy_report_pdf, name="export_lab_pharmacy_report_pdf"),

    path("staff-performance/", staff_performance_report, name="staff_performance_report"),
    path(
        "staff-performance/export/xlsx/",
        export_staff_performance_report_xlsx,
        name="export_staff_performance_report_xlsx",
    ),
    path(
        "staff-performance/export/pdf/",
        export_staff_performance_report_pdf,
        name="export_staff_performance_report_pdf",
    ),
]