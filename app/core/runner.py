import os
import shutil
import subprocess
import logging
import json
from uuid import uuid4

from app.core.testcases.basegrader import BaseGrader

def grade_repository(repo_path: str, assignment_name: str) -> int:
    container_name = f"grader_{uuid4().hex[:8]}"

    abs_repo_path = os.path.abspath(repo_path)

    try:
        subprocess.run([
            "docker", "run", "--rm",
            "--name", container_name,
            "-v", f"{abs_repo_path}:/app/student:ro",
            "grader-image:latest",
            assignment_name
        ], check=True)

    except subprocess.CalledProcessError as e:
        logging.error(f"Docker execution failed: {e}")
        raise RuntimeError("Docker grading failed")
    
    report_path = os.path.join(repo_path, ".report.json")
    if not os.path.exists(report_path):
        raise FileNotFoundError("Graded file does not exist.")
    
    with open(report_path, "r") as f:
        result = json.load(f)

    score = result.get("score", 0)

    shutil.rmtree(repo_path, ignore_errors=True)

    logging.info(f"Grading completed for {repo_path}. Score: {score}")
    return score