from generate_stack_section import (
    README_MARKER_END,
    README_MARKER_START,
    build_stack_block,
    detect_tools_from_content,
    detect_tools_from_paths,
    replace_stack_block,
)


def test_detect_tools_from_paths():
    paths = [
        "package.json",
        "next.config.js",
        ".github/workflows/deploy.yml",
        "Dockerfile",
        "requirements.txt",
    ]
    detected = detect_tools_from_paths(paths)
    assert {"Node.js", "Next.js", "React", "GitHub Actions", "Docker", "Python"} <= detected


def test_detect_tools_from_content():
    content = """
    {
      "dependencies": {
        "react": "^18.0.0",
        "next": "^14.0.0",
        "prisma": "^5.0.0",
        "mongoose": "^8.0.0"
      }
    }
    """
    detected = detect_tools_from_content(content)
    assert {"React", "Next.js", "Prisma", "MongoDB"} <= detected


def test_build_stack_block_contains_markers():
    block = build_stack_block(["JavaScript", "Python"], ["Docker", "Git"])
    assert README_MARKER_START in block
    assert README_MARKER_END in block
    assert "JavaScript" in block
    assert "Docker" in block


def test_replace_stack_block_updates_only_marker_content():
    original = f"""Header
{README_MARKER_START}
old
{README_MARKER_END}
Footer
"""
    replacement = build_stack_block(["JavaScript"], ["Docker"])
    updated = replace_stack_block(original, replacement)
    assert "old" not in updated
    assert updated.startswith("Header")
    assert updated.strip().endswith("Footer")
