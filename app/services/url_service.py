import secrets
import string

from sqlalchemy.orm import Session

from app.database.models import URL


SHORT_CODE_LENGTH = 7


def generate_short_code() -> str:
    characters = (
        string.ascii_letters
        + string.digits
    )

    return "".join(
        secrets.choice(characters)
        for _ in range(SHORT_CODE_LENGTH)
    )


def generate_unique_short_code(
    database: Session,
) -> str:

    while True:
        short_code = generate_short_code()

        existing_url = (
            database.query(URL)
            .filter(URL.short_code == short_code)
            .first()
        )

        if existing_url is None:
            return short_code
