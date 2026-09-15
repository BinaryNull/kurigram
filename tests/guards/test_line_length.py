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

"""No line of code runs past the column limit `pyproject.toml` sets.

Nothing else asserts it, and the two things that look as if they do are both something
else. `ruff format --check` asks whether a file is byte-identical to its own output, not
whether a line fits: a literal already alone on its line has no break point left, so the
formatter's output is the long line and the check passes on it. `E501` is the only rule
that measures a column, and `[tool.ruff].select` carries `E9` alone out of the `E` family.

Selecting `E501` is not the missing piece either. Measured on 2026-09-15, 2350 lines of the
hand-written tree run past 100 columns and five of them are code: 2258 sit inside a string,
almost all of them docstrings copied from Telegram's API documentation, and 87 inside a
comment holding a URL. Neither can be wrapped and neither is ours to rewrite.
`per-file-ignores` cannot express that split, because the docstrings are spread over dozens
of files and exempting a file also exempts every line nobody has written in it yet.

So this reads the column the limit falls on and asks what is sitting there. Prose that has
no break point is left alone; code is not.
"""

from __future__ import annotations as _annotations

import io
import re
import tokenize
from collections.abc import Mapping
from itertools import chain
from typing import Final

from tests.guards.name_resolution import REPOSITORY_ROOT, hand_written_files, tooling_files

# Canonical: `[tool.ruff].line-length` in `pyproject.toml`, which
#  `test_the_limit_is_the_one_the_formatter_targets` reads to keep the two equal.
_LIMIT: Final[int] = 100

_DECLARED_LIMIT: Final[re.Pattern[str]] = re.compile(r"^line-length = (\d+)$", re.MULTILINE)

# A line no wrapping can bring under the limit, and why. The key is the line's own text, so
#  an entry survives the line moving and stops matching the moment the line is edited and
#  has to be judged again.
_UNSHORTENABLE: Final[Mapping[str, str]] = {
    "chat_has_protected_content_disable_requested=chat_has_protected_content_disable_requested,": (
        "`chat_has_protected_content_disable_requested` is a field of `Message`, and the local "
        "it forwards carries the field's name. 44 columns twice, plus the indent of the "
        "constructor call, is 102, and shortening either half renames a public attribute."
    ),
}


def prose_at(source: str, *, column: int) -> set[int]:
    """The lines of `source` whose character at `column` sits inside a string or a comment.

    An f-string counts whole, from its opening quote to its closing one. Python 3.12 split it
    into a start token, its literal pieces and the tokens of every replacement field, so
    reading its interior would make one line pass on 3.11 and fail on 3.12.
    https://peps.python.org/pep-0701/
    """
    found: set[int] = set()
    fstring_depth: int = 0

    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        name = tokenize.tok_name[token.type]

        if name == "FSTRING_START":
            fstring_depth += 1

        is_prose: bool = fstring_depth > 0 or name in {"STRING", "COMMENT"}

        if name == "FSTRING_END":
            fstring_depth -= 1

        if not is_prose:
            continue

        start_row, start_column = token.start
        end_row, end_column = token.end

        for row in range(start_row, end_row + 1):
            starts_at_or_before = start_column <= column if row == start_row else True
            ends_after = column < end_column if row == end_row else True

            if starts_at_or_before and ends_after:
                found.add(row)

    return found


def code_over_the_limit(source: str) -> list[int]:
    """The line of every statement in `source` running past the limit with code at the limit."""
    excused = prose_at(source, column=_LIMIT)

    return [
        number
        for number, line in enumerate(source.splitlines(), start=1)
        if len(line) > _LIMIT and number not in excused and line.strip() not in _UNSHORTENABLE
    ]


def lines_over_the_limit() -> list[str]:
    found: list[str] = []

    for path in chain(hand_written_files(), tooling_files()):
        relative = path.relative_to(REPOSITORY_ROOT).as_posix()
        found.extend(f"{relative}:{line}" for line in code_over_the_limit(path.read_text()))

    return found


def test_no_line_of_code_runs_past_the_limit() -> None:
    assert lines_over_the_limit() == []


def test_the_limit_is_the_one_the_formatter_targets() -> None:
    declared = _DECLARED_LIMIT.search((REPOSITORY_ROOT / "pyproject.toml").read_text())

    assert declared is not None
    assert int(declared.group(1)) == _LIMIT


def test_the_sweep_reads_the_modules_it_claims_to() -> None:
    swept = [
        path.relative_to(REPOSITORY_ROOT).as_posix()
        for path in chain(hand_written_files(), tooling_files())
    ]

    assert len(swept) > 700

    # One from each root, so dropping a root fails here rather than passing quietly.
    assert "pyrogram/client.py" in swept
    assert "tests/guards/test_line_length.py" in swept
    assert "compiler/api/compiler.py" in swept


def test_the_sweep_reads_both_halves_of_what_it_asks() -> None:
    code: str = " " * 90 + "value = compute(argument)\n"
    assert code_over_the_limit(code) == [1]

    docstring: str = '"""' + "documented " * 12 + '"""\n'
    assert len(docstring) > _LIMIT
    assert code_over_the_limit(docstring) == []

    comment: str = "# " + "https://example.com/" * 6 + "\n"
    assert len(comment) > _LIMIT
    assert code_over_the_limit(comment) == []

    # A trailing comment is prose, and the code before it still has to fit.
    assert code_over_the_limit("value = 1  # " + "reason " * 20 + "\n") == []
    assert code_over_the_limit(" " * 95 + "value = 1  # short\n") == [1]


def test_an_f_string_counts_as_one_literal_on_every_supported_interpreter() -> None:
    # So an over-long f-string is prose here and goes unreported, which is the cost of the
    #  rule reading the same on 3.10 and on 3.12: 3.12 tokenizes the replacement fields
    #  separately, so anything reading inside one answers differently per interpreter.
    #  https://peps.python.org/pep-0701/
    assert code_over_the_limit('log.info(f"{name} ' + "padding " * 12 + '")\n') == []


def test_every_recorded_line_is_still_in_the_tree() -> None:
    recorded = {
        line.strip()
        for path in chain(hand_written_files(), tooling_files())
        for line in path.read_text().splitlines()
        if line.strip() in _UNSHORTENABLE
    }

    assert recorded == set(_UNSHORTENABLE)
