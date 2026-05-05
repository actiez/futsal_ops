import json
import urllib.request
import urllib.error
from datetime import datetime, time, timedelta

from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from accounts.models import User
from events.models import Event
from registrations.models import EventRegistration
from registrations.services import register_user_for_event, rebalance_event_slots
from system_settings.models import SystemSettings

from .models import BotMessageLog, BotSession

def normalize_phone_number(phone_number):
    """
    Normalize SG numbers for matching.
    Examples:
    +6591234567 -> 91234567
    6591234567 -> 91234567
    9123 4567 -> 91234567
    """
    if not phone_number:
        return ""

    cleaned = (
        phone_number
        .replace("+", "")
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    if cleaned.startswith("65") and len(cleaned) == 10:
        cleaned = cleaned[2:]

    return cleaned


def get_user_by_phone(phone_number):
    normalized = normalize_phone_number(phone_number)

    if not normalized:
        return None, normalized

    user = User.objects.filter(mobile_number=normalized).first()

    if not user:
        user = User.objects.filter(mobile_number=f"+65{normalized}").first()

    return user, normalized


def build_help_reply(user):
    if user and user.is_admin_level():
        return (
            "Hi, I’m Pepz ⚽\n\n"
            "Player commands:\n"
            "JOIN <event code>\n"
            "STATUS <event code>\n"
            "LEAVE <event code>\n\n"
            "Admin commands:\n"
            "ADMIN HELP\n"
            "EVENT SUMMARY <event code>\n"
            "SEND INVITE <event code>\n\n"
            "Example:\n"
            "JOIN EVT-9K2XQ7"
        )

    return (
        "Hi, I’m Pepz ⚽\n\n"
        "You can send:\n"
        "JOIN <event code>\n"
        "STATUS <event code>\n"
        "LEAVE <event code>\n"
        "HELP\n\n"
        "Example:\n"
        "JOIN EVT-9K2XQ7"
    )

def extract_event_code(normalized_message):
    parts = normalized_message.split()

    for part in parts:
        if part.startswith("EVT-"):
            return part.strip()

    return None


def get_bot_visible_status(registration, event):
    if not registration:
        return None

    if registration.status == EventRegistration.STATUS_PLAYING:
        return {
            "label": "Playing",
            "queue_number": None,
        }

    if registration.status == EventRegistration.STATUS_WAITING:
        waiting_regs = (
            event.registrations
            .filter(status=EventRegistration.STATUS_WAITING)
            .order_by("sequence_number", "id")
        )

        queue_number = 1
        for reg in waiting_regs:
            if reg.id == registration.id:
                break
            queue_number += 1

        return {
            "label": "Waiting",
            "queue_number": queue_number,
        }

    return {
        "label": "Pending",
        "queue_number": None,
    }


def format_event_brief(event):
    return (
        f"{event.weekday_display}, {event.date_display}\n"
        f"{event.time_range_display}\n"
        f"{event.location}"
    )


def build_status_reply(user, event_code):
    if not user:
        return (
            "I couldn’t find an account linked to this WhatsApp number.\n\n"
            "Please register an account or update your mobile number in your profile first."
        )

    if not event_code:
        return (
            "Please include the event code.\n\n"
            "Example:\n"
            "STATUS EVT-9K2XQ7"
        )

    event = Event.objects.filter(event_code=event_code).first()

    if not event:
        return (
            "I couldn’t find that game.\n\n"
            "Please check the event code or ask the organiser to resend the invite."
        )

    registration = (
        EventRegistration.objects
        .filter(event=event, user=user)
        .first()
    )

    if not registration:
        return (
            "You are not registered for this game yet.\n\n"
            f"{format_event_brief(event)}\n\n"
            "To register, send:\n"
            f"JOIN {event.event_code}"
        )

    visible_status = get_bot_visible_status(registration, event)

    if visible_status["label"] == "Waiting":
        status_text = f"Waiting (#{visible_status['queue_number']})"
    else:
        status_text = visible_status["label"]

    return (
        "Your status for this game:\n\n"
        f"{format_event_brief(event)}\n\n"
        f"Status: {status_text}"
    )

def get_weekly_registration_conflict(user, event):
    settings_obj = SystemSettings.get_solo()

    if not settings_obj.only_allow_once_per_week_registration:
        return None

    local_start = timezone.localtime(event.start_datetime)
    week_start_date = local_start.date() - timedelta(days=local_start.weekday())
    week_end_date = week_start_date + timedelta(days=7)

    week_start_dt = timezone.make_aware(
        datetime.combine(week_start_date, time.min),
        timezone.get_current_timezone(),
    )
    week_end_dt = timezone.make_aware(
        datetime.combine(week_end_date, time.min),
        timezone.get_current_timezone(),
    )

    return (
        EventRegistration.objects
        .filter(
            user=user,
            event__start_datetime__gte=week_start_dt,
            event__start_datetime__lt=week_end_dt,
        )
        .exclude(event=event)
        .exclude(status=EventRegistration.STATUS_REMOVED)
        .select_related("event")
        .first()
    )

def build_join_reply(user, event_code):
    if not user:
        return (
            "I couldn’t find an account linked to this WhatsApp number.\n\n"
            "Please register an account or update your mobile number in your profile first."
        )

    if not event_code:
        return (
            "Please include the event code.\n\n"
            "Example:\n"
            "JOIN EVT-9K2XQ7"
        )

    event = Event.objects.filter(event_code=event_code).first()

    if not event:
        return (
            "I couldn’t find that game.\n\n"
            "Please check the event code or ask the organiser to resend the invite."
        )

    if event.status == Event.STATUS_CANCELLED:
        return "This game has been cancelled."

    if timezone.now() >= event.start_datetime:
        return "Registration for this game is closed."

    existing_registration = (
        EventRegistration.objects
        .filter(event=event, user=user)
        .first()
    )

    if existing_registration:
        visible_status = get_bot_visible_status(existing_registration, event)

        if visible_status["label"] == "Waiting":
            status_text = f"Waiting (#{visible_status['queue_number']})"
        else:
            status_text = visible_status["label"]

        return (
            "You are already registered for this game.\n\n"
            f"{format_event_brief(event)}\n\n"
            f"Status: {status_text}"
        )

    weekly_conflict = get_weekly_registration_conflict(user, event)

    if weekly_conflict:
        conflict_event = weekly_conflict.event

        return (
            "You are already registered for another game this week:\n\n"
            f"{format_event_brief(conflict_event)}\n\n"
            "To keep slots fair, each player can only register for one game per week."
        )

    registration, created = register_user_for_event(
        event,
        user,
        changed_by=user,
    )

    if created and hasattr(registration, "source"):
        registration.source = EventRegistration.SOURCE_WHATSAPP
        registration.save(update_fields=["source"])

    visible_status = get_bot_visible_status(registration, event)

    if visible_status["label"] == "Waiting":
        status_text = f"Waiting (#{visible_status['queue_number']})"
    else:
        status_text = visible_status["label"]

    return (
        "You’re registered for:\n\n"
        f"{format_event_brief(event)}\n\n"
        f"Status: {status_text}"
    )

def clear_bot_session(phone_number):
    BotSession.objects.filter(phone_number=phone_number).delete()


def get_active_bot_session(phone_number):
    session = BotSession.objects.filter(phone_number=phone_number).first()

    if not session:
        return None

    if session.expires_at <= timezone.now():
        session.delete()
        return None

    return session


def create_bot_session(phone_number, user, current_flow, step, context_data, minutes=10):
    BotSession.objects.filter(phone_number=phone_number).delete()

    return BotSession.objects.create(
        phone_number=phone_number,
        user=user,
        current_flow=current_flow,
        step=step,
        context_data=context_data,
        expires_at=timezone.now() + timedelta(minutes=minutes),
    )

def build_leave_request_reply(user, event_code, phone_number):
    if not user:
        return (
            "I couldn’t find an account linked to this WhatsApp number.\n\n"
            "Please register an account or update your mobile number in your profile first."
        )

    if not event_code:
        return (
            "Please include the event code.\n\n"
            "Example:\n"
            "LEAVE EVT-9K2XQ7"
        )

    event = Event.objects.filter(event_code=event_code).first()

    if not event:
        return (
            "I couldn’t find that game.\n\n"
            "Please check the event code or ask the organiser to resend the invite."
        )

    if timezone.now() >= event.start_datetime:
        return "This game has already started or ended, so leaving is closed."

    registration = (
        EventRegistration.objects
        .filter(event=event, user=user)
        .first()
    )

    if not registration:
        return (
            "You are not registered for this game.\n\n"
            f"{format_event_brief(event)}"
        )

    create_bot_session(
        phone_number=phone_number,
        user=user,
        current_flow="leave_event",
        step="awaiting_confirm",
        context_data={"event_code": event.event_code},
        minutes=10,
    )

    return (
        "Are you sure you want to leave this game?\n\n"
        f"{format_event_brief(event)}\n\n"
        "If you join again later, you may need to queue again.\n\n"
        "Reply CONFIRM to leave."
    )

def handle_confirm_reply(user, phone_number):
    session = get_active_bot_session(phone_number)

    if not session:
        return (
            "I don’t have anything pending for you to confirm.\n\n"
            "Send HELP to see what I can do."
        )

    if session.current_flow == "leave_event" and session.step == "awaiting_confirm":
        event_code = session.context_data.get("event_code")
        event = Event.objects.filter(event_code=event_code).first()

        if not event:
            clear_bot_session(phone_number)
            return "I couldn’t find that game anymore. Please ask the organiser to resend the invite."

        registration = (
            EventRegistration.objects
            .filter(event=event, user=user)
            .first()
        )

        if not registration:
            clear_bot_session(phone_number)
            return "You are not registered for this game."

        registration.delete()
        rebalance_event_slots(event, changed_by=user)

        clear_bot_session(phone_number)

        return (
            "You have left the game.\n\n"
            "If you register again later, you may need to queue again."
        )
    
    if session.current_flow == "send_invite" and session.step == "awaiting_confirm":
        event_code = session.context_data.get("event_code")
        invite_text = session.context_data.get("invite_text", "")

        clear_bot_session(phone_number)

        return (
            "Invite confirmed.\n\n"
            "Broadcast sending is not connected yet.\n\n"
            "This is the invite text that will be sent later:\n\n"
            f"{invite_text}"
        )

    return (
        "I don’t have anything pending for that command.\n\n"
        "Send HELP to see what I can do."
    )

def handle_cancel_reply(phone_number):
    session = get_active_bot_session(phone_number)

    if not session:
        return "There’s nothing pending to cancel."

    clear_bot_session(phone_number)
    return "Okay, I’ve cancelled the current action."

def get_display_name(user):
    return user.get_full_name() or user.username


def build_event_summary_text(event):
    playing_regs = (
        event.registrations
        .filter(status=EventRegistration.STATUS_PLAYING)
        .select_related("user")
        .order_by("sequence_number", "id")
    )

    waiting_regs = (
        event.registrations
        .filter(status=EventRegistration.STATUS_WAITING)
        .select_related("user")
        .order_by("sequence_number", "id")
    )

    lines = [
        f"{event.weekday_display}, {event.date_display}",
        event.time_range_display,
        event.location,
        f"${event.amount_payable} per pax",
        "",
        f"Playing ({playing_regs.count()}):",
    ]

    if playing_regs.exists():
        for idx, reg in enumerate(playing_regs, start=1):
            lines.append(f"{idx}. {get_display_name(reg.user)}")
    else:
        lines.append("-")

    lines.extend([
        "",
        f"Waiting ({waiting_regs.count()}):",
    ])

    if waiting_regs.exists():
        for idx, reg in enumerate(waiting_regs, start=1):
            lines.append(f"{idx}. {get_display_name(reg.user)}")
    else:
        lines.append("-")

    lines.extend([
        "",
        "PM me if you want to register or leave the game.",
    ])

    return "\n".join(lines)


def build_event_summary_reply(user, event_code):
    if not user or not user.is_admin_level():
        return "You don’t have admin access for this command."

    if not event_code:
        return (
            "Please include the event code.\n\n"
            "Example:\n"
            "EVENT SUMMARY EVT-9K2XQ7"
        )

    event = Event.objects.filter(event_code=event_code).first()

    if not event:
        return (
            "I couldn’t find that game.\n\n"
            "Please check the event code or ask the organiser to resend the invite."
        )

    return build_event_summary_text(event)

def build_event_invite_text(event):
    pepz_number = "65XXXXXXXX"  # replace later with actual Pepz number

    pepz_join_link = (
        f"https://wa.me/{pepz_number}?text=JOIN%20{event.event_code}"
    )

    lines = [
        "⚽ Futsal Session",
        "",
        f"{event.weekday_display}, {event.date_display}",
        event.time_range_display,
        event.location,
        f"${event.amount_payable} per pax",
        "",
        f"Playing slots: {event.playing_slots}",
        f"Waiting slots: {event.waiting_slots}",
        "",
        "PM Pepz to register or leave:",
        pepz_join_link,
    ]

    return "\n".join(lines)

def build_send_invite_reply(user, event_code, phone_number):
    if not user or not user.is_admin_level():
        return "You don’t have admin access for this command."

    if not event_code:
        return (
            "Please include the event code.\n\n"
            "Example:\n"
            "SEND INVITE EVT-9K2XQ7"
        )

    event = Event.objects.filter(event_code=event_code).first()

    if not event:
        return (
            "I couldn’t find that game.\n\n"
            "Please check the event code or ask the organiser to resend the invite."
        )

    invite_text = build_event_invite_text(event)

    create_bot_session(
        phone_number=phone_number,
        user=user,
        current_flow="send_invite",
        step="awaiting_confirm",
        context_data={
            "event_code": event.event_code,
            "invite_text": invite_text,
        },
        minutes=10,
    )

    return (
        "Ready to send invite:\n\n"
        f"{invite_text}\n\n"
        "Reply CONFIRM to approve sending."
    )

def detect_basic_intent(normalized_message):
    if normalized_message in {"HELP", "HI", "HELLO", "START"}:
        return "HELP"

    if normalized_message == "CANCEL":
        return "CANCEL"

    if normalized_message == "CONFIRM":
        return "CONFIRM"

    if normalized_message.startswith("EVENT SUMMARY"):
        return "EVENT_SUMMARY"

    if normalized_message.startswith("SEND INVITE"):
        return "SEND_INVITE"

    if normalized_message.startswith("STATUS"):
        return "STATUS"

    if normalized_message.startswith("JOIN"):
        return "JOIN"

    if normalized_message.startswith("LEAVE"):
        return "LEAVE"

    return "UNKNOWN"


def is_overall_spam(phone_number):
    """
    More than 8 messages from same phone number within 60 seconds = silent ignore.
    """
    since = timezone.now() - timedelta(seconds=60)

    recent_count = BotMessageLog.objects.filter(
        phone_number=phone_number,
        created_at__gte=since,
    ).count()

    return recent_count >= 8


def is_unknown_spam(phone_number):
    """
    If user has triggered unknown spam recently, keep ignoring unknown messages
    for 5 minutes.

    Also trigger ignore when more than 2 UNKNOWN messages happen within 10 minutes.
    """

    five_minutes_ago = timezone.now() - timedelta(minutes=5)

    recent_ignore_exists = BotMessageLog.objects.filter(
        phone_number=phone_number,
        detected_intent="IGNORED_SPAM",
        action_taken="silent_ignore_unknown_spam",
        created_at__gte=five_minutes_ago,
    ).exists()

    if recent_ignore_exists:
        return True

    ten_minutes_ago = timezone.now() - timedelta(minutes=10)

    recent_unknown_count = BotMessageLog.objects.filter(
        phone_number=phone_number,
        detected_intent="UNKNOWN",
        created_at__gte=ten_minutes_ago,
    ).count()

    return recent_unknown_count >= 2


def build_silent_ignore_response(phone_number, user, message_text, reason, channel):
    BotMessageLog.objects.create(
        phone_number=phone_number,
        user=user,
        message_text=message_text,
        detected_intent="IGNORED_SPAM",
        action_taken=reason,
        reply_text="",
        ok=True,
    )

    return JsonResponse(
        {
            "ok": True,
            "reply_text": "",
            "intent": "IGNORED_SPAM",
            "action_taken": reason,
            "matched_user": bool(user),
            "phone_number": phone_number,
            "channel": channel,
            "timestamp": timezone.now().isoformat(),
        }
    )

def is_repeated_command_spam(phone_number, basic_intent):
    """
    Allow the same valid command max 3 times within 5 minutes.
    4th same command within 5 minutes = silent ignore.

    UNKNOWN has its own spam rule.
    """
    if basic_intent == "UNKNOWN":
        return False

    since = timezone.now() - timedelta(minutes=5)

    recent_count = BotMessageLog.objects.filter(
        phone_number=phone_number,
        detected_intent=basic_intent,
        created_at__gte=since,
    ).count()

    return recent_count >= 3

def process_bot_message(phone_number, message_text, channel="whatsapp"):
    message_text = (message_text or "").strip()

    user, normalized_phone = get_user_by_phone(phone_number)

    normalized_message = message_text.upper().strip()
    log_phone_number = normalized_phone or phone_number
    basic_intent = detect_basic_intent(normalized_message)

    if is_overall_spam(log_phone_number):
        BotMessageLog.objects.create(
            phone_number=log_phone_number,
            user=user,
            message_text=message_text,
            detected_intent="IGNORED_SPAM",
            action_taken="silent_ignore_overall_spam",
            reply_text="",
            ok=True,
        )

        return {
            "ok": True,
            "reply_text": "",
            "intent": "IGNORED_SPAM",
            "action_taken": "silent_ignore_overall_spam",
            "matched_user": bool(user),
            "phone_number": log_phone_number,
            "channel": channel,
            "timestamp": timezone.now().isoformat(),
        }

    if is_repeated_command_spam(log_phone_number, basic_intent):
        reason = f"silent_ignore_{basic_intent.lower()}_spam"

        BotMessageLog.objects.create(
            phone_number=log_phone_number,
            user=user,
            message_text=message_text,
            detected_intent="IGNORED_SPAM",
            action_taken=reason,
            reply_text="",
            ok=True,
        )

        return {
            "ok": True,
            "reply_text": "",
            "intent": "IGNORED_SPAM",
            "action_taken": reason,
            "matched_user": bool(user),
            "phone_number": log_phone_number,
            "channel": channel,
            "timestamp": timezone.now().isoformat(),
        }

    if basic_intent == "UNKNOWN" and is_unknown_spam(log_phone_number):
        BotMessageLog.objects.create(
            phone_number=log_phone_number,
            user=user,
            message_text=message_text,
            detected_intent="IGNORED_SPAM",
            action_taken="silent_ignore_unknown_spam",
            reply_text="",
            ok=True,
        )

        return {
            "ok": True,
            "reply_text": "",
            "intent": "IGNORED_SPAM",
            "action_taken": "silent_ignore_unknown_spam",
            "matched_user": bool(user),
            "phone_number": log_phone_number,
            "channel": channel,
            "timestamp": timezone.now().isoformat(),
        }

    ok = True
    detected_intent = "UNKNOWN"
    action_taken = "fallback"

    if normalized_message in {"HELP", "HI", "HELLO", "START"}:
        detected_intent = "HELP"
        action_taken = "sent_help"
        reply_text = build_help_reply(user)

    elif normalized_message == "CANCEL":
        detected_intent = "CANCEL"
        action_taken = "cancelled_session"
        reply_text = handle_cancel_reply(log_phone_number)

    elif normalized_message == "CONFIRM":
        detected_intent = "CONFIRM"
        action_taken = "confirmed_action"
        reply_text = handle_confirm_reply(user, log_phone_number)

    elif normalized_message.startswith("EVENT SUMMARY"):
        detected_intent = "EVENT_SUMMARY"
        action_taken = "sent_event_summary"

        event_code = extract_event_code(normalized_message)
        reply_text = build_event_summary_reply(user, event_code)

    elif normalized_message.startswith("SEND INVITE"):
        detected_intent = "SEND_INVITE"
        action_taken = "send_invite_preview"

        event_code = extract_event_code(normalized_message)
        reply_text = build_send_invite_reply(user, event_code, log_phone_number)

    elif normalized_message.startswith("STATUS"):
        detected_intent = "STATUS"
        action_taken = "checked_status"

        event_code = extract_event_code(normalized_message)
        reply_text = build_status_reply(user, event_code)

    elif normalized_message.startswith("JOIN"):
        detected_intent = "JOIN"
        action_taken = "joined_event"

        event_code = extract_event_code(normalized_message)
        reply_text = build_join_reply(user, event_code)

    elif normalized_message.startswith("LEAVE"):
        detected_intent = "LEAVE"
        action_taken = "leave_requested"

        event_code = extract_event_code(normalized_message)
        reply_text = build_leave_request_reply(user, event_code, log_phone_number)

    else:
        reply_text = (
            "I didn’t catch that.\n\n"
            "Send HELP to see what I can do."
        )

    BotMessageLog.objects.create(
        phone_number=log_phone_number,
        user=user,
        message_text=message_text,
        detected_intent=detected_intent,
        action_taken=action_taken,
        reply_text=reply_text,
        ok=ok,
    )

    return {
        "ok": ok,
        "reply_text": reply_text,
        "intent": detected_intent,
        "action_taken": action_taken,
        "matched_user": bool(user),
        "phone_number": log_phone_number,
        "channel": channel,
        "timestamp": timezone.now().isoformat(),
    }

@csrf_exempt
def bot_message(request):
    if request.method != "POST":
        return JsonResponse(
            {
                "ok": False,
                "reply_text": "Method not allowed.",
            },
            status=405,
        )

    auth_header = request.headers.get("Authorization", "")
    expected_token = getattr(settings, "BOT_API_TOKEN", "")

    if auth_header != f"Bearer {expected_token}":
        return JsonResponse(
            {
                "ok": False,
                "reply_text": "Unauthorized.",
            },
            status=401,
        )

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "ok": False,
                "reply_text": "Invalid JSON.",
            },
            status=400,
        )

    phone_number = payload.get("phone_number", "")
    message_text = payload.get("message_text", "").strip()
    channel = payload.get("channel", "whatsapp")

    result = process_bot_message(
        phone_number=phone_number,
        message_text=message_text,
        channel=channel,
    )

    return JsonResponse(result)

def send_meta_text_message(to_number, message_text):
    """
    Send a WhatsApp text message using Meta WhatsApp Cloud API.

    If message_text is blank, do nothing.
    This protects us from replying to spam / ignored messages.
    """
    message_text = (message_text or "").strip()

    if not message_text:
        return {
            "sent": False,
            "reason": "blank_reply_text",
        }

    token = getattr(settings, "META_WHATSAPP_TOKEN", "")
    phone_number_id = getattr(settings, "META_PHONE_NUMBER_ID", "")
    api_version = getattr(settings, "META_GRAPH_API_VERSION", "v22.0")

    if not token or not phone_number_id:
        return {
            "sent": False,
            "reason": "missing_meta_credentials",
        }

    url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message_text,
        },
    }

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url=url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            response_body = response.read().decode("utf-8")

            return {
                "sent": True,
                "status_code": response.status,
                "response": response_body,
            }

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")

        return {
            "sent": False,
            "status_code": e.code,
            "error": error_body,
        }

    except Exception as e:
        return {
            "sent": False,
            "error": str(e),
        }

@csrf_exempt
def meta_webhook(request):
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and token == settings.META_VERIFY_TOKEN:
            return HttpResponse(challenge)

        return JsonResponse({"error": "Verification failed"}, status=403)

    if request.method == "POST":
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"ok": False, "error": "Invalid JSON"}, status=400)

        # Meta sends many event types. We only handle text messages for v1.
        try:
            entry = payload.get("entry", [])[0]
            change = entry.get("changes", [])[0]
            value = change.get("value", {})

            messages = value.get("messages", [])
            if not messages:
                return JsonResponse({"ok": True, "ignored": "no_messages"})

            message = messages[0]
            from_number = message.get("from", "")
            message_type = message.get("type")

            if message_type != "text":
                return JsonResponse({"ok": True, "ignored": "non_text_message"})

            message_text = message.get("text", {}).get("body", "").strip()

        except (IndexError, AttributeError, KeyError):
            return JsonResponse({"ok": True, "ignored": "unrecognized_payload"})

        result = process_bot_message(
            phone_number=from_number,
            message_text=message_text,
            channel="whatsapp_meta",
        )

        send_result = send_meta_text_message(
            to_number=from_number,
            message_text=result.get("reply_text", ""),
        )

        return JsonResponse(
            {
                "ok": True,
                "received": True,
                "pepz_result": result,
                "send_result": send_result,
            }
        )
    return JsonResponse({"ok": False, "error": "Method not allowed"}, status=405)


