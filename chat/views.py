import json

from django.db import transaction
from django.db.models import OuterRef, Q, Subquery
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import (
    require_GET,
    require_POST,
    require_http_methods,
)

from accounts.permissions import api_login_required
from items.models import Report

from .forms import MessageForm
from .models import Conversation, Message, MessageNotification


def _json_object(request, allowed_fields):
    if request.content_type != "application/json":
        return None, JsonResponse(
            {"errors": {"request": ["Send application/json."]}},
            status=415,
        )

    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return None, JsonResponse(
            {"errors": {"request": ["Invalid JSON."]}},
            status=400,
        )

    if not isinstance(data, dict):
        return None, JsonResponse(
            {"errors": {"request": ["Send a JSON object."]}},
            status=400,
        )

    if set(data) - allowed_fields:
        return None, JsonResponse(
            {"errors": {"request": ["Unexpected request field."]}},
            status=400,
        )

    return data, None


def _serialize_message(message):
    return {
        "id": message.pk,
        "sender": {
            "id": message.sender_id,
            "full_name": message.sender.full_name,
        },
        "body": message.body,
        "created_at": message.created_at.isoformat(),
    }


def _serialize_conversation(conversation, current_user):
    if conversation.report.author_id == current_user.pk:
        other_participant = conversation.seeker
    else:
        other_participant = conversation.report.author

    last_message_body = getattr(conversation, "last_message_body", None)
    last_message_at = getattr(conversation, "last_message_at", None)
    last_message = None
    if last_message_body is not None:
        last_message = {
            "body": last_message_body,
            "created_at": last_message_at.isoformat(),
        }

    return {
        "id": conversation.pk,
        "report": {
            "id": conversation.report_id,
            "title": conversation.report.title,
            "item_type": conversation.report.item_type,
            "is_resolved": conversation.report.is_resolved,
        },
        "other_participant": {
            "id": other_participant.pk,
            "full_name": other_participant.full_name,
        },
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "last_message": last_message,
    }


def _accessible_conversation(conversation_id, user):
    """Find a conversation only if the user is one of its participants."""
    return (
        Conversation.objects.select_related(
            "report",
            "report__author",
            "seeker",
        )
        .filter(pk=conversation_id)
        .filter(Q(seeker=user) | Q(report__author=user))
        .first()
    )


@never_cache
@require_POST
@csrf_protect
@api_login_required
@transaction.atomic
def conversation_start(request, report_id):
    """Open an existing conversation or start one on an open report."""
    report = Report.objects.select_for_update().filter(pk=report_id).first()
    if report is None:
        return JsonResponse(
            {"errors": {"report": ["Report not found."]}},
            status=404,
        )

    if report.author_id == request.user.pk:
        return JsonResponse(
            {"errors": {"conversation": ["You cannot chat about your own report."]}},
            status=400,
        )

    if report.is_resolved:
        conversation = Conversation.objects.filter(
            report=report, seeker=request.user,
        ).first()
        if conversation is None:
            return JsonResponse(
                {"errors": {"report": ["Resolved reports cannot start new conversations."]}},
                status=409,
            )
        created = False
    else:
        conversation, created = Conversation.objects.get_or_create(
            report=report,
            seeker=request.user,
        )
    conversation = (
        Conversation.objects.select_related(
            "report",
            "report__author",
            "seeker",
        )
        .get(pk=conversation.pk)
    )

    return JsonResponse(
        {
            "conversation": _serialize_conversation(
                conversation,
                request.user,
            )
        },
        status=201 if created else 200,
    )


@never_cache
@require_GET
@api_login_required
def conversation_list(request):
    """Return the conversations in which the current user participates."""
    latest_messages = Message.objects.filter(
        conversation_id=OuterRef("pk")
    ).order_by("-created_at", "-pk")
    conversations = (
        Conversation.objects.filter(
            Q(seeker=request.user) | Q(report__author=request.user)
        )
        .select_related("report", "report__author", "seeker")
        .annotate(
            last_message_body=Subquery(
                latest_messages.values("body")[:1]
            ),
            last_message_at=Subquery(
                latest_messages.values("created_at")[:1]
            ),
        )
        .order_by("-updated_at", "-pk")
    )

    return JsonResponse(
        {
            "conversations": [
                _serialize_conversation(conversation, request.user)
                for conversation in conversations
            ]
        }
    )


def _message_list(request, conversation):
    messages = conversation.messages.select_related("sender").all()
    return JsonResponse(
        {"messages": [_serialize_message(message) for message in messages]}
    )


def _message_create(request, conversation):
    data, error = _json_object(request, {"body"})
    if error is not None:
        return error

    form = MessageForm(data)
    if not form.is_valid():
        errors = {
            field: [str(error) for error in field_errors]
            for field, field_errors in form.errors.items()
        }
        return JsonResponse({"errors": errors}, status=400)

    body = form.cleaned_data["body"]

    with transaction.atomic():
        report = Report.objects.select_for_update().get(pk=conversation.report_id)
        if report.is_resolved:
            return JsonResponse(
                {"errors": {"report": ["Resolved reports cannot receive new messages."]}},
                status=409,
            )

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            body=body,
        )
        recipient_id = (
            conversation.seeker_id
            if request.user.pk == report.author_id
            else report.author_id
        )
        MessageNotification.objects.create(
            message=message, recipient_id=recipient_id,
        )
        updated_at = timezone.now()
        Conversation.objects.filter(pk=conversation.pk).update(
            updated_at=updated_at
        )
        conversation.updated_at = updated_at

    message = Message.objects.select_related("sender").get(pk=message.pk)
    return JsonResponse(
        {"message": _serialize_message(message)},
        status=201,
    )


@never_cache
@require_http_methods(["GET", "POST"])
@csrf_protect
@api_login_required
def message_collection(request, conversation_id):
    """List or send messages after checking conversation membership."""
    conversation = _accessible_conversation(
        conversation_id,
        request.user,
    )
    if conversation is None:
        return JsonResponse(
            {"errors": {"conversation": ["Conversation not found."]}},
            status=404,
        )

    if request.method == "GET":
        return _message_list(request, conversation)

    return _message_create(request, conversation)
