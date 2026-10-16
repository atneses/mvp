from django.conf import settings

from tools.http import post_json

from .base import Agent, AgentContext, AgentResult


class NotifierAgent(Agent):
    name = "notifier"
    # Ids and status only: no PII ever leaves in a notification.
    fields = frozenset({"id", "country", "status", "version"})

    def run(self, context: AgentContext) -> AgentResult:
        post_json(
            settings.NOTIFICATION_WEBHOOK_URL,
            {
                "event": "application.status_changed",
                # Retries may deliver twice: the receiver uses this id to ignore duplicates.
                "event_id": f"{context['id']}:{context['version']}",
                "application_id": str(context["id"]),
                "country": context["country"],
                "status": context["status"],
            },
        )
        return AgentResult(next_status=None)
