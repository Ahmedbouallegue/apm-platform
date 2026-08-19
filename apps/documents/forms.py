from django import forms

from apps.applications.models import Application
from apps.core.validators import require_non_empty
from apps.documents.models import Document, Tag


class DocumentForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all().order_by("name"),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "field-input", "size": "6"}),
        label="Tags",
    )

    class Meta:
        model = Document
        fields = (
            "title",
            "file_type",
            "category",
            "description",
            "file",
            "application",
            "tags",
            "is_active",
        )
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "field-input", "data-validate": "required|min:3|max:255"}
            ),
            "file_type": forms.TextInput(
                attrs={"class": "field-input", "placeholder": "PDF, DOCX…", "data-validate": "max:64"}
            ),
            "category": forms.Select(attrs={"class": "field-input", "data-validate": "required"}),
            "description": forms.Textarea(attrs={"class": "field-input", "rows": 3}),
            "file": forms.ClearableFileInput(attrs={"class": "field-input"}),
            "application": forms.Select(attrs={"class": "field-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "field-check"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["application"].queryset = Application.objects.filter(is_deleted=False)
        self.fields["application"].required = False
        self.fields["file"].required = False
        self.fields["file_type"].required = False
        self.fields["description"].required = False

    def clean_title(self):
        return require_non_empty(self.cleaned_data.get("title"), "Le titre")

    def clean_file(self):
        from django.conf import settings

        uploaded = self.cleaned_data.get("file")
        from apps.core.validators import validate_uploaded_document

        max_bytes = int(getattr(settings, "MAX_UPLOAD_SIZE_BYTES", 10 * 1024 * 1024))
        validate_uploaded_document(uploaded, max_bytes=max_bytes)
        return uploaded
