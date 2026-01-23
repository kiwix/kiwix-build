# pyright: strict, reportUntypedFunctionDecorator=false
import os
import sys

from invoke.context import Context
from invoke.tasks import task

# Windows fix: Disable PTY if on Windows
use_pty = not os.getenv("CI", "") and sys.platform != "win32"

@task(optional=["args"], help={"args": "ruff additional arguments"})
def lint(ctx: Context, args: str = "."):
    """Check code logic and style with ruff"""
    args = args or "."
    print("Checking ruff...")
    # Using 'ruff check' to find issues
    ctx.run(f"ruff check {args}", pty=use_pty)

@task(optional=["args"], help={"args": "ruff additional arguments"})
def format_check(ctx: Context, args: str = "."):
    """Check code formatting with ruff (Replaces Black)"""
    args = args or "."
    print("Checking formatting...")
    # Using 'ruff format --check' to replace 'black --check'
    ctx.run(f"ruff format --check --diff {args}", pty=use_pty)

@task(help={"args": "path to lint"})
def lintall(ctx: Context, args: str = "."):
    """Run all linting and format checks"""
    lint(ctx, args)
    format_check(ctx, args)

@task(optional=["args"], help={"args": "ruff additional arguments"})
def format(ctx: Context, args: str = "."):
    """Fix all issues (Replaces fixall/fix_black)"""
    args = args or "."
    print("Fixing formatting and lint errors...")
    ctx.run(f"ruff format {args}", pty=use_pty)
    ctx.run(f"ruff check --fix {args}", pty=use_pty)