"""Map public commands to Meta Graph API payloads."""

from __future__ import annotations

from typing import Any

from outlabs_whatsapp.commands import (
    InteractiveButtonsCommand,
    OutboundCommand,
    TemplateBodyComponent,
    TemplateButtonComponent,
    TemplateCommand,
    TemplatePayloadParameter,
    TextCommand,
)


def _base_payload(recipient: str, message_type: str) -> dict[str, Any]:
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": message_type,
    }


def _text_payload(command: TextCommand) -> dict[str, Any]:
    payload = _base_payload(command.to, "text")
    payload["text"] = {"preview_url": command.preview_url, "body": command.body}
    if command.reply_to_message_id is not None:
        payload["context"] = {"message_id": command.reply_to_message_id}
    return payload


def _template_payload(command: TemplateCommand) -> dict[str, Any]:
    payload = _base_payload(command.to, "template")
    components: list[dict[str, Any]] = []
    for component in command.components:
        if isinstance(component, TemplateBodyComponent):
            components.append(
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": parameter.text}
                        for parameter in component.parameters
                    ],
                }
            )
        elif isinstance(component, TemplateButtonComponent):
            parameters: list[dict[str, Any]] = []
            for parameter in component.parameters:
                if isinstance(parameter, TemplatePayloadParameter):
                    parameters.append({"type": "payload", "payload": parameter.payload})
                else:
                    parameters.append({"type": "text", "text": parameter.text})
            components.append(
                {
                    "type": "button",
                    "sub_type": component.sub_type,
                    "index": str(component.index),
                    "parameters": parameters,
                }
            )
        else:  # pragma: no cover - closed public union
            raise TypeError("unsupported template component")
    payload["template"] = {
        "name": command.name,
        "language": {"policy": "deterministic", "code": command.language_code},
        "components": components,
    }
    return payload


def _interactive_payload(command: InteractiveButtonsCommand) -> dict[str, Any]:
    payload = _base_payload(command.to, "interactive")
    interactive: dict[str, Any] = {
        "type": "button",
        "body": {"text": command.body},
        "action": {
            "buttons": [
                {
                    "type": "reply",
                    "reply": {"id": button.id, "title": button.title},
                }
                for button in command.buttons
            ]
        },
    }
    if command.header is not None:
        interactive["header"] = {"type": "text", "text": command.header}
    if command.footer is not None:
        interactive["footer"] = {"text": command.footer}
    payload["interactive"] = interactive
    return payload


def command_to_meta_payload(command: OutboundCommand) -> dict[str, Any]:
    if isinstance(command, TextCommand):
        return _text_payload(command)
    if isinstance(command, TemplateCommand):
        return _template_payload(command)
    if isinstance(command, InteractiveButtonsCommand):
        return _interactive_payload(command)
    raise TypeError("unsupported outbound command")


__all__ = ["command_to_meta_payload"]
