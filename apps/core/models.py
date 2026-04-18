from django.db import models


class HospitalSetting(models.Model):
    hospital_name = models.CharField(max_length=255, default="Hospital Management System")
    short_name = models.CharField(max_length=50, default="HMS")
    hospital_address = models.TextField(blank=True)
    hospital_phone = models.CharField(max_length=50, blank=True)
    hospital_email = models.EmailField(blank=True)
    hospital_website = models.URLField(blank=True)
    hospital_motto = models.CharField(max_length=255, blank=True)
    hospital_logo = models.ImageField(upload_to="hospital/", blank=True, null=True)

    currency_symbol = models.CharField(max_length=10, default="₦")
    timezone_label = models.CharField(max_length=100, default="Africa/Lagos")
    default_e_card_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    record_retention_days = models.PositiveIntegerField(default=3650)

    backup_instructions = models.TextField(
        blank=True,
        help_text="Internal instructions for backup/export operations.",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hospital Setting"
        verbose_name_plural = "Hospital Settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.hospital_name