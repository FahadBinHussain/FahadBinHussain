import os
import re
from collections import Counter
from typing import Iterable

import requests
from dotenv import load_dotenv

load_dotenv()

README_MARKER_START = "<!--START_SECTION:stack-->"
README_MARKER_END = "<!--END_SECTION:stack-->"
GITHUB_API_URL = "https://api.github.com"


BADGE_MAP = {
    "JavaScript": ("JavaScript", "javascript", "F7DF1E", "323330"),
    "TypeScript": ("TypeScript", "typescript", "white", "3178C6"),
    "Python": ("Python", "python", "ffdd54", "3670A0"),
    "Java": ("Java", "openjdk", "white", "ED8B00"),
    "HTML": ("HTML5", "html5", "white", "E34F26"),
    "CSS": ("CSS3", "css3", "white", "1572B6"),
    "Shell": ("Shell", "gnubash", "white", "121011"),
    "C++": ("C++", "cplusplus", "white", "00599C"),
    "C": ("C", "c", "white", "A8B9CC"),
    "Rust": ("Rust", "rust", "white", "000000"),
    "Go": ("Go", "go", "white", "00ADD8"),
    "Kotlin": ("Kotlin", "kotlin", "white", "7F52FF"),
    "Dart": ("Dart", "dart", "white", "0175C2"),
    "PHP": ("PHP", "php", "white", "777BB4"),
    "Ruby": ("Ruby", "ruby", "white", "CC342D"),
    "C#": ("C%23", "csharp", "white", "512BD4"),
    ".NET": (".NET", "dotnet", "white", "512BD4"),
    "Android": ("Android", "android", "white", "3DDC84"),
    "Jetpack Compose": ("Jetpack Compose", "jetpackcompose", "white", "4285F4"),
    "Jupyter": ("Jupyter", "jupyter", "white", "F37626"),
    "Cython": ("Cython", "python", "white", "3670A0"),
    "SQL": ("SQL", "postgresql", "white", "336791"),
    "Chrome Extension": ("Chrome Extension", "googlechrome", "white", "4285F4"),
    "Docker": ("Docker", "docker", "white", "2496ED"),
    "Flask": ("Flask", "flask", "white", "000000"),
    "Django": ("Django", "django", "white", "092E20"),
    "Node.js": ("Node.js", "node.js", "white", "339933"),
    "React": ("React", "react", "61DAFB", "20232A"),
    "Next.js": ("Next.js", "nextdotjs", "white", "000000"),
    "Vue": ("Vue", "vuedotjs", "white", "4FC08D"),
    "Svelte": ("Svelte", "svelte", "white", "FF3E00"),
    "Express": ("Express", "express", "white", "000000"),
    "Prisma": ("Prisma", "prisma", "white", "2D3748"),
    "Tauri": ("Tauri", "tauri", "white", "FFC131"),
    "Electron": ("Electron", "electron", "white", "47848F"),
    "Vite": ("Vite", "vite", "white", "646CFF"),
    "Tailwind CSS": ("Tailwind CSS", "tailwindcss", "white", "06B6D4"),
    "Bootstrap": ("Bootstrap", "bootstrap", "white", "7952B3"),
    "Redux": ("Redux", "redux", "white", "764ABC"),
    "FastAPI": ("FastAPI", "fastapi", "white", "009688"),
    "Jest": ("Jest", "jest", "white", "C21325"),
    "Vitest": ("Vitest", "vitest", "white", "6E9F18"),
    "ESLint": ("ESLint", "eslint", "white", "4B32C3"),
    "Prettier": ("Prettier", "prettier", "black", "F7B93E"),
    "Axios": ("Axios", "axios", "white", "5A29E4"),
    "Discord.py": ("Discord.py", "discord", "white", "5865F2"),
    "Discord.js": ("Discord.js", "discord", "white", "5865F2"),
    "Telegram Bot": ("Telegram Bot", "telegram", "white", "26A5E4"),
    "Beautiful Soup": ("Beautiful Soup", "python", "white", "3670A0"),
    "Requests": ("Requests", "python", "white", "3670A0"),
    "Pandas": ("Pandas", "pandas", "white", "150458"),
    "NumPy": ("NumPy", "numpy", "white", "013243"),
    "scikit-learn": ("scikit-learn", "scikitlearn", "white", "F7931E"),
    "TensorFlow": ("TensorFlow", "tensorflow", "white", "FF6F00"),
    "PyTorch": ("PyTorch", "pytorch", "white", "EE4C2C"),
    "MongoDB": ("MongoDB", "mongodb", "white", "47A248"),
    "PostgreSQL": ("PostgreSQL", "postgresql", "white", "4169E1"),
    "MySQL": ("MySQL", "mysql", "white", "4479A1"),
    "SQLite": ("SQLite", "sqlite", "white", "003B57"),
    "Redis": ("Redis", "redis", "white", "DC382D"),
    "Firebase": ("Firebase", "firebase", "black", "FFCA28"),
    "Supabase": ("Supabase", "supabase", "white", "3ECF8E"),
    "Terraform": ("Terraform", "terraform", "white", "844FBA"),
    "Kubernetes": ("Kubernetes", "kubernetes", "white", "326CE5"),
    "Nginx": ("Nginx", "nginx", "white", "009639"),
    "AWS": ("AWS", "amazonaws", "white", "232F3E"),
    "Selenium": ("Selenium", "selenium", "white", "43B02A"),
    "Puppeteer": ("Puppeteer", "puppeteer", "white", "40B5A4"),
    "Playwright": ("Playwright", "playwright", "white", "2EAD33"),
    "GitHub Actions": ("GitHub Actions", "githubactions", "white", "2088FF"),
    "Git": ("Git", "git", "white", "F05032"),
    "Linux": ("Linux", "linux", "white", "000000"),
    "PowerShell": ("PowerShell", "powershell", "white", "5391FE"),
    "Google Cloud": ("Google Cloud", "googlecloud", "white", "4285F4"),
    "Docker Compose": ("Docker Compose", "docker", "white", "2496ED"),
    "GitLab CI": ("GitLab CI", "gitlab", "white", "FC6D26"),
    "Vercel": ("Vercel", "vercel", "white", "000000"),
    "Netlify": ("Netlify", "netlify", "white", "00C7B7"),
    "GitHub Pages": ("GitHub Pages", "githubpages", "white", "222222"),
    "Jekyll": ("Jekyll", "jekyll", "white", "CC0000"),
    # Modern Frameworks, Runtimes & Fullstack
    "Bun": ("Bun", "bun", "white", "000000"),
    "Deno": ("Deno", "deno", "white", "000000"),
    "pnpm": ("pnpm", "pnpm", "white", "F69220"),
    "Turborepo": ("Turborepo", "turborepo", "white", "EF4444"),
    "SolidJS": ("SolidJS", "solid", "white", "2C4F7C"),
    "Astro": ("Astro", "astro", "white", "BC52EE"),
    "Remix": ("Remix", "remix", "white", "000000"),
    "Nuxt": ("Nuxt", "nuxt", "white", "00DC82"),
    "Hono": ("Hono", "hono", "white", "E36002"),
    "Angular": ("Angular", "angular", "white", "DD0031"),
    # Databases, ORMs & BaaS
    "Drizzle ORM": ("Drizzle ORM", "drizzle", "black", "C5F74F"),
    "tRPC": ("tRPC", "trpc", "white", "2596BE"),
    "GraphQL": ("GraphQL", "graphql", "white", "E10098"),
    "Neon": ("Neon", "neon", "black", "00E599"),
    "Upstash": ("Upstash", "upstash", "black", "00E9A3"),
    "MariaDB": ("MariaDB", "mariadb", "white", "003545"),
    # UI, Components, Styling & Animation
    "Radix UI": ("Radix UI", "radixui", "white", "161618"),
    "shadcn/ui": ("shadcn/ui", "shadcnui", "white", "000000"),
    "Lucide": ("Lucide", "lucide", "white", "F56565"),
    "Framer Motion": ("Framer Motion", "framer", "white", "0055FF"),
    "Three.js": ("Three.js", "threedotjs", "white", "000000"),
    "Zustand": ("Zustand", "react", "white", "443E38"),
    "TanStack Query": ("TanStack Query", "reactquery", "white", "FF4154"),
    "React Hook Form": ("React Hook Form", "reacthookform", "white", "EC5990"),
    "Zod": ("Zod", "zod", "white", "3E67B1"),
    "DaisyUI": ("DaisyUI", "daisyui", "black", "5AD8E6"),
    "GSAP": ("GSAP", "greensock", "black", "88CE02"),
    "Chakra UI": ("Chakra UI", "chakraui", "white", "319795"),
    "MUI": ("MUI", "mui", "white", "007FFF"),
    "Ant Design": ("Ant Design", "antdesign", "white", "0170FE"),
    "Styled Components": ("Styled Components", "styledcomponents", "white", "DB7093"),
    "NextAuth": ("NextAuth", "nextdotjs", "white", "000000"),
    "TipTap": ("TipTap", "javascript", "white", "000000"),
    "Sonner": ("Sonner", "react", "white", "000000"),
    "Recharts": ("Recharts", "chartdotjs", "white", "22B5BF"),
    # AI, LLM & Machine Learning
    "OpenAI": ("OpenAI", "openai", "white", "412991"),
    "Anthropic": ("Anthropic", "anthropic", "white", "191919"),
    "Google Gemini": ("Google Gemini", "googlegemini", "white", "8E75C2"),
    "LangChain": ("LangChain", "langchain", "white", "1C3C3C"),
    "Ollama": ("Ollama", "ollama", "white", "000000"),
    "Hugging Face": ("Hugging Face", "huggingface", "black", "FFD21E"),
    "OpenCV": ("OpenCV", "opencv", "white", "5C3EE8"),
    "PaddleOCR": ("PaddleOCR", "baidu", "white", "2932E1"),
    "Model Context Protocol": ("MCP", "anthropic", "white", "2D3748"),
    # Mobile, Desktop & Extensions
    "Flutter": ("Flutter", "flutter", "white", "02569B"),
    "React Native": ("React Native", "react", "black", "61DAFB"),
    "Tampermonkey": ("Tampermonkey", "tampermonkey", "white", "00485B"),
    "WXT": ("WXT", "googlechrome", "white", "4285F4"),
    # Cloud, DevOps & Testing
    "Cloudflare": ("Cloudflare", "cloudflare", "white", "F38020"),
    "Render": ("Render", "render", "white", "000000"),
    "Railway": ("Railway", "railway", "white", "0B0D0E"),
    "DigitalOcean": ("DigitalOcean", "digitalocean", "white", "0080FF"),
    "Biome": ("Biome", "biome", "white", "60A5FA"),
    "Cypress": ("Cypress", "cypress", "black", "69D3A7"),
    "Pytest": ("Pytest", "pytest", "white", "0A9EDC"),
    "Storybook": ("Storybook", "storybook", "white", "FF4785"),
    "Postman": ("Postman", "postman", "white", "FF6C37"),
    "Apache": ("Apache", "apache", "white", "D22128"),
    "RabbitMQ": ("RabbitMQ", "rabbitmq", "white", "FF6600"),
    "Apache Kafka": ("Apache Kafka", "apachekafka", "white", "231F20"),
    "Elasticsearch": ("Elasticsearch", "elasticsearch", "white", "005571"),
    # Languages
    "Swift": ("Swift", "swift", "white", "F05138"),
    "Lua": ("Lua", "lua", "white", "000080"),
    "Elixir": ("Elixir", "elixir", "white", "4B275F"),
    "Scala": ("Scala", "scala", "white", "DC322F"),
    "Perl": ("Perl", "perl", "white", "39457E"),
    "Haskell": ("Haskell", "haskell", "white", "5D4F85"),
    "R": ("R", "r", "white", "276DC3"),
    "Julia": ("Julia", "julia", "white", "9558B2"),
    "Solidity": ("Solidity", "solidity", "white", "363636"),
    "Assembly": ("Assembly", "assemblyscript", "white", "007ACC"),
    # Build, Bundlers & Tooling
    "PostCSS": ("PostCSS", "postcss", "white", "DD3A0A"),
    "esbuild": ("esbuild", "esbuild", "black", "FFCF00"),
    "Rollup": ("Rollup", "rollupdotjs", "white", "EC4A3F"),
    "Webpack": ("Webpack", "webpack", "black", "8DD6F7"),
    "Babel": ("Babel", "babel", "black", "F9DC3E"),
    "Sass": ("Sass", "sass", "white", "CC6699"),
    "Less": ("Less", "less", "white", "1D365D"),
    "Oxlint": ("Oxlint", "oxc", "white", "F472B6"),
    "Knip": ("Knip", "knip", "black", "E58516"),
    "Husky": ("Husky", "git", "white", "4A4A4A"),
    # Editors, Surfaces & UI Primitives
    "Monaco Editor": ("Monaco Editor", "visualstudiocode", "white", "007ACC"),
    "Xterm.js": ("Xterm.js", "gnometerminal", "white", "4E9A06"),
    "Quill": ("Quill", "feather", "white", "333333"),
    "Markdown": ("Markdown", "markdown", "white", "000000"),
    "Prism.js": ("Prism.js", "prism", "white", "000000"),
    "Socket.io": ("Socket.io", "socketdotio", "white", "010101"),
    "Lottie": ("Lottie", "lottie", "black", "00DDB3"),
    # Android, Systems & Embedded
    "LSPosed": ("LSPosed", "android", "white", "3DDC84"),
    "Magisk": ("Magisk", "android", "white", "00BCD4"),
    "WebAssembly": ("WebAssembly", "webassembly", "white", "654FF0"),
    "Capacitor": ("Capacitor", "capacitor", "white", "119EFF"),
    "Ionic": ("Ionic", "ionic", "white", "3880FF"),
    "Qt": ("Qt", "qt", "black", "41CD52"),
    "GNOME / GTK": ("GNOME / GTK", "gnome", "white", "4A90D9"),
    "Arduino": ("Arduino", "arduino", "white", "00979D"),
    "Raspberry Pi": ("Raspberry Pi", "raspberrypi", "white", "A22846"),
    # Backend Frameworks & Protocols
    "NestJS": ("NestJS", "nestjs", "white", "E0234E"),
    "Fastify": ("Fastify", "fastify", "white", "000000"),
    "Koa": ("Koa", "koa", "white", "33333D"),
    "Spring Boot": ("Spring Boot", "springboot", "white", "6DB33F"),
    "Laravel": ("Laravel", "laravel", "white", "FF2D20"),
    "Ruby on Rails": ("Ruby on Rails", "rubyonrails", "white", "D30001"),
    "Phoenix": ("Phoenix", "phoenixframework", "white", "FD4F00"),
    "ASP.NET Core": ("ASP.NET Core", "dotnet", "white", "512BD4"),
    "gRPC": ("gRPC", "grpc", "white", "244C5A"),
    "Swagger": ("Swagger", "swagger", "black", "85EA2D"),
    "Celery": ("Celery", "celery", "white", "37814A"),
    # Databases, Search & Advanced ORMs
    "Turso": ("Turso", "turso", "black", "4FF8D2"),
    "DuckDB": ("DuckDB", "duckdb", "black", "FFF000"),
    "ClickHouse": ("ClickHouse", "clickhouse", "black", "FFCC01"),
    "SurrealDB": ("SurrealDB", "surrealdb", "white", "FF00A0"),
    "PlanetScale": ("PlanetScale", "planetscale", "white", "000000"),
    "Meilisearch": ("Meilisearch", "meilisearch", "white", "FF5CAA"),
    "Algolia": ("Algolia", "algolia", "white", "003DFF"),
    "Typesense": ("Typesense", "typesense", "white", "C82B57"),
    "Neo4j": ("Neo4j", "neo4j", "white", "008CC1"),
    "InfluxDB": ("InfluxDB", "influxdb", "white", "22ADF6"),
    "SQLAlchemy": ("SQLAlchemy", "sqlalchemy", "white", "D71F00"),
    "TypeORM": ("TypeORM", "typeorm", "white", "FE0803"),
    "Sequelize": ("Sequelize", "sequelize", "white", "52B0E7"),
    # AI, ML, Data & Vector
    "PyTorch Lightning": ("PyTorch Lightning", "lightning", "white", "792EE5"),
    "Gradio": ("Gradio", "gradio", "white", "FD5545"),
    "Streamlit": ("Streamlit", "streamlit", "white", "FF4B4B"),
    "Pinecone": ("Pinecone", "pinecone", "white", "000000"),
    "Qdrant": ("Qdrant", "qdrant", "white", "DC244C"),
    "Weaviate": ("Weaviate", "weaviate", "white", "00D1B2"),
    "Chroma": ("Chroma", "chroma", "white", "FF6B35"),
    "Milvus": ("Milvus", "milvus", "white", "00A1EA"),
    "Polars": ("Polars", "polars", "white", "CD792C"),
    "SciPy": ("SciPy", "scipy", "white", "8CAAE6"),
    "Matplotlib": ("Matplotlib", "matplotlib", "white", "11557C"),
    "Plotly": ("Plotly", "plotly", "white", "3F4F75"),
    "Weights & Biases": ("Weights & Biases", "weightsandbiases", "black", "FFBE00"),
    "MLflow": ("MLflow", "mlflow", "white", "0194E2"),
    # Auth, Payments & Observability
    "Clerk": ("Clerk", "clerk", "white", "6C47FF"),
    "Kinde": ("Kinde", "kinde", "white", "000000"),
    "Auth0": ("Auth0", "auth0", "white", "EB5424"),
    "Lucia Auth": ("Lucia Auth", "lucia", "white", "5F57FF"),
    "Stripe": ("Stripe", "stripe", "white", "008CDD"),
    "Lemon Squeezy": ("Lemon Squeezy", "lemonsqueezy", "white", "7047EB"),
    "PayPal": ("PayPal", "paypal", "white", "00457C"),
    "Sentry": ("Sentry", "sentry", "white", "362D59"),
    "PostHog": ("PostHog", "posthog", "white", "000000"),
    "Umami": ("Umami", "umami", "white", "000000"),
    "Plausible": ("Plausible", "plausibleanalytics", "white", "5850EC"),
    "Datadog": ("Datadog", "datadog", "white", "632CA6"),
    "Prometheus": ("Prometheus", "prometheus", "white", "E6522C"),
    "Grafana": ("Grafana", "grafana", "white", "F46800"),
    # Infra, Self-Hosting & Networking
    "Tailscale": ("Tailscale", "tailscale", "white", "000000"),
    "Proxmox": ("Proxmox", "proxmox", "white", "E57000"),
    "Nix / NixOS": ("Nix / NixOS", "nixos", "white", "5277C3"),
    "Ansible": ("Ansible", "ansible", "white", "EE0000"),
    "Pulumi": ("Pulumi", "pulumi", "white", "8A3391"),
    "Vagrant": ("Vagrant", "vagrant", "white", "1563FF"),
    "Helm": ("Helm", "helm", "white", "0F1689"),
    "ArgoCD": ("ArgoCD", "argo", "white", "EF7B4D"),
    "Traefik": ("Traefik", "traefikproxy", "white", "24A1C1"),
    "Caddy": ("Caddy", "caddy", "white", "1F88C0"),
    "Fly.io": ("Fly.io", "flydotio", "white", "24185B"),
    "Hetzner": ("Hetzner", "hetzner", "white", "D50C2D"),

}


FILE_HINTS = {
    "package.json": {"Node.js"},
    "package-lock.json": {"Node.js"},
    "pnpm-lock.yaml": {"Node.js"},
    "yarn.lock": {"Node.js"},
    "requirements.txt": {"Python"},
    "pyproject.toml": {"Python"},
    "Pipfile": {"Python"},
    "ipynb": {"Jupyter", "Python"},
    "Cargo.toml": {"Rust"},
    "Cargo.lock": {"Rust"},
    "go.mod": {"Go"},
    "go.sum": {"Go"},
    "pom.xml": {"Java"},
    "build.gradle": {"Java"},
    "build.gradle.kts": {"Java"},
    "settings.gradle.kts": {"Java", "Kotlin"},
    "settings.gradle": {"Java", "Kotlin"},
    "pubspec.yaml": {"Dart"},
    "composer.json": {"PHP"},
    "Gemfile": {"Ruby"},
    "manifest.json": {"Chrome Extension"},
    "AndroidManifest.xml": {"Android"},
    "gradle.properties": {"Android"},
    "app/build.gradle": {"Android", "Java"},
    "app/build.gradle.kts": {"Android", "Kotlin"},
    "Directory.Build.props": {".NET"},
    "Directory.Build.targets": {".NET"},
    ".csproj": {".NET", "C#"},
    ".sln": {".NET", "C#"},
    "Dockerfile": {"Docker"},
    "docker-compose.yml": {"Docker Compose", "Docker"},
    "docker-compose.yaml": {"Docker Compose", "Docker"},
    ".github/workflows": {"GitHub Actions"},
    ".gitlab-ci.yml": {"GitLab CI"},
    "next.config.js": {"Next.js", "React", "Node.js"},
    "next.config.mjs": {"Next.js", "React", "Node.js"},
    "next.config.ts": {"Next.js", "React", "Node.js"},
    "vite.config.js": {"Node.js", "Vite"},
    "vite.config.ts": {"Node.js", "Vite"},
    "vite.config.mjs": {"Node.js", "Vite"},
    "tailwind.config.js": {"Tailwind CSS"},
    "tailwind.config.ts": {"Tailwind CSS"},
    "tailwind.config.cjs": {"Tailwind CSS"},
    "jest.config.js": {"Jest", "Node.js"},
    "jest.config.ts": {"Jest", "Node.js"},
    "vitest.config.js": {"Vitest", "Vite", "Node.js"},
    "vitest.config.ts": {"Vitest", "Vite", "Node.js"},
    ".eslintrc": {"ESLint"},
    ".eslintrc.json": {"ESLint"},
    ".prettierrc": {"Prettier"},
    ".prettierrc.json": {"Prettier"},
    "manage.py": {"Django", "Python"},
    "wsgi.py": {"Django", "Python"},
    "flask_app.py": {"Flask", "Python"},
    "main.tf": {"Terraform"},
    "terraform.tf": {"Terraform"},
    "terraform.lock.hcl": {"Terraform"},
    "Chart.yaml": {"Kubernetes"},
    "vercel.json": {"Vercel"},
    "netlify.toml": {"Netlify"},
    "_config.yml": {"Jekyll", "GitHub Pages"},
    ".nojekyll": {"GitHub Pages"},
    "nginx.conf": {"Nginx"},
    "tauri.conf.json": {"Tauri"},
    "src-tauri/Cargo.toml": {"Tauri", "Rust"},
    "bun.lockb": {"Bun"},
    "bunfig.toml": {"Bun"},
    "deno.json": {"Deno"},
    "deno.lock": {"Deno"},
    "turbo.json": {"Turborepo"},
    "svelte.config.js": {"Svelte", "Node.js"},
    "astro.config.mjs": {"Astro", "Node.js"},
    "astro.config.ts": {"Astro", "Node.js"},
    "remix.config.js": {"Remix", "Node.js"},
    "nuxt.config.ts": {"Nuxt", "Node.js"},
    "drizzle.config.ts": {"Drizzle ORM"},
    "drizzle.config.js": {"Drizzle ORM"},
    "schema.prisma": {"Prisma"},
    "components.json": {"shadcn/ui"},
    "wxt.config.ts": {"WXT", "Chrome Extension"},
    "wrangler.toml": {"Cloudflare"},
    "biome.json": {"Biome"},
    "render.yaml": {"Render"},
    "cypress.config.ts": {"Cypress"},
    "cypress.config.js": {"Cypress"},
    "pytest.ini": {"Pytest", "Python"},
    ".storybook": {"Storybook"},
    "CMakeLists.txt": {"C++"},
    ".user.js": {"Tampermonkey", "JavaScript"},
    "Caddyfile": {"Caddy"},
    "flake.nix": {"Nix / NixOS"},
    "default.nix": {"Nix / NixOS"},
    "Vagrantfile": {"Vagrant"},
    "ansible.cfg": {"Ansible"},
    "playbook.yml": {"Ansible"},
    "Pulumi.yaml": {"Pulumi"},
    "postcss.config.js": {"PostCSS"},
    "postcss.config.mjs": {"PostCSS"},
    "postcss.config.ts": {"PostCSS"},
    "webpack.config.js": {"Webpack"},
    "rollup.config.js": {"Rollup"},
    ".babelrc": {"Babel"},
    "babel.config.json": {"Babel"},
    "knip.json": {"Knip"},
    "knip.ts": {"Knip"},
    ".husky": {"Husky"},
    "capacitor.config.ts": {"Capacitor"},
    "capacitor.config.json": {"Capacitor"},
    "ionic.config.json": {"Ionic"},
    "swagger.json": {"Swagger"},
    "swagger.yaml": {"Swagger"},
    "openapi.json": {"Swagger"},
    "openapi.yaml": {"Swagger"},
    "fly.toml": {"Fly.io"},
    "streamlit_app.py": {"Streamlit", "Python"},

}


CONTENT_HINTS = {
    "react": {"React"},
    "next": {"Next.js", "React"},
    "tauri": {"Tauri"},
    "electron": {"Electron"},
    "vite": {"Vite"},
    "tailwindcss": {"Tailwind CSS"},
    "bootstrap": {"Bootstrap"},
    "jest": {"Jest"},
    "vitest": {"Vitest", "Vite"},
    "eslint": {"ESLint"},
    "prettier": {"Prettier"},
    "axios": {"Axios"},
    "@reduxjs/toolkit": {"Redux"},
    "redux": {"Redux"},
    "express": {"Express"},
    "prisma": {"Prisma"},
    "fastapi": {"FastAPI"},
    "flask": {"Flask"},
    "django": {"Django"},
    "discord.py": {"Discord.py"},
    "discord.js": {"Discord.js"},
    "python-telegram-bot": {"Telegram Bot"},
    "beautifulsoup4": {"Beautiful Soup"},
    "bs4": {"Beautiful Soup"},
    "requests": {"Requests"},
    "pandas": {"Pandas"},
    "numpy": {"NumPy"},
    "scikit-learn": {"scikit-learn"},
    "sklearn": {"scikit-learn"},
    "tensorflow": {"TensorFlow"},
    "torch": {"PyTorch"},
    "pytorch": {"PyTorch"},
    "mongoose": {"MongoDB"},
    "mongodb": {"MongoDB"},
    "postgres": {"PostgreSQL"},
    "mysql": {"MySQL"},
    "sqlite": {"SQLite"},
    "redis": {"Redis"},
    "firebase": {"Firebase"},
    "supabase": {"Supabase"},
    "terraform": {"Terraform"},
    "kubernetes": {"Kubernetes"},
    "helm": {"Kubernetes"},
    "nginx": {"Nginx"},
    "aws-sdk": {"AWS"},
    "boto3": {"AWS"},
    "amazonaws": {"AWS"},
    "selenium": {"Selenium"},
    "puppeteer": {"Puppeteer"},
    "playwright": {"Playwright"},
    "google-cloud": {"Google Cloud"},
    "@google-cloud": {"Google Cloud"},
    "vercel": {"Vercel"},
    "netlify": {"Netlify"},
    "github-pages": {"GitHub Pages"},
    "jekyll": {"Jekyll"},
    "androidx.compose": {"Jetpack Compose", "Android"},
    "jetpack compose": {"Jetpack Compose", "Android"},
    "com.android.application": {"Android"},
    "microsoft.net.sdk": {".NET", "C#"},
    "targetframework": {".NET", "C#"},
    "drizzle-orm": {"Drizzle ORM"},
    "drizzle-kit": {"Drizzle ORM"},
    "@neondatabase/serverless": {"Neon"},
    "neon": {"Neon"},
    "@upstash/redis": {"Upstash"},
    "@upstash/ratelimit": {"Upstash"},
    "upstash": {"Upstash"},
    "@trpc/": {"tRPC"},
    "trpc": {"tRPC"},
    "graphql": {"GraphQL"},
    "@radix-ui/": {"Radix UI"},
    "shadcn": {"shadcn/ui"},
    "lucide": {"Lucide"},
    "framer-motion": {"Framer Motion"},
    "motion": {"Framer Motion"},
    "three": {"Three.js"},
    "@react-three/": {"Three.js"},
    "zustand": {"Zustand"},
    "@tanstack/react-query": {"TanStack Query"},
    "react-query": {"TanStack Query"},
    "react-hook-form": {"React Hook Form"},
    "zod": {"Zod"},
    "daisyui": {"DaisyUI"},
    "gsap": {"GSAP"},
    "@chakra-ui/": {"Chakra UI"},
    "@mui/": {"MUI"},
    "antd": {"Ant Design"},
    "styled-components": {"Styled Components"},
    "openai": {"OpenAI"},
    "anthropic": {"Anthropic"},
    "@anthropic-ai/sdk": {"Anthropic"},
    "google-generativeai": {"Google Gemini"},
    "@google/genai": {"Google Gemini"},
    "langchain": {"LangChain"},
    "ollama": {"Ollama"},
    "huggingface": {"Hugging Face"},
    "@modelcontextprotocol/sdk": {"Model Context Protocol"},
    "opencv": {"OpenCV"},
    "cv2": {"OpenCV"},
    "paddleocr": {"PaddleOCR"},
    "flutter": {"Flutter"},
    "react-native": {"React Native"},
    "tampermonkey": {"Tampermonkey"},
    "userscript": {"Tampermonkey"},
    "cloudflare": {"Cloudflare"},
    "wrangler": {"Cloudflare"},
    "render": {"Render"},
    "railway": {"Railway"},
    "digitalocean": {"DigitalOcean"},
    "biome": {"Biome"},
    "cypress": {"Cypress"},
    "pytest": {"Pytest"},
    "storybook": {"Storybook"},
    "postman": {"Postman"},
    "apache": {"Apache"},
    "rabbitmq": {"RabbitMQ"},
    "kafka": {"Apache Kafka"},
    "elasticsearch": {"Elasticsearch"},
    "hono": {"Hono"},
    "bun": {"Bun"},
    "deno": {"Deno"},
    "pnpm": {"pnpm"},
    "turbo": {"Turborepo"},
    "svelte": {"Svelte"},
    "solid-js": {"SolidJS"},
    "astro": {"Astro"},
    "remix": {"Remix"},
    "nuxt": {"Nuxt"},
    "mariadb": {"MariaDB"},
    "next-auth": {"NextAuth"},
    "@auth/": {"NextAuth"},
    "tiptap": {"TipTap"},
    "recharts": {"Recharts"},
    "sonner": {"Sonner"},
    "wxt": {"WXT"},
    "postcss": {"PostCSS"},
    "esbuild": {"esbuild"},
    "rollup": {"Rollup"},
    "webpack": {"Webpack"},
    "@babel/": {"Babel"},
    "sass": {"Sass"},
    "less": {"Less"},
    "oxlint": {"Oxlint"},
    "knip": {"Knip"},
    "husky": {"Husky"},
    "monaco-editor": {"Monaco Editor"},
    "@xterm/": {"Xterm.js"},
    "xterm": {"Xterm.js"},
    "quill": {"Quill"},
    "marked": {"Markdown"},
    "remark": {"Markdown"},
    "prismjs": {"Prism.js"},
    "socket.io": {"Socket.io"},
    "lottie": {"Lottie"},
    "@capacitor/": {"Capacitor"},
    "@ionic/": {"Ionic"},
    "nestjs": {"NestJS"},
    "@nestjs/": {"NestJS"},
    "fastify": {"Fastify"},
    "koa": {"Koa"},
    "spring-boot": {"Spring Boot"},
    "laravel": {"Laravel"},
    "rails": {"Ruby on Rails"},
    "phoenix": {"Phoenix"},
    "grpc": {"gRPC"},
    "swagger": {"Swagger"},
    "celery": {"Celery"},
    "@libsql/": {"Turso"},
    "turso": {"Turso"},
    "duckdb": {"DuckDB"},
    "clickhouse": {"ClickHouse"},
    "surrealdb": {"SurrealDB"},
    "@planetscale/": {"PlanetScale"},
    "meilisearch": {"Meilisearch"},
    "algoliasearch": {"Algolia"},
    "typesense": {"Typesense"},
    "neo4j": {"Neo4j"},
    "influxdb": {"InfluxDB"},
    "sqlalchemy": {"SQLAlchemy"},
    "typeorm": {"TypeORM"},
    "sequelize": {"Sequelize"},
    "pytorch-lightning": {"PyTorch Lightning"},
    "gradio": {"Gradio"},
    "streamlit": {"Streamlit"},
    "pinecone": {"Pinecone"},
    "qdrant": {"Qdrant"},
    "weaviate": {"Weaviate"},
    "chromadb": {"Chroma"},
    "milvus": {"Milvus"},
    "polars": {"Polars"},
    "scipy": {"SciPy"},
    "matplotlib": {"Matplotlib"},
    "plotly": {"Plotly"},
    "wandb": {"Weights & Biases"},
    "mlflow": {"MLflow"},
    "@clerk/": {"Clerk"},
    "clerk": {"Clerk"},
    "@kinde-oss/": {"Kinde"},
    "auth0": {"Auth0"},
    "lucia": {"Lucia Auth"},
    "stripe": {"Stripe"},
    "lemonsqueezy": {"Lemon Squeezy"},
    "paypal": {"PayPal"},
    "@sentry/": {"Sentry"},
    "sentry": {"Sentry"},
    "posthog": {"PostHog"},
    "umami": {"Umami"},
    "plausible": {"Plausible"},
    "datadog": {"Datadog"},
    "prometheus": {"Prometheus"},
    "grafana": {"Grafana"},
    "tailscale": {"Tailscale"},
    "ansible": {"Ansible"},
    "pulumi": {"Pulumi"},
    "helm": {"Helm"},
    "traefik": {"Traefik"},
    "caddy": {"Caddy"},
    "lsposed": {"LSPosed"},
    "xposed": {"LSPosed"},
    "magisk": {"Magisk"},

}


def build_headers() -> dict[str, str]:
    token = (
        os.getenv("GITHUB_TOKEN")
        or os.getenv("PAT_1")
        or os.getenv("GITHUB_TOKEN1")
        or os.getenv("METRICS_TOKEN")
    )
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def has_auth(headers: dict[str, str]) -> bool:
    return "Authorization" in headers


def fetch_json(url: str, headers: dict[str, str], params: dict | None = None):
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_repositories(username: str, headers: dict[str, str]) -> list[dict]:
    repos: list[dict] = []
    page = 1
    per_page = 100
    repo_url = f"{GITHUB_API_URL}/user/repos" if has_auth(headers) else f"{GITHUB_API_URL}/users/{username}/repos"

    while True:
        params = {"per_page": per_page, "page": page, "sort": "updated", "type": "owner"}
        if has_auth(headers):
            params = {
                "per_page": per_page,
                "page": page,
                "sort": "updated",
                "visibility": "all",
                "affiliation": "owner",
            }
        batch = fetch_json(
            repo_url,
            headers,
            params=params,
        )
        if not batch:
            break
        repos.extend(
            repo
            for repo in batch
            if not repo.get("fork") and repo.get("owner", {}).get("login", "").lower() == username.lower()
        )
        if len(batch) < per_page:
            break
        page += 1

    return repos


def fetch_languages(repo: dict, headers: dict[str, str]) -> Counter:
    data = fetch_json(repo["languages_url"], headers)
    return Counter(data)


def fetch_repo_tree(repo: dict, headers: dict[str, str]) -> list[str]:
    branch = repo.get("default_branch", "main")
    tree = fetch_json(
        f"{GITHUB_API_URL}/repos/{repo['full_name']}/git/trees/{branch}",
        headers,
        params={"recursive": "1"},
    )
    return [item["path"] for item in tree.get("tree", []) if item.get("type") == "blob"]


def fetch_file_content(repo: dict, headers: dict[str, str], path: str) -> str:
    data = fetch_json(f"{GITHUB_API_URL}/repos/{repo['full_name']}/contents/{path}", headers)
    if data.get("encoding") != "base64" or "content" not in data:
        return ""
    import base64

    return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")


def detect_tools_from_paths(paths: Iterable[str]) -> set[str]:
    detected: set[str] = set()
    path_set = set(paths)
    for hint_path, tools in FILE_HINTS.items():
        if (
            hint_path in path_set
            or any(path.startswith(f"{hint_path}/") for path in path_set)
            or any(path.endswith(f"/{hint_path}") for path in path_set)
            or any(path.endswith(hint_path) for path in path_set if hint_path.startswith("."))
            or any(path.endswith(f".{hint_path}") for path in path_set if "." not in hint_path and "/" not in hint_path)
        ):
            detected.update(tools)
    return detected


def detect_tools_from_content(content: str) -> set[str]:
    detected: set[str] = set()
    lowered = content.lower()
    for needle, tools in CONTENT_HINTS.items():
        if needle in lowered:
            detected.update(tools)
    return detected


def normalize_language_name(name: str) -> str | None:
    mapping = {
        "Jupyter Notebook": "Python",
        "Vue": "Vue",
        "HTML": "HTML",
        "CSS": "CSS",
        "JavaScript": "JavaScript",
        "TypeScript": "TypeScript",
        "Python": "Python",
        "Java": "Java",
        "Kotlin": "Kotlin",
        "Rust": "Rust",
        "Go": "Go",
        "Dart": "Dart",
        "PHP": "PHP",
        "Ruby": "Ruby",
        "C#": "C#",
        "Cython": "Cython",
        "PLpgSQL": "SQL",
        "Shell": "Shell",
        "C++": "C++",
                "C": "C",
        "Swift": "Swift",
        "Lua": "Lua",
        "Elixir": "Elixir",
        "Scala": "Scala",
        "Perl": "Perl",
        "Haskell": "Haskell",
        "R": "R",
        "Julia": "Julia",
        "Solidity": "Solidity",
        "Assembly": "Assembly",
        "MIPS": "Assembly",
        "Batchfile": "Shell",
        "PowerShell": "PowerShell",
    }
    return mapping.get(name)


def gather_stack(username: str) -> tuple[list[str], list[str]]:
    headers = build_headers()
    repos = fetch_repositories(username, headers)
    print(f"Scanning {len(repos)} non-fork repositories for {username}")
    language_counts: Counter = Counter()
    tool_counts: Counter = Counter()

    for index, repo in enumerate(repos, start=1):
        repo_name = repo["full_name"]
        print(f"[{index}/{len(repos)}] Scanning {repo_name}")

        repo_languages = fetch_languages(repo, headers)
        language_counts.update(repo_languages)
        if repo_languages:
            top_languages = ", ".join(
                language for language, _ in repo_languages.most_common(5)
            )
            print(f"  Languages: {top_languages}")
        else:
            print("  Languages: none reported by GitHub")

        try:
            paths = fetch_repo_tree(repo, headers)
            print(f"  Indexed {len(paths)} files")
        except requests.RequestException:
            paths = []
            print("  Could not fetch repository tree")

        detected_tools = detect_tools_from_paths(paths)

        for candidate in (
            "package.json",
            "requirements.txt",
            "pyproject.toml",
            "Pipfile",
            "pom.xml",
            "Cargo.toml",
            "go.mod",
            "pubspec.yaml",
            "composer.json",
            "Gemfile",
            "manifest.json",
            "AndroidManifest.xml",
            "app/build.gradle",
            "app/build.gradle.kts",
            "Directory.Build.props",
            "vercel.json",
            "netlify.toml",
            "tauri.conf.json",
            "_config.yml",
        ):
            if candidate in paths:
                try:
                    print(f"  Inspecting {candidate}")
                    detected_tools.update(detect_tools_from_content(fetch_file_content(repo, headers, candidate)))
                except requests.RequestException:
                    print(f"  Failed to inspect {candidate}")
                    continue

        for tool in detected_tools:
            tool_counts[tool] += 1

        if detected_tools:
            print(f"  Tools: {', '.join(sorted(detected_tools))}")
        else:
            print("  Tools: none detected")

    languages = [
        name
        for name, _ in language_counts.most_common()
        if normalize_language_name(name) in BADGE_MAP
    ]
    normalized_languages = []
    seen_languages = set()
    for language in languages:
        normalized = normalize_language_name(language)
        if normalized and normalized not in seen_languages:
            normalized_languages.append(normalized)
            seen_languages.add(normalized)

    tools = [name for name, _ in tool_counts.most_common() if name in BADGE_MAP and name not in seen_languages]
    print(f"Final languages: {', '.join(normalized_languages[:8]) if normalized_languages else 'none'}")
    print(f"Final tools: {', '.join(tools) if tools else 'none'}")
    return normalized_languages[:8], tools


def badge_markdown(name: str) -> str:
    label, logo, logo_color, color = BADGE_MAP[name]
    return (
        f"![{label}](https://img.shields.io/badge/{label.replace(' ', '%20')}-{color}"
        f"?style=for-the-badge&logo={logo}&logoColor={logo_color})"
    )


def build_stack_block(languages: list[str], tools: list[str], featured_tool_count: int = 11) -> str:
    parts = ["", README_MARKER_START, ""]
    featured_tools = tools[:featured_tool_count]
    remaining_tools = tools[featured_tool_count:]

    if languages:
        parts.append("**Primary Languages**")
        parts.append("")
        parts.append(" ".join(badge_markdown(language) for language in languages))
        parts.append("")
    if featured_tools:
        parts.append("**Primary Tools & Frameworks**")
        parts.append("")
        parts.append(" ".join(badge_markdown(tool) for tool in featured_tools))
        parts.append("")
    if remaining_tools:
        parts.append("<details>")
        parts.append("  <summary><b>Full auto-detected stack</b></summary>")
        parts.append("")
        parts.append(" ".join(badge_markdown(tool) for tool in tools))
        parts.append("")
        parts.append("</details>")
        parts.append("")
    parts.append(README_MARKER_END)
    return "\n".join(parts)


def replace_stack_block(readme_content: str, new_block: str) -> str:
    pattern = re.compile(
        rf"{re.escape(README_MARKER_START)}.*?{re.escape(README_MARKER_END)}",
        re.DOTALL,
    )
    if pattern.search(readme_content):
        return pattern.sub(new_block.strip(), readme_content)
    return readme_content


def update_readme_stack(readme_path: str = "README.md", username: str | None = None) -> None:
    username = username or os.getenv("GITHUB_USERNAME") or "FahadBinHussain"
    languages, tools = gather_stack(username)
    new_block = build_stack_block(languages, tools)

    with open(readme_path, "r", encoding="utf-8") as file:
        readme_content = file.read()

    updated_content = replace_stack_block(readme_content, new_block)

    with open(readme_path, "w", encoding="utf-8") as file:
        file.write(updated_content)
    print(f"Updated {readme_path} stack section")


if __name__ == "__main__":
    update_readme_stack()
