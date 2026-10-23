"""Latex text splitter."""

from __future__ import annotations

from typing import Any

from langchain_text_splitters.base import Language
from langchain_text_splitters.character import RecursiveCharacterTextSplitter


class LatexTextSplitter(RecursiveCharacterTextSplitter):
    """Attempts to split the text along Latex-formatted layout elements."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize a LatexTextSplitter."""
        separators = self.get_separators_for_language(Language.LATEX)
        # The language separators are regexes (e.g. "\n\\\\section{"), as in
        # `from_language`; escaping them would never match a section.
        kwargs.setdefault("is_separator_regex", True)
        super().__init__(separators=separators, **kwargs)
