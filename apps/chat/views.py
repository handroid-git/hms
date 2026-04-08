from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from .forms import MessageForm, StartConversationForm
from .models import Conversation, Message
from .services import get_or_create_direct_conversation, mark_conversation_read, send_message


@login_required
def conversation_list(request):
    conversations = (
        request.user.chat_conversations.annotate(
            last_message_time=Max("messages__created_at"),
            unread_count=Count(
                "messages",
                filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user),
            ),
        )
        .prefetch_related("participants")
        .order_by("-last_message_time", "-updated_at")
    )

    start_form = StartConversationForm()
    start_form.fields["recipient"].queryset = start_form.fields["recipient"].queryset.exclude(pk=request.user.pk)

    return render(
        request,
        "chat/conversation_list.html",
        {
            "conversations": conversations,
            "start_form": start_form,
        },
    )


@login_required
def start_conversation(request):
    if request.method != "POST":
        return redirect("conversation_list")

    form = StartConversationForm(request.POST)
    form.fields["recipient"].queryset = form.fields["recipient"].queryset.exclude(pk=request.user.pk)

    if form.is_valid():
        recipient = form.cleaned_data["recipient"]
        conversation, _ = get_or_create_direct_conversation(request.user, recipient)
        return redirect("conversation_detail", pk=conversation.pk)

    conversations = (
        request.user.chat_conversations.annotate(
            last_message_time=Max("messages__created_at"),
            unread_count=Count(
                "messages",
                filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user),
            ),
        )
        .prefetch_related("participants")
        .order_by("-last_message_time", "-updated_at")
    )

    return render(
        request,
        "chat/conversation_list.html",
        {
            "conversations": conversations,
            "start_form": form,
        },
    )


@login_required
def conversation_detail(request, pk):
    conversation = get_object_or_404(
        request.user.chat_conversations.prefetch_related("participants", "messages__sender"),
        pk=pk,
    )

    mark_conversation_read(conversation, request.user)

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = send_message(
                conversation=conversation,
                sender=request.user,
                body=form.cleaned_data["body"],
            )

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "message": {
                            "id": str(message.pk),
                            "body": message.body,
                            "sender_name": message.sender.get_full_name() or message.sender.username,
                            "is_mine": True,
                            "created_at": message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        },
                    }
                )

            messages.success(request, "Message sent.")
            return redirect("conversation_detail", pk=conversation.pk)
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": False,
                        "errors": form.errors,
                    },
                    status=400,
                )
    else:
        form = MessageForm()

    other_participants = conversation.participants.exclude(pk=request.user.pk)

    return render(
        request,
        "chat/conversation_detail.html",
        {
            "conversation": conversation,
            "messages_list": conversation.messages.select_related("sender").all(),
            "other_participants": other_participants,
            "form": form,
        },
    )


@login_required
def conversation_messages_json(request, pk):
    conversation = get_object_or_404(
        request.user.chat_conversations.prefetch_related("messages__sender"),
        pk=pk,
    )

    mark_conversation_read(conversation, request.user)

    messages_data = [
        {
            "id": str(message.pk),
            "body": message.body,
            "sender_name": message.sender.get_full_name() or message.sender.username,
            "is_mine": message.sender_id == request.user.pk,
            "created_at": message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for message in conversation.messages.select_related("sender").all()
    ]

    return JsonResponse(
        {
            "messages": messages_data,
        }
    )


@login_required
def chat_unread_count(request):
    unread_chat_count = Message.objects.filter(
        conversation__participants=request.user,
        is_read=False,
    ).exclude(sender=request.user).count()

    return JsonResponse(
        {
            "unread_chat_count": unread_chat_count,
        }
    )