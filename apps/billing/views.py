from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from apps.accounts.models import Role
from .forms import BillingExtraItemForm, BillingUpdateForm, PaymentTransactionForm
from .models import Billing
from .services import (
    add_billing_extra_item,
    archive_paid_bill,
    receive_payment,
    update_billing_adjustments,
)


@login_required
def billing_dashboard(request):
    if request.user.role != Role.ACCOUNTANT:
        return render(request, "dashboards/access_denied.html", status=403)

    today = timezone.localdate()

    total_generated_today = (
        Billing.objects.filter(created_at__date=today, is_archived=False).aggregate(total=Sum("total_amount"))["total"]
        or 0
    )
    total_paid_today = (
        Billing.objects.filter(updated_at__date=today, is_archived=False).aggregate(total=Sum("amount_paid"))["total"]
        or 0
    )
    bills_today_count = Billing.objects.filter(created_at__date=today, is_archived=False).count()
    all_time_processed = Billing.objects.exclude(handled_by__isnull=True).count()

    recent_bills = Billing.objects.select_related("patient", "consultation").filter(is_archived=False).order_by("-updated_at")[:10]

    context = {
        "total_generated_today": total_generated_today,
        "total_paid_today": total_paid_today,
        "bills_today_count": bills_today_count,
        "all_time_processed": all_time_processed,
        "recent_bills": recent_bills,
    }
    return render(request, "billing/billing_dashboard.html", context)


@login_required
def billing_list(request):
    if request.user.role != Role.ACCOUNTANT:
        return render(request, "dashboards/access_denied.html", status=403)

    query = request.GET.get("q", "").strip()

    bills = Billing.objects.select_related("patient", "consultation").filter(is_archived=False).order_by("-updated_at")
    if query:
        bills = bills.filter(
            Q(patient__first_name__icontains=query)
            | Q(patient__last_name__icontains=query)
            | Q(patient__hospital_number__icontains=query)
        )

    return render(
        request,
        "billing/billing_list.html",
        {
            "bills": bills,
            "query": query,
        },
    )


@login_required
def archived_billing_list(request):
    if request.user.role != Role.ACCOUNTANT:
        return render(request, "dashboards/access_denied.html", status=403)

    bills = Billing.objects.select_related("patient").filter(is_archived=True).order_by("-updated_at")
    return render(request, "billing/archived_billing_list.html", {"bills": bills})


@login_required
def billing_detail(request, pk):
    if request.user.role != Role.ACCOUNTANT:
        return render(request, "dashboards/access_denied.html", status=403)

    billing = get_object_or_404(
        Billing.objects.select_related("patient", "consultation", "handled_by", "created_by"),
        pk=pk,
    )

    if request.method == "POST":
        if "update_billing" in request.POST:
            billing_form = BillingUpdateForm(request.POST, instance=billing)
            payment_form = PaymentTransactionForm()
            extra_item_form = BillingExtraItemForm()
            if billing_form.is_valid():
                update_billing_adjustments(
                    billing=billing,
                    handled_by=request.user,
                    other_charges=billing_form.cleaned_data["other_charges"],
                    discount=billing_form.cleaned_data["discount"],
                )
                messages.success(request, "Billing updated successfully.")
                return redirect("billing_detail", pk=billing.pk)

        elif "receive_payment" in request.POST:
            billing_form = BillingUpdateForm(instance=billing)
            payment_form = PaymentTransactionForm(request.POST)
            extra_item_form = BillingExtraItemForm()
            if payment_form.is_valid():
                receive_payment(
                    billing=billing,
                    handled_by=request.user,
                    amount=payment_form.cleaned_data["amount"],
                    payment_type=payment_form.cleaned_data["payment_type"],
                    notes=payment_form.cleaned_data["notes"],
                )
                messages.success(request, "Payment recorded successfully.")
                return redirect("billing_detail", pk=billing.pk)

        elif "add_extra_item" in request.POST:
            billing_form = BillingUpdateForm(instance=billing)
            payment_form = PaymentTransactionForm()
            extra_item_form = BillingExtraItemForm(request.POST)
            if extra_item_form.is_valid():
                add_billing_extra_item(
                    billing=billing,
                    handled_by=request.user,
                    title=extra_item_form.cleaned_data["title"],
                    price=extra_item_form.cleaned_data["price"],
                )
                messages.success(request, "Extra billing item added.")
                return redirect("billing_detail", pk=billing.pk)

        elif "archive_bill" in request.POST:
            billing_form = BillingUpdateForm(instance=billing)
            payment_form = PaymentTransactionForm()
            extra_item_form = BillingExtraItemForm()
            try:
                archive_paid_bill(billing, request.user)
                messages.success(request, "Bill archived successfully.")
                return redirect("billing_list")
            except ValueError as exc:
                messages.error(request, str(exc))
    else:
        billing_form = BillingUpdateForm(instance=billing)
        payment_form = PaymentTransactionForm()
        extra_item_form = BillingExtraItemForm()

    payments = billing.payments.select_related("received_by").order_by("-created_at")
    extra_items = billing.extra_items.order_by("-created_at")

    return render(
        request,
        "billing/billing_detail.html",
        {
            "billing": billing,
            "billing_form": billing_form,
            "payment_form": payment_form,
            "extra_item_form": extra_item_form,
            "payments": payments,
            "extra_items": extra_items,
        },
    )