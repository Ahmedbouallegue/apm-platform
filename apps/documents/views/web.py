from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, ListView

from apps.applications.models import Application
from apps.documents.forms import DocumentForm
from apps.documents.models import Document
from apps.documents.selectors.documents import document_list, tag_list
from apps.documents.services.documents import (
    document_create,
    document_soft_delete,
    document_update,
)


def _can_view(user) -> bool:
    return bool(user.is_authenticated)


def _can_write(user) -> bool:
    return bool(
        user.is_authenticated
        and (user.is_superuser or user.role in {"admin", "dsi", "manager"})
    )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class DocumentListView(ListView):
    template_name = "documents/list.html"
    context_object_name = "documents"
    paginate_by = 15

    def get_queryset(self):
        active = self.request.GET.get("active")
        is_active = None
        if active == "1":
            is_active = True
        elif active == "0":
            is_active = False
        application_id = self.request.GET.get("application") or None
        return document_list(
            search=self.request.GET.get("q") or None,
            category=self.request.GET.get("category") or None,
            application_id=int(application_id) if application_id and application_id.isdigit() else None,
            tag=self.request.GET.get("tag") or None,
            is_active=is_active,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Document.Category.choices
        ctx["applications"] = Application.objects.filter(is_deleted=False).order_by("name")
        ctx["tags"] = tag_list()
        ctx["q"] = self.request.GET.get("q", "")
        ctx["category"] = self.request.GET.get("category", "")
        ctx["application"] = self.request.GET.get("application", "")
        ctx["tag"] = self.request.GET.get("tag", "")
        ctx["active"] = self.request.GET.get("active", "")
        ctx["can_write"] = _can_write(self.request.user)
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class DocumentDetailView(DetailView):
    template_name = "documents/detail.html"
    context_object_name = "document"

    def get_queryset(self):
        return document_list()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_write"] = _can_write(self.request.user)
        return ctx


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_write), name="dispatch")
class DocumentCreateView(View):
    template_name = "documents/form.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": DocumentForm(), "title": "Nouveau document", "mode": "create"},
        )

    def post(self, request):
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = document_create(data=form.cleaned_data, user=request.user)
            messages.success(request, f"Document « {document.title} » créé.")
            return redirect("documents:detail", pk=document.pk)
        return render(
            request,
            self.template_name,
            {"form": form, "title": "Nouveau document", "mode": "create"},
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_write), name="dispatch")
class DocumentUpdateView(View):
    template_name = "documents/form.html"

    def get(self, request, pk):
        document = get_object_or_404(document_list(), pk=pk)
        return render(
            request,
            self.template_name,
            {
                "form": DocumentForm(instance=document),
                "title": f"Modifier — {document.title}",
                "mode": "edit",
                "document": document,
            },
        )

    def post(self, request, pk):
        document = get_object_or_404(document_list(), pk=pk)
        form = DocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            document_update(document=document, data=form.cleaned_data, user=request.user)
            messages.success(request, "Document mis à jour.")
            return redirect("documents:detail", pk=document.pk)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "title": f"Modifier — {document.title}",
                "mode": "edit",
                "document": document,
            },
        )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_write), name="dispatch")
class DocumentDeleteView(View):
    def post(self, request, pk):
        document = get_object_or_404(document_list(), pk=pk)
        label = document.title
        document_soft_delete(document=document, user=request.user)
        messages.warning(request, f"Document « {label} » archivé.")
        return redirect("documents:list")
