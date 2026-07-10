import subprocess
from dataclasses import dataclass

from loguru import logger

from app.core.config import settings


@dataclass
class KubectlResult:
    command: list[str]
    success: bool
    stdout: str
    stderr: str
    return_code: int


class KubectlExecutor:
    def __init__(
        self,
        timeout_seconds: int = 30,
        context: str | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.context = context

    def run(self, args: list[str], timeout_seconds: int | None = None) -> KubectlResult:
        command = self._build_command(args)
        logger.info("Running kubectl command: {}", " ".join(command))

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_seconds or self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError:
            logger.error("kubectl executable was not found")
            return KubectlResult(
                command=command,
                success=False,
                stdout="",
                stderr="kubectl executable was not found",
                return_code=127,
            )
        except subprocess.TimeoutExpired:
            logger.error("kubectl command timed out: {}", " ".join(command))
            return KubectlResult(
                command=command,
                success=False,
                stdout="",
                stderr="kubectl command timed out",
                return_code=124,
            )

        if completed.returncode != 0:
            logger.warning(
                "kubectl command failed with code {}: {}",
                completed.returncode,
                completed.stderr.strip(),
            )

        return KubectlResult(
            command=command,
            success=completed.returncode == 0,
            stdout=completed.stdout,
            stderr=completed.stderr,
            return_code=completed.returncode,
        )

    def _build_command(self, args: list[str]) -> list[str]:
        command = ["kubectl"]

        if settings.kubeconfig_path:
            command.extend(["--kubeconfig", settings.kubeconfig_path])

        if self.context:
            command.extend(["--context", self.context])

        command.extend(args)
        return command

    def list_contexts(self) -> dict[str, object]:
        contexts_result = self.run(["config", "get-contexts", "-o", "name"])
        current_result = self.run(["config", "current-context"])

        contexts = [
            line.strip()
            for line in contexts_result.stdout.splitlines()
            if line.strip()
        ]

        return {
            "healthy": contexts_result.success,
            "contexts": contexts,
            "current_context": current_result.stdout.strip()
            if current_result.success
            else "",
            "error": contexts_result.stderr.strip()
            if not contexts_result.success
            else "",
        }
