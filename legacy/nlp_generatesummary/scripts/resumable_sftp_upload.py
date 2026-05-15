#!/usr/bin/env python
"""Resumable SFTP uploader for large project assets.

Designed for Windows -> Linux transfers where long-lived scp/ssh sessions are
unstable. The uploader works file-by-file, skips completed files, resumes
partially uploaded files, and reconnects automatically on transient failures.
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import posixpath
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import paramiko


CHUNK_SIZE = 8 * 1024 * 1024


@dataclass(frozen=True)
class Mapping:
    source: Path
    dest: str
    mode: str


class Logger:
    def __init__(self, log_file: Path | None) -> None:
        self.log_file = log_file

    def log(self, message: str) -> None:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}"
        print(line, flush=True)
        if self.log_file is not None:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with self.log_file.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")


class ResumableUploader:
    def __init__(
        self,
        *,
        host: str,
        user: str,
        port: int,
        log: Logger,
        retries: int = 5,
        connect_timeout: int = 30,
    ) -> None:
        self.host = host
        self.user = user
        self.port = port
        self.log = log
        self.retries = retries
        self.connect_timeout = connect_timeout
        self._ssh: paramiko.SSHClient | None = None
        self._sftp: paramiko.SFTPClient | None = None

    def connect(self) -> None:
        self.close()
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=self.host,
            port=self.port,
            username=self.user,
            allow_agent=True,
            look_for_keys=True,
            timeout=self.connect_timeout,
        )
        transport = ssh.get_transport()
        if transport is None:
            raise RuntimeError("SSH transport is unavailable after connect")
        transport.set_keepalive(30)
        self._ssh = ssh
        self._sftp = ssh.open_sftp()
        self.log.log(f"Connected to {self.user}@{self.host}:{self.port}")

    def close(self) -> None:
        if self._sftp is not None:
            try:
                self._sftp.close()
            except Exception:
                pass
        if self._ssh is not None:
            try:
                self._ssh.close()
            except Exception:
                pass
        self._sftp = None
        self._ssh = None

    @property
    def sftp(self) -> paramiko.SFTPClient:
        if self._sftp is None:
            self.connect()
        assert self._sftp is not None
        return self._sftp

    def mkdir_p(self, remote_dir: str) -> None:
        remote_dir = posixpath.normpath(remote_dir)
        if remote_dir in ("", "/"):
            return
        parts = remote_dir.strip("/").split("/")
        current = "/" if remote_dir.startswith("/") else ""
        for part in parts:
            current = posixpath.join(current, part) if current else part
            try:
                self.sftp.stat(current)
            except FileNotFoundError:
                self.sftp.mkdir(current)

    def remote_size(self, remote_path: str) -> int | None:
        try:
            return self.sftp.stat(remote_path).st_size
        except FileNotFoundError:
            return None

    def upload_file(self, local_path: Path, remote_path: str) -> str:
        attempt = 0
        while True:
            try:
                self.mkdir_p(posixpath.dirname(remote_path))
                local_size = local_path.stat().st_size
                remote_size = self.remote_size(remote_path)

                if remote_size == local_size:
                    return "skip"

                if remote_size is not None and remote_size > local_size:
                    raise RuntimeError(
                        f"Remote file is larger than local file: {remote_path} ({remote_size} > {local_size})"
                    )

                offset = remote_size or 0
                mode = "ab" if offset else "wb"

                with local_path.open("rb") as src, self.sftp.open(remote_path, mode) as dst:
                    if offset:
                        src.seek(offset)
                        dst.set_pipelined(True)
                    while True:
                        chunk = src.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        dst.write(chunk)

                final_size = self.remote_size(remote_path)
                if final_size != local_size:
                    raise RuntimeError(
                        f"Size mismatch after upload: {remote_path} ({final_size} != {local_size})"
                    )
                return "resume" if offset else "upload"
            except Exception as exc:
                attempt += 1
                if attempt > self.retries:
                    raise RuntimeError(f"Upload failed for {local_path} -> {remote_path}: {exc}") from exc
                self.log.log(
                    f"Retry {attempt}/{self.retries} for {local_path.name} after error: {exc!r}"
                )
                time.sleep(min(5 * attempt, 30))
                self.connect()


def iter_mapping_files(source: Path, mode: str, excludes: list[str]) -> Iterable[tuple[Path, str]]:
    if source.is_file():
        yield source, source.name
        return

    for path in source.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(source).as_posix()
        if any(fnmatch.fnmatch(relative, pattern) for pattern in excludes):
            continue
        yield path, relative


def parse_mapping(value: str) -> Mapping:
    try:
        raw_source, raw_dest, mode = value.split("|", 2)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Mapping must be formatted as SOURCE|REMOTE_DEST|MODE"
        ) from exc

    source = Path(raw_source).expanduser().resolve()
    if mode not in {"dir", "contents", "file"}:
        raise argparse.ArgumentTypeError("MODE must be 'dir', 'contents', or 'file'")
    return Mapping(source=source, dest=raw_dest.replace("\\", "/"), mode=mode)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resumable SFTP uploader")
    parser.add_argument("--host", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument(
        "--mapping",
        action="append",
        type=parse_mapping,
        required=True,
        help="SOURCE|REMOTE_DEST|MODE, where MODE is dir or contents",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Glob pattern applied to mapping-relative POSIX paths, e.g. .git/*",
    )
    parser.add_argument("--log-file", type=Path, default=None)
    parser.add_argument("--retries", type=int, default=5)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    logger = Logger(args.log_file)
    uploader = ResumableUploader(
        host=args.host,
        user=args.user,
        port=args.port,
        log=logger,
        retries=args.retries,
    )

    uploaded = 0
    resumed = 0
    skipped = 0
    total = 0

    try:
        uploader.connect()
        for mapping in args.mapping:
            if not mapping.source.exists():
                raise FileNotFoundError(f"Source does not exist: {mapping.source}")

            logger.log(f"Start mapping: {mapping.source} -> {mapping.dest} ({mapping.mode})")
            if mapping.mode == "dir":
                target_root = posixpath.join(mapping.dest.rstrip("/"), mapping.source.name)
            elif mapping.mode == "file":
                target_root = mapping.dest
            else:
                target_root = mapping.dest.rstrip("/")

            mapping_total = 0
            mapping_uploaded = 0
            mapping_resumed = 0
            mapping_skipped = 0
            for local_path, relative in iter_mapping_files(mapping.source, mapping.mode, args.exclude):
                total += 1
                mapping_total += 1
                if mapping.mode == "file":
                    remote_path = target_root
                else:
                    remote_path = posixpath.join(target_root, relative)
                action = uploader.upload_file(local_path, remote_path)
                if action == "upload":
                    uploaded += 1
                    mapping_uploaded += 1
                elif action == "resume":
                    resumed += 1
                    mapping_resumed += 1
                    logger.log(f"RESUME {local_path} -> {remote_path}")
                else:
                    skipped += 1
                    mapping_skipped += 1

                if mapping_total % 200 == 0:
                    logger.log(
                        "Progress "
                        f"{mapping.source.name}: files={mapping_total} "
                        f"uploaded={mapping_uploaded} resumed={mapping_resumed} skipped={mapping_skipped} "
                        f"last={relative}"
                    )

            logger.log(
                f"Finished mapping: {mapping.source} "
                f"(files={mapping_total} uploaded={mapping_uploaded} resumed={mapping_resumed} skipped={mapping_skipped})"
            )
    finally:
        uploader.close()

    logger.log(
        f"Done. total_files={total} uploaded={uploaded} resumed={resumed} skipped={skipped}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
