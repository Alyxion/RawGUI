#!/usr/bin/env python3
"""Form example demonstrating input handling.

Run with: poetry run python examples/form.py
Press Escape or Ctrl+C to quit.
"""

from rawgui import ui


class FormState:
    username = ""
    password = ""
    email = ""
    submitted = False
    message = ""


def on_username(value):
    FormState.username = value


def on_password(value):
    FormState.password = value


def on_email(value):
    FormState.email = value


def submit():
    if FormState.username and FormState.email:
        FormState.submitted = True
        FormState.message = f"Welcome, {FormState.username}!"
    else:
        FormState.message = "Please fill in all required fields"
    ui.navigate.to("/")


def clear_form():
    FormState.username = ""
    FormState.password = ""
    FormState.email = ""
    FormState.submitted = False
    FormState.message = ""
    ui.navigate.to("/")


@ui.page("/")
def index():
    with ui.column().classes("gap-2 p-2"):
        ui.label("Registration Form").classes("text-bold text-cyan")

        with ui.card():
            ui.label("User Information").classes("text-bold")

            ui.input(
                label="Username",
                placeholder="Enter username",
                value=FormState.username,
                on_change=on_username,
            )

            ui.input(
                label="Email",
                placeholder="your@email.com",
                value=FormState.email,
                on_change=on_email,
            )

            ui.input(
                label="Password",
                placeholder="Enter password",
                password=True,
                value=FormState.password,
                on_change=on_password,
            )

            with ui.row().classes("gap-2"):
                ui.button("Submit", on_click=submit).classes("text-green")
                ui.button("Clear", on_click=clear_form).classes("text-yellow")

        if FormState.message:
            with ui.card():
                color = "text-green" if FormState.submitted else "text-red"
                ui.label(FormState.message).classes(color)

        ui.label("").classes("")
        ui.label("Tab to navigate, type to enter text").classes("text-bright_black")
        ui.label("Press Escape or Ctrl+C to quit").classes("text-bright_black")


if __name__ == "__main__":
    ui.run(title="Form Demo", reload=False)
