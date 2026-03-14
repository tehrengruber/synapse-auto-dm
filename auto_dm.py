import logging

from synapse.module_api import ModuleApi

logger = logging.getLogger(__name__)


class AutoDMModule:
    def __init__(self, config: dict, api: ModuleApi):
        self._api = api
        api.register_account_validity_callbacks(
            on_user_registration=self.on_user_registration,
        )
        logger.info("AutoDMModule loaded")

    @staticmethod
    def parse_config(config: dict) -> dict:
        return config

    async def on_user_registration(self, user_id: str) -> None:
        logger.info("New user registered: %s — creating DM rooms", user_id)

        def _get_all_users(txn):
            txn.execute("SELECT name FROM users WHERE deactivated = 0")
            return [row[0] for row in txn.fetchall()]

        all_users = await self._api.run_db_interaction(
            "get_all_local_users", _get_all_users
        )

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
                logger.info(
                    "Created DM %s <-> %s: %s", user_id, other_user_id, room_id
                )
            except Exception:
                logger.exception(
                    "Failed to create DM %s <-> %s", user_id, other_user_id
                )