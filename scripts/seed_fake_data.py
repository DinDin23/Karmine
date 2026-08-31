"""Seed fake users/wagers/transactions into the TEST database only.

Usage:
    poetry run python scripts/seed_fake_data.py [--count N] [--reset]

Loads DATABASE_URL from .env.test (never from .env) and refuses to run
unless that URL points at a database named "karmine_test" -- this is the
hard gate that keeps fake data from ever landing in the production DB.

All seeded users share the password "password123" for easy manual login
during testing.
"""

import argparse
import random
import sys
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
env_test_path = REPO_ROOT / ".env.test"

if not env_test_path.exists():
    sys.exit(f"Missing {env_test_path} -- refusing to guess a database to seed.")

# Override any inherited DATABASE_URL so app.config.Settings picks up the
# test database, not whatever is in the real .env.
load_dotenv(env_test_path, override=True)

# Running this file directly (not `python -m`) doesn't put the repo root on
# sys.path, so the "app" package wouldn't otherwise be importable.
sys.path.insert(0, str(REPO_ROOT))

from app.core.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models.matchmaking_request import MatchmakingRequest  # noqa: E402,F401
from app.models.transaction import Transaction, TransactionType  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.wager import Wager, WagerStatus  # noqa: E402

from faker import Faker  # noqa: E402

SEED_PASSWORD = "password123"


def _assert_test_database() -> None:
    db_name = engine.url.database or ""
    if db_name != "karmine_test":
        sys.exit(
            f"Refusing to seed database '{db_name}' -- this script only ever "
            "targets 'karmine_test'. Check .env.test."
        )


def reset(db) -> None:
    print("Resetting: truncating all tables...")
    db.execute(
        Base.metadata.tables["transactions"].delete()
    )
    db.execute(Base.metadata.tables["matchmaking_requests"].delete())
    db.execute(Base.metadata.tables["wagers"].delete())
    db.execute(Base.metadata.tables["users"].delete())
    db.commit()


def seed_users(db, fake: Faker, count: int) -> list[User]:
    users = []
    for _ in range(count):
        user = User(
            username=fake.unique.user_name()[:32],
            email=fake.unique.email(),
            hashed_password=hash_password(SEED_PASSWORD),
            cr_player_tag="#" + fake.unique.bothify(text="????????").upper(),
            phone_number=fake.unique.numerify("+1##########"),
            sms_consent=True,
            supercell_id_link=f"https://link.clashroyale.com/invite/friend/en?tag={fake.bothify('??????')}",
        )
        db.add(user)
        users.append(user)
    db.flush()  # assign IDs without committing yet

    for user in users:
        deposit_amount = Decimal(random.randint(2000, 50000)) / 100
        db.add(
            Transaction(
                user_id=user.id,
                type=TransactionType.DEPOSIT,
                amount=deposit_amount,
            )
        )
    return users


def seed_wagers(db, users: list[User], count: int) -> None:
    for _ in range(count):
        player1, player2 = random.sample(users, 2)
        stake = Decimal(random.randint(500, 5000)) / 100
        winner = random.choice([player1, player2])

        wager = Wager(
            player1_id=player1.id,
            player2_id=player2.id,
            stake_amount=stake,
            status=WagerStatus.SETTLED,
            winner_id=winner.id,
        )
        db.add(wager)
        db.flush()

        db.add(Transaction(user_id=player1.id, wager_id=wager.id, type=TransactionType.WAGER_LOCK, amount=-stake))
        db.add(Transaction(user_id=player2.id, wager_id=wager.id, type=TransactionType.WAGER_LOCK, amount=-stake))
        db.add(
            Transaction(
                user_id=winner.id,
                wager_id=wager.id,
                type=TransactionType.WAGER_PAYOUT,
                amount=stake * 2,
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=20, help="number of fake users to create")
    parser.add_argument("--reset", action="store_true", help="wipe all rows before seeding")
    args = parser.parse_args()

    _assert_test_database()

    fake = Faker()
    db = SessionLocal()
    try:
        if args.reset:
            reset(db)

        users = seed_users(db, fake, args.count)
        seed_wagers(db, users, count=max(args.count // 4, 1))
        db.commit()

        print(f"Seeded {len(users)} fake users into 'karmine_test' (password: {SEED_PASSWORD})")
        print(f"Sample login: {users[0].email} / {SEED_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
