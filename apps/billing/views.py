from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from apps.accounts.models import Role
from .forms import BillingUpdateForm, PaymentTransactionForm
from .models import Billing
from .services import receive_payment, update_billing_adjustments


@login_required
def billing_dashboard(request):
    if request.user.role != Role.ACCOUNTANT:
        return render(request, "dashboards/access_denied.html", status=403)

    today = timezone.localdate()

    total_generated_today = (
        Billing.objects.filter(created_at__date=today).aggregate(total=Sum("total_amount"))["total"]
        or 0
    )
    total_paid_today = (
        Billing.objects.filter(updated_at__date=today).aggregate(total=Sum("amount_paid"))["total"]
        or 0
    )
    bills_today_count = Billing.objects.filter(created_at__date=today).count()
    all_time_processed = Billing.objects.exclude(handled_by__isnull=True).count()

    recent_bills = Billing.objects.select_related("patient", "consultation").order_by("-updated_at")[:10]

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

    bills = Billing.objects.select_related("patient", "consultation").order_by("-updated_at")
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
    else:
        billing_form = BillingUpdateForm(instance=billing)
        payment_form = PaymentTransactionForm()

    payments = billing.payments.select_related("received_by").order_by("-created_at")

    return render(
        request,
        "billing/billing_detail.html",
        {
            "billing": billing,
            "billing_form": billing_form,
            "payment_form": payment_form,
            "payments": payments,
        },
    )