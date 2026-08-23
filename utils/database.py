import json
import os

from config import DATABASE_FILE


def load_database():
    """Load the database from the JSON file."""

    if not os.path.exists(DATABASE_FILE):
        return {}

    try:
        with open(
            DATABASE_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return {}


def save_database(data):
    """Save database data to the JSON file."""

    directory = os.path.dirname(DATABASE_FILE)

    if directory:
        os.makedirs(
            directory,
            exist_ok=True
        )

    with open(
        DATABASE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


def get_guild(guild_id):
    """Get a guild's saved data."""

    database = load_database()

    guild_id = str(guild_id)

    if guild_id not in database:

        database[guild_id] = {
            "activity_log_channel": None,
            "invites": {},
            "giveaways": {},
            "games": {}
        }

        save_database(database)

    else:

        database[guild_id].setdefault(
            "activity_log_channel",
            None
        )

        database[guild_id].setdefault(
            "invites",
            {}
        )

        database[guild_id].setdefault(
            "giveaways",
            {}
        )

        database[guild_id].setdefault(
            "games",
            {}
        )

        save_database(database)

    return database[guild_id]


def update_guild(guild_id, data):
    """Update a guild's saved data."""

    database = load_database()

    database[str(guild_id)] = data

    save_database(database)


# ==========================================
# ACTIVITY LOG
# ==========================================

def set_activity_log_channel(
    guild_id,
    channel_id
):
    """Save the moderation activity log channel."""

    guild_data = get_guild(
        guild_id
    )

    guild_data[
        "activity_log_channel"
    ] = channel_id

    update_guild(
        guild_id,
        guild_data
    )


def get_activity_log_channel(
    guild_id
):
    """Get the moderation activity log channel."""

    guild_data = get_guild(
        guild_id
    )

    return guild_data.get(
        "activity_log_channel"
    )


# ==========================================
# INVITES
# ==========================================

def get_invite_data(guild_id):
    """Get invite tracking data."""

    guild_data = get_guild(
        guild_id
    )

    return guild_data.setdefault(
        "invites",
        {}
    )


def save_invite_data(
    guild_id,
    invites
):
    """Save invite tracking data."""

    guild_data = get_guild(
        guild_id
    )

    guild_data["invites"] = invites

    update_guild(
        guild_id,
        guild_data
    )


# ==========================================
# GIVEAWAYS
# ==========================================

def get_giveaway_data(guild_id):
    """Get giveaway data."""

    guild_data = get_guild(
        guild_id
    )

    return guild_data.setdefault(
        "giveaways",
        {}
    )


def save_giveaway_data(
    guild_id,
    giveaways
):
    """Save giveaway data."""

    guild_data = get_guild(
        guild_id
    )

    guild_data["giveaways"] = giveaways

    update_guild(
        guild_id,
        guild_data
    )


# ==========================================
# GAMES
# ==========================================

def add_game(
    guild_id,
    name,
    status,
    event,
    event_key,
    link
):
    """Add a game to a guild."""

    guild_data = get_guild(
        guild_id
    )

    games = guild_data.setdefault(
        "games",
        {}
    )

    games[name] = {
        "status": status,
        "event": event,
        "event_key": event_key,
        "link": link
    }

    update_guild(
        guild_id,
        guild_data
    )


def edit_game(
    guild_id,
    name,
    status,
    event,
    event_key,
    link
):
    """Edit an existing game."""

    guild_data = get_guild(
        guild_id
    )

    games = guild_data.setdefault(
        "games",
        {}
    )

    if name not in games:
        return False

    games[name] = {
        "status": status,
        "event": event,
        "event_key": event_key,
        "link": link
    }

    update_guild(
        guild_id,
        guild_data
    )

    return True


def delete_game(
    guild_id,
    name
):
    """Delete a game."""

    guild_data = get_guild(
        guild_id
    )

    games = guild_data.setdefault(
        "games",
        {}
    )

    if name not in games:
        return False

    del games[name]

    update_guild(
        guild_id,
        guild_data
    )

    return True


def get_game(
    guild_id,
    name
):
    """Get one game."""

    guild_data = get_guild(
        guild_id
    )

    games = guild_data.setdefault(
        "games",
        {}
    )

    return games.get(
        name
    )


def get_all_games(guild_id):
    """Get all games."""

    guild_data = get_guild(
        guild_id
    )

    return guild_data.setdefault(
        "games",
        {}
    )