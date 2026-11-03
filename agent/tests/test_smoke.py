"""Checks the test harness itself (not a product behaviour, so it has no AC ID)."""

import socket

import pytest


def test_smoke():
    """The autouse socket guard blocks network connections."""
    with pytest.raises(RuntimeError, match="socket guard"):
        socket.create_connection(("example.com", 80))
    sock = socket.socket()
    try:
        with pytest.raises(RuntimeError, match="socket guard"):
            sock.connect(("127.0.0.1", 9))
    finally:
        sock.close()
