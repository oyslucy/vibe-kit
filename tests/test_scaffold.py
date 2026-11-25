from vibe_kit import scaffold


def test_copies_template_and_renames_gitignore(repo_root, tmp_path):
    scaffold.apply_template(repo_root / "templates" / "project", tmp_path, "demo")
    assert (tmp_path / "CLAUDE.md").read_text().startswith("# demo")
    assert "/CLAUDE.md" in (tmp_path / ".gitignore").read_text().splitlines()
    assert not (tmp_path / "gitignore").exists()


def test_keeps_existing_files_and_merges_gitignore(repo_root, tmp_path):
    (tmp_path / "CLAUDE.md").write_text("mine\n")
    (tmp_path / ".gitignore").write_text("node_modules/")
    scaffold.apply_template(repo_root / "templates" / "project", tmp_path, "demo")
    assert (tmp_path / "CLAUDE.md").read_text() == "mine\n"
    lines = (tmp_path / ".gitignore").read_text().splitlines()
    assert lines[0] == "node_modules/"
    assert "/CLAUDE.md" in lines and ".env" in lines


def test_is_idempotent(repo_root, tmp_path):
    tpl = repo_root / "templates" / "project"
    scaffold.apply_template(tpl, tmp_path, "demo")
    before = (tmp_path / ".gitignore").read_text()
    assert scaffold.apply_template(tpl, tmp_path, "demo") == []
    assert (tmp_path / ".gitignore").read_text() == before


def test_adds_claude_ignore_even_without_template_gitignore(tmp_path):
    tpl = tmp_path / "tpl"
    tpl.mkdir()
    dest = tmp_path / "dest"
    dest.mkdir()
    scaffold.apply_template(tpl, dest, "x")
    assert (dest / ".gitignore").read_text() == "/CLAUDE.md\n"
