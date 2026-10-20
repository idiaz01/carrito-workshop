"""The same text on every computer, so a check gives the same result for every student."""

import unicodedata

# The model sometimes writes special dashes and quotes. A check must not depend on them.
_SAME = str.maketrans(
    {
        "‐": "-",  # hyphen
        "‑": "-",  # non-breaking hyphen: «2026‑10‑12»
        "‒": "-",
        "–": "-",  # en dash
        "—": "-",  # em dash
        "−": "-",  # minus sign
        "‘": "'",
        "’": "'",
        "“": '"',
        "”": '"',
        "«": '"',
        "»": '"',
    }
)


def normalize(text):
    """Text for a check: one form of each letter, one kind of space, dash and quote, lower case.

    NFKC changes the special spaces (no-break space, narrow no-break space in «69,85 €»)
    to a normal space and joins «a» + accent into «á». Accents stay.
    """
    text = unicodedata.normalize("NFKC", str(text)).translate(_SAME)
    return " ".join(text.split()).casefold()
