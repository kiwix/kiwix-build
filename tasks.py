# pyright: strict, reportUntypedFunctionDecorator=false
import os
import sys

from invoke.context import Context
from invoke.tasks import task

# Use PTY unless in a CI environment to ensure colored output works correctly
use_pty = not os.getenv("CI", "") and sys.platform != "win32"


@task(optional=["args"], help={"args": "black additional arguments"})
def lint_black(ctx: Context, args: str = "."):
    """Check code formatting with black"""
    args = args or "."
    print("Checking black...")
    ctx.run(f"black --check --diff {args}", pty=use_pty)


@task(optional=["args"], help={"args": "ruff additional arguments"})
def lint_ruff(ctx: Context, args: str = "."):
    """Check code logic and style with ruff"""
    args = args or "."
    print("Checking ruff...")
    ctx.run(f"ruff check {args}", pty=use_pty)


@task(
    optional=["args"],
    help={
        "args": "linting tools (black, ruff) additional arguments, typically a path",
    },
)
def lintall(ctx: Context, args: str = "."):
    """Run all linting checks (The primary requirement for #263)"""
    args = args or "."
    lint_black(ctx, args)
    lint_ruff(ctx, args)


@task(optional=["args"], help={"args": "black additional arguments"})
def fix_black(ctx: Context, args: str = "."):
    """Automatically fix black formatting issues"""
    args = args or "."
    ctx.run(f"black {args}", pty=use_pty)


@task(optional=["args"], help={"args": "ruff additional arguments"})
def fix_ruff(ctx: Context, args: str = "."):
    """Automatically fix ruff linting errors"""
    args = args or "."
    ctx.run(f"ruff check --fix {args}", pty=use_pty)


@task(
    optional=["args"],
    help={
        "args": "linting tools (black, ruff) additional arguments, typically a path",
    },
)
def format(ctx: Context, args: str = "."):
    """Fix all formatting and linting issues automatically"""
    args = args or "."
    fix_black(ctx, args)
    fix_ruff(ctx, args)
    lintall(ctx, args)
