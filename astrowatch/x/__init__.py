"""
Astrowatch Online -- optional X (Twitter) publishing module.
================================================================
Entirely optional: the rest of the platform (calculation engine, AI layer,
autonomous agent, scheduler) works completely without this package being
configured or even importable. Gated by X_ENABLED (default "false") --
publisher.py checks this BEFORE doing anything else, including before
constructing a client or touching credentials.

No third-party Twitter SDK dependency (tweepy etc.) -- implements the minimal
OAuth 1.0a User Context signing needed for POST /2/tweets directly with the
standard library (hmac/hashlib/urllib), consistent with this project's
stdlib-first convention (see requirements.txt's own note, and api.py's
docstring on the same point).
"""
