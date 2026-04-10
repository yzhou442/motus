import os
from typing import Mapping, Self

import httpx

from ...core import Sandbox

_WORKSPACE_PREFIX = "/home/agent/workspace/"


def _workspace_relative(sandbox_path: str) -> str:
    """Strip the workspace prefix and return the relative path, or raise."""
    if not sandbox_path.startswith(_WORKSPACE_PREFIX):
        raise ValueError(
            f"CloudSandbox only supports paths under {_WORKSPACE_PREFIX!r}, "
            f"got {sandbox_path!r}"
        )
    return sandbox_path[len(_WORKSPACE_PREFIX) :]


class CloudSandbox(Sandbox):
    """Cloud-based sandbox backed by the sandbox REST API.

    Connects to a pre-provisioned sandbox identified by URL and bearer token.
    Does NOT manage the sandbox lifecycle (create/delete/pause).

    Usage::

        async with CloudSandbox(sandbox_url="https://...", token="...") as sb:
            output = await sb.sh("echo hello")
    """

    def __init__(self, *, sandbox_url: str, token: str) -> None:
        self._sandbox_url = sandbox_url.rstrip("/")
        self._token = token
        self._client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {token}"},
            timeout=httpx.Timeout(300.0),
        )

    @classmethod
    def create(cls, image: str = "python:3.12", **kwargs) -> Self:
        raise NotImplementedError(
            "CloudSandbox does not support create(). "
            "Use CloudSandboxToolProvider or pass sandbox_url and token directly."
        )

    async def exec(
        self,
        *cmd: str,
        input: str | None = None,
        cwd: str | None = None,
        env: Mapping[str, str] | None = None,
    ) -> str:
        body: dict = {"command": list(cmd)}
        if cwd is not None:
            body["working_directory"] = cwd
        if env is not None:
            body["env"] = dict(env)
        if input is not None:
            body["stdin"] = input
        body["timeout"] = 300

        resp = await self._client.post(f"{self._sandbox_url}/exec", json=body)
        resp.raise_for_status()
        data = resp.json()

        stdout = data.get("stdout", "")
        stderr = data.get("stderr", "")
        exit_code = data.get("exit_code", 0)

        if exit_code != 0:
            return (stdout + stderr).rstrip("\n")
        return stdout

    async def put(self, local_path: str, sandbox_path: str) -> None:
        relative = _workspace_relative(sandbox_path)
        with open(local_path, "rb") as f:
            content = f.read()
        resp = await self._client.put(
            f"{self._sandbox_url}/workspace/{relative}", content=content
        )
        resp.raise_for_status()

    async def get(self, sandbox_path: str, local_path: str) -> str:
        if os.path.isdir(local_path):
            local_path = os.path.join(local_path, os.path.basename(sandbox_path))

        relative = _workspace_relative(sandbox_path)
        resp = await self._client.get(
            f"{self._sandbox_url}/workspace/{relative}"
        )
        resp.raise_for_status()
        with open(local_path, "wb") as f:
            f.write(resp.content)

        return local_path

    def close(self) -> None:
        pass

    async def aclose(self) -> None:
        await self._client.aclose()
