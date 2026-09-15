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

from io import BytesIO

import pytest

from pyrogram import raw, types
from pyrogram.methods.messages.edit_message_reply_markup import EditMessageReplyMarkup


class FakeClient(EditMessageReplyMarkup):
    """A client that captures the raw `messages.EditMessage` instead of sending it."""

    def __init__(self) -> None:
        self.captured: raw.functions.messages.EditMessage | None = None

    async def resolve_peer(self, peer_id: int) -> raw.base.InputPeer:
        return raw.types.InputPeerUser(
            user_id=peer_id,
            access_hash=0,
        )

    async def invoke(self, query: raw.functions.messages.EditMessage) -> raw.base.Updates:
        self.captured = query

        return raw.types.Updates(
            updates=[],
            users=[],
            chats=[],
            date=0,
            seq=0,
        )


def reply_markup_on_the_wire(client: FakeClient) -> raw.base.ReplyMarkup | None:
    """The captured request's `reply_markup`, read back from the bytes it serializes to."""
    assert client.captured is not None

    # `write()` prepends the constructor id that `read()` does not consume, so the round trip
    #  starts four bytes in. Reading the request back is what proves an omitted field is absent
    #  from the payload, rather than merely `None` on the object.
    payload = BytesIO(client.captured.write()[4:])

    return raw.functions.messages.EditMessage.read(payload).reply_markup


@pytest.mark.asyncio
async def test_not_passing_a_reply_markup_leaves_the_field_out_of_the_request() -> None:
    client = FakeClient()

    await client.edit_message_reply_markup(
        chat_id=7,
        message_id=11,
    )

    assert reply_markup_on_the_wire(client) is None


@pytest.mark.asyncio
async def test_passing_none_sends_an_inline_markup_with_no_rows() -> None:
    client = FakeClient()

    await client.edit_message_reply_markup(
        chat_id=7,
        message_id=11,
        reply_markup=None,
    )

    sent = reply_markup_on_the_wire(client)

    assert isinstance(sent, raw.types.ReplyInlineMarkup)
    assert sent.rows == []


@pytest.mark.asyncio
async def test_passing_a_markup_sends_its_buttons() -> None:
    client = FakeClient()

    await client.edit_message_reply_markup(
        chat_id=7,
        message_id=11,
        reply_markup=types.InlineKeyboardMarkup(
            [[types.InlineKeyboardButton("New button", callback_data="new_data")]]
        ),
    )

    sent = reply_markup_on_the_wire(client)

    assert isinstance(sent, raw.types.ReplyInlineMarkup)
    assert [button.text for row in sent.rows for button in row.buttons] == ["New button"]
