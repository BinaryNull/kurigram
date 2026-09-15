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

import pytest

import pyrogram
from pyrogram import types


def test_a_callback_written_against_a_plain_list_keeps_working() -> None:
    """Everything a pre-existing callback could do with the old `list` batch still holds."""
    messages = types.DeletedMessages([types.Message(id=1), types.Message(id=2)])

    assert isinstance(messages, list)
    assert len(messages) == 2

    assert messages[0].id == 1
    assert [message.id for message in messages] == [1, 2]
    assert [message.id for message in messages[1:]] == [2]


def test_the_batch_is_an_update() -> None:
    assert isinstance(types.DeletedMessages([]), types.Update)


def test_stop_propagation_raises_what_the_dispatcher_catches() -> None:
    with pytest.raises(pyrogram.StopPropagation):
        types.DeletedMessages([]).stop_propagation()


def test_continue_propagation_raises_what_the_dispatcher_catches() -> None:
    with pytest.raises(pyrogram.ContinuePropagation):
        types.DeletedMessages([]).continue_propagation()


def test_the_batch_reports_its_own_class_name() -> None:
    assert repr(types.DeletedMessages([1])) == "pyrogram.types.DeletedMessages([1])"
