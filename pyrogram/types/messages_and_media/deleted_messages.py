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

from ..list import List
from ..update import Update


class DeletedMessages(List, Update):
    """The batch of messages a single deletion event removed.

    A ``list`` of :obj:`~pyrogram.types.Message`: iteration, indexing, slicing and
    ``len()`` work as on a plain list, so a callback written against one keeps working
    unchanged. Being an update as well, it carries ``stop_propagation()`` and
    ``continue_propagation()``, so a deleted-messages callback can control the handler
    chain the way every other callback can.
    """
