from chunklint.rules.boundary import (
    BrokenChunkBoundaryRule,
    EndsMidSentenceRule,
    StartsMidSentenceRule,
)
from chunklint.rules.code_block import BrokenCodeBlockRule
from chunklint.rules.duplicate import NearDuplicateRule
from chunklint.rules.markdown_table import BrokenMarkdownTableRule
from chunklint.rules.missing_heading import MissingHeadingRule
from chunklint.rules.missing_id import MissingIdRule
from chunklint.rules.missing_source import MissingSourceRule
from chunklint.rules.missing_text import MissingTextRule
from chunklint.rules.pdf_noise import PdfNoiseRule
from chunklint.rules.size import TooLongRule, TooShortRule

DEFAULT_RULES = [
    MissingTextRule(),
    MissingIdRule(),
    MissingSourceRule(),
    MissingHeadingRule(),
    StartsMidSentenceRule(),
    EndsMidSentenceRule(),
    TooShortRule(),
    TooLongRule(),
    BrokenMarkdownTableRule(),
    BrokenCodeBlockRule(),
]

DEFAULT_CROSS_CHUNK_RULES = [
    BrokenChunkBoundaryRule(),
    NearDuplicateRule(),
    PdfNoiseRule(),
]

ALL_RULES = [*DEFAULT_RULES, *DEFAULT_CROSS_CHUNK_RULES]
