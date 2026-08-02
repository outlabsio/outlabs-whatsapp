from __future__ import annotations

import subprocess
import sys


def test_core_import_does_not_import_optional_frameworks() -> None:
    script = """
import sys
import outlabs_whatsapp
for forbidden in ('fastapi', 'sqlalchemy', 'taskq', 'outlabs_auth'):
    assert forbidden not in sys.modules, forbidden
assert outlabs_whatsapp.__version__ == '0.1.0a1'
"""
    subprocess.run([sys.executable, "-c", script], check=True)
