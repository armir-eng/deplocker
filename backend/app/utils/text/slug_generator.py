import re
from typing import Annotated

from anyascii import anyascii
from pydantic import AfterValidator


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
        raise ValueError("Name must contain at least one alphanumeric character!")

    return slug


def ensure_sluggable(name: str) -> str:
    generate_slug(name)
    return name


# A name that `generate_slug` accepts. Request schemas use it, so an unusable
# name is rejected as a 422 before it reaches a route.
SluggableName = Annotated[str, AfterValidator(ensure_sluggable)]
