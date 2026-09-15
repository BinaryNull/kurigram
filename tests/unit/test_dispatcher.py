#  Pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-present Dan <https://github.com/delivrance>
#
#  This file is part of Pyrogram.
#
#  Pyrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pyrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Pyrogram.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations as _annotations

import asyncio

import pytest

import pyrogram
from pyrogram import raw, types
from pyrogram.dispatcher import Dispatcher
from pyrogram.handlers import DeletedMessagesHandler


# The packet shape is the element type of `Dispatcher.updates_queue`.
def _deletion_packet() -> tuple[
    raw.base.Update, dict[int, raw.base.User], dict[int, raw.base.Chat]
]:
    deletion = raw.types.UpdateDeleteMessages(
        messages=[1, 2],
        pts=0,
        pts_count=0,
    )

    return (deletion, {}, {})


async def _drain(dispatcher: Dispatcher) -> None:
    """Run one worker over what is queued: the `None` sentinel makes it return."""
    dispatcher.updates_queue.put_nowait(None)

    await dispatcher.handler_worker(asyncio.Lock())


@pytest.mark.asyncio
async def test_stop_propagation_on_a_deleted_messages_batch_stops_the_chain() -> None:
    reached: list[str] = []

    # Every callback in this module is positional-only: `Dispatcher.handler_worker`
    #  calls `callback(client, *args)`.
    async def stopping(_client: pyrogram.Client, messages: types.DeletedMessages, /) -> None:
        reached.append("stopping")
        messages.stop_propagation()

    async def never_reached(_client: pyrogram.Client, messages: types.DeletedMessages, /) -> None:
        reached.append("never_reached")

    dispatcher = Dispatcher(
        pyrogram.Client(
            name="test_client",
            in_memory=True,
        )
    )
    dispatcher.groups[0] = [DeletedMessagesHandler(stopping)]
    dispatcher.groups[1] = [DeletedMessagesHandler(never_reached)]

    dispatcher.updates_queue.put_nowait(_deletion_packet())

    await _drain(dispatcher)

    assert reached == ["stopping"]


@pytest.mark.asyncio
async def test_continue_propagation_on_a_deleted_messages_batch_reaches_the_next_handler() -> None:
    reached: list[str] = []

    async def continuing(_client: pyrogram.Client, messages: types.DeletedMessages, /) -> None:
        reached.append("continuing")
        messages.continue_propagation()

    async def next_in_group(_client: pyrogram.Client, messages: types.DeletedMessages, /) -> None:
        reached.append("next_in_group")

    dispatcher = Dispatcher(
        pyrogram.Client(
            name="test_client",
            in_memory=True,
        )
    )

    # One group: without `continue_propagation()` the first match ends the group.
    dispatcher.groups[0] = [
        DeletedMessagesHandler(continuing),
        DeletedMessagesHandler(next_in_group),
    ]

    dispatcher.updates_queue.put_nowait(_deletion_packet())

    await _drain(dispatcher)

    assert reached == ["continuing", "next_in_group"]
