from .models import HospitalSetting


def hospital_identity(request):
    settings_obj = HospitalSetting.get_solo()
    return {
        "hospital_settings": settings_obj,
        "hospital_name": settings_obj.hospital_name,
        "hospital_short_name": settings_obj.short_name,
        "hospital_currency_symbol": settings_obj.currency_symbol,
    }