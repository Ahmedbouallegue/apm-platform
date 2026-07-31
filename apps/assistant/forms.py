from django import forms

from apps.assistant.models import KnowledgeSource
from apps.core.validators import require_non_empty


class ManualKnowledgeForm(forms.ModelForm):
    class Meta:
        model = KnowledgeSource
        fields = ("title", "content", "is_active")
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "field-input",
                    "data-validate": "required|min:3|max:255",
                    "placeholder": "Ex. Procédure bascule PROD CRM",
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "field-input",
                    "rows": 8,
                    "data-validate": "required|min:20",
                    "placeholder": "Contenu métier à indexer pour l'assistant…",
                }
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "field-check"}),
        }

    def clean_title(self):
        return require_non_empty(self.cleaned_data.get("title"), "Le titre")

    def clean_content(self):
        return require_non_empty(self.cleaned_data.get("content"), "Le contenu")


class AskForm(forms.Form):
    question = forms.CharField(
        label="Votre question",
        widget=forms.Textarea(
            attrs={
                "class": "field-input",
                "rows": 3,
                "data-validate": "required|min:5|max:2000",
                "placeholder": "Ex. Quelles applications critiques utilisent PostgreSQL ?",
            }
        ),
    )
