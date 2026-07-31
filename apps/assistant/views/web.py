from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from apps.assistant.forms import AskForm, ManualKnowledgeForm
from apps.assistant.models import ChatSession, KnowledgeChunk, KnowledgeSource
from apps.assistant.services.indexing import reindex_all, reindex_source
from apps.assistant.services.rag import ask_question
from apps.assistant.tasks import task_reindex_all


def _can_view(user) -> bool:
    return bool(user.is_authenticated)


def _can_write(user) -> bool:
    return bool(
        user.is_authenticated
        and (user.is_superuser or user.role in {"admin", "dsi", "manager"})
    )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(_can_view), name="dispatch")
class AssistantChatView(View):
    template_name = "assistant/chat.html"

    def get(self, request):
        session_id = request.GET.get("session")
        session = None
        if session_id:
            session = get_object_or_404(ChatSession, pk=session_id, user=request.user)
        sessions = ChatSession.objects.filter(user=request.user)[:20]
        stats = {
            "sources": KnowledgeSource.objects.filter(is_active=True).count(),
            "chunks": KnowledgeChunk.objects.count(),
        }
        return render(
            request,
            self.template_name,
            {
                "form": AskForm(),
                "session": session,
                "sessions": sessions,
                "messages_list": list(session.messages.all()) if session else [],
                "stats": stats,
                "can_write": _can_write(request.user),
                "knowledge_form": ManualKnowledgeForm() if _can_write(request.user) else None,
            },
        )

    def post(self, request):
        action = request.POST.get("action", "ask")
        if action == "reindex":
            if not _can_write(request.user):
                messages.error(request, "Droits insuffisants pour réindexer.")
                return redirect("assistant:chat")
            async_mode = request.POST.get("async") == "1"
            if async_mode:
                task_reindex_all.delay()
                messages.success(request, "Réindexation lancée en arrière-plan (Celery).")
            else:
                stats = reindex_all()
                messages.success(
                    request,
                    f"Réindexation terminée — {stats['sources']} sources, {stats['chunks']} chunks.",
                )
            return redirect("assistant:chat")

        if action == "add_note":
            if not _can_write(request.user):
                messages.error(request, "Droits insuffisants.")
                return redirect("assistant:chat")
            form = ManualKnowledgeForm(request.POST)
            if form.is_valid():
                import uuid

                source = form.save(commit=False)
                source.source_type = KnowledgeSource.SourceType.MANUAL
                source.source_id = f"manual-{uuid.uuid4().hex[:12]}"
                source.save()
                reindex_source(source)
                messages.success(request, f"Note « {source.title} » indexée.")
                return redirect("assistant:chat")
            messages.error(request, "Note invalide — vérifiez le formulaire.")
            return redirect("assistant:chat")

        form = AskForm(request.POST)
        session = None
        session_id = request.POST.get("session_id")
        if session_id:
            session = get_object_or_404(ChatSession, pk=session_id, user=request.user)

        if form.is_valid():
            result = ask_question(
                user=request.user,
                question=form.cleaned_data["question"],
                session=session,
            )
            return redirect(f"{request.path}?session={result['session_id']}")

        sessions = ChatSession.objects.filter(user=request.user)[:20]
        stats = {
            "sources": KnowledgeSource.objects.filter(is_active=True).count(),
            "chunks": KnowledgeChunk.objects.count(),
        }
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "session": session,
                "sessions": sessions,
                "messages_list": list(session.messages.all()) if session else [],
                "stats": stats,
                "can_write": _can_write(request.user),
                "knowledge_form": ManualKnowledgeForm() if _can_write(request.user) else None,
            },
        )
