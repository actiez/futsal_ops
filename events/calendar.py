
from datetime import timezone as datetime_timezone
from zoneinfo import ZoneInfo

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Event


SG_TZ = ZoneInfo("Asia/Singapore")


def escape_ics(value):
    value = str(value or "")

    return (
        value.replace("\\", "\\\\")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def utc_ics(value):
    return value.astimezone(
        datetime_timezone.utc
    ).strftime("%Y%m%dT%H%M%SZ")


def fold_line(line):
    """
    Fold lines to a maximum of 75 UTF-8 octets,
    as required by the iCalendar specification.
    """
    lines = []
    current = ""
    size = 0

    for character in line:
        byte_size = len(character.encode("utf-8"))

        if size + byte_size > 75:
            lines.append(current)
            current = " "
            size = 1

        current += character
        size += byte_size

    lines.append(current)
    return "\r\n".join(lines)


def get_calendar_alarms(event):
    """
    Returns alarm offsets in minutes before kick-off.

    Reminder 1:
    30 minutes before the self-leaving cutoff.

    Reminder 2:
    60 minutes before kick-off.
    """
    alarms = {}

    if event.leave_cutoff_minutes:
        first_offset = event.leave_cutoff_minutes + 30

        alarms[first_offset] = (
            "Futsal: self-leaving closes in 30 minutes. "
            "Please confirm your availability."
        )

    second_offset = 60

    second_message = (
        "Futsal begins in 1 hour. "
        "Please check your playing status."
    )

    if second_offset in alarms:
        alarms[second_offset] += " " + second_message
    else:
        alarms[second_offset] = second_message

    return sorted(alarms.items(), reverse=True)


def download_event_calendar(request, token):
    event = get_object_or_404(
        Event,
        registration_token=token,
    )

    local_start = timezone.localtime(
        event.start_datetime,
        SG_TZ,
    )

    description_lines = [
        "Futsal Ops",
        "",
        f"Venue: {event.location}",
        f"Fee: SGD {event.amount_payable} per pax",
    ]

    if event.leave_cutoff_minutes:
        cutoff = timezone.localtime(
            event.leave_cutoff_datetime,
            SG_TZ,
        )

        description_lines.extend([
            "",
            "Self-leaving deadline: "
            + cutoff.strftime("%d %b %Y, %I:%M %p"),
            "Contact the organiser if unable to attend "
            "after the cutoff.",
        ])
    else:
        description_lines.extend([
            "",
            "Self-leaving: No early cutoff.",
        ])

    description_lines.extend([
        "",
        "Please check your Playing / Waiting / "
        "Pending status in Futsal Ops.",
    ])

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Futsal Ops//Event Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{event.registration_token}@futsal-ops",
        f"DTSTAMP:{utc_ics(timezone.now())}",
        f"CREATED:{utc_ics(event.created_at)}",
        f"LAST-MODIFIED:{utc_ics(event.updated_at)}",
        f"DTSTART:{utc_ics(event.start_datetime)}",
        f"DTEND:{utc_ics(event.end_datetime)}",
        f"SUMMARY:{escape_ics(event.title)}",
        f"LOCATION:{escape_ics(event.location)}",
        "DESCRIPTION:" + escape_ics(
            "\n".join(description_lines)
        ),
        (
            "STATUS:CANCELLED"
            if event.status == Event.STATUS_CANCELLED
            else "STATUS:CONFIRMED"
        ),
    ]

    for minutes_before, message in get_calendar_alarms(event):
        lines.extend([
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            f"DESCRIPTION:{escape_ics(message)}",
            f"TRIGGER:-PT{minutes_before}M",
            "END:VALARM",
        ])

    lines.extend([
        "END:VEVENT",
        "END:VCALENDAR",
    ])

    content = "\r\n".join(
        fold_line(line) for line in lines
    ) + "\r\n"

    response = HttpResponse(
        content,
        content_type="text/calendar; charset=utf-8",
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{event.event_code}.ics"'
    )
    response["Cache-Control"] = "no-store"

    return response
