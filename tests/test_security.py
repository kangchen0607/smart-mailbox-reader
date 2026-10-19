import email
from email.policy import default

from smart_mailbox.security import analyze


def msg(headers: str):
    return email.message_from_string(headers + "\n\ncorps", policy=default)


def test_legit():
    m = msg("From: Free <info@newsletter.free.fr>\n"
            "Authentication-Results: mx.free.fr; spf=pass; dkim=pass; dmarc=pass")
    assert analyze(m) == ([], False)


def test_dmarc_fail_is_certain():
    signals, certain = analyze(msg("From: x@y.fr\nAuthentication-Results: mx; dmarc=fail"))
    assert certain and signals


def test_reply_to_and_lookalike():
    signals, certain = analyze(msg(
        "From: \"Service PayPal\" <alerte@paypal-securite.com>\nReply-To: a@gmail.com"))
    assert not certain
    assert any("gmail.com" in s for s in signals)
    assert any("paypal" in s for s in signals)


def test_display_name_spoof():
    signals, _ = analyze(msg("From: \"impots.gouv.fr <contact@dgfip.fr>\" <x@spam.ru>"))
    assert any("autre adresse" in s for s in signals)
