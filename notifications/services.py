def build_whatsapp_template(event):
    playing = event.registrations.filter(status="playing").select_related("user")
    waiting = event.registrations.filter(status="waiting").select_related("user")
    backup = event.registrations.filter(status="backup").select_related("user")

    lines = [
        "⚽ Futsal Session Confirmed",
        "",
        f"{event.weekday_display}, {event.date_display}",
        event.time_range_display,
        event.location,
        f"${event.amount_payable} per pax",
        "",
        f"Playing ({playing.count()}):",
    ]

    for index, reg in enumerate(playing, start=1):
        lines.append(f"{index}. {reg.user.get_full_name() or reg.user.username}")

    lines.append("")
    lines.append(f"Waiting ({waiting.count()}):")
    for index, reg in enumerate(waiting, start=1):
        lines.append(f"{index}. {reg.user.get_full_name() or reg.user.username}")

    lines.append("")
    lines.append("Backup:")
    for index, reg in enumerate(backup, start=1):
        lines.append(f"{index}. {reg.user.get_full_name() or reg.user.username}")

    return "\n".join(lines)