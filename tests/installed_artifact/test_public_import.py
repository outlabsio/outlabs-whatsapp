from __future__ import annotations


def test_public_import_and_version() -> None:
    import outlabs_whatsapp

    assert outlabs_whatsapp.__version__ == "0.1.0a1"
