import discord

from config import EMBED_COLOR, FOOTER_TEXT


def base_embed(
    title: str,
    description: str = None
):
    """Create a standard bot embed."""

    embed = discord.Embed(
        title=title,
        description=description,
        color=EMBED_COLOR
    )

    embed.set_footer(
        text=FOOTER_TEXT
    )

    return embed


def success_embed(
    title: str,
    description: str
):
    """Create a success embed."""

    embed = base_embed(
        title=f"✅ {title}",
        description=description
    )

    return embed


def error_embed(
    title: str,
    description: str
):
    """Create an error embed."""

    embed = base_embed(
        title=f"❌ {title}",
        description=description
    )

    return embed


def info_embed(
    title: str,
    description: str
):
    """Create an information embed."""

    embed = base_embed(
        title=f"ℹ️ {title}",
        description=description
    )

    return embed


def moderation_embed(
    action: str,
    user: discord.Member,
    moderator: discord.Member,
    reason: str
):
    """Create a moderation activity log embed."""

    embed = base_embed(
        title=f"🛡️ Member {action}"
    )

    embed.add_field(
        name="👤 User",
        value=f"{user.mention}\n`{user.id}`",
        inline=False
    )

    embed.add_field(
        name="👮 Moderator",
        value=f"{moderator.mention}\n`{moderator.id}`",
        inline=False
    )

    embed.add_field(
        name="📝 Reason",
        value=reason,
        inline=False
    )

    return embed


def invite_embed(
    member: discord.Member,
    total: int,
    joined: int,
    left: int
):
    """Create an invite statistics embed."""

    embed = base_embed(
        title="📨 Invite Statistics"
    )

    embed.set_author(
        name=member.display_name,
        icon_url=member.display_avatar.url
    )

    embed.add_field(
        name="📊 Total Invites",
        value=f"`{total}`",
        inline=False
    )

    embed.add_field(
        name="✅ Joined",
        value=f"`{joined}`",
        inline=True
    )

    embed.add_field(
        name="❌ Left",
        value=f"`{left}`",
        inline=True
    )

    return embed


def invite_leaderboard_embed(
    entries: list
):
    """Create the invite leaderboard embed."""

    embed = base_embed(
        title="🏆 Invite Leaderboard",
        description="Top 10 members by invites."
    )

    if not entries:
        embed.description = "📂 No invite data available."
        return embed

    lines = []

    medals = {
        1: "🥇",
        2: "🥈",
        3: "🥉"
    }

    for position, entry in enumerate(
        entries[:10],
        start=1
    ):
        user_id = entry["user_id"]
        invites = entry["invites"]

        medal = medals.get(
            position,
            f"`#{position}`"
        )

        lines.append(
            f"{medal} <@{user_id}> — **{invites}** invites"
        )

    embed.description = "\n".join(lines)

    return embed


def giveaway_embed(
    prize: str,
    winners: int,
    end_text: str,
    host: discord.Member
):
    """Create a giveaway embed."""

    embed = base_embed(
        title="🎉 Giveaway!"
    )

    embed.add_field(
        name="🎁 Prize",
        value=prize,
        inline=False
    )

    embed.add_field(
        name="🏆 Winners",
        value=str(winners),
        inline=True
    )

    embed.add_field(
        name="⏰ Ends",
        value=end_text,
        inline=True
    )

    embed.add_field(
        name="👑 Hosted By",
        value=host.mention,
        inline=False
    )

    return embed