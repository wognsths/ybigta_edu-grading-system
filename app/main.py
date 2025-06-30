from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
import uvicorn

import os
import hmac
import hashlib
import shutil
import subprocess
import logging
import time
from typing import List

from app.config import settings
from core.runner import grade_repository

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(message)s")

app = FastAPI(title="YBIGTA Grading API")

def _verify_signature(req: Request, body: bytes) -> None:
    header = req.headers.get("X-Hub-Signature-256")
    if not header or not header.startswith("sha256="):
        raise HTTPException(status_code=400, detail="Missing signature header")

    _, sent_sig = header.split("=")
    expected_sig = hmac.new(settings.SECRET.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sent_sig, expected_sig):
        raise HTTPException(status_code=401, detail="Invalid signature")


def _check_whitelist(full_name: str) -> None:
    if full_name.strip() not in settings.ALLOWED_REPOS:
        raise HTTPException(status_code=403, detail=f"{full_name} is not allowed")


@app.get("/")
async def root():
    return {"message": "YBIGTA EDU-Session Grading API", "port": settings.PORT}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/webhook")
async def webhook(req: Request, bg: BackgroundTasks):
    body = await req.body()
    _verify_signature(req, body)

    if req.headers.get("X-GitHub-Event") != "push":
        return {"ignored": True}

    payload = await req.json()
    repo = payload["repository"]
    repo_full = repo["full_name"]
    _check_whitelist(repo_full)

    student_id = repo["owner"]["login"]
    commit_sha = payload["after"][:8]
    repo_path = os.path.join("submissions", f"{student_id}_{commit_sha}")

    def _clone_and_grade():
        logging.info(f"[CLONE] {repo_full} → {repo_path}")
        shutil.rmtree(repo_path, ignore_errors=True)
        subprocess.run(["git", "clone", "--depth", "1", repo["clone_url"], repo_path], check=True)

        try:
            score = grade_repository(repo_path, assignment_name="hw1")
            logging.info(f"[DONE] {repo_full} score={score}")
        except Exception as exc:
            logging.error(f"[ERROR] {repo_full}: {exc}")
        finally:
            shutil.rmtree(repo_path, ignore_errors=True)

    bg.add_task(_clone_and_grade)
    return {"accepted": True}
if __name__ == "__main__":
    uvicorn.run(
        "grader_api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )