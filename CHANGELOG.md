# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-10-13

### Added
- **Dynamic Pattern Clustering**: Normalizes dynamic timestamps (ISO-8601, HTTP dates, Syslog), UUIDs, IPv4/IPv6 addresses, hex memory pointers, duration latencies, and file sizes.
- **Incident Boundary Detection**: Multi-line stack trace detection across Python, Go, Java/JVM, Rust, and Node.js.
- **Visual Terminal Output**: High-contrast ANSI colored badges (`[x480 suppressed]`) and boxed incident banners with syntax-highlighted frames.
- **CLI Streaming Modes**:
  - Standard pipe input (`sys.stdin`) with graceful `BrokenPipeError` handling.
  - Multi-file arguments processing.
  - Live real-time tailing (`-f` / `--follow`) with file rotation and truncation support.
- **Zero-Config Presets**:
  - `auto`: Automatic detection of JSON lines, Docker prefixes, and plain text.
  - `docker`: Container prefix and timestamp stripping.
  - `json`: Structured JSON payload unpacking (`level`, `msg`, `status`, `path`).
  - `web`: HTTP access log pattern extraction (Nginx, Apache, Caddy, uvicorn).
  - `raw`: Literal line-by-line deduplication without fuzzy masking.
- **Incident Reporting & Clipboard**:
  - Markdown report export (`--export PATH`) summarizing noise reduction and captured stack traces.
  - One-click native clipboard copying (`--copy`) via PowerShell/pbcopy/xclip.
- **Configurable Filters**:
  - `--errors-only` (`-e`) to filter out routine noise and isolate errors.
  - `--ignore` (`-i`) regex patterns to drop matching noisy lines entirely.
  - `--window` (`-w`) and `--threshold` (`-t`) to tune debouncing windows.
  - `--no-color` / `NO_COLOR=1` support and `--no-stats` summary toggle.
- **Test Suite**: 59 test cases covering edge cases, scaling, false-positive prevention, and formatters.
- **CI/CD Matrix**: GitHub Actions workflow testing Python 3.9 through 3.14 on Linux, macOS, and Windows.
