from django.db import transaction
from apps.notifications.services import create_notification
from .models import Conversation, Message, MessageReadReceipt


def get_or_create_direct_conversation(user1, user2):
    conversations = Conversation.objects.filter(participants=user1).filter(participants=user2).distinct()

    for conversation in conversations:
        if conversation.participants.count() == 2:
            return conversation, False

    conversation = Conversation.objects.create()
    conversation.participants.add(user1, user2)
    return conversation, True


@transaction.atomic
def send_message(conversation, sender, body):
    message = Message.objects.create(
        conversation=conversation,
        sender=sender,
        body=body,
        is_read=False,
    )

    conversation.save(update_fields=["updated_at"])

    recipients = conversation.participants.exclude(pk=sender.pk)
    for recipient in recipients:
        create_notification(
            user=recipient,
            title="New Chat Message",
            message=f"You received a new message from {sender.get_full_name() or sender.username}.",
            notification_type="INFO",
            link=f"/chat/conversations/{conversation.pk}/",
        )

    return message


@transaction.atomic
def mark_conversation_read(conversation, user):
    unread_messages = conversation.messages.exclude(sender=user).filter(is_read=False)

    for message in unread_messages:
        message.is_read = True
        message.save(update_fields=["is_read"])
        MessageReadReceipt.objects.get_or_create(message=message, user=user)