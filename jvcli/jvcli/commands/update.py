"""Update command group operations for Jivas Package Repository CLI tool."""

import click

from jvcli.api import RegistryAPI
from jvcli.auth import load_token


@click.group()
def update() -> None:
    """Group for updating resources like namespaces."""
    pass  # pragma: no cover


@update.command(name="namespace")
@click.argument("namespace", required=True)
@click.option(
    "--invite",
    type=str,
    help="Invite a user to the namespace by their email.",
    metavar="EMAIL",
)
@click.option(
    "--transfer",
    type=str,
    help="Transfer ownership of the namespace to a specified user by their email.",
    metavar="EMAIL",
)
@click.pass_context
def namespace(ctx: click.Context, namespace: str, invite: str, transfer: str) -> None:
    """
    Update operations for a specified namespace.
    Use one of the available options: --invite, --transfer.
    """

    token = load_token().get("token")
    if not token:
        click.secho("You need to login first.", fg="red")
        ctx.exit(1)

    # Validate mutually exclusive options
    if invite and transfer:
        click.secho(
            "You can only use one of --invite or --transfer at a time.", fg="red"
        )
        ctx.exit(1)

    # Handle different operations
    if invite:
        click.secho(f"Inviting '{invite}' to namespace '{namespace}'...", fg="yellow")
        # Logic to invite a user to the namespace
        RegistryAPI.invite_user_to_namespace(
            namespace_name=namespace, user_email=invite, token=str(token)
        )
    elif transfer:
        click.secho(
            f"Transferring ownership of namespace '{namespace}' to '{transfer}'...",
            fg="yellow",
        )
        # Logic to transfer ownership of the namespace
        RegistryAPI.transfer_namespace_ownership(
            namespace_name=namespace, new_owner_email=transfer, token=str(token)
        )

    click.secho(
        f"Operation on namespace '{namespace}' completed successfully.", fg="green"
    )
