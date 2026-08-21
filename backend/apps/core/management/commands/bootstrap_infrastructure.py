"""Bootstrap relational schema and LangGraph checkpoint tables."""

from __future__ import annotations

from django.core.management import BaseCommand, call_command

from agents.base.checkpointer import get_checkpointer


class Command(BaseCommand):
    help = "Apply Django migrations and initialize LangGraph Postgres checkpoints."

    def handle(self, *args, **options) -> None:
        self.stdout.write("Applying Django migrations...")
        call_command("migrate", interactive=False, verbosity=options["verbosity"])

        self.stdout.write("Initializing LangGraph checkpoint tables...")
        with get_checkpointer(setup=True):
            pass

        self.stdout.write(self.style.SUCCESS("Infrastructure bootstrap complete."))
