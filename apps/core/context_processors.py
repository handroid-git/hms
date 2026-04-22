from .models import HospitalSetting


def hospital_identity(request):
    hospital_settings = HospitalSetting.get_solo()
    return {
        "hospital_settings": hospital_settings,
        "hospital_name": hospital_settings.hospital_name,
        "hospital_short_name": hospital_settings.short_name,
        "hospital_logo": hospital_settings.hospital_logo,
        "hospital_currency_symbol": hospital_settings.currency_symbol,
        "hospital_timezone_label": hospital_settings.timezone_label,
        "hospital_default_e_card_fee": hospital_settings.default_e_card_fee,
    }