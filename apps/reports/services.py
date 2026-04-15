from django.utils import timezone


def apply_date_filter(queryset, start_date=None, end_date=None, field_name="created_at"):
    if start_date:
        queryset = queryset.filter(**{f"{field_name}__date__gte": start_date})
    if end_date:
        queryset = queryset.filter(**{f"{field_name}__date__lte": end_date})
    return queryset


def get_default_report_dates():
    today = timezone.localdate()
    return today, today