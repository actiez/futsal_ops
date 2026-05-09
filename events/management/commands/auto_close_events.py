from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from events.models import Event, EventCloseout
from events.services import auto_close_event


class Command(BaseCommand):
    help = "Auto-close events that ended more than 3 days ago and have no closeout."

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=3)

        events = (
            Event.objects
            .filter(end_datetime__lte=cutoff)
            .exclude(status=Event.STATUS_CANCELLED)
            .filter(closeout__isnull=True)
        )

        closed_count = 0

        for event in events:
            closeout = auto_close_event(event)

            if closeout:
                closed_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Auto-closed event {event.id}: {event}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Auto-close complete. Events closed: {closed_count}"
            )
        )