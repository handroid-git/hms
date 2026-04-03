from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from apps.accounts.models import Role
from .forms import BillingExtraItemForm, BillingNoteForm, BillingUpdateForm, PaymentTransactionForm
from .models import Billing
from .services import (
    add_billing_extra_item,
    archive_bill,
    auto_archive_old_bills,
    receive_payment,
    update_billing_adjustments,
    update_billing_note,
)


@login_required
def billing_dashboard(request):
    if request.user.role != Role.ACCOUNTANT:
        return render(request, "dashboards/access_denied.html", status=403)

    auto_archive_old_bills()
    today = timezone.localdate()

    unpaid_bills = Billing.objects.filter(
        is_archived=False,
        payment_status=Billing.PaymentStatus.UNPAID,
    ).select_related("patient").order_by("-updated_at")[:10]

    part_paid_bills = Billing.objects.filter(
        is_archived=False,
        payment_status__in=[Billing.PaymentStatus.PART_PAYMENT, Billing.PaymentStatus.DEPOSIT],
    ).select_related("patient").order_by("-updated_at")[:10]

    recent_completed_today = Billing.objects.filter(
        is_archived=False,
        payment_status=Billing.PaymentStatus.PAID_FULL,
        updated_at__date=today,
    ).select_related("patient").order_by("-updated_at")[:10]

    context = {
        "unpaid_bills": unpaid_bills,
        "part_paid_bills": part_paid_bills,
        "recent_completed_today": recent_completed_today,
    }
    return render(request, "billing/billing_dashboard.html", context)


@login_required
def billing_list(request):
    if request.user.role != Role.ACCOUNTANT:
        return render(request, "dashboards/access_denied.html", status=403)

    auto_archive_old_bills()
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

    query = request.GET.get("q", "").strip()
    bills = Billing.objects.select_related("patient").filter(is_archived=True).order_by("-updated_at")

    if query:
        bills = bills.filter(
            Q(patient__first_name__icontains=query)
            | Q(patient__last_name__icontains=query)
            | Q(patient__hospital_number__icontains=query)
        )

    return render(
        request,
        "billing/archived_billing_list.html",
        {
            "bills": bills,
            "query": query,
        },
    )


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
            note_form = BillingNoteForm(instance=billing)

            if billing_form.is_valid():
                try:
                    update_billing_adjustments(
                        billing=billing,
                        handled_by=request.user,
                        other_charges=billing_form.cleaned_data["other_charges"],
                        discount=billing_form.cleaned_data["discount"],
                    )
                    messages.success(request, "Billing updated successfully.")
                    return redirect("billing_detail", pk=billing.pk)
                except ValueError as exc:
                    messages.error(request, str(exc))

        elif "receive_payment" in request.POST:
            billing_form = BillingUpdateForm(instance=billing)
            payment_form = PaymentTransactionForm(request.POST)
            extra_item_form = BillingExtraItemForm()
            note_form = BillingNoteForm(instance=billing)

            if payment_form.is_valid():
                try:
                    receive_payment(
                        billing=billing,
                        handled_by=request.user,
                        amount=payment_form.cleaned_data["amount"],
                        payment_type=payment_form.cleaned_data["payment_type"],
                        notes=payment_form.cleaned_data["notes"],
                    )
                    messages.success(request, "Payment recorded successfully.")
                    return redirect("billing_detail", pk=billing.pk)
                except ValueError as exc:
                    messages.error(request, str(exc))

        elif "add_extra_item" in request.POST:
            billing_form = BillingUpdateForm(instance=billing)
            payment_form = PaymentTransactionForm()
            extra_item_form = BillingExtraItemForm(request.POST)
            note_form = BillingNoteForm(instance=billing)

            if extra_item_form.is_valid():
                try:
                    add_billing_extra_item(
                        billing=billing,
                        handled_by=request.user,
                        title=extra_item_form.cleaned_data["title"],
                        price=extra_item_form.cleaned_data["price"],
                    )
                    messages.success(request, "Extra billing item added.")
                    return redirect("billing_detail", pk=billing.pk)
                except ValueError as exc:
                    messages.error(request, str(exc))

        elif "archive_bill" in request.POST:
            billing_form = BillingUpdateForm(instance=billing)
            payment_form = PaymentTransactionForm()
            extra_item_form = BillingExtraItemForm()
            note_form = BillingNoteForm(instance=billing)
            archive_bill(billing, request.user)
            messages.success(request, "Bill archived successfully.")
            return redirect("billing_list")

        elif "update_note" in request.POST:
            billing_form = BillingUpdateForm(instance=billing)
            payment_form = PaymentTransactionForm()
            extra_item_form = BillingExtraItemForm()
            note_form = BillingNoteForm(request.POST, instance=billing)

            if note_form.is_valid():
                update_billing_note(
                    billing=billing,
                    handled_by=request.user,
                    internal_note=note_form.cleaned_data["internal_note"],
                )
                messages.success(request, "Billing note updated.")
                return redirect("billing_detail", pk=billing.pk)

    else:
        billing_form = BillingUpdateForm(instance=billing)
        payment_form = PaymentTransactionForm()
        extra_item_form = BillingExtraItemForm()
        note_form = BillingNoteForm(instance=billing)

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
            "note_form": note_form,
            "payments": payments,
            "extra_items": extra_items,
        },
    )