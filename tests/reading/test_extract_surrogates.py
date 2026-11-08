"""Extraction must survive unpaired surrogate code points.

PDFs with broken embedded-font CMaps (this hit 《销售铁军》's bookmark titles
and some headings) yield lone surrogates that every later UTF-8 write rejects
with ``surrogates not allowed`` — the whole ingest used to crash. They are
mojibake artifacts, not content: the extraction boundary strips them from
units, title and outline.
"""

import pytest

from deeptutor.reading.extract import Extraction, _strip_surrogates, extract_material


def test_strip_surrogates_removes_only_lone_surrogates():
    dirty = "正常文字\ud83c残缺代理\r\n第二行\udfff结尾"
    assert _strip_surrogates(dirty) == "正常文字残缺代理\r\n第二行结尾"
    assert _strip_surrogates("无害文本") == "无害文本"


def test_extract_material_sanitizes_surrogates(tmp_path, monkeypatch):
    import deeptutor.reading.extract as extract_module

    dirty = Extraction(
        units=("第一页\ud83c正文\r\n", "\udfff第二页"),
        unit="page",
        extractor="pymupdf",
        title="销售\ud83c铁军",
        outline=(extract_module.OutlineEntry(level=1, title="第一章\udfff 阿里铁军", locator=1),),
    )
    monkeypatch.setattr(extract_module, "_extract_pdf", lambda source: dirty)
    # A .pdf suffix routes to the (patched) PDF extractor; the file only has
    # to exist for the boundary check.
    source = tmp_path / "book.pdf"
    source.write_bytes(b"%PDF-1.4 fake")

    result = extract_material(source)

    assert result.units == ("第一页正文\r\n", "第二页")
    assert result.title == "销售铁军"
    assert result.outline[0].title == "第一章 阿里铁军"


def test_extract_material_still_rejects_empty_text(tmp_path, monkeypatch):
    import deeptutor.reading.extract as extract_module

    empty = Extraction(units=("", ""), unit="page", extractor="pymupdf")
    monkeypatch.setattr(extract_module, "_extract_pdf", lambda source: empty)
    source = tmp_path / "book.pdf"
    source.write_bytes(b"%PDF-1.4 fake")
    with pytest.raises(Exception, match="no readable text"):
        extract_material(source)
