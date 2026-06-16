"""
Generalized GitHub HDL / Code Extractor
=======================================

Extracts HDL (and adjacent) projects from *any* GitHub repository or
organization/user account into a structured, queryable report for use as
input to a multi-modal hardware-design LLM.

This is the generalized evolution of the original OpenCores/FreeCores
extractor. The original behaviour is preserved as two of several modes:

    * ``branches`` mode reproduces the klyone/opencores-ip case
      (each project lives on its own git branch).
    * ``org`` mode reproduces the freecores case
      (each repository in an organization is a project).

Extraction modes
----------------
    repo      Clone one repository and extract it as a single project.
    org       Discover every public repo under an org/user, extract each.
    subdirs   Treat each top-level (HDL-containing) folder as a project.
    branches  Treat each remote branch as a project (klyone behaviour).
    auto      Inspect the URL: account URL -> org, repo URL -> repo.

Artifact classification (preserved from the original)
-----------------------------------------------------
Each analyzed project is still classified into the same logical buckets:

    README.md                 # original readme if present
    docs/                     # PDFs, markdown, text docs
    images/                   # PNG/JPG/SVG diagrams
    code/verilog/             # .v, .sv, .vh, .svh, .verilog
    code/vhdl/                # .vhd, .vhdl
    code/other/               # .chisel/.scala/.bsv/.myhdl + build files
    references/links.json     # URLs / references found in docs

The extractor now operates in report-only mode: it analyzes repositories and
records categorized artifact paths in metadata instead of copying extracted
files into a local output directory.

Usage examples
--------------
    python extractor.py --url https://github.com/lowrisc/ibex --mode repo
    python extractor.py --url https://github.com/freecores --mode org --max-projects 100
    python extractor.py --url https://github.com/user/repo --mode subdirs
    python extractor.py --url https://github.com/klyone/opencores-ip --mode branches
    python extractor.py --url https://github.com/chipsalliance/rocket-chip --mode auto
    python extractor.py --url https://github.com/lowrisc/ibex --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urlparse

# Optional dependencies — gracefully degrade if missing
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# File-type classification by extension
HDL_VERILOG_EXTS = {".v", ".sv", ".vh", ".svh", ".verilog"}
HDL_VHDL_EXTS = {".vhd", ".vhdl"}
HDL_OTHER_EXTS = {".chisel", ".scala", ".bsv", ".myhdl"}
DOC_EXTS = {".pdf", ".md", ".txt", ".rst", ".tex", ".docx", ".doc"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".bmp", ".tif", ".tiff", ".webp"}
BUILD_EXTS = {".tcl", ".sdc", ".xdc", ".ucf", ".do", ".f"}

# All HDL extensions (used for HDL-containing folder detection in subdirs mode)
HDL_ALL_EXTS = HDL_VERILOG_EXTS | HDL_VHDL_EXTS | HDL_OTHER_EXTS

# Files/folders to ignore inside a project
IGNORE_PATTERNS = {".git", ".github", "__pycache__", "node_modules", ".vscode"}

# Quality filters (defaults; can be overridden via CLI)
DEFAULT_MIN_HDL_FILES = 1
DEFAULT_MIN_TOTAL_BYTES = 500  # truly empty projects

# Default cache path
DEFAULT_CACHE_DIR = Path("cache")

# Git operation timeouts (seconds)
CLONE_TIMEOUT = 600
FETCH_TIMEOUT = 180

VALID_MODES = ("auto", "repo", "org", "subdirs", "branches")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("extractor")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ProjectStats:
    """Summary statistics for a single extracted project."""

    verilog_files: int = 0
    vhdl_files: int = 0
    other_hdl_files: int = 0
    pdf_files: int = 0
    markdown_files: int = 0
    text_files: int = 0
    image_files: int = 0
    total_bytes: int = 0
    languages_seen: list[str] = field(default_factory=list)

    @property
    def total_hdl_files(self) -> int:
        return self.verilog_files + self.vhdl_files + self.other_hdl_files


@dataclass
class ProjectMeta:
    """Metadata describing one analyzed project."""

    project_id: str
    name: str
    source: str                  # GitHub owner (e.g. "klyone", "freecores", "lowrisc")
    source_url: str
    extraction_date: str
    mode: str = "repo"           # repo | org | subdirs | branches
    license: Optional[str] = None
    has_readme: bool = False
    readme_excerpt: str = ""
    stats: ProjectStats = field(default_factory=ProjectStats)
    quality_tier: str = "C"      # A | B | C | rejected
    quality_reason: str = ""
    references: list[str] = field(default_factory=list)
    artifacts: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class Connection:
    """Readable relationship between one visual/doc artifact and likely code."""

    subject: str
    docs: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    code: list[str] = field(default_factory=list)
    confidence: str = "low"
    reason: str = ""


@dataclass
class GitHubTarget:
    """Result of parsing a GitHub URL."""

    host: str
    owner: str
    repo: Optional[str]          # None for account (org/user) URLs

    @property
    def is_repo(self) -> bool:
        return self.repo is not None

    @property
    def html_url(self) -> str:
        if self.repo:
            return f"https://{self.host}/{self.owner}/{self.repo}"
        return f"https://{self.host}/{self.owner}"

    @property
    def clone_url(self) -> str:
        return f"https://{self.host}/{self.owner}/{self.repo}.git"


# ---------------------------------------------------------------------------
# 1. URL parsing layer
# ---------------------------------------------------------------------------

class URLParseError(ValueError):
    """Raised when a string is not a usable GitHub URL."""


# git@github.com:owner/repo.git
_SSH_RE = re.compile(r"^git@(?P<host>[^:]+):(?P<path>.+)$")


def parse_github_url(url: str) -> GitHubTarget:
    """
    Parse a GitHub URL into (host, owner, repo).

    Accepts, with or without a trailing slash:
        https://github.com/owner
        https://github.com/owner/repo
        https://github.com/owner/repo.git
        github.com/owner/repo
        git@github.com:owner/repo.git

    Returns a :class:`GitHubTarget`. ``repo`` is ``None`` for account URLs.
    Raises :class:`URLParseError` with a helpful message on bad input.
    """
    if not url or not url.strip():
        raise URLParseError("Empty URL.")
    raw = url.strip()

    # Normalise SSH form into a path we can split.
    ssh = _SSH_RE.match(raw)
    if ssh:
        host = ssh.group("host")
        path = ssh.group("path")
    else:
        # Add a scheme if the user omitted it so urlparse populates netloc.
        if "://" not in raw:
            raw = "https://" + raw
        parsed = urlparse(raw)
        host = parsed.netloc.lower()
        path = parsed.path

    if not host:
        raise URLParseError(f"Could not determine host from URL: {url!r}")
    if "github.com" not in host and "github" not in host:
        raise URLParseError(
            f"Not a GitHub URL (host={host!r}). "
            f"Expected something like https://github.com/owner/repo."
        )

    # Split the path into non-empty segments and drop a trailing .git.
    segments = [s for s in path.split("/") if s]
    if not segments:
        raise URLParseError(
            f"No owner found in URL: {url!r}. "
            f"Expected https://github.com/<owner>[/<repo>]."
        )

    owner = segments[0]
    repo = None
    if len(segments) >= 2:
        repo = segments[1]
        if repo.endswith(".git"):
            repo = repo[:-4]

    # Reject obviously non-account first segments.
    if owner.lower() in {"orgs", "users", "search", "settings", "marketplace"}:
        raise URLParseError(
            f"URL {url!r} does not point at a repository or account. "
            f"Use https://github.com/<owner>[/<repo>]."
        )

    return GitHubTarget(host=host, owner=owner, repo=repo)


# ---------------------------------------------------------------------------
# 2. Git cloning / fetching layer
# ---------------------------------------------------------------------------

def run_git(args: list[str], cwd: Optional[Path] = None,
            timeout: int = CLONE_TIMEOUT) -> subprocess.CompletedProcess:
    """Run a git command, capturing output. Never raises on non-zero exit."""
    try:
        return subprocess.run(
            ["git", *args],
            cwd=str(cwd) if cwd else None,
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        log.warning("git %s timed out after %ss", " ".join(args), timeout)
        return subprocess.CompletedProcess(args, returncode=124, stdout="", stderr="timeout")
    except FileNotFoundError:
        log.error("`git` executable not found on PATH — cannot clone repositories.")
        return subprocess.CompletedProcess(args, returncode=127, stdout="", stderr="git missing")


def ensure_clone(clone_url: str, dest: Path, depth: int = 1) -> bool:
    """
    Ensure a shallow clone of ``clone_url`` exists at ``dest``.
    Reuses an existing clone (cache hit) rather than re-cloning.
    Returns True if the working tree is available.
    """
    if dest.exists() and any(dest.iterdir()):
        log.debug("Reusing cached clone at %s", dest)
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    log.info("Cloning %s -> %s (depth=%d)", clone_url, dest, depth)
    r = run_git(["clone", "--depth", str(depth), clone_url, str(dest)], timeout=CLONE_TIMEOUT)
    if r.returncode != 0:
        log.warning("Clone failed for %s: %s", clone_url, r.stderr.strip()[:200])
        # Clean up a half-written directory so the next run can retry cleanly.
        if dest.exists():
            shutil.rmtree(dest, ignore_errors=True)
        return False
    return True


def list_remote_branches(clone_url: str) -> list[str]:
    """
    List remote branch names directly from a URL (no clone needed).
    Excludes the default/index branches (master/main/HEAD).
    """
    r = run_git(["ls-remote", "--heads", clone_url], timeout=FETCH_TIMEOUT)
    if r.returncode != 0:
        log.error("Failed to list branches for %s: %s", clone_url, r.stderr.strip()[:200])
        return []
    branches: list[str] = []
    for line in r.stdout.strip().splitlines():
        parts = line.split("refs/heads/")
        if len(parts) == 2:
            branches.append(parts[1].strip())
    return [b for b in branches if b not in {"master", "main", "HEAD"}]


def fetch_and_checkout_branch(repo_dir: Path, clone_url: str, branch: str,
                              depth: int = 1) -> bool:
    """Shallow-fetch a single branch into ``repo_dir`` and check it out."""
    f = run_git(["fetch", "--depth", str(depth), clone_url, branch],
                cwd=repo_dir, timeout=FETCH_TIMEOUT)
    if f.returncode != 0:
        log.warning("Fetch failed for branch %s: %s", branch, f.stderr.strip()[:120])
        return False
    co = run_git(["checkout", "-f", "FETCH_HEAD"], cwd=repo_dir, timeout=FETCH_TIMEOUT)
    if co.returncode != 0:
        log.warning("Checkout failed for branch %s: %s", branch, co.stderr.strip()[:120])
        return False
    return True


def current_branch(repo_dir: Path) -> str:
    """Best-effort name of the currently checked-out branch (for source URLs)."""
    r = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir, timeout=30)
    name = r.stdout.strip() if r.returncode == 0 else ""
    return name if name and name != "HEAD" else "master"


# ---------------------------------------------------------------------------
# 3. Discovery layer
# ---------------------------------------------------------------------------
#
# Each discovery function returns a list of *candidate* dicts. A candidate
# describes how to obtain a project but does NOT clone it yet (so --dry-run
# stays cheap). ``materialize()`` later turns a candidate into a project_info
# dict with a concrete ``local_path``.
#
#   candidate = {
#       "name":       str,            # project name (drives project_id)
#       "source":     str,            # GitHub owner
#       "source_url": str,            # human-facing URL
#       "clone_url":  str,            # repo to clone
#       "cache_key":  str,            # subdir of cache to clone into
#       "subdir":     Optional[str],  # subdir within the clone (subdirs mode)
#       "fetch_ref":  Optional[str],  # branch to fetch (branches mode)
#       "license":    Optional[str],  # SPDX id if known from the API
#   }


def discover_repo(target: GitHubTarget) -> list[dict]:
    """One repository -> one project."""
    return [{
        "name": target.repo,
        "source": target.owner,
        "source_url": target.html_url,
        "clone_url": target.clone_url,
        "cache_key": f"{target.owner}_{target.repo}",
        "subdir": None,
        "fetch_ref": None,
        "license": None,
    }]


def discover_org(target: GitHubTarget, max_projects: Optional[int] = None,
                 github_token: Optional[str] = None) -> list[dict]:
    """
    Every public repository under an org OR user account -> one project each.
    Uses the GitHub REST API with Link-header pagination. Works for both
    organizations and user accounts (tries /orgs first, falls back to /users).
    """
    if not HAS_REQUESTS:
        log.error("`requests` not installed — cannot query the GitHub API. "
                  "Install it (`pip install requests`) for org/user mode.")
        return []

    headers = {"Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    repos = _github_list_repos(target.owner, headers)
    if repos is None:
        return []

    log.info("Found %d public repositories under %s", len(repos), target.owner)
    if max_projects:
        repos = repos[:max_projects]

    candidates: list[dict] = []
    for repo in repos:
        candidates.append({
            "name": repo["name"],
            "source": target.owner,
            "source_url": repo["html_url"],
            "clone_url": repo["clone_url"],
            "cache_key": f"{target.owner}_{repo['name']}",
            "subdir": None,
            "fetch_ref": None,
            "license": (repo.get("license") or {}).get("spdx_id"),
        })
    return candidates


def _github_list_repos(owner: str, headers: dict) -> Optional[list[dict]]:
    """List repos for an org or user. Returns None on hard failure."""
    for kind in ("orgs", "users"):
        url = f"https://api.github.com/{kind}/{owner}/repos"
        repos: list[dict] = []
        page = 1
        while True:
            try:
                resp = requests.get(
                    url,
                    params={"per_page": 100, "page": page, "type": "public"},
                    headers=headers, timeout=30,
                )
            except requests.RequestException as e:
                log.error("GitHub API request failed: %s", e)
                return None

            if resp.status_code == 404:
                # Not this kind of account — try the next (orgs -> users).
                break
            if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
                log.warning("GitHub API rate limit exhausted. "
                            "Pass --github-token or set GITHUB_TOKEN. "
                            "Returning %d repos discovered so far.", len(repos))
                return repos
            if resp.status_code != 200:
                log.error("GitHub API returned %s for %s: %s",
                          resp.status_code, url, resp.text[:200])
                return None

            page_repos = resp.json()
            if not page_repos:
                break
            repos.extend(page_repos)
            # Stop when the Link header has no "next", else advance politely.
            if 'rel="next"' not in resp.headers.get("Link", ""):
                break
            page += 1
            time.sleep(0.3)

        if repos:
            return repos
    log.error("No public repositories found for account %r (not an org or user?).", owner)
    return []


def discover_subdirs(target: GitHubTarget, cache_dir: Path) -> list[dict]:
    """
    Top-level folders of a repo -> one project each. Prefers folders that
    contain HDL files anywhere within; falls back to all top-level folders
    if none qualify. Requires cloning the repo once to inspect it.
    """
    cache_key = f"{target.owner}_{target.repo}"
    repo_dir = cache_dir / cache_key
    if not ensure_clone(target.clone_url, repo_dir):
        return []

    branch = current_branch(repo_dir)
    top_dirs = [d for d in sorted(repo_dir.iterdir())
                if d.is_dir() and d.name not in IGNORE_PATTERNS]

    hdl_dirs = [d for d in top_dirs if _dir_contains_hdl(d)]
    chosen = hdl_dirs if hdl_dirs else top_dirs
    if hdl_dirs:
        log.info("Found %d top-level folders, %d containing HDL.",
                 len(top_dirs), len(hdl_dirs))
    else:
        log.info("No HDL-containing top-level folder detected; "
                 "treating all %d top-level folders as projects.", len(top_dirs))

    candidates: list[dict] = []
    for d in chosen:
        candidates.append({
            "name": f"{target.repo}_{d.name}",
            "source": target.owner,
            "source_url": f"{target.html_url}/tree/{branch}/{d.name}",
            "clone_url": target.clone_url,
            "cache_key": cache_key,
            "subdir": d.name,
            "fetch_ref": None,
            "license": None,
        })
    return candidates


def _dir_contains_hdl(directory: Path) -> bool:
    """True if any file under ``directory`` has an HDL extension."""
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in IGNORE_PATTERNS]
        for f in files:
            if Path(f).suffix.lower() in HDL_ALL_EXTS:
                return True
    return False


def discover_branches(target: GitHubTarget, max_projects: Optional[int] = None) -> list[dict]:
    """
    Each remote branch -> one project (the klyone/opencores-ip case).
    Branch listing is done directly against the URL (no clone required for
    discovery); each branch is fetched lazily during materialization.
    """
    branches = list_remote_branches(target.clone_url)
    log.info("Found %d project branches in %s/%s",
             len(branches), target.owner, target.repo)
    if max_projects:
        branches = branches[:max_projects]

    cache_key = f"{target.owner}_{target.repo}"
    candidates: list[dict] = []
    for branch in branches:
        candidates.append({
            "name": branch,
            "source": target.owner,
            "source_url": f"{target.html_url}/tree/{branch}",
            "clone_url": target.clone_url,
            "cache_key": cache_key,
            "subdir": None,
            "fetch_ref": branch,
            "license": None,
        })
    return candidates


def materialize(candidate: dict, cache_dir: Path) -> Optional[dict]:
    """
    Turn a discovery candidate into a project_info dict with a concrete
    ``local_path``, cloning/fetching as needed. Returns None on failure so
    the caller can skip this project and continue with the rest.
    """
    repo_dir = cache_dir / candidate["cache_key"]

    if candidate.get("fetch_ref"):
        # branches mode: shared repo dir, fetch + checkout this branch.
        if not ensure_clone(candidate["clone_url"], repo_dir):
            return None
        if not fetch_and_checkout_branch(repo_dir, candidate["clone_url"],
                                         candidate["fetch_ref"]):
            return None
        local_path = repo_dir
    else:
        if not ensure_clone(candidate["clone_url"], repo_dir):
            return None
        local_path = repo_dir / candidate["subdir"] if candidate.get("subdir") else repo_dir
        if not local_path.exists():
            log.warning("Subdir %s vanished from %s", candidate.get("subdir"), repo_dir)
            return None

    return {
        "name": candidate["name"],
        "source": candidate["source"],
        "source_url": candidate["source_url"],
        "license": candidate.get("license"),
        "local_path": local_path,
    }


def discover(target: GitHubTarget, mode: str, cache_dir: Path,
             max_projects: Optional[int], github_token: Optional[str]) -> list[dict]:
    """Dispatch to the right discovery strategy for the resolved mode."""
    if mode == "repo":
        return discover_repo(target)
    if mode == "org":
        return discover_org(target, max_projects=max_projects, github_token=github_token)
    if mode == "subdirs":
        return discover_subdirs(target, cache_dir)
    if mode == "branches":
        return discover_branches(target, max_projects=max_projects)
    raise ValueError(f"Unknown mode: {mode!r}")


def resolve_mode(target: GitHubTarget, mode: str) -> str:
    """
    Resolve ``auto`` to a concrete mode based on the URL shape:
        account URL (no repo) -> org
        repository URL        -> repo
    Branch/subdir extraction must be requested explicitly.
    """
    if mode != "auto":
        return mode
    if target.is_repo:
        log.info("auto: repository URL detected -> 'repo' mode.")
        return "repo"
    log.info("auto: account URL detected -> 'org' mode.")
    return "org"


# ---------------------------------------------------------------------------
# 4. Project extraction layer
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    """Make a filesystem-safe project ID component."""
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip())
    return s.strip("_") or "unnamed"


def classify_file(path: Path) -> str:
    """Classify a single file by extension into a category."""
    ext = path.suffix.lower()
    if ext in HDL_VERILOG_EXTS:
        return "verilog"
    if ext in HDL_VHDL_EXTS:
        return "vhdl"
    if ext in HDL_OTHER_EXTS:
        return "other_hdl"
    if ext == ".pdf":
        return "pdf"
    if ext in {".md", ".rst"}:
        return "markdown"
    if ext in {".txt", ".tex"}:
        return "text"
    if ext in IMAGE_EXTS:
        return "image"
    if ext in BUILD_EXTS:
        return "build"
    return "ignored"


def find_readme(project_path: Path) -> Optional[Path]:
    """Find a README at the project root, case-insensitive."""
    try:
        children = list(project_path.iterdir())
    except OSError:
        return None
    for child in children:
        if child.is_file() and child.name.lower().startswith("readme"):
            return child
    return None


def walk_project_files(project_path: Path) -> Iterable[Path]:
    """Yield every file in the project, skipping ignored directories."""
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_PATTERNS]
        root_path = Path(root)
        for f in files:
            yield root_path / f


def extract_pdf_text(pdf_path: Path, max_chars: int = 4000) -> str:
    """Extract a text preview from a PDF. Empty string if extraction fails."""
    if not HAS_PYPDF:
        return ""
    try:
        reader = pypdf.PdfReader(str(pdf_path))
        chunks = []
        total = 0
        for page in reader.pages[:20]:  # cap pages
            text = page.extract_text() or ""
            chunks.append(text)
            total += len(text)
            if total >= max_chars:
                break
        return ("\n".join(chunks))[:max_chars]
    except Exception as e:  # pypdf raises a variety of exceptions on bad PDFs
        log.debug("PDF extraction failed for %s: %s", pdf_path.name, e)
        return ""


URL_RE = re.compile(r"https?://[^\s\)\>\]\"']+", re.IGNORECASE)


def extract_links_from_text(text: str) -> list[str]:
    """Pull all URLs from a string of text and deduplicate."""
    return sorted(set(URL_RE.findall(text)))


def detect_license(project_path: Path) -> Optional[str]:
    """Look for and heuristically identify a LICENSE / COPYING file at root."""
    try:
        children = list(project_path.iterdir())
    except OSError:
        return None
    for child in children:
        if child.is_file() and child.name.upper() in {
            "LICENSE", "LICENSE.TXT", "LICENSE.MD",
            "COPYING", "COPYING.TXT", "COPYRIGHT",
        }:
            try:
                content = child.read_text(encoding="utf-8", errors="ignore")[:2000]
                lower = content.lower()
                if "mit license" in lower:
                    return "MIT"
                if "apache license" in lower:
                    return "Apache-2.0"
                if "gnu general public license" in lower:
                    if "version 3" in lower:
                        return "GPL-3.0"
                    if "version 2" in lower:
                        return "GPL-2.0"
                    return "GPL"
                if "gnu lesser general public license" in lower:
                    return "LGPL"
                if "bsd" in lower:
                    return "BSD"
                return "Unknown"
            except OSError:
                return None
    return None


def extract_project(
    project_info: dict,
    mode: str = "repo",
    min_hdl_files: int = DEFAULT_MIN_HDL_FILES,
    min_total_bytes: int = DEFAULT_MIN_TOTAL_BYTES,
) -> Optional[ProjectMeta]:
    """
    Walk one project, classify its files, and produce a ProjectMeta.
    Returns None if the project is rejected by quality filters.
    """
    name = project_info["name"]
    src_path: Path = project_info["local_path"]
    project_id = f"{slugify(project_info['source'])}_{slugify(name)}"

    stats = ProjectStats()
    references_aggregated: set[str] = set()
    artifacts: dict[str, list[str]] = {
        "readme": [],
        "docs": [],
        "images": [],
        "code/verilog": [],
        "code/vhdl": [],
        "code/other": [],
    }

    # 1. README
    readme_path = find_readme(src_path)
    readme_excerpt = ""
    has_readme = False
    if readme_path:
        has_readme = True
        try:
            content = readme_path.read_text(encoding="utf-8", errors="ignore")
            readme_excerpt = content[:1500]
            references_aggregated.update(extract_links_from_text(content))
            artifacts["readme"].append(str(readme_path.relative_to(src_path)).replace("\\", "/"))
        except OSError as e:
            log.debug("README read failed for %s: %s", name, e)

    # 2. Walk and classify
    for file_path in walk_project_files(src_path):
        if not file_path.is_file():
            continue
        try:
            size = file_path.stat().st_size
        except OSError:
            continue
        stats.total_bytes += size
        category = classify_file(file_path)
        rel = file_path.relative_to(src_path)
        rel_str = str(rel).replace("\\", "/")

        if category == "verilog":
            artifacts["code/verilog"].append(rel_str)
            stats.verilog_files += 1
            if "Verilog" not in stats.languages_seen:
                stats.languages_seen.append("Verilog")
        elif category == "vhdl":
            artifacts["code/vhdl"].append(rel_str)
            stats.vhdl_files += 1
            if "VHDL" not in stats.languages_seen:
                stats.languages_seen.append("VHDL")
        elif category == "other_hdl":
            artifacts["code/other"].append(rel_str)
            stats.other_hdl_files += 1
        elif category == "pdf":
            artifacts["docs"].append(rel_str)
            stats.pdf_files += 1
            preview = extract_pdf_text(file_path)
            if preview:
                references_aggregated.update(extract_links_from_text(preview))
        elif category == "markdown":
            is_root_readme = (
                file_path == readme_path
                or (file_path.parent == src_path
                    and file_path.name.lower().startswith("readme"))
            )
            if not is_root_readme:
                artifacts["docs"].append(rel_str)
                stats.markdown_files += 1
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                references_aggregated.update(extract_links_from_text(content))
            except OSError:
                pass
        elif category == "text":
            artifacts["docs"].append(rel_str)
            stats.text_files += 1
        elif category == "image":
            artifacts["images"].append(rel_str)
            stats.image_files += 1
        elif category == "build":
            artifacts["code/other"].append(rel_str)
        # "ignored" => skip

    # 3. License detection (API value wins, else heuristic)
    detected_license = project_info.get("license") or detect_license(src_path)

    refs_list = sorted(references_aggregated)

    # 4. Quality scoring
    tier, reason = score_quality(
        stats, has_readme,
        min_hdl_files=min_hdl_files, min_total_bytes=min_total_bytes,
    )

    meta = ProjectMeta(
        project_id=project_id,
        name=name,
        source=project_info["source"],
        source_url=project_info["source_url"],
        extraction_date=time.strftime("%Y-%m-%dT%H:%M:%S"),
        mode=mode,
        license=detected_license,
        has_readme=has_readme,
        readme_excerpt=readme_excerpt,
        stats=stats,
        quality_tier=tier,
        quality_reason=reason,
        references=refs_list,
        artifacts={k: v for k, v in artifacts.items() if v},
    )

    if tier == "rejected":
        log.info("REJECT %-40s  (%s)", project_id, reason)
        return None

    log.info(
        "EXTRACT [%s] %-40s  V=%d VHDL=%d PDF=%d IMG=%d",
        tier, project_id,
        stats.verilog_files, stats.vhdl_files, stats.pdf_files, stats.image_files,
    )
    return meta


def score_quality(
    stats: ProjectStats,
    has_readme: bool,
    min_hdl_files: int,
    min_total_bytes: int,
) -> tuple[str, str]:
    """
    Assign a quality tier:
      A = HDL + (PDF or images) + README + 3+ HDL files
      B = HDL + README + 2+ HDL files
      C = HDL only / marginal
      rejected = below the minimum bar
    """
    if stats.total_hdl_files < min_hdl_files:
        return "rejected", f"Insufficient HDL files ({stats.total_hdl_files} < {min_hdl_files})"
    if stats.total_bytes < min_total_bytes:
        return "rejected", f"Project too small ({stats.total_bytes} bytes)"

    has_visual_or_spec = (stats.pdf_files > 0) or (stats.image_files > 0)
    if has_readme and has_visual_or_spec and stats.total_hdl_files >= 3:
        return "A", "README + (PDF or images) + 3+ HDL files"
    if has_readme and stats.total_hdl_files >= 2:
        return "B", "README + 2+ HDL files"
    return "C", "Minimal but valid (HDL present)"


# ---------------------------------------------------------------------------
# 5. Serialization helpers
# ---------------------------------------------------------------------------

def _meta_to_dict(meta: ProjectMeta) -> dict:
    return asdict(meta)


def _meta_from_dict(d: dict) -> ProjectMeta:
    d = dict(d)  # don't mutate caller's dict
    stats_d = d.pop("stats", {})
    stats = ProjectStats(**stats_d) if stats_d else ProjectStats()
    # Tolerate older meta.json files that predate the "mode" field.
    d.setdefault("mode", "repo")
    return ProjectMeta(stats=stats, **d)


# ---------------------------------------------------------------------------
# 6. Project packaging / connection mapping
# ---------------------------------------------------------------------------

SUBSYSTEM_KEYWORDS: dict[str, list[str]] = {
    "instruction_fetch": ["instruction_fetch", "if_stage", "prefetch", "fetch_fifo"],
    "instruction_decode_execute": [
        "instruction_decode_execute", "decode_execute", "decoder", "ex_block",
        "de_ex_stage", "alu", "multdiv",
    ],
    "load_store_unit": ["load_store", "lsu", "load_store_unit"],
    "icache": ["icache", "instruction_cache"],
    "pmp": ["pmp", "physical_memory_protection"],
    "register_file": ["register_file", "regfile"],
    "cs_registers": ["cs_register", "csr", "csr_register"],
    "tracer": ["tracer", "trace"],
    "debug": ["debug", "dm_", "jtag"],
    "verification": ["verification", "uvm", "formal", "testbench", "tb_", "dv/"],
    "simple_system": ["simple_system"],
    "synthesis": ["synthesis", "/syn/", "yosys", "sta_", ".sdc"],
}

IMAGE_REF_RE = re.compile(
    r"(?:image::|figure::|!\[[^\]]*\]\()(?P<path>[^\s\)]+)",
    re.IGNORECASE,
)


def artifact_bucket_for_category(category: str) -> Optional[str]:
    """Map a classifier category to the preserved output bucket."""
    if category == "verilog":
        return "code/verilog"
    if category == "vhdl":
        return "code/vhdl"
    if category in {"other_hdl", "build"}:
        return "code/other"
    if category in {"pdf", "markdown", "text"}:
        return "docs"
    if category == "image":
        return "images"
    return None


def normalize_subsystem_name(name: str) -> str:
    """Create a stable folder name for an inferred subsystem."""
    name = re.sub(r"^(ibex_|prim_)", "", name.lower())
    name = re.sub(r"[^a-z0-9]+", "_", name).strip("_")
    name = re.sub(r"_+", "_", name)
    return name or "misc"


def infer_subsystem_from_path(rel_path: str, category: str) -> Optional[str]:
    """Infer a subsystem/project group from a source-relative path."""
    normalized = rel_path.replace("\\", "/")
    lower = normalized.lower()
    stem = normalize_subsystem_name(Path(normalized).stem)

    # Vendored collateral is useful training material, but it should not explode
    # the main project into hundreds of tiny primitive folders.
    if lower.startswith("vendor/") or "/vendor/" in lower:
        return None

    for subsystem, keywords in SUBSYSTEM_KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            return subsystem

    if category in {"verilog", "vhdl", "other_hdl"}:
        if "/rtl/" in lower or lower.startswith("rtl/"):
            return stem
        if "/ip/" in lower:
            parts = [p for p in lower.split("/") if p]
            try:
                ip_index = parts.index("ip")
                if ip_index + 1 < len(parts):
                    return normalize_subsystem_name(parts[ip_index + 1])
            except ValueError:
                pass

    if category in {"markdown", "text", "pdf"}:
        if "/doc/03_reference/" in lower:
            return stem
        if "/doc/" in lower and stem not in {"index", "readme", "license"}:
            return stem

    if category == "image":
        for suffix in ("_block", "_diagram", "_mux", "_stage"):
            if stem.endswith(suffix):
                stem = stem[: -len(suffix)]
        if stem not in {"logo", "tb", "tb2"}:
            return normalize_subsystem_name(stem)

    return None


def scan_doc_image_references(src_path: Path) -> dict[str, set[str]]:
    """Return image basename -> docs that reference that image."""
    image_to_docs: dict[str, set[str]] = {}
    for file_path in walk_project_files(src_path):
        if classify_file(file_path) not in {"markdown", "text"}:
            continue
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel_doc = str(file_path.relative_to(src_path)).replace("\\", "/")
        for match in IMAGE_REF_RE.finditer(text):
            ref_name = Path(match.group("path").strip()).name.lower()
            if ref_name:
                image_to_docs.setdefault(ref_name, set()).add(rel_doc)
    return image_to_docs


def build_project_groups(src_path: Path) -> tuple[dict[str, dict[str, list[str]]], dict[str, set[str]]]:
    """
    Group artifacts into inferred subsystems while preserving docs/images/code buckets.
    Unmatched artifacts go to the special "__extra__" group.
    """
    groups: dict[str, dict[str, list[str]]] = {}
    image_refs = scan_doc_image_references(src_path)
    doc_subsystems: dict[str, str] = {}

    for file_path in walk_project_files(src_path):
        category = classify_file(file_path)
        if category not in {"markdown", "text", "pdf"}:
            continue
        rel = str(file_path.relative_to(src_path)).replace("\\", "/")
        subsystem = infer_subsystem_from_path(rel, category)
        if subsystem:
            doc_subsystems[rel] = subsystem

    for file_path in walk_project_files(src_path):
        if not file_path.is_file():
            continue
        category = classify_file(file_path)
        bucket = artifact_bucket_for_category(category)
        if not bucket:
            continue

        rel = str(file_path.relative_to(src_path)).replace("\\", "/")
        subsystem = infer_subsystem_from_path(rel, category)
        if category == "image":
            for doc_rel in image_refs.get(file_path.name.lower(), set()):
                subsystem = doc_subsystems.get(doc_rel, subsystem)
                if subsystem:
                    break

        group_name = subsystem or "__extra__"
        groups.setdefault(group_name, {
            "docs": [],
            "images": [],
            "code/verilog": [],
            "code/vhdl": [],
            "code/other": [],
        })
        groups[group_name][bucket].append(rel)

    return groups, image_refs


def copy_grouped_artifacts(src_path: Path, project_root: Path,
                           groups: dict[str, dict[str, list[str]]]) -> None:
    """Copy grouped artifacts into Projects/<name>/... and Extra/Additional_data/..."""
    if project_root.exists():
        shutil.rmtree(project_root)
    project_root.mkdir(parents=True, exist_ok=True)

    for group_name, buckets in groups.items():
        if group_name == "__extra__":
            group_root = project_root / "Extra" / "Additional_data"
        else:
            group_root = project_root / "Projects" / group_name

        for bucket, rel_paths in buckets.items():
            for rel in sorted(set(rel_paths)):
                src = src_path / rel
                if not src.exists() or not src.is_file():
                    continue
                dst = group_root / bucket / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

                if classify_file(src) == "pdf":
                    preview = extract_pdf_text(src)
                    if preview:
                        preview_dst = dst.with_suffix(dst.suffix + ".extracted.txt")
                        preview_dst.write_text(preview, encoding="utf-8")


def build_connections(groups: dict[str, dict[str, list[str]]],
                      image_refs: dict[str, set[str]]) -> dict[str, list[Connection]]:
    """Create readable relationships for each inferred project/subsystem."""
    result: dict[str, list[Connection]] = {}
    for group_name, buckets in groups.items():
        if group_name == "__extra__":
            continue

        docs = sorted(set(buckets.get("docs", [])))
        images = sorted(set(buckets.get("images", [])))
        code = sorted(set(
            buckets.get("code/verilog", [])
            + buckets.get("code/vhdl", [])
            + buckets.get("code/other", [])
        ))

        if not docs and not images and not code:
            continue

        connections: list[Connection] = []
        for image in images:
            referenced_docs = sorted(image_refs.get(Path(image).name.lower(), set()))
            linked_docs = [doc for doc in referenced_docs if doc in docs] or docs[:5]
            confidence = "high" if referenced_docs and code else "medium" if code else "low"
            reason = (
                "Image is referenced by documentation in this subsystem and matched to code by subsystem name."
                if referenced_docs and code else
                "Files share subsystem keywords or path proximity."
            )
            connections.append(Connection(
                subject=image,
                docs=linked_docs,
                images=[image],
                code=code[:12],
                confidence=confidence,
                reason=reason,
            ))

        if not images:
            connections.append(Connection(
                subject=group_name,
                docs=docs[:8],
                code=code[:12],
                confidence="medium" if docs and code else "low",
                reason="Documentation and code were grouped by shared subsystem keywords or path proximity.",
            ))

        result[group_name] = connections
    return result


def write_connection_reports(project_root: Path, project_id: str,
                             groups: dict[str, dict[str, list[str]]],
                             connections: dict[str, list[Connection]]) -> None:
    """Write project-wide and per-subsystem connection maps."""
    lines = [
        f"# What Connects To What: {project_id}",
        "",
        "This file maps images and documentation to likely related HDL/code files.",
        "Confidence is heuristic: high means a documentation reference and subsystem/code match; medium means path/name matching; low means weak or incomplete evidence.",
        "",
    ]

    for group_name in sorted(connections):
        lines.extend([f"## {group_name}", ""])
        for connection in connections[group_name]:
            lines.extend([
                f"- Subject: `{connection.subject}`",
                f"  Confidence: {connection.confidence}",
                f"  Reason: {connection.reason}",
            ])
            if connection.docs:
                lines.append("  Docs:")
                lines.extend(f"  - `{doc}`" for doc in connection.docs)
            if connection.images:
                lines.append("  Images:")
                lines.extend(f"  - `{image}`" for image in connection.images)
            if connection.code:
                lines.append("  Likely related code:")
                lines.extend(f"  - `{code}`" for code in connection.code)
            lines.append("")

        group_report = project_root / "Projects" / group_name / "CONNECTIONS.md"
        group_report.parent.mkdir(parents=True, exist_ok=True)
        group_report.write_text("\n".join(lines_for_group(group_name, connections[group_name])), encoding="utf-8")

    extra = groups.get("__extra__", {})
    if extra:
        lines.extend([
            "## Extra / Additional data",
            "",
            "These files were preserved but did not have enough evidence to connect to a specific subsystem.",
        ])
        for bucket, rel_paths in extra.items():
            if rel_paths:
                lines.append(f"- `{bucket}`: {len(set(rel_paths))} files")
        lines.append("")

    (project_root / "WHAT_CONNECTS_TO_WHAT.md").write_text("\n".join(lines), encoding="utf-8")


def lines_for_group(group_name: str, connections: list[Connection]) -> list[str]:
    """Render one subsystem connection report."""
    lines = [
        f"# Connections: {group_name}",
        "",
        "This subsystem folder keeps related docs, images, and code together.",
        "",
    ]
    for connection in connections:
        lines.extend([
            f"## {connection.subject}",
            "",
            f"Confidence: {connection.confidence}",
            "",
            f"Reason: {connection.reason}",
            "",
        ])
        if connection.docs:
            lines.append("Docs:")
            lines.extend(f"- `{doc}`" for doc in connection.docs)
            lines.append("")
        if connection.images:
            lines.append("Images:")
            lines.extend(f"- `{image}`" for image in connection.images)
            lines.append("")
        if connection.code:
            lines.append("Likely related code:")
            lines.extend(f"- `{code}`" for code in connection.code)
            lines.append("")
    return lines


def write_project_report(project_root: Path, meta: ProjectMeta,
                         groups: dict[str, dict[str, list[str]]]) -> None:
    """Write a compact project-level report for humans and dataset review."""
    stats = meta.stats
    subsystem_count = len([name for name in groups if name != "__extra__"])
    lines = [
        f"# {meta.name} Extraction Report",
        "",
        f"Source repository: {meta.source_url}",
        f"Extraction date: {meta.extraction_date}",
        f"Extraction mode: {meta.mode}",
        f"Quality tier: {meta.quality_tier} - {meta.quality_reason}",
        f"Detected license: {meta.license or 'Not detected'}",
        "",
        "## Summary",
        "",
        f"- README present: {'yes' if meta.has_readme else 'no'}",
        f"- Verilog/SystemVerilog files: {stats.verilog_files}",
        f"- VHDL files: {stats.vhdl_files}",
        f"- Other HDL/model/build files: {stats.other_hdl_files}",
        f"- PDF files: {stats.pdf_files}",
        f"- Markdown documentation files: {stats.markdown_files}",
        f"- Text documentation files: {stats.text_files}",
        f"- Image/block-diagram assets: {stats.image_files}",
        f"- Inferred subsystem folders: {subsystem_count}",
        f"- References/links extracted: {len(meta.references)}",
        "",
        "## Layout",
        "",
        "- `Projects/`: subsystem folders with their own docs/images/code buckets.",
        "- `Extra/Additional_data/`: preserved files that could not be confidently mapped.",
        "- `WHAT_CONNECTS_TO_WHAT.md`: project-wide image/doc/code relationship map.",
        "- `meta.json`: machine-readable extraction metadata.",
        "- `references/links.json`: URLs found in README/docs/PDF text.",
        "",
    ]
    (project_root / "PROJECT_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def package_project_output(project_info: dict, meta: ProjectMeta, output_dir: Path) -> None:
    """Create the organized project folder expected by the reference dataset."""
    src_path: Path = project_info["local_path"]
    project_root = output_dir / meta.project_id
    groups, image_refs = build_project_groups(src_path)
    copy_grouped_artifacts(src_path, project_root, groups)

    readme_path = find_readme(src_path)
    if readme_path:
        shutil.copy2(readme_path, project_root / "README.md")

    refs_dir = project_root / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)
    (refs_dir / "links.json").write_text(json.dumps(meta.references, indent=2), encoding="utf-8")
    (project_root / "meta.json").write_text(json.dumps(_meta_to_dict(meta), indent=2), encoding="utf-8")

    connections = build_connections(groups, image_refs)
    write_project_report(project_root, meta, groups)
    write_connection_reports(project_root, meta.project_id, groups, connections)


# ---------------------------------------------------------------------------
# 7. CLI driver layer
# ---------------------------------------------------------------------------

def run(
    url: str,
    mode: str,
    max_projects: Optional[int],
    cache_dir: Path,
    output_dir: Optional[Path],
    min_hdl_files: int,
    min_total_bytes: int,
    github_token: Optional[str],
    dry_run: bool = False,
) -> dict:
    """Run the full extraction pipeline for a single GitHub URL."""
    target = parse_github_url(url)            # raises URLParseError on bad input
    resolved_mode = resolve_mode(target, mode)
    log.info("URL=%s  owner=%s  repo=%s  mode=%s",
             target.html_url, target.owner, target.repo, resolved_mode)

    cache_dir.mkdir(parents=True, exist_ok=True)
    candidates = discover(target, resolved_mode, cache_dir, max_projects, github_token)
    # Belt-and-braces cap (org/branches already cap during discovery).
    if max_projects:
        candidates = candidates[:max_projects]

    log.info("Discovered %d candidate project(s).", len(candidates))

    if dry_run:
        print(f"\n--- DRY RUN: {len(candidates)} project(s) discovered "
              f"({resolved_mode} mode) ---")
        for i, c in enumerate(candidates, 1):
            extra = f"  branch={c['fetch_ref']}" if c.get("fetch_ref") else (
                    f"  subdir={c['subdir']}" if c.get("subdir") else "")
            print(f"  [{i:>4}] {c['source']}/{c['name']}{extra}")
        return {"discovered": len(candidates), "extracted": 0,
                "rejected": 0, "by_tier": {}, "dry_run": True}

    extracted = 0
    rejected = 0
    failed = 0
    by_tier: dict[str, int] = {"A": 0, "B": 0, "C": 0}

    for i, candidate in enumerate(candidates, 1):
        log.info("--- [%d/%d] %s/%s ---", i, len(candidates),
                 candidate["source"], candidate["name"])
        try:
            project_info = materialize(candidate, cache_dir)
            if project_info is None:
                failed += 1
                continue
            meta = extract_project(
                project_info,
                mode=resolved_mode,
                min_hdl_files=min_hdl_files, min_total_bytes=min_total_bytes,
            )
            if meta is None:
                rejected += 1
            else:
                extracted += 1
                by_tier[meta.quality_tier] = by_tier.get(meta.quality_tier, 0) + 1
                if output_dir:
                    package_project_output(project_info, meta, output_dir)
        except Exception as e:  # never let one bad project abort the whole run
            log.exception("Unexpected error on %s: %s", candidate["name"], e)
            failed += 1

    if extracted == 0 and rejected == 0:
        log.warning("No projects extracted. Check the URL, mode, and connectivity.")

    summary = {
        "discovered": len(candidates),
        "extracted": extracted,
        "rejected": rejected,
        "failed": failed,
        "by_tier": by_tier,
    }
    log.info("=" * 60)
    log.info("SUMMARY: %s", json.dumps(summary, indent=2))
    log.info("=" * 60)
    return summary


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generalized GitHub HDL/code project extractor.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python extractor.py --url https://github.com/lowrisc/ibex --mode repo\n"
            "  python extractor.py --url https://github.com/freecores --mode org --max-projects 100\n"
            "  python extractor.py --url https://github.com/user/repo --mode subdirs\n"
            "  python extractor.py --url https://github.com/klyone/opencores-ip --mode branches\n"
            "  python extractor.py --url https://github.com/chipsalliance/rocket-chip --dry-run\n"
        ),
    )
    parser.add_argument("--url", required=True,
                        help="GitHub repository or organization/user URL.")
    parser.add_argument("--mode", choices=VALID_MODES, default="auto",
                        help="Extraction strategy (default: auto).")
    parser.add_argument("--max-projects", type=int, default=None,
                        help="Cap on number of projects (org/branches modes).")
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR,
                        help="Where to clone source repos (default: ./cache).")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="Optional destination for organized extracted project folders.")
    parser.add_argument("--min-hdl-files", type=int, default=DEFAULT_MIN_HDL_FILES,
                        help="Minimum HDL files required to keep a project.")
    parser.add_argument("--min-total-bytes", type=int, default=DEFAULT_MIN_TOTAL_BYTES,
                        help="Minimum project size in bytes to keep.")
    parser.add_argument("--github-token", type=str,
                        default=os.environ.get("GITHUB_TOKEN"),
                        help="GitHub token (or env GITHUB_TOKEN) for higher "
                             "API rate limits in org/user mode.")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable debug logging.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Only list discovered projects; do not extract.")

    args = parser.parse_args(argv)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        run(
            url=args.url,
            mode=args.mode,
            max_projects=args.max_projects,
            cache_dir=args.cache_dir,
            output_dir=args.output_dir,
            min_hdl_files=args.min_hdl_files,
            min_total_bytes=args.min_total_bytes,
            github_token=args.github_token,
            dry_run=args.dry_run,
        )
    except URLParseError as e:
        log.error("Invalid --url: %s", e)
        return 2
    except KeyboardInterrupt:
        log.warning("Interrupted by user.")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
