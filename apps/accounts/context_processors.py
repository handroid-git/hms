from django.utils import timezone


def dashboard_identity(request):
    if not request.user.is_authenticated:
        return {
            "is_dashboard_page": False,
            "dashboard_identity_label": "",
            "dashboard_welcome_until": "",
        }

    resolver_match = getattr(request, "resolver_match", None)
    url_name = getattr(resolver_match, "url_name", "") or ""

    is_dashboard_page = (
        "dashboard" in url_name and url_name != "dashboard_redirect"
    )

    role_label = getattr(request.user, "get_role_display", lambda: "")()
    full_name = request.user.get_full_name().strip() or request.user.username
    dashboard_identity_label = f"{role_label} {full_name}".strip()

    dashboard_welcome_until = request.session.get("dashboard_welcome_until", "")

    return {
        "is_dashboard_page": is_dashboard_page,
        "dashboard_identity_label": dashboard_identity_label,
        "dashboard_welcome_until": dashboard_welcome_until,
    }