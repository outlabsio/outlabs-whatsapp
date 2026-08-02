"""Typed outbound WhatsApp commands.

Command representations deliberately hide recipients and content. Applications still own the
authorization and policy decision to construct and send a command.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class _CommandModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)


def _normalized_recipient(value: str) -> str:
    normalized = value.strip()
    if normalized.startswith("+"):
        normalized = normalized[1:]
    if not 7 <= len(normalized) <= 20 or not normalized.isdigit():
        raise ValueError("recipient must contain 7-20 digits, optionally prefixed with +")
    return normalized


class TextCommand(_CommandModel):
    kind: Literal["text"] = "text"
    to: str = Field(repr=False)
    body: str = Field(min_length=1, max_length=4096, repr=False)
    preview_url: bool = False
    reply_to_message_id: str | None = Field(default=None, min_length=1, max_length=256)
    host_reference: str | None = Field(default=None, min_length=1, max_length=256)

    _normalize_to = field_validator("to")(_normalized_recipient)


class TemplateTextParameter(_CommandModel):
    type: Literal["text"] = "text"
    text: str = Field(min_length=1, max_length=1024, repr=False)


class TemplatePayloadParameter(_CommandModel):
    type: Literal["payload"] = "payload"
    payload: str = Field(min_length=1, max_length=1024, repr=False)


type TemplateButtonParameter = Annotated[
    TemplateTextParameter | TemplatePayloadParameter,
    Field(discriminator="type"),
]


class TemplateBodyComponent(_CommandModel):
    type: Literal["body"] = "body"
    parameters: tuple[TemplateTextParameter, ...] = Field(default=(), max_length=32)


class TemplateButtonComponent(_CommandModel):
    type: Literal["button"] = "button"
    sub_type: Literal["url", "quick_reply"]
    index: int = Field(ge=0, le=9)
    parameters: tuple[TemplateButtonParameter, ...] = Field(min_length=1, max_length=1)

    def model_post_init(self, __context: object) -> None:
        parameter = self.parameters[0]
        if self.sub_type == "url" and not isinstance(parameter, TemplateTextParameter):
            raise ValueError("URL template buttons require a text parameter")
        if self.sub_type == "quick_reply" and not isinstance(
            parameter, TemplatePayloadParameter
        ):
            raise ValueError("quick-reply template buttons require a payload parameter")


type TemplateComponent = Annotated[
    TemplateBodyComponent | TemplateButtonComponent,
    Field(discriminator="type"),
]


class TemplateCommand(_CommandModel):
    kind: Literal["template"] = "template"
    to: str = Field(repr=False)
    name: str = Field(min_length=1, max_length=512, pattern=r"^[a-z0-9_]+$")
    language_code: str = Field(
        min_length=2,
        max_length=16,
        pattern=r"^[A-Za-z]{2,3}(?:_[A-Za-z]{2})?$",
    )
    components: tuple[TemplateComponent, ...] = Field(default=(), max_length=16)
    host_reference: str | None = Field(default=None, min_length=1, max_length=256)

    _normalize_to = field_validator("to")(_normalized_recipient)

    @model_validator(mode="after")
    def _unique_components(self) -> TemplateCommand:
        body_count = sum(
            isinstance(component, TemplateBodyComponent) for component in self.components
        )
        if body_count > 1:
            raise ValueError("template commands may contain at most one body component")
        button_keys = [
            (component.sub_type, component.index)
            for component in self.components
            if isinstance(component, TemplateButtonComponent)
        ]
        if len(set(button_keys)) != len(button_keys):
            raise ValueError("template button subtype/index pairs must be unique")
        return self


class ReplyButton(_CommandModel):
    id: str = Field(min_length=1, max_length=256, repr=False)
    title: str = Field(min_length=1, max_length=20, repr=False)


class InteractiveButtonsCommand(_CommandModel):
    kind: Literal["interactive_buttons"] = "interactive_buttons"
    to: str = Field(repr=False)
    body: str = Field(min_length=1, max_length=1024, repr=False)
    buttons: tuple[ReplyButton, ...] = Field(min_length=1, max_length=3)
    header: str | None = Field(default=None, min_length=1, max_length=60, repr=False)
    footer: str | None = Field(default=None, min_length=1, max_length=60, repr=False)
    host_reference: str | None = Field(default=None, min_length=1, max_length=256)

    _normalize_to = field_validator("to")(_normalized_recipient)

    @field_validator("buttons")
    @classmethod
    def _unique_button_ids(cls, value: tuple[ReplyButton, ...]) -> tuple[ReplyButton, ...]:
        if len({button.id for button in value}) != len(value):
            raise ValueError("button IDs must be unique")
        return value


type OutboundCommand = Annotated[
    TextCommand | TemplateCommand | InteractiveButtonsCommand,
    Field(discriminator="kind"),
]


__all__ = [
    "InteractiveButtonsCommand",
    "OutboundCommand",
    "ReplyButton",
    "TemplateBodyComponent",
    "TemplateButtonComponent",
    "TemplateButtonParameter",
    "TemplateCommand",
    "TemplateComponent",
    "TemplatePayloadParameter",
    "TemplateTextParameter",
    "TextCommand",
]
