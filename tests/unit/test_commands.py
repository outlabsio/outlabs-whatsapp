from __future__ import annotations

import pytest
from pydantic import ValidationError

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


def test_sensitive_command_fields_are_hidden_from_repr() -> None:
    command = TextCommand(
        to="+15550001111",
        body="Private message body",
        host_reference="intent-1",
    )

    rendered = repr(command)

    assert "15550001111" not in rendered
    assert "Private message body" not in rendered
    assert command.to == "15550001111"


def test_template_parameter_is_hidden_from_nested_repr() -> None:
    command = TemplateCommand(
        to="15550001111",
        name="application_update_available",
        language_code="es_AR",
        components=(
            TemplateBodyComponent(
                parameters=(TemplateTextParameter(text="secret portal token"),)
            ),
        ),
    )

    assert "secret portal token" not in repr(command)
    assert command.model_dump()["components"][0]["parameters"][0]["text"] == (
        "secret portal token"
    )


def test_recipient_rejects_non_digits() -> None:
    with pytest.raises(ValidationError):
        TextCommand(to="+54 9 2664", body="hello")
    with pytest.raises(ValidationError):
        TextCommand(to="١٥٥٥٠٠٠١١١١", body="hello")


def test_interactive_buttons_require_unique_ids() -> None:
    with pytest.raises(ValidationError, match="button IDs must be unique"):
        InteractiveButtonsCommand(
            to="15550001111",
            body="Choose",
            buttons=(ReplyButton(id="same", title="One"), ReplyButton(id="same", title="Two")),
        )


def test_template_button_parameter_must_match_subtype() -> None:
    with pytest.raises(ValidationError, match="URL template buttons require a text parameter"):
        TemplateButtonComponent(
            sub_type="url",
            index=0,
            parameters=(TemplatePayloadParameter(payload="opaque"),),
        )

    with pytest.raises(
        ValidationError,
        match="quick-reply template buttons require a payload parameter",
    ):
        TemplateButtonComponent(
            sub_type="quick_reply",
            index=0,
            parameters=(TemplateTextParameter(text="opaque"),),
        )


def test_sensitive_inputs_are_hidden_from_validation_errors() -> None:
    sensitive_body = "PRIVATE-CUSTOMER-CONTENT" * 300

    with pytest.raises(ValidationError) as captured:
        TextCommand(to="15550001111", body=sensitive_body)

    assert sensitive_body not in str(captured.value)


def test_template_body_component_may_not_be_repeated() -> None:
    with pytest.raises(ValidationError, match="at most one body component"):
        TemplateCommand(
            to="15550001111",
            name="portal_access_ready",
            language_code="es_AR",
            components=(TemplateBodyComponent(), TemplateBodyComponent()),
        )


def test_template_button_subtype_and_index_pair_must_be_unique() -> None:
    button = TemplateButtonComponent(
        sub_type="quick_reply",
        index=0,
        parameters=(TemplatePayloadParameter(payload="opaque"),),
    )

    with pytest.raises(ValidationError, match="subtype/index pairs must be unique"):
        TemplateCommand(
            to="15550001111",
            name="portal_access_ready",
            language_code="es_AR",
            components=(button, button),
        )


def test_different_template_button_subtypes_may_share_an_index() -> None:
    command = TemplateCommand(
        to="15550001111",
        name="portal_access_ready",
        language_code="es_AR",
        components=(
            TemplateButtonComponent(
                sub_type="url",
                index=0,
                parameters=(TemplateTextParameter(text="opaque"),),
            ),
            TemplateButtonComponent(
                sub_type="quick_reply",
                index=0,
                parameters=(TemplatePayloadParameter(payload="opaque"),),
            ),
        ),
    )

    assert len(command.components) == 2
