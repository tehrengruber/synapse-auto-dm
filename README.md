# synapse-auto-dm

Synapse module that automatically creates DM rooms between users, and one room per
user with themselves. When a user registers it creates a DM with every other local
user, and that one self room.

Nobody can be invited to the self room, so it is marked as a DM by writing the user's
`m.direct` account data keyed by their own ID. It is named after the user's display
name, falling back to their localpart when the display name is not set yet at
registration time.

Users who registered before the module existed never ran through that hook, so ten
seconds into every startup the module also creates the missing self rooms for all
existing users. Users who already have theirs are skipped, so the pass costs one
query plus one account data lookup per user and is a no-op from the second startup
on. It runs on the instance configured for background tasks, which is the main
process unless workers say otherwise.

Requires Synapse 1.90 or newer.

## Install

On Arch, from the checkout:

```bash
makepkg -si
```

Anywhere else, as an ordinary Python package:

```bash
pip install .
```

## Configure

In `homeserver.yaml`:

```yaml
modules:
  - module: synapse_auto_dm.AutoDMModule
    config: {}
```

| Option | Default | Purpose |
| --- | --- | --- |
| `self_room_name` | the user's display name | fixed name for the room a user shares with themselves, e.g. `Notizen` |
