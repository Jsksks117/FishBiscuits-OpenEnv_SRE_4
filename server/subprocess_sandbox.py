"""
Subprocess-based Sandbox — drop-in replacement for Docker containers.

Provides the same interface as a docker-py Container object (exec_run, stop,
remove, name) so that SRE_Agent_environment.py and tasks.py graders work
without any code changes.

Used automatically when Docker daemon is unavailable (e.g. HF Spaces).
"""

import logging
import subprocess
import uuid
from collections import namedtuple

logger = logging.getLogger(__name__)

# Docker's exec_run returns an object with .exit_code and .output (bytes)
ExecResult = namedtuple("ExecResult", ["exit_code", "output"])

# Cleanup script that runs at the start of each "fresh sandbox" to simulate
# the isolation of a brand-new Docker container.
_CLEANUP_SCRIPT = r"""
# Kill any running nginx from a previous episode
pkill -9 nginx 2>/dev/null || true
sleep 0.2

# Remove stale PID / lock files
rm -f /run/nginx.pid /var/run/nginx.pid 2>/dev/null || true
rm -f /var/lock/nginx.lock 2>/dev/null || true

# Restore default nginx config if nginx is installed
if command -v nginx >/dev/null 2>&1 && [ -f /etc/nginx/nginx.conf.dpkg-dist ]; then
    cp /etc/nginx/nginx.conf.dpkg-dist /etc/nginx/nginx.conf 2>/dev/null || true
elif command -v nginx >/dev/null 2>&1 && dpkg -s nginx >/dev/null 2>&1; then
    # Reinstall nginx config files only (fast, no download)
    apt-get install -y --reinstall -o Dpkg::Options::="--force-confmiss" \
        -o Dpkg::Options::="--force-confnew" nginx-common >/dev/null 2>&1 || true
fi

# Clean up web content from previous episodes
rm -rf /var/www/html/* 2>/dev/null || true

# Kill rogue python socket listeners (task 4 - port conflict)
pkill -f 'python3 -c import socket' 2>/dev/null || true

# Remove oversized log files (task 5 - disk pressure)
rm -f /var/log/app/debug.log.1 2>/dev/null || true

# Restore clean /etc/hosts (task 6 - dns poisoning)
sed -i '/db.local/d' /etc/hosts 2>/dev/null || true

# Clear bash history so graders see a clean slate
> ~/.bash_history 2>/dev/null || true
history -c 2>/dev/null || true
"""


class SubprocessSandbox:
    """
    A subprocess-based sandbox that mimics the Docker container interface.

    On creation, runs a thorough cleanup to simulate a fresh container.
    Commands are executed via subprocess.run() in the host environment.
    """

    def __init__(self):
        self.name = f"sre_subprocess_{uuid.uuid4().hex[:8]}"
        logger.info("Creating subprocess sandbox: %s", self.name)
        self._run_cleanup()

    def _run_cleanup(self):
        """Run the cleanup script to simulate a fresh container."""
        try:
            result = subprocess.run(
                ["/bin/bash", "-c", _CLEANUP_SCRIPT],
                capture_output=True,
                timeout=30,
            )
            if result.returncode != 0:
                logger.warning(
                    "Cleanup script returned %d: %s",
                    result.returncode,
                    result.stderr.decode("utf-8", errors="replace")[:200],
                )
            logger.info("Subprocess sandbox cleanup complete: %s", self.name)
        except Exception as exc:
            logger.warning("Cleanup script error: %s", exc)

    def exec_run(self, cmd, **kwargs):
        """
        Execute a command in the sandbox (same interface as Docker exec_run).

        Args:
            cmd: Either a string or a list like ["/bin/bash", "-c", "command"]

        Returns:
            ExecResult namedtuple with .exit_code and .output (bytes)
        """
        # Docker's exec_run accepts both list and string forms
        if isinstance(cmd, (list, tuple)):
            shell_cmd = cmd
        else:
            shell_cmd = ["/bin/bash", "-c", str(cmd)]

        try:
            result = subprocess.run(
                shell_cmd,
                capture_output=True,
                timeout=120,
            )
            # Combine stdout + stderr like Docker's exec_run does with tty=True
            output = result.stdout + result.stderr
            return ExecResult(exit_code=result.returncode, output=output)
        except subprocess.TimeoutExpired:
            return ExecResult(
                exit_code=124,
                output=b"Error: Command timed out after 120 seconds",
            )
        except Exception as exc:
            return ExecResult(
                exit_code=1,
                output=f"Execution error: {exc}".encode("utf-8"),
            )

    def stop(self, **kwargs):
        """No-op — subprocess sandbox has no container to stop."""
        logger.debug("SubprocessSandbox.stop() called (no-op)")

    def remove(self, **kwargs):
        """No-op — subprocess sandbox has no container to remove."""
        logger.debug("SubprocessSandbox.remove() called (no-op)")

    def kill(self, **kwargs):
        """No-op — subprocess sandbox has no container to kill."""
        logger.debug("SubprocessSandbox.kill() called (no-op)")
