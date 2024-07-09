from dataclasses import dataclass

from apps.notifications.tasks import INotificationAdapter
from seedwork.mediator import command_handler


@dataclass(frozen=True)
class SendInviteCommand:
    message: str


@dataclass(frozen=True)
class NotificationService:
    notification_adapter: INotificationAdapter

    @command_handler
    def send_invite_to_client(self, command: SendInviteCommand) -> None:
        self.notification_adapter.send_invite_to_client(command.message)
