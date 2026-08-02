from __future__ import annotations

from outlabs_whatsapp import (
    InteractiveButtonsCommand,
    ReplyButton,
    TemplateBodyComponent,
    TemplateButtonComponent,
    TemplateCommand,
    TemplatePayloadParameter,
    TemplateTextParameter,
    TextCommand,
)
from outlabs_whatsapp.meta.dto import command_to_meta_payload


def test_text_payload_maps_context() -> None:
    payload = command_to_meta_payload(
        TextCommand(
            to="+15550001111",
            body="Hello",
            preview_url=True,
            reply_to_message_id="wamid.parent",
        )
    )

    assert payload == {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": "15550001111",
        "type": "text",
        "text": {"preview_url": True, "body": "Hello"},
        "context": {"message_id": "wamid.parent"},
    }


def test_template_payload_maps_body_and_url_button() -> None:
    payload = command_to_meta_payload(
        TemplateCommand(
            to="15550001111",
            name="portal_access_ready",
            language_code="es_AR",
            components=(
                TemplateBodyComponent(
                    parameters=(TemplateTextParameter(text="Andi"),)
                ),
                TemplateButtonComponent(
                    sub_type="url",
                    index=0,
                    parameters=(TemplateTextParameter(text="opaque-suffix"),),
                ),
            ),
        )
    )

    assert payload["template"] == {
        "name": "portal_access_ready",
        "language": {"policy": "deterministic", "code": "es_AR"},
        "components": [
            {"type": "body", "parameters": [{"type": "text", "text": "Andi"}]},
            {
                "type": "button",
                "sub_type": "url",
                "index": "0",
                "parameters": [{"type": "text", "text": "opaque-suffix"}],
            },
        ],
    }


def test_interactive_button_payload() -> None:
    payload = command_to_meta_payload(
        InteractiveButtonsCommand(
            to="15550001111",
            header="Status",
            body="Continue?",
            footer="Synthetic",
            buttons=(ReplyButton(id="continue", title="Continue"),),
        )
    )

    assert payload["interactive"] == {
        "type": "button",
        "header": {"type": "text", "text": "Status"},
        "body": {"text": "Continue?"},
        "footer": {"text": "Synthetic"},
        "action": {
            "buttons": [
                {"type": "reply", "reply": {"id": "continue", "title": "Continue"}}
            ]
        },
    }


def test_quick_reply_template_button_uses_payload_parameter() -> None:
    payload = command_to_meta_payload(
        TemplateCommand(
            to="15550001111",
            name="support_followup",
            language_code="es_AR",
            components=(
                TemplateButtonComponent(
                    sub_type="quick_reply",
                    index=0,
                    parameters=(TemplatePayloadParameter(payload="continue"),),
                ),
            ),
        )
    )

    assert payload["template"]["components"] == [
        {
            "type": "button",
            "sub_type": "quick_reply",
            "index": "0",
            "parameters": [{"type": "payload", "payload": "continue"}],
        }
    ]
