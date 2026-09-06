import re

from anyascii import anyascii


def generate_slug(name: str) -> str:
    """
    Converts a string into URL-safe slug
    Removes accents, converts to lowercase, replaces spaces with hyphens,
    and strips special characters.

    Examples:
        "Café Médiatech" → "cafe-mediatech"
        "My___Org" → "my-org"
    """

    slug = anyascii(name)
    slug = slug.lower()

    slug = re.sub(r"[\s_]", "-", slug)  # Replace spaces and underscores with hyphens
    slug = re.sub(r"[^a-z0-9-]", "", slug)  # Remove all non-alphanumeric except hyphens
    slug = re.sub(r"-+", "-", slug)  # Remove duplicate hyphens
    slug = slug.strip("-")  # Strip leading or trailing hyphens

    if not slug:
        raise ValueError(
            "Project name must contain at least one alphanumeric character!"
        )

    return slug
