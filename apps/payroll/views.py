from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import Role
from .forms import PayrollGenerateForm, PayrollUpdateForm, StaffSalaryStructureForm
from .models import PayrollRecord, StaffSalaryStructure
from .services import generate_payroll_for_period, mark_payroll_paid, update_payroll_record


@login_required
def payroll_dashboard(request):
    if request.user.role != Role.ACCOUNTANT and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    today = date.today()
    generate_form = PayrollGenerateForm(initial={"year": today.year, "month": today.month})

    total_generated = PayrollRecord.objects.aggregate(total=Sum("net_pay"))["total"] or 0
    total_paid = PayrollRecord.objects.filter(status=PayrollRecord.Status.PAID).aggregate(total=Sum("net_pay"))["total"] or 0
    pending_total = PayrollRecord.objects.exclude(status=PayrollRecord.Status.PAID).aggregate(total=Sum("net_pay"))["total"] or 0

    recent_payrolls = PayrollRecord.objects.select_related("staff").all()[:10]
    salary_structures = StaffSalaryStructure.objects.select_related("staff").all()[:10]

    return render(
        request,
        "payroll/payroll_dashboard.html",
        {
            "generate_form": generate_form,
            "total_generated": total_generated,
            "total_paid": total_paid,
            "pending_total": pending_total,
            "recent_payrolls": recent_payrolls,
            "salary_structures": salary_structures,
        },
    )


@login_required
def payroll_generate(request):
    if request.user.role != Role.ACCOUNTANT and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    if request.method == "POST":
        form = PayrollGenerateForm(request.POST)
        if form.is_valid():
            year = form.cleaned_data["year"]
            month = form.cleaned_data["month"]
            generate_payroll_for_period(year=year, month=month, generated_by=request.user)
            messages.success(request, f"Payroll generated for {year}-{month:02d}.")
    return redirect("payroll_dashboard")


@login_required
def payroll_list(request):
    if request.user.role == Role.ACCOUNTANT or request.user.is_superuser:
        payrolls = PayrollRecord.objects.select_related("staff", "paid_by").all()
    else:
        payrolls = PayrollRecord.objects.select_related("staff", "paid_by").filter(staff=request.user)

    return render(
        request,
        "payroll/payroll_list.html",
        {
            "payrolls": payrolls,
        },
    )


@login_required
def payroll_detail(request, pk):
    payroll = get_object_or_404(
        PayrollRecord.objects.select_related("staff", "generated_by", "paid_by"),
        pk=pk,
    )

    if request.user.role != Role.ACCOUNTANT and not request.user.is_superuser and payroll.staff != request.user:
        return render(request, "dashboards/access_denied.html", status=403)

    if request.method == "POST":
        if request.user.role != Role.ACCOUNTANT and not request.user.is_superuser:
            return render(request, "dashboards/access_denied.html", status=403)

        if "update_payroll" in request.POST:
            form = PayrollUpdateForm(request.POST, instance=payroll)
            if form.is_valid():
                try:
                    update_payroll_record(
                        payroll=payroll,
                        bonus=form.cleaned_data["bonus"],
                        deduction=form.cleaned_data["deduction"],
                        accountant_note=form.cleaned_data["accountant_note"],
                        updated_by=request.user,
                    )
                    messages.success(request, "Payroll updated successfully.")
                    return redirect("payroll_detail", pk=payroll.pk)
                except ValueError as exc:
                    messages.error(request, str(exc))
        elif "mark_paid" in request.POST:
            mark_payroll_paid(payroll, request.user)
            messages.success(request, "Payroll marked as paid.")
            return redirect("payroll_detail", pk=payroll.pk)
    else:
        form = PayrollUpdateForm(instance=payroll)

    return render(
        request,
        "payroll/payroll_detail.html",
        {
            "payroll": payroll,
            "form": form,
        },
    )


@login_required
def salary_structure_list(request):
    if request.user.role != Role.ACCOUNTANT and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    structures = StaffSalaryStructure.objects.select_related("staff", "updated_by").all()
    return render(
        request,
        "payroll/salary_structure_list.html",
        {
            "structures": structures,
        },
    )


@login_required
def salary_structure_create(request):
    if request.user.role != Role.ACCOUNTANT and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    if request.method == "POST":
        form = StaffSalaryStructureForm(request.POST)
        if form.is_valid():
            structure = form.save(commit=False)
            structure.updated_by = request.user
            structure.save()
            messages.success(request, "Salary structure created successfully.")
            return redirect("salary_structure_list")
    else:
        form = StaffSalaryStructureForm()

    return render(
        request,
        "payroll/salary_structure_form.html",
        {
            "form": form,
            "title": "Create Salary Structure",
        },
    )


@login_required
def salary_structure_update(request, pk):
    if request.user.role != Role.ACCOUNTANT and not request.user.is_superuser:
        return render(request, "dashboards/access_denied.html", status=403)

    structure = get_object_or_404(StaffSalaryStructure, pk=pk)

    if request.method == "POST":
        form = StaffSalaryStructureForm(request.POST, instance=structure)
        if form.is_valid():
            structure = form.save(commit=False)
            structure.updated_by = request.user
            structure.save()
            messages.success(request, "Salary structure updated successfully.")
            return redirect("salary_structure_list")
    else:
        form = StaffSalaryStructureForm(instance=structure)

    return render(
        request,
        "payroll/salary_structure_form.html",
        {
            "form": form,
            "title": "Update Salary Structure",
        },
    )