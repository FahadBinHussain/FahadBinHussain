import generate_stack_section
from generate_stack_section import (
    README_MARKER_END,
    README_MARKER_START,
    build_stack_block,
    detect_tools_from_content,
    detect_tools_from_paths,
    fetch_repositories,
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


def test_fetch_repositories_uses_authenticated_listing(monkeypatch):
    calls = []

    def fake_fetch_json(url, headers, params=None):
        calls.append((url, params))
        return [
            {"fork": False, "owner": {"login": "FahadBinHussain"}, "name": "public-or-private"},
            {"fork": True, "owner": {"login": "FahadBinHussain"}, "name": "forked"},
            {"fork": False, "owner": {"login": "OtherUser"}, "name": "other-owner"},
        ]

    monkeypatch.setattr(generate_stack_section, "fetch_json", fake_fetch_json)
    repos = fetch_repositories("FahadBinHussain", {"Authorization": "Bearer token"})

    assert calls[0][0].endswith("/user/repos")
    assert calls[0][1]["visibility"] == "all"
    assert calls[0][1]["affiliation"] == "owner"
    assert [repo["name"] for repo in repos] == ["public-or-private"]


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


def test_detect_tools_from_paths_for_additional_ecosystems():
    paths = [
        "src-tauri/Cargo.toml",
        "tauri.conf.json",
        "go.mod",
        "pubspec.yaml",
        "main.tf",
        "Chart.yaml",
        "vercel.json",
    ]
    detected = detect_tools_from_paths(paths)
    assert {"Tauri", "Rust", "Go", "Dart", "Terraform", "Kubernetes", "Vercel"} <= detected


def test_detect_tools_from_content_for_additional_ecosystems():
    content = """
    dependencies:
      tauri: latest
      tailwindcss: latest
      fastapi: latest
      supabase: latest
      aws-sdk: latest
      playwright: latest
    """
    detected = detect_tools_from_content(content)
    assert {"Tauri", "Tailwind CSS", "FastAPI", "Supabase", "AWS", "Playwright"} <= detected


def test_detect_tools_from_paths_for_project_types():
    paths = [
        "notebooks/model.ipynb",
        "src/App.csproj",
        "MyApp.sln",
        "app/src/main/AndroidManifest.xml",
        "manifest.json",
        "_config.yml",
        ".eslintrc.json",
        ".prettierrc",
    ]
    detected = detect_tools_from_paths(paths)
    assert {"Jupyter", ".NET", "C#", "Android", "Chrome Extension", "Jekyll", "GitHub Pages"} <= detected
    assert {"ESLint", "Prettier"} <= detected


def test_detect_tools_from_content_for_python_and_android_libraries():
    content = """
    discord.py
    python-telegram-bot
    beautifulsoup4
    requests
    pandas
    numpy
    scikit-learn
    tensorflow
    torch
    androidx.compose
    com.android.application
    """
    detected = detect_tools_from_content(content)
    assert {"Discord.py", "Telegram Bot", "Beautiful Soup", "Requests"} <= detected
    assert {"Pandas", "NumPy", "scikit-learn", "TensorFlow", "PyTorch"} <= detected
    assert {"Android", "Jetpack Compose"} <= detected


def test_build_stack_block_contains_markers():
    block = build_stack_block(["JavaScript", "Python"], ["Docker", "Git"])
    assert README_MARKER_START in block
    assert README_MARKER_END in block
    assert "Primary Languages" in block
    assert "Primary Tools & Frameworks" in block
    assert "JavaScript" in block
    assert "Docker" in block


def test_build_stack_block_adds_collapsed_all_tools_view():
    tools = [
        "Docker",
        "Git",
        "React",
        "Next.js",
        "Node.js",
        "Vite",
        "Prisma",
        "Supabase",
        "Redis",
        "Firebase",
        "Vercel",
        "Tauri",
    ]
    block = build_stack_block(["JavaScript"], tools)
    assert "<details>" in block
    assert "Full auto-detected stack" in block
    assert "Tauri" in block


def test_build_stack_block_omits_collapsed_view_for_short_tool_list():
    block = build_stack_block(["JavaScript"], ["Docker", "Git"])
    assert "<details>" not in block


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


def test_detect_tools_from_paths_and_content_for_expanded_stack():
    paths = [
        "bun.lockb",
        "drizzle.config.ts",
        "components.json",
        "wxt.config.ts",
        "wrangler.toml",
        "turbo.json",
    ]
    detected_paths = detect_tools_from_paths(paths)
    assert {"Bun", "Drizzle ORM", "shadcn/ui", "WXT", "Cloudflare", "Turborepo"} <= detected_paths

    content = """
    dependencies:
      drizzle-orm: latest
      @neondatabase/serverless: latest
      @upstash/redis: latest
      @trpc/server: latest
      @radix-ui/react-dialog: latest
      lucide-react: latest
      framer-motion: latest
      three: latest
      zustand: latest
      zod: latest
      openai: latest
      @anthropic-ai/sdk: latest
      @google/genai: latest
    """
    detected_content = detect_tools_from_content(content)
    assert {
        "Drizzle ORM",
        "Neon",
        "Upstash",
        "tRPC",
        "Radix UI",
        "Lucide",
        "Framer Motion",
        "Three.js",
        "Zustand",
        "Zod",
        "OpenAI",
        "Anthropic",
        "Google Gemini",
    } <= detected_content


def test_detect_tools_for_mega_batch():
    paths = [
        "postcss.config.js",
        "webpack.config.js",
        "flake.nix",
        "Caddyfile",
        "capacitor.config.ts",
    ]
    detected_paths = detect_tools_from_paths(paths)
    assert {"PostCSS", "Webpack", "Nix / NixOS", "Caddy", "Capacitor"} <= detected_paths

    content = """
    dependencies:
      fastify: latest
      @clerk/nextjs: latest
      stripe: latest
      @sentry/nextjs: latest
      tailscale: latest
      posthog-js: latest
      meilisearch: latest
    """
    detected_content = detect_tools_from_content(content)
    assert {"Fastify", "Clerk", "Stripe", "Sentry", "Tailscale", "PostHog", "Meilisearch"} <= detected_content
