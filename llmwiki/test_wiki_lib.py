"""Test cho wiki_lib.py — logic thuần (frontmatter/wikilink/index), tham số hoá `wiki_root` để
verify DÙNG CHUNG ĐÚNG cho cả wiki dự án (`llmwiki/wiki/`) LẪN wiki riêng từng agent
(`demo_agents/*/wiki/`) — không phải 2 bản logic khác nhau. Dùng CHÍNH `llmwiki/wiki/` thật làm
input cho phần test index/wikilink thực (không fixture giả). Verify sống qua curl/http.client đã
làm tay lúc build — xem wiki/log.md."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from llmwiki import wiki_lib  # noqa: E402

_PROJECT_WIKI = Path(__file__).parent / "wiki"


def test_build_index_finds_real_project_wiki_pages():
    pages, slug_to_rel = wiki_lib.build_index(_PROJECT_WIKI)
    assert len(pages) > 40  # dự án hiện có 56+ file .md, trừ index.md/log.md
    assert "agent" in slug_to_rel
    assert slug_to_rel["agent"] == "concepts/agent.md"


def test_build_index_excludes_index_and_log_md():
    pages, _ = wiki_lib.build_index(_PROJECT_WIKI)
    rels = {p["rel"] for p in pages}
    assert "index.md" not in rels
    assert "log.md" not in rels


def test_build_index_registers_aliases():
    """aliases: [..] trong frontmatter phải trỏ TỚI CÙNG 1 rel — dùng cho wiki riêng từng agent
    (vd 1 note thời tiết Hà Nội có alias 'hanoi'/'ha noi')."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "wiki" / "sources"
        root.mkdir(parents=True)
        (root / "hanoi.md").write_text(
            "---\ntype: source\ntitle: Hanoi\naliases: [hanoi, \"ha noi\"]\n---\nBody.\n",
            encoding="utf-8",
        )
        pages, slug_to_rel = wiki_lib.build_index(Path(tmp) / "wiki")
        assert slug_to_rel["hanoi"] == "sources/hanoi.md"
        assert slug_to_rel["ha noi"] == "sources/hanoi.md"


def test_parse_frontmatter_extracts_type_title_tags():
    text = "---\ntype: concept\ntitle: Test Page\ntags: [a, b]\n---\n\nBody text here."
    meta, body = wiki_lib.parse_frontmatter(text)
    assert meta["type"] == "concept"
    assert meta["title"] == "Test Page"
    assert meta["tags"] == ["a", "b"]
    assert body.strip() == "Body text here."


def test_parse_frontmatter_missing_returns_empty_meta():
    meta, body = wiki_lib.parse_frontmatter("# Just a heading\n\nNo frontmatter.")
    assert meta == {}
    assert "Just a heading" in body


def test_parse_frontmatter_malformed_yaml_fails_open():
    text = "---\ntype: [unclosed\n---\n\nBody."
    meta, body = wiki_lib.parse_frontmatter(text)
    assert meta == {}  # fail-open, không raise


def test_resolve_wikilinks_known_slug_becomes_real_link():
    out = wiki_lib.resolve_wikilinks("See [[agent]] for details.", {"agent": "concepts/agent.md"})
    assert '<a class="wl" href="/wiki/concepts/agent.md">agent</a>' in out


def test_resolve_wikilinks_unknown_slug_becomes_missing_span():
    out = wiki_lib.resolve_wikilinks("See [[nonexistent-page]] for details.", {})
    assert "wl-missing" in out
    assert "nonexistent-page" in out
    assert "<a " not in out  # KHÔNG được render thành link giả


def test_resolve_wikilinks_supports_custom_label():
    out = wiki_lib.resolve_wikilinks("See [[agent|the Agent concept]].", {"agent": "concepts/agent.md"})
    assert ">the Agent concept</a>" in out


def test_resolve_wikilinks_respects_custom_prefix():
    """Route /wiki của mỗi agent dùng CÙNG prefix '/wiki' (mount trên chính port của agent đó) —
    nhưng hàm phải hỗ trợ prefix khác nếu sau này cần, không hardcode."""
    out = wiki_lib.resolve_wikilinks("[[agent]]", {"agent": "concepts/agent.md"}, prefix="/custom")
    assert 'href="/custom/concepts/agent.md"' in out


def test_render_markdown_handles_tables_and_wikilinks_together():
    body = "# Title\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\nSee [[agent]].\n"
    out = wiki_lib.render_markdown(body, {"agent": "concepts/agent.md"})
    assert "<table>" in out
    assert '<a class="wl" href="/wiki/concepts/agent.md">agent</a>' in out


def test_sidebar_html_groups_by_type_and_marks_active():
    pages = [
        {"rel": "concepts/a.md", "meta": {"type": "concept"}, "title": "A"},
        {"rel": "sources/b.md", "meta": {"type": "source"}, "title": "B"},
    ]
    out = wiki_lib.sidebar_html(pages, "concepts/a.md")
    assert "Concepts" in out
    assert "Sources" in out
    assert 'class="active"' in out


def test_resolve_safe_path_blocks_traversal_outside_wiki_root():
    assert wiki_lib.resolve_safe_path(_PROJECT_WIKI, "../../etc/passwd") is None


def test_resolve_safe_path_allows_real_file_inside_root():
    target = wiki_lib.resolve_safe_path(_PROJECT_WIKI, "concepts/agent.md")
    assert target is not None
    assert target.is_file()


def test_render_wiki_page_404_for_missing_file():
    status, body = wiki_lib.render_wiki_page(_PROJECT_WIKI, "concepts/does-not-exist.md", "test")
    assert status == 404


def test_render_wiki_page_200_for_real_file():
    status, body = wiki_lib.render_wiki_page(_PROJECT_WIKI, "concepts/agent.md", "test")
    assert status == 200
    assert "<h1>" in body


def _write_page(root, rel, type_="source", title="T", body="Body."):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"---\ntype: {type_}\ntitle: {title}\n---\n\n{body}\n\n## Origin\n- test\n", encoding="utf-8")
    return p


def test_iter_md_files_excludes_raw_siblings():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "wiki"
        _write_page(root, "sources/topic/topic.md", body="Linted.")
        _write_page(root, "sources/topic/topic-raw.md", body="Raw dump.")
        rels = {str(rel) for _, rel in wiki_lib.iter_md_files(root)}
        assert "sources/topic/topic.md" in rels
        assert "sources/topic/topic-raw.md" not in rels


def test_build_index_excludes_raw_from_pages_and_slugs():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "wiki"
        _write_page(root, "sources/topic/topic.md", body="Linted.")
        _write_page(root, "sources/topic/topic-raw.md", body="Raw dump.")
        pages, slug_to_rel = wiki_lib.build_index(root)
        assert {p["rel"] for p in pages} == {"sources/topic/topic.md"}
        assert "topic-raw" not in slug_to_rel


def test_render_wiki_page_linted_links_to_raw_sibling():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "wiki"
        _write_page(root, "sources/topic/topic.md", body="Linted.")
        _write_page(root, "sources/topic/topic-raw.md", body="Raw dump.")
        status, body = wiki_lib.render_wiki_page(root, "sources/topic/topic.md", "test")
        assert status == 200
        assert 'href="/wiki/sources/topic/topic-raw.md"' in body
        assert "Xem bản gốc" in body


def test_render_wiki_page_raw_links_back_to_linted():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "wiki"
        _write_page(root, "sources/topic/topic.md", body="Linted.")
        _write_page(root, "sources/topic/topic-raw.md", body="Raw dump.")
        status, body = wiki_lib.render_wiki_page(root, "sources/topic/topic-raw.md", "test")
        assert status == 200
        assert 'href="/wiki/sources/topic/topic.md"' in body
        assert "bản đã biên tập" in body


def test_render_wiki_page_no_raw_link_when_no_sibling():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "wiki"
        _write_page(root, "sources/topic/topic.md", body="Linted only.")
        status, body = wiki_lib.render_wiki_page(root, "sources/topic/topic.md", "test")
        assert status == 200
        assert 'class="raw-link"' not in body
