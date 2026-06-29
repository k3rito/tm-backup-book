import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from utils import sanitize_filename, current_rss_bytes

def test_sanitize_filename():
    assert sanitize_filename("hello.txt") == "hello.txt"
    assert sanitize_filename("some/path/file.txt") == "file.txt"
    assert sanitize_filename("unclean@filename!.txt") == "unclean_filename_.txt"
    assert sanitize_filename("   spaced name   ") == "spaced_name"
    assert sanitize_filename("") == "file"

def test_current_rss_bytes():
    rss = current_rss_bytes()
    assert isinstance(rss, int)
    assert rss > 0
