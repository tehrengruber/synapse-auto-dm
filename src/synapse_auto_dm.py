import logging

from synapse.module_api import ModuleApi

logger = logging.getLogger(__name__)

DIRECT_ACCOUNT_DATA_TYPE = "m.direct"

# Long enough to stay out of the way of the rest of the startup, short enough that
# a user logging in right after a restart finds their rooms.
BACKFILL_DELAY_MS = 10 * 1000


def _select_all_users(txn):
    txn.execute("SELECT name FROM users WHERE deactivated = 0")
    return [row[0] for row in txn.fetchall()]


class AutoDMModule:
    def __init__(self, config: dict, api: ModuleApi):
        self._api = api
        self._self_room_name = config.get("self_room_name")
        api.register_account_validity_callbacks(
            on_user_registration=self.on_user_registration,
        )
        # Users who registered before the module gained the self DM never went
        # through on_user_registration for one, so catch them up once per startup.
        # The call cannot be awaited here — the reactor is not serving yet — and it
        # is scheduled on the background worker only, so it runs a single time.
        if api.should_run_background_tasks():
            api.delayed_background_call(
                BACKFILL_DELAY_MS,
                self.backfill_self_rooms,
                desc="auto_dm_self_room_backfill",
            )
        logger.info("AutoDMModule loaded")

    @staticmethod
    def parse_config(config: dict) -> dict:
        return config

    async def on_user_registration(self, user_id: str) -> None:
        logger.info("New user registered: %s — creating DM rooms", user_id)

        all_users = await self._get_all_users()

        for other_user_id in all_users:
            if other_user_id == user_id:
                continue
            try:
                room_id, _ = await self._api.create_room(
                    user_id=user_id,
                    config={
                        "preset": "trusted_private_chat",
                        "is_direct": True,
                        "invite": [other_user_id],
                    },
                    ratelimit=False,
                )
                await self._api.update_room_membership(
                    sender=other_user_id,
                    target=other_user_id,
                    room_id=room_id,
                    new_membership="join",
                )
                await self._mark_direct(user_id, other_user_id, room_id)
                await self._mark_direct(other_user_id, user_id, room_id)
                logger.info(
                    "Created DM %s <-> %s: %s", user_id, other_user_id, room_id
                )
            except Exception:
                logger.exception(
                    "Failed to create DM %s <-> %s", user_id, other_user_id
                )

        try:
            await self._create_self_room(user_id)
        except Exception:
            logger.exception("Failed to create self DM for %s", user_id)

    async def backfill_self_rooms(self) -> None:
        """Give every existing user the room they share with themselves.

        Creating one is a no-op for users who already have it, so this can run on
        every startup.
        """
        for user_id in await self._get_all_users():
            try:
                await self._create_self_room(user_id)
            except Exception:
                logger.exception("Failed to create self DM for %s", user_id)

    async def _get_all_users(self) -> list:
        return await self._api.run_db_interaction(
            "get_all_local_users", _select_all_users
        )

    async def _create_self_room(self, user_id: str) -> None:
        """Create the room a user shares with nobody but themselves.

        A user cannot invite themselves, so the room is keyed by the user's own ID
        in their ``m.direct`` account data.
        """
        if await self._has_self_room(user_id):
            logger.debug("Self DM for %s already exists", user_id)
            return

        room_id, _ = await self._api.create_room(
            user_id=user_id,
            config={
                "preset": "trusted_private_chat",
                "is_direct": True,
                "name": self._self_room_name or await self._get_room_name(user_id),
            },
            ratelimit=False,
        )
        await self._mark_direct(user_id, user_id, room_id)
        logger.info("Created self DM for %s: %s", user_id, room_id)

    async def _has_self_room(self, user_id: str) -> bool:
        direct = await self._get_direct_account_data(user_id)
        return bool(direct.get(user_id))

    async def _mark_direct(
        self, user_id: str, other_user_id: str, room_id: str
    ) -> None:
        """Record a room as a DM with ``other_user_id`` in ``user_id``'s account data.

        ``is_direct`` on room creation only reaches the invite event; writing
        ``m.direct`` is the client's job, and no client takes part in creating these
        rooms. Clients that go by the account data treat an untagged room as a group
        room, which on Element Classic means offering a Jitsi conference rather than
        a 1:1 call.
        """
        direct = await self._get_direct_account_data(user_id)
        rooms = list(direct.get(other_user_id) or [])
        if room_id in rooms:
            return
        rooms.append(room_id)
        direct[other_user_id] = rooms
        await self._api.account_data_manager.put_global(
            user_id, DIRECT_ACCOUNT_DATA_TYPE, direct
        )

    async def _get_direct_account_data(self, user_id: str) -> dict:
        direct = await self._api.account_data_manager.get_global(
            user_id, DIRECT_ACCOUNT_DATA_TYPE
        )
        return dict(direct) if isinstance(direct, dict) else {}

    async def _get_room_name(self, user_id: str) -> str:
        """Name the self DM after the user, the way Element names a DM after its
        other member. The display name is not necessarily set yet at registration
        time, in which case the localpart has to do."""
        localpart = user_id.split(":", 1)[0].lstrip("@")
        try:
            profile = await self._api.get_profile_for_user(localpart)
            return profile.display_name or localpart
        except Exception:
            logger.exception("Failed to read the display name of %s", user_id)
            return localpart
