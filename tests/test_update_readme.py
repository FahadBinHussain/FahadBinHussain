import re
from update_readme import (
    PROJECTS_SECTION_END,
    PROJECTS_SECTION_START,
    replace_projects_block,
    build_new_projects_text,
    filter_existing_github_projects,
)


def test_replace_multiple_singular_lines():
    content = """Some intro text
- 🔭 Currently actively developing my [vubon-skills](https://github.com/FahadBinHussain/vubon-skills) project.
- 🔭 Currently actively developing my [vubon-skills](https://github.com/FahadBinHussain/vubon-skills) project.
- 🔭 Currently actively developing my [vubon-skills](https://github.com/FahadBinHussain/vubon-skills) project.
Other content
"""
    new_text = build_new_projects_text(["vubon-skills"])  # single project
    updated = replace_projects_block(content, new_text)
    assert updated.count("Currently actively developing my") == 1
    assert new_text in updated


def test_replace_mixed_plural_and_singular_lines():
    content = """Header
- 🔭 Currently actively developing my [Wall-You-Need-Next-Gen](https://github.com/FahadBinHussain/Wall-You-Need-Next-Gen) project.
- 🔭 Currently actively developing my [CSE391](https://github.com/FahadBinHussain/CSE391) project.
- 🔭 Currently actively developing my [DotProject](https://github.com/FahadBinHussain/DotProject) projects.
- 🔭 Currently actively developing my [Another](https://github.com/FahadBinHussain/Another) projects.
Footer
"""
    new_text = build_new_projects_text(["DotProject", "Another"])  # two projects
    updated = replace_projects_block(content, new_text)
    assert updated.count("Currently actively developing my") == 1
    assert new_text in updated


def test_append_when_no_line_found():
    content = """Intro
Some other info
Final line
"""
    new_text = build_new_projects_text(["vubon-skills"])  # single project
    updated = replace_projects_block(content, new_text)
    # should append a marked dynamic block at the end
    assert updated.strip().endswith(PROJECTS_SECTION_END)
    assert new_text in updated


def test_replace_across_multiple_blocks():
    content = """Header
- 🎓 I am pursuing a Bachelor of Science
- 🔭 Currently actively developing my [A](https://github.com/A) project.
Mid content
- 🔭 Currently actively developing my [B](https://github.com/B) project.
Footer
"""
    new_text = build_new_projects_text(["new-proj"])  # single project
    updated = replace_projects_block(content, new_text)
    # Exactly one line for the currently developing project
    assert updated.count("Currently actively developing my") == 1
    assert new_text in updated
    assert PROJECTS_SECTION_START in updated
    assert PROJECTS_SECTION_END in updated


def test_update_readme_writes_file(tmp_path):
    temp_file = tmp_path / "TEMP_README.md"
    content = """Intro
- 🎓 I am pursuing a Bachelor of Science in Computer Science and Engineering.
- 🔭 Currently actively developing my [vubon-skills](https://github.com/FahadBinHussain/vubon-skills) project.
- 🔭 Currently actively developing my [vubon-skills](https://github.com/FahadBinHussain/vubon-skills) project.
Other content
"""
    temp_file.write_text(content, encoding="utf-8")
    from update_readme import update_readme

    # Run update_readme to replace duplicates in the temporary file
    update_readme(["vubon-skills"], readme_path=str(temp_file))
    result = temp_file.read_text(encoding="utf-8")
    assert result.count("Currently actively developing my") == 1
    assert "vubon-skills" in result
    assert PROJECTS_SECTION_START in result


def test_build_new_projects_text_three_projects():
    from update_readme import build_new_projects_text
    projects = ["A", "B", "C"]
    new_text = build_new_projects_text(projects, max_projects=3)
    assert new_text.count("<a ") == 3  # three links
    assert new_text.endswith("projects.</p>")
    assert 'href="https://github.com/FahadBinHussain/A">A</a>' in new_text
    assert 'href="https://github.com/FahadBinHussain/B">B</a>' in new_text
    assert 'href="https://github.com/FahadBinHussain/C">C</a>' in new_text
    assert "[A](" not in new_text
    # Should be of form A, B & C projects.
    assert "," in new_text and " &amp; " in new_text


def test_replace_html_projects_line():
    content = """Header
<p>🔭 Currently actively developing my <a href="https://github.com/FahadBinHussain/Old">Old</a> project.</p>
Footer
"""
    new_text = build_new_projects_text(["new-proj"])
    updated = replace_projects_block(content, new_text)
    assert updated.count("Currently actively developing my") == 1
    assert new_text in updated
    assert PROJECTS_SECTION_START in updated


def test_projects_section_is_inserted_before_contributors():
    content = """Intro
<p>🔭 Currently actively developing my <a href="https://github.com/FahadBinHussain/Old">Old</a> project.</p>

## Contributors

Contributor content
"""
    new_text = build_new_projects_text(["new-proj"])
    updated = replace_projects_block(content, new_text)

    assert updated.count("Currently actively developing my") == 1
    assert updated.index("## Current Focus") < updated.index("## Contributors")
    assert new_text in updated


def test_filter_existing_github_projects_skips_non_repos():
    projects = ["scoopcryo", "how-many-mails-currently-on-this", "hi", "lore"]
    existing = {"scoopcryo", "lore"}

    filtered = filter_existing_github_projects(projects, repo_exists=existing.__contains__)

    assert filtered == ["scoopcryo", "lore"]


def test_filter_existing_github_projects_keeps_scanning_until_max():
    projects = ["thread-one", "scoopcryo", "thread-two", "lore", "thread-three", "imgvault"]
    existing = {"scoopcryo", "lore", "imgvault"}

    filtered = filter_existing_github_projects(projects, max_projects=3, repo_exists=existing.__contains__)

    assert filtered == ["scoopcryo", "lore", "imgvault"]
