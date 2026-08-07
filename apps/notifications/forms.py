from django import forms

from apps.notifications.models import PlatformSettings


class PlatformSettingsForm(forms.ModelForm):
    class Meta:
        model = PlatformSettings
        fields = (
            "alert_days_60",
            "alert_days_30",
            "alert_on_expiry",
            "alert_cooldown_days",
        )
        widgets = {
            "alert_days_60": forms.NumberInput(
                attrs={"class": "field-input", "min": 1, "max": 365}
            ),
            "alert_days_30": forms.NumberInput(
                attrs={"class": "field-input", "min": 1, "max": 365}
            ),
            "alert_on_expiry": forms.CheckboxInput(attrs={"class": "field-check"}),
            "alert_cooldown_days": forms.NumberInput(
                attrs={"class": "field-input", "min": 1, "max": 90}
            ),
        }

    def clean(self):
        cleaned = super().clean()
        d60 = cleaned.get("alert_days_60")
        d30 = cleaned.get("alert_days_30")
        if d60 is not None and d30 is not None and d30 > d60:
            self.add_error(
                "alert_days_30",
                "Le seuil J-30 doit être inférieur ou égal au seuil J-60.",
            )
        return cleaned
