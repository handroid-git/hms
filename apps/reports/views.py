from decimal import Decimal
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render

from openpyxl import Workbook
from openpyxl.styles import Font

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.accounts.models import Role, User
from apps.admissions.models import Admission
from apps.billing.models import Billing, PaymentTransaction
from apps.consultations.models import Consultation
from apps.laboratory.models import (
    LabRequest,
    LabRequestItem,
    LabStockMovement,
    LabTest,
    LabTestRestock,
)
from apps.pharmacy.models import (
    Drug,
    DrugIssue,
    DrugRestock,
    DrugStockMovement,
    PrescriptionItem,
)
from apps.scheduling.models import Appointment
from apps.waiting_room.models import WaitingRoomEntry

from .forms import DateRangeForm
from .services import apply_date_filter, get_default_report_dates


def _user_can_access_reports(user):
    return user.role in [Role.ADMIN, Role.ACCOUNTANT] or user.is_superuser


def _resolve_date_range(request):
    default_start_date, default_end_date = get_default_report_dates()
    form = DateRangeForm(request.GET or None)

    if form.is_valid():
        start_date = form.cleaned_data.get("start_date") or default_start_date
        end_date = form.cleaned_data.get("end_date") or default_end_date
    else:
        start_date = default_start_date
        end_date = default_end_date

    return form, start_date, end_date


def _money(value):
    return f"₦{value}"


def _safe_name(user_obj):
    if not user_obj:
        return "-"
    return user_obj.get_full_name() or user_obj.username


def _create_xlsx_response(filename, sheets_data):
    workbook = Workbook()
    first_sheet = True

    for sheet_name, rows in sheets_data:
        if first_sheet:
            worksheet = workbook.active
            worksheet.title = sheet_name[:31]
            first_sheet = False
        else:
            worksheet = workbook.create_sheet(title=sheet_name[:31])

        for row_index, row in enumerate(rows, start=1):
            worksheet.append(row)
            if row_index == 1:
                for cell in worksheet[row_index]:
                    cell.font = Font(bold=True)

        for column_cells in worksheet.columns:
            max_length = 0
            column_letter = column_cells[0].column_letter
            for cell in column_cells:
                cell_value = "" if cell.value is None else str(cell.value)
                if len(cell_value) > max_length:
                    max_length = len(cell_value)
            worksheet.column_dimensions[column_letter].width = min(max_length + 2, 40)

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _create_pdf_response(filename, title, sections):
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        leftMargin=24,
        rightMargin=24,
        topMargin=24,
        bottomMargin=24,
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 12))

    for index, (section_title, rows) in enumerate(sections):
        story.append(Paragraph(section_title, styles["Heading2"]))
        story.append(Spacer(1, 8))

        if not rows:
            story.append(Paragraph("No data available.", styles["BodyText"]))
            story.append(Spacer(1, 12))
            continue

        table = Table(rows, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
                ]
            )
        )
        story.append(table)

        if index < len(sections) - 1:
            story.append(PageBreak())

    document.build(story)
    output.seek(0)

    response = HttpResponse(output.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _build_financial_report_context(start_date, end_date):
    billings = Billing.objects.select_related(
        "patient",
        "consultation",
        "handled_by",
        "created_by",
    ).order_by("-created_at")

    filtered_billings = apply_date_filter(
        billings,
        start_date=start_date,
        end_date=end_date,
        field_name="created_at",
    )

    payment_transactions = PaymentTransaction.objects.select_related(
        "billing",
        "billing__patient",
        "received_by",
    ).order_by("-created_at")

    filtered_payments = apply_date_filter(
        payment_transactions,
        start_date=start_date,
        end_date=end_date,
        field_name="created_at",
    )

    return {
        "billings": filtered_billings[:100],
        "all_billings": filtered_billings,
        "total_generated": filtered_billings.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00"),
        "total_paid": filtered_billings.aggregate(total=Sum("amount_paid"))["total"] or Decimal("0.00"),
        "total_balance": filtered_billings.aggregate(total=Sum("balance"))["total"] or Decimal("0.00"),
        "total_consultation_fees": filtered_billings.aggregate(total=Sum("consultation_fee"))["total"] or Decimal("0.00"),
        "total_lab": filtered_billings.aggregate(total=Sum("lab_total"))["total"] or Decimal("0.00"),
        "total_prescriptions": filtered_billings.aggregate(total=Sum("prescription_total"))["total"] or Decimal("0.00"),
        "total_medications": filtered_billings.aggregate(total=Sum("medication_total"))["total"] or Decimal("0.00"),
        "total_other_charges": filtered_billings.aggregate(total=Sum("other_charges"))["total"] or Decimal("0.00"),
        "total_discounts": filtered_billings.aggregate(total=Sum("discount"))["total"] or Decimal("0.00"),
        "total_brought_forward": filtered_billings.aggregate(total=Sum("brought_forward_balance"))["total"] or Decimal("0.00"),
        "unpaid_count": filtered_billings.filter(payment_status=Billing.PaymentStatus.UNPAID).count(),
        "part_paid_count": filtered_billings.filter(payment_status=Billing.PaymentStatus.PART_PAYMENT).count(),
        "deposit_count": filtered_billings.filter(payment_status=Billing.PaymentStatus.DEPOSIT).count(),
        "paid_full_count": filtered_billings.filter(payment_status=Billing.PaymentStatus.PAID_FULL).count(),
        "archived_count": filtered_billings.filter(is_archived=True).count(),
        "active_count": filtered_billings.filter(is_archived=False).count(),
        "payment_total": filtered_payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00"),
        "deposit_payment_total": filtered_payments.filter(
            payment_type=PaymentTransaction.PaymentType.DEPOSIT
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00"),
        "part_payment_total": filtered_payments.filter(
            payment_type=PaymentTransaction.PaymentType.PART_PAYMENT
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00"),
        "full_payment_total": filtered_payments.filter(
            payment_type=PaymentTransaction.PaymentType.FULL_PAYMENT
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00"),
    }


def _build_clinical_workflow_report_context(start_date, end_date):
    consultations = Consultation.objects.select_related(
        "patient",
        "doctor",
        "waiting_room_entry",
    ).order_by("-consulted_at")

    filtered_consultations = apply_date_filter(
        consultations,
        start_date=start_date,
        end_date=end_date,
        field_name="consulted_at",
    )

    waiting_entries = WaitingRoomEntry.objects.select_related(
        "patient",
        "assigned_doctor",
        "added_by",
    ).order_by("-created_at")

    filtered_waiting_entries = apply_date_filter(
        waiting_entries,
        start_date=start_date,
        end_date=end_date,
        field_name="created_at",
    )

    appointments = Appointment.objects.select_related(
        "patient",
        "doctor",
        "created_by",
        "reassigned_to",
    ).order_by("-created_at")

    filtered_appointments = apply_date_filter(
        appointments,
        start_date=start_date,
        end_date=end_date,
        field_name="created_at",
    )

    admissions = Admission.objects.select_related(
        "patient",
        "consultation",
        "admitted_by",
        "discharged_by",
        "nurse_discharge_confirmed_by",
    ).order_by("-admitted_at")

    filtered_admissions = apply_date_filter(
        admissions,
        start_date=start_date,
        end_date=end_date,
        field_name="admitted_at",
    )

    return {
        "consultations": filtered_consultations[:100],
        "all_consultations": filtered_consultations,
        "waiting_entries": filtered_waiting_entries[:100],
        "all_waiting_entries": filtered_waiting_entries,
        "appointments": filtered_appointments[:100],
        "all_appointments": filtered_appointments,
        "admissions": filtered_admissions[:100],
        "all_admissions": filtered_admissions,
        "total_consultations": filtered_consultations.count(),
        "ongoing_consultations": filtered_consultations.filter(
            status=Consultation.Status.IN_PROGRESS,
            complete=False,
        ).count(),
        "completed_consultations": filtered_consultations.filter(
            status=Consultation.Status.COMPLETED
        ).count(),
        "referred_consultations": filtered_consultations.filter(
            status=Consultation.Status.REFERRED
        ).count(),
        "cancelled_consultations": filtered_consultations.filter(
            status=Consultation.Status.CANCELLED
        ).count(),
        "admitted_from_consultation": filtered_consultations.filter(admitted=True).count(),
        "discharged_from_consultation": filtered_consultations.filter(discharged=True).count(),
        "died_from_consultation": filtered_consultations.filter(died=True).count(),
        "total_waiting_entries": filtered_waiting_entries.count(),
        "active_waiting_entries": filtered_waiting_entries.filter(is_active=True).count(),
        "waiting_completed": filtered_waiting_entries.filter(status=WaitingRoomEntry.Status.COMPLETED).count(),
        "waiting_in_consultation": filtered_waiting_entries.filter(
            status=WaitingRoomEntry.Status.IN_CONSULTATION
        ).count(),
        "emergency_waiting": filtered_waiting_entries.filter(
            priority=WaitingRoomEntry.Priority.EMERGENCY
        ).count(),
        "appointment_waiting": filtered_waiting_entries.filter(
            priority=WaitingRoomEntry.Priority.APPOINTMENT
        ).count(),
        "normal_waiting": filtered_waiting_entries.filter(
            priority=WaitingRoomEntry.Priority.NORMAL
        ).count(),
        "total_appointments": filtered_appointments.count(),
        "scheduled_appointments": filtered_appointments.filter(
            status=Appointment.Status.SCHEDULED
        ).count(),
        "checked_in_appointments": filtered_appointments.filter(
            status=Appointment.Status.CHECKED_IN
        ).count(),
        "missed_appointments": filtered_appointments.filter(
            status=Appointment.Status.MISSED
        ).count(),
        "completed_appointments": filtered_appointments.filter(
            status=Appointment.Status.COMPLETED
        ).count(),
        "cancelled_appointments": filtered_appointments.filter(
            status=Appointment.Status.CANCELLED
        ).count(),
        "reassigned_appointments": filtered_appointments.filter(
            status=Appointment.Status.REASSIGNED
        ).count(),
        "total_admissions": filtered_admissions.count(),
        "active_admissions": filtered_admissions.filter(status=Admission.Status.ACTIVE).count(),
        "discharge_pending_nurse": filtered_admissions.filter(
            status=Admission.Status.DISCHARGE_PENDING_NURSE
        ).count(),
        "discharged_admissions": filtered_admissions.filter(
            status=Admission.Status.DISCHARGED
        ).count(),
    }


def _build_lab_pharmacy_report_context(start_date, end_date):
    lab_requests = LabRequest.objects.select_related(
        "patient",
        "consultation",
        "requested_by",
        "assigned_to",
    ).order_by("-created_at")

    filtered_lab_requests = apply_date_filter(
        lab_requests,
        start_date=start_date,
        end_date=end_date,
        field_name="created_at",
    )

    lab_request_items = LabRequestItem.objects.select_related(
        "lab_request",
        "lab_request__patient",
        "lab_test",
        "uploaded_by",
        "doctor_reviewed_by",
    ).order_by("-lab_request__created_at", "-uploaded_at")

    filtered_lab_request_items = apply_date_filter(
        lab_request_items,
        start_date=start_date,
        end_date=end_date,
        field_name="lab_request__created_at",
    )

    lab_restocks = LabTestRestock.objects.select_related(
        "lab_test",
        "restocked_by",
    ).order_by("-restocked_at")

    filtered_lab_restocks = apply_date_filter(
        lab_restocks,
        start_date=start_date,
        end_date=end_date,
        field_name="restocked_at",
    )

    lab_stock_movements = LabStockMovement.objects.select_related(
        "lab_test",
        "performed_by",
        "lab_request_item",
        "restock_record",
    ).order_by("-created_at")

    filtered_lab_stock_movements = apply_date_filter(
        lab_stock_movements,
        start_date=start_date,
        end_date=end_date,
        field_name="created_at",
    )

    prescription_items = PrescriptionItem.objects.select_related(
        "patient",
        "consultation",
        "drug",
        "prescribed_by",
    ).order_by("-created_at")

    filtered_prescription_items = apply_date_filter(
        prescription_items,
        start_date=start_date,
        end_date=end_date,
        field_name="created_at",
    )

    drug_issues = DrugIssue.objects.select_related(
        "prescription_item",
        "prescription_item__patient",
        "prescription_item__drug",
        "issued_by",
    ).order_by("-issued_at")

    filtered_drug_issues = apply_date_filter(
        drug_issues,
        start_date=start_date,
        end_date=end_date,
        field_name="issued_at",
    )

    drug_restocks = DrugRestock.objects.select_related(
        "drug",
        "restocked_by",
    ).order_by("-restocked_at")

    filtered_drug_restocks = apply_date_filter(
        drug_restocks,
        start_date=start_date,
        end_date=end_date,
        field_name="restocked_at",
    )

    drug_stock_movements = DrugStockMovement.objects.select_related(
        "drug",
        "performed_by",
        "prescription_item",
        "restock_record",
    ).order_by("-created_at")

    filtered_drug_stock_movements = apply_date_filter(
        drug_stock_movements,
        start_date=start_date,
        end_date=end_date,
        field_name="created_at",
    )

    return {
        "lab_requests": filtered_lab_requests[:50],
        "all_lab_requests": filtered_lab_requests,
        "lab_request_items": filtered_lab_request_items[:50],
        "all_lab_request_items": filtered_lab_request_items,
        "prescription_items": filtered_prescription_items[:50],
        "all_prescription_items": filtered_prescription_items,
        "drug_issues": filtered_drug_issues[:50],
        "all_drug_issues": filtered_drug_issues,
        "total_lab_requests": filtered_lab_requests.count(),
        "pending_lab_requests": filtered_lab_requests.filter(status=LabRequest.Status.PENDING).count(),
        "in_progress_lab_requests": filtered_lab_requests.filter(status=LabRequest.Status.IN_PROGRESS).count(),
        "ready_lab_requests": filtered_lab_requests.filter(status=LabRequest.Status.READY).count(),
        "rejected_lab_requests": filtered_lab_requests.filter(status=LabRequest.Status.REJECTED).count(),
        "accepted_lab_requests": filtered_lab_requests.filter(status=LabRequest.Status.ACCEPTED).count(),
        "unavailable_lab_requests": filtered_lab_requests.filter(status=LabRequest.Status.UNAVAILABLE).count(),
        "total_lab_request_items": filtered_lab_request_items.count(),
        "pending_lab_items": filtered_lab_request_items.filter(status=LabRequestItem.Status.PENDING).count(),
        "in_progress_lab_items": filtered_lab_request_items.filter(status=LabRequestItem.Status.IN_PROGRESS).count(),
        "ready_lab_items": filtered_lab_request_items.filter(status=LabRequestItem.Status.READY).count(),
        "rejected_lab_items": filtered_lab_request_items.filter(status=LabRequestItem.Status.REJECTED).count(),
        "accepted_lab_items": filtered_lab_request_items.filter(status=LabRequestItem.Status.ACCEPTED).count(),
        "unavailable_lab_items": filtered_lab_request_items.filter(status=LabRequestItem.Status.UNAVAILABLE).count(),
        "total_lab_item_value": filtered_lab_request_items.aggregate(total=Sum("price"))["total"] or Decimal("0.00"),
        "total_lab_tests": LabTest.objects.count(),
        "available_lab_tests": LabTest.objects.filter(is_available=True).count(),
        "low_stock_lab_tests": sum(
            1 for test in LabTest.objects.all() if test.is_low_stock and test.stock_quantity > 0
        ),
        "out_of_stock_lab_tests": LabTest.objects.filter(stock_quantity=0).count(),
        "total_lab_restock_quantity": filtered_lab_restocks.aggregate(total=Sum("quantity_added"))["total"] or 0,
        "total_lab_stock_movement_count": filtered_lab_stock_movements.count(),
        "total_prescriptions": filtered_prescription_items.count(),
        "pending_prescriptions": filtered_prescription_items.filter(status=PrescriptionItem.Status.PENDING).count(),
        "awaiting_payment_prescriptions": filtered_prescription_items.filter(
            status=PrescriptionItem.Status.AWAITING_PAYMENT
        ).count(),
        "ready_to_issue_prescriptions": filtered_prescription_items.filter(
            status=PrescriptionItem.Status.READY_TO_ISSUE
        ).count(),
        "issued_prescriptions": filtered_prescription_items.filter(status=PrescriptionItem.Status.ISSUED).count(),
        "cancelled_prescriptions": filtered_prescription_items.filter(
            status=PrescriptionItem.Status.CANCELLED
        ).count(),
        "unavailable_prescriptions": filtered_prescription_items.filter(
            status=PrescriptionItem.Status.UNAVAILABLE
        ).count(),
        "total_prescription_value": filtered_prescription_items.aggregate(
            total=Sum("total_price")
        )["total"] or Decimal("0.00"),
        "total_drugs": Drug.objects.count(),
        "available_drugs": Drug.objects.filter(is_available=True).count(),
        "low_stock_drugs": sum(
            1
            for drug in Drug.objects.all()
            if drug.is_low_stock and drug.stock_quantity > 0 and not drug.is_expired
        ),
        "out_of_stock_drugs": Drug.objects.filter(stock_quantity=0).count(),
        "expired_drugs": sum(1 for drug in Drug.objects.all() if drug.is_expired),
        "near_expiry_drugs": sum(1 for drug in Drug.objects.all() if drug.is_near_expiry),
        "total_drug_issue_count": filtered_drug_issues.count(),
        "total_drug_restock_quantity": filtered_drug_restocks.aggregate(
            total=Sum("quantity_added")
        )["total"] or 0,
        "total_drug_stock_movement_count": filtered_drug_stock_movements.count(),
    }


def _build_staff_performance_report_context(start_date, end_date):
    doctors = User.objects.filter(role=Role.DOCTOR, is_verified_staff=True)
    nurses = User.objects.filter(role=Role.NURSE, is_verified_staff=True)
    lab_techs = User.objects.filter(role=Role.LAB_TECHNICIAN, is_verified_staff=True)
    pharmacists = User.objects.filter(role=Role.PHARMACIST, is_verified_staff=True)

    doctor_stats = []
    for doctor in doctors:
        consultations = apply_date_filter(
            Consultation.objects.filter(doctor=doctor),
            start_date,
            end_date,
            "consulted_at",
        )
        doctor_billings = apply_date_filter(
            Billing.objects.filter(consultation__doctor=doctor),
            start_date,
            end_date,
            "created_at",
        )

        doctor_stats.append(
            {
                "doctor": doctor,
                "total_consultations": consultations.count(),
                "completed": consultations.filter(status=Consultation.Status.COMPLETED).count(),
                "admitted": consultations.filter(admitted=True).count(),
                "revenue_generated": doctor_billings.aggregate(total=Sum("amount_paid"))["total"] or Decimal("0.00"),
            }
        )

    nurse_stats = []
    for nurse in nurses:
        discharges = apply_date_filter(
            Admission.objects.filter(nurse_discharge_confirmed_by=nurse),
            start_date,
            end_date,
            "discharged_at",
        )
        nurse_stats.append(
            {
                "nurse": nurse,
                "discharges_confirmed": discharges.count(),
            }
        )

    lab_stats = []
    for tech in lab_techs:
        tests = apply_date_filter(
            LabRequestItem.objects.filter(uploaded_by=tech),
            start_date,
            end_date,
            "uploaded_at",
        )
        lab_stats.append(
            {
                "tech": tech,
                "completed_tests": tests.filter(
                    status__in=[LabRequestItem.Status.READY, LabRequestItem.Status.ACCEPTED]
                ).count(),
                "rejected_tests": tests.filter(status=LabRequestItem.Status.REJECTED).count(),
            }
        )

    pharmacy_stats = []
    for pharmacist in pharmacists:
        issued = apply_date_filter(
            PrescriptionItem.objects.filter(
                status=PrescriptionItem.Status.ISSUED,
                issue_record__issued_by=pharmacist,
            ),
            start_date,
            end_date,
            "issue_record__issued_at",
        ).count()

        pharmacy_stats.append(
            {
                "pharmacist": pharmacist,
                "drugs_issued": issued,
            }
        )

    return {
        "doctor_stats": doctor_stats,
        "nurse_stats": nurse_stats,
        "lab_stats": lab_stats,
        "pharmacy_stats": pharmacy_stats,
    }


@login_required
def reports_home(request):
    if not _user_can_access_reports(request.user):
        return render(request, "dashboards/access_denied.html", status=403)

    return render(request, "reports/reports_home.html")


@login_required
def financial_report(request):
    if not _user_can_access_reports(request.user):
        return render(request, "dashboards/access_denied.html", status=403)

    form, start_date, end_date = _resolve_date_range(request)
    context = _build_financial_report_context(start_date, end_date)
    context.update(
        {
            "form": form,
            "start_date": start_date,
            "end_date": end_date,
        }
    )
    return render(request, "reports/financial_report.html", context)


@login_required
def clinical_workflow_report(request):
    if not _user_can_access_reports(request.user):
        return render(request, "dashboards/access_denied.html", status=403)

    form, start_date, end_date = _resolve_date_range(request)
    context = _build_clinical_workflow_report_context(start_date, end_date)
    context.update(
        {
            "form": form,
            "start_date": start_date,
            "end_date": end_date,
        }
    )
    return render(request, "reports/clinical_workflow_report.html", context)


@login_required
def lab_pharmacy_report(request):
    if not _user_can_access_reports(request.user):
        return render(request, "dashboards/access_denied.html", status=403)

    form, start_date, end_date = _resolve_date_range(request)
    context = _build_lab_pharmacy_report_context(start_date, end_date)
    context.update(
        {
            "form": form,
            "start_date": start_date,
            "end_date": end_date,
        }
    )
    return render(request, "reports/lab_pharmacy_report.html", context)


@login_required
def staff_performance_report(request):
    if not _user_can_access_reports(request.user):
        return render(request, "dashboards/access_denied.html", status=403)

    form, start_date, end_date = _resolve_date_range(request)
    context = _build_staff_performance_report_context(start_date, end_date)
    context.update(
        {
            "form": form,
            "start_date": start_date,
            "end_date": end_date,
        }
    )
    return render(request, "reports/staff_performance_report.html", context)


@login_required
def export_financial_report_xlsx(request):
    if not _user_can_access_reports(request.user):
        return render(request, "dashboards/access_denied.html", status=403)

    _, start_date, end_date = _resolve_date_range(request)
    context = _build_financial_report_context(start_date, end_date)

    summary_rows = [
        ["Metric", "Value"],
        ["Start Date", str(start_date)],
        ["End Date", str(end_date)],
        ["Total Billing Generated", str(context["total_generated"])],
        ["Total Paid", str(context["total_paid"])],
        ["Outstanding Balance", str(context["total_balance"])],
        ["Consultation Fees", str(context["total_consultation_fees"])],
        ["Lab Total", str(context["total_lab"])],
        ["Prescription Total", str(context["total_prescriptions"])],
        ["Medication Total", str(context["total_medications"])],
        ["Other Charges", str(context["total_other_charges"])],
        ["Discounts", str(context["total_discounts"])],
        ["Brought Forward", str(context["total_brought_forward"])],
        ["Unpaid Bills", context["unpaid_count"]],
        ["Part Paid Bills", context["part_paid_count"]],
        ["Deposit Bills", context["deposit_count"]],
        ["Paid Full Bills", context["paid_full_count"]],
        ["Archived Bills", context["archived_count"]],
        ["Active Bills", context["active_count"]],
        ["Payment Transactions Total", str(context["payment_total"])],
    ]

    bill_rows = [[
        "Patient",
        "Hospital Number",
        "Total Amount",
        "Amount Paid",
        "Balance",
        "Payment Status",
        "Archived",
        "Created At",
    ]]

    for bill in context["all_billings"]:
        bill_rows.append([
            bill.patient.full_name,
            bill.patient.hospital_number,
            str(bill.total_amount),
            str(bill.amount_paid),
            str(bill.balance),
            bill.get_payment_status_display(),
            "Yes" if bill.is_archived else "No",
            bill.created_at.strftime("%Y-%m-%d %H:%M"),
        ])

    return _create_xlsx_response(
        "financial_report.xlsx",
        [
            ("Summary", summary_rows),
            ("Billing Records", bill_rows),
        ],
    )


@login_required
def export_financial_report_pdf(request):
    if not _user_can_access_reports(request.user):
        return render(request, "dashboards/access_denied.html", status=403)

    _, start_date, end_date = _resolve_date_range(request)
    context = _build_financial_report_context(start_date, end_date)

    summary_rows = [
        ["Metric", "Value"],
        ["Start Date", str(start_date)],
        ["End Date", str(end_date)],
        ["Total Billing Generated", _money(context["total_generated"])],
        ["Total Paid", _money(context["total_paid"])],
        ["Outstanding Balance", _money(context["total_balance"])],
        ["Unpaid Bills", str(context["unpaid_count"])],
        ["Part Paid Bills", str(context["part_paid_count"])],
        ["Deposit Bills", str(context["deposit_count"])],
        ["Paid Full Bills", str(context["paid_full_count"])],
    ]

    bill_rows = [[
        "Patient",
        "Hospital No.",
        "Total",
        "Paid",
        "Balance",
        "Status",
    ]]

    for bill in context["all_billings"][:40]:
        bill_rows.append([
            bill.patient.full_name,
            bill.patient.hospital_number,
            _money(bill.total_amount),
            _money(bill.amount_paid),
            _money(bill.balance),
            bill.get_payment_status_display(),
        ])

    return _create_pdf_response(
        "financial_report.pdf",
        "Financial Report",
        [
            ("Summary", summary_rows),
            ("Billing Records", bill_rows),
        ],
    )


@login_required
def export_clinical_workflow_report_xlsx(request):
    if not _user_can_access_reports(request.user):
        return render(request, "dashboards/access_denied.html", status=403)

    _, start_date, end_date = _resolve_date_range(request)
    context = _build_clinical_workflow_report_context(start_date, end_date)

    summary_rows = [
        ["Metric", "Value"],
        ["Start Date", str(start_date)],
        ["End Date", str(end_date)],
        ["Total Consultations", context["total_consultations"]],
        ["Ongoing Consultations", context["ongoing_consultations"]],
        ["Completed Consultations", context["completed_consultations"]],
        ["Referred Consultations", context["referred_consultations"]],
        ["Cancelled Consultations", context["cancelled_consultations"]],
        ["Total Waiting Entries", context["total_waiting_entries"]],
        ["Active Waiting Entries", context["active_waiting_entries"]],
        ["Total Appointments", context["total_appointments"]],
        ["Total Admissions", context["total_admissions"]],
    ]

    consultation_rows = [[
        "Patient",
        "Doctor",
        "Status",
        "Admitted",
        "Discharged",
        "Died",
        "Consulted At",
    ]]
    for item in context["all_consultations"]:
        consultation_rows.append([
            item.patient.full_name,
            _safe_name(item.doctor),
            item.get_status_display(),
            "Yes" if item.admitted else "No",
            "Yes" if item.discharged else "No",
            "Yes" if item.died else "No",
            item.consulted_at.strftime("%Y-%m-%d %H:%M"),
        ])

    waiting_rows = [[
        "Patient",
        "Priority",
        "Status",
        "Assigned Doctor",
        "Added By",
        "Created At",
    ]]
    for item in context["all_waiting_entries"]:
        waiting_rows.append([
            item.patient.full_name,
            item.get_priority_display(),
            item.get_status_display(),
            _safe_name(item.assigned_doctor),
            _safe_name(item.added_by),
            item.created_at.strftime("%Y-%m-%d %H:%M"),
        ])

    appointment_rows = [[
        "Patient",
        "Doctor",
        "Date",
        "Time",
        "Status",
        "Created At",
    ]]
    for item in context["all_appointments"]:
        appointment_rows.append([
            item.patient.full_name,
            _safe_name(item.assigned_doctor),
            str(item.appointment_date),
            str(item.appointment_time),
            item.get_status_display(),
            item.created_at.strftime("%Y-%m-%d %H:%M"),
        ])

    admission_rows = [[
        "Patient",
        "Status",
        "Ward",
        "Bed Number",
        "Admitted At",
        "Discharged At",
    ]]
    for item in context["all_admissions"]:
        admission_rows.append([
            item.patient.full_name,
            item.get_status_display(),
            item.ward or "-",
            item.bed_number or "-",
            item.admitted_at.strftime("%Y-%m-%d %H:%M"),
            item.discharged_at.strftime("%Y-%m-%d %H:%M") if item.discharged_at else "-",
        ])

    return _create_xlsx_response(
        "clinical_workflow_report.xlsx",
        [
            ("Summary", summary_rows),
            ("Consultations", consultation_rows),
            ("Waiting Room", waiting_rows),
            ("Appointments", appointment_rows),
            ("Admissions", admission_rows),
        ],
    )


@login_required
def export_clinical_workflow_report_pdf(request):
    if not _user_can_access_reports(request.user):
        return render(request, "dashboards/access_denied.html", status=403)

    _, start_date, end_date = _resolve_date_range(request)
    context = _build_clinical_workflow_report_context(start_date, end_date)

    summary_rows = [
        ["Metric", "Value"],
        ["Start Date", str(start_date)],
        ["End Date", str(end_date)],
        ["Total Consultations", str(context["total_consultations"])],
        ["Ongoing Consultations", str(context["ongoing_consultations"])],
        ["Completed Consultations", str(context["completed_consultations"])],
        ["Total Waiting Entries", str(context["total_waiting_entries"])],
        ["Total Appointments", str(context["total_appointments"])],
        ["Total Admissions", str(context["total_admissions"])],
    ]

    consultation_rows = [[
        "Patient",
        "Doctor",
        "Status",
        "Consulted At",
    ]]
    for item in context["all_consultations"][:40]:
        consultation_rows.append([
            item.patient.full_name,
            _safe_name(item.doctor),
            item.get_status_display(),
            item.consulted_at.strftime("%Y-%m-%d %H:%M"),
        ])

    waiting_rows = [[
        "Patient",
        "Priority",
        "Status",
        "Created At",
    ]]
    for item in context["all_waiting_entries"][:40]:
        waiting_rows.append([
            item.patient.full_name,
            item.get_priority_display(),
            item.get_status_display(),
            item.created_at.strftime("%Y-%m-%d %H:%M"),
        ])

    return _create_pdf_response(
        "clinical_workflow_report.pdf",
        "Clinical & Workflow Report",
        [
            ("Summary", summary_rows),
            ("Recent Consultations", consultation_rows),
            ("Recent Waiting Room Entries", waiting_rows),
        ],
    )


@login_required
def export_lab_pharmacy_report_xlsx(request):
    if not _user_can_access_reports(request.user):
        return render(request, "dashboards/access_denied.html", status=403)

    _, start_date, end_date = _resolve_date_range(request)
    context = _build_lab_pharmacy_report_context(start_date, end_date)

    summary_rows = [
        ["Metric", "Value"],
        ["Start Date", str(start_date)],
        ["End Date", str(end_date)],
        ["Total Lab Requests", context["total_lab_requests"]],
        ["Accepted Lab Requests", context["accepted_lab_requests"]],
        ["Rejected Lab Requests", context["rejected_lab_requests"]],
        ["Unavailable Lab Requests", context["unavailable_lab_requests"]],
        ["Total Lab Item Value", str(context["total_lab_item_value"])],
        ["Total Prescriptions", context["total_prescriptions"]],
        ["Issued Prescriptions", context["issued_prescriptions"]],
        ["Unavailable Prescriptions", context["unavailable_prescriptions"]],
        ["Total Prescription Value", str(context["total_prescription_value"])],
        ["Total Drugs", context["total_drugs"]],
        ["Low Stock Drugs", context["low_stock_drugs"]],
        ["Expired Drugs", context["expired_drugs"]],
    ]

    lab_request_rows = [[
        "Patient",
        "Status",
        "Requested By",
        "Assigned To",
        "Created At",
    ]]
    for item in context["all_lab_requests"]:
        lab_request_rows.append([
            item.patient.full_name,
            item.get_status_display(),
            _safe_name(item.requested_by),
            _safe_name(item.assigned_to),
            item.created_at.strftime("%Y-%m-%d %H:%M"),
        ])

    lab_item_rows = [[
        "Patient",
        "Test",
        "Status",
        "Price",
        "Uploaded By",
    ]]
    for item in context["all_lab_request_items"]:
        lab_item_rows.append([
            item.lab_request.patient.full_name,
            item.lab_test.name,
            item.get_status_display(),
            str(item.price),
            _safe_name(item.uploaded_by),
        ])

    prescription_rows = [[
        "Patient",
        "Drug",
        "Prescription",
        "Status",
        "Total Price",
        "Prescribed By",
    ]]
    for item in context["all_prescription_items"]:
        prescription_rows.append([
            item.patient.full_name,
            item.drug.name,
            item.prescription_summary,
            item.get_status_display(),
            str(item.total_price),
            _safe_name(item.prescribed_by),
        ])

    issue_rows = [[
        "Patient",
        "Drug",
        "Issued By",
        "Issued At",
    ]]
    for item in context["all_drug_issues"]:
        issue_rows.append([
            item.prescription_item.patient.full_name,
            item.prescription_item.drug.name,
            _safe_name(item.issued_by),
            item.issued_at.strftime("%Y-%m-%d %H:%M"),
        ])

    return _create_xlsx_response(
        "lab_pharmacy_report.xlsx",
        [
            ("Summary", summary_rows),
            ("Lab Requests", lab_request_rows),
            ("Lab Items", lab_item_rows),
            ("Prescriptions", prescription_rows),
            ("Drug Issues", issue_rows),
        ],
    )


@login_required
def export_lab_pharmacy_report_pdf(request):
    if not _user_can_access_reports(request.user):
        return render(request, "dashboards/access_denied.html", status=403)

    _, start_date, end_date = _resolve_date_range(request)
    context = _build_lab_pharmacy_report_context(start_date, end_date)

    summary_rows = [
        ["Metric", "Value"],
        ["Start Date", str(start_date)],
        ["End Date", str(end_date)],
        ["Total Lab Requests", str(context["total_lab_requests"])],
        ["Accepted Lab Requests", str(context["accepted_lab_requests"])],
        ["Rejected Lab Requests", str(context["rejected_lab_requests"])],
        ["Total Prescriptions", str(context["total_prescriptions"])],
        ["Issued Prescriptions", str(context["issued_prescriptions"])],
        ["Total Drugs", str(context["total_drugs"])],
        ["Low Stock Drugs", str(context["low_stock_drugs"])],
    ]

    lab_rows = [[
        "Patient",
        "Status",
        "Created At",
    ]]
    for item in context["all_lab_requests"][:40]:
        lab_rows.append([
            item.patient.full_name,
            item.get_status_display(),
            item.created_at.strftime("%Y-%m-%d %H:%M"),
        ])

    pharmacy_rows = [[
        "Patient",
        "Drug",
        "Status",
        "Total",
    ]]
    for item in context["all_prescription_items"][:40]:
        pharmacy_rows.append([
            item.patient.full_name,
            item.drug.name,
            item.get_status_display(),
            _money(item.total_price),
        ])

    return _create_pdf_response(
        "lab_pharmacy_report.pdf",
        "Lab & Pharmacy Report",
        [
            ("Summary", summary_rows),
            ("Recent Lab Requests", lab_rows),
            ("Recent Prescriptions", pharmacy_rows),
        ],
    )


@login_required
def export_staff_performance_report_xlsx(request):
    if not _user_can_access_reports(request.user):
        return render(request, "dashboards/access_denied.html", status=403)

    _, start_date, end_date = _resolve_date_range(request)
    context = _build_staff_performance_report_context(start_date, end_date)

    doctor_rows = [[
        "Doctor",
        "Total Consultations",
        "Completed",
        "Admitted",
        "Revenue Generated",
    ]]
    for item in context["doctor_stats"]:
        doctor_rows.append([
            _safe_name(item["doctor"]),
            item["total_consultations"],
            item["completed"],
            item["admitted"],
            str(item["revenue_generated"]),
        ])

    nurse_rows = [[
        "Nurse",
        "Discharges Confirmed",
    ]]
    for item in context["nurse_stats"]:
        nurse_rows.append([
            _safe_name(item["nurse"]),
            item["discharges_confirmed"],
        ])

    lab_rows = [[
        "Lab Technician",
        "Completed Tests",
        "Rejected Tests",
    ]]
    for item in context["lab_stats"]:
        lab_rows.append([
            _safe_name(item["tech"]),
            item["completed_tests"],
            item["rejected_tests"],
        ])

    pharmacy_rows = [[
        "Pharmacist",
        "Drugs Issued",
    ]]
    for item in context["pharmacy_stats"]:
        pharmacy_rows.append([
            _safe_name(item["pharmacist"]),
            item["drugs_issued"],
        ])

    return _create_xlsx_response(
        "staff_performance_report.xlsx",
        [
            ("Doctors", doctor_rows),
            ("Nurses", nurse_rows),
            ("Lab Technicians", lab_rows),
            ("Pharmacists", pharmacy_rows),
        ],
    )


@login_required
def export_staff_performance_report_pdf(request):
    if not _user_can_access_reports(request.user):
        return render(request, "dashboards/access_denied.html", status=403)

    _, start_date, end_date = _resolve_date_range(request)
    context = _build_staff_performance_report_context(start_date, end_date)

    doctor_rows = [[
        "Doctor",
        "Consultations",
        "Completed",
        "Admitted",
        "Revenue",
    ]]
    for item in context["doctor_stats"]:
        doctor_rows.append([
            _safe_name(item["doctor"]),
            str(item["total_consultations"]),
            str(item["completed"]),
            str(item["admitted"]),
            _money(item["revenue_generated"]),
        ])

    nurse_rows = [[
        "Nurse",
        "Discharges Confirmed",
    ]]
    for item in context["nurse_stats"]:
        nurse_rows.append([
            _safe_name(item["nurse"]),
            str(item["discharges_confirmed"]),
        ])

    lab_rows = [[
        "Lab Technician",
        "Completed Tests",
        "Rejected Tests",
    ]]
    for item in context["lab_stats"]:
        lab_rows.append([
            _safe_name(item["tech"]),
            str(item["completed_tests"]),
            str(item["rejected_tests"]),
        ])

    pharmacy_rows = [[
        "Pharmacist",
        "Drugs Issued",
    ]]
    for item in context["pharmacy_stats"]:
        pharmacy_rows.append([
            _safe_name(item["pharmacist"]),
            str(item["drugs_issued"]),
        ])

    return _create_pdf_response(
        "staff_performance_report.pdf",
        "Staff Performance Report",
        [
            ("Doctors", doctor_rows),
            ("Nurses", nurse_rows),
            ("Lab Technicians", lab_rows),
            ("Pharmacists", pharmacy_rows),
        ],
    )
