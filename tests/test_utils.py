import pytest
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from utils import sanitize_filename, current_rss_bytes

def test_sanitize_filename():
    assert sanitize_filename("hello world.txt") == "hello_world.txt"
    assert sanitize_filename("file/with/path.jpg") == "path.jpg"
    assert sanitize_filename("invalid*char?.png") == "invalid_char_.png"
    assert sanitize_filename("___multiple___underscores___") == "multiple_underscores"
    assert sanitize_filename("a" * 200 + ".txt") == "a" * 176 + ".txt"

def test_current_rss_bytes():
    rss = current_rss_bytes()
    assert isinstance(rss, int)
    assert rss >= 0
