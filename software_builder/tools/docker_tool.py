"""
tools/docker_tool.py
--------------------
Utility that builds a Docker image from a folder and optionally runs it.
Used by the RunnerAgent when the generated repo contains a Dockerfile.
"""

import subprocess
from pathlib import Path
from typing import Dict, Any

class DockerTool:
    def __init__(self, config: Dict[str, Any]):
        self.build_context = Path(config.get("build_context", "./output/repo"))
        self.image_tag = config.get("image_tag", "generated-app:latest")
        self.run_args = config.get("run_args", ["-p", "8000:8000"])

    async def __call__(self, **_) -> str:
        # Build the image
        subprocess.run(
            ["docker", "build", "-t", self.image_tag, str(self.build_context)],
            check=True,
        )
        # Run the container (detached)
        run_cmd = ["docker", "run", "--rm"]
        run_cmd.extend(self.run_args)
        run_cmd.append(self.image_tag)
        proc = subprocess.run(run_cmd, capture_output=True, text=True, check=True)
        return proc.stdout
