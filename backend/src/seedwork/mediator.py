import inspect
from collections.abc import Callable
from dataclasses import dataclass, field, is_dataclass
from typing import Any, TypeAlias

from injector import Injector, inject

from seedwork.exceptions import (
    CommandHandlerNotRegisteredException,
    HandlerDoesNotHaveCommandsException,
    MissingFirstArgumentAnnotationException,
    ServiceDoesNotHaveInitMethodException,
    CommandIsNotDataClassException,
)
from seedwork.uows import IUnitOfWork

Command: TypeAlias = Any


# TODO: provide behavior for staticmethods
def get_first_argument_annotation(func: Callable) -> Any:
    signature = inspect.signature(func)
    parameters = list(signature.parameters.values())

    if not parameters:
        raise HandlerDoesNotHaveCommandsException(func)

    first_param = parameters[0]
    annotation = first_param.annotation

    # noinspection PyProtectedMember
    # noinspection PyUnresolvedReferences
    if annotation is inspect._empty:
        raise MissingFirstArgumentAnnotationException(func)

    if not is_dataclass(annotation):
        raise CommandIsNotDataClassException(func)

    return annotation


@dataclass(frozen=True)
class Mediator:
    uow: IUnitOfWork
    container: Injector
    command_map: dict[type[Command], Callable] = field(default_factory=dict)

    def register_command(
        self,
        command_type: type[Command],
        command_handler: Callable,
    ) -> None:
        self.command_map[command_type] = command_handler

    def register_service_commands(
        self,
        service_type: Any,
    ) -> None:
        try:
            service = self.container.get(inject(service_type))
        except AttributeError:
            raise ServiceDoesNotHaveInitMethodException(service_type)

        methods = inspect.getmembers(service, inspect.ismethod)

        for method_name, method in methods:
            if method_name.startswith("_"):
                continue

            command_type = get_first_argument_annotation(method)
            self.register_command(command_type, method)

    def handle(self, command: Command) -> Any:
        command_type = type(command)
        handler = self.command_map[command_type]

        if not handler:
            raise CommandHandlerNotRegisteredException(command_type)

        with self.uow:
            res = handler(command)
            self.uow.commit()
            return res