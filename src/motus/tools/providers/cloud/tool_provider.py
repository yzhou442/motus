import os

from ...core import Sandbox, SandboxProvider
from .sandbox import CloudSandbox


class CloudSandboxToolProvider(SandboxProvider):
    """Cloud-based sandbox provider.

    Reads ``SANDBOX_URL`` and ``SANDBOX_TOKEN`` from the environment.
    Returns ``None`` from :meth:`get_sandbox` when the env vars are not set,
    allowing a :class:`CompositeToolProvider` to fall through to the next
    provider (e.g. Docker).
    """

    def __init__(self) -> None:
        self._sandbox: CloudSandbox | None = None

    def get_sandbox(
        self,
        *,
        image: str = "python:3.12",
        dockerfile: str | None = None,
        name: str | None = None,
        env: dict[str, str] | None = None,
        mounts: dict[str, str] | None = None,
        connect: str | None = None,
        ports: dict[int, int | None] | None = None,
    ) -> Sandbox | None:
        sandbox_url = os.environ.get("SANDBOX_URL")
        sandbox_token = os.environ.get("SANDBOX_TOKEN")
        if not sandbox_url or not sandbox_token:
            return None
        if self._sandbox is None:
            self._sandbox = CloudSandbox(sandbox_url=sandbox_url, token=sandbox_token)
        return self._sandbox

    def close(self) -> None:
        if self._sandbox is not None:
            self._sandbox.close()
            self._sandbox = None

    async def aclose(self) -> None:
        if self._sandbox is not None:
            await self._sandbox.aclose()
            self._sandbox = None
