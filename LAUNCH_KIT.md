# 🚀 LogShrink GitHub Star & Launch Kit

> **Goal**: Turn **LogShrink** into a high-visibility, 1,000+ star open-source project by reaching developers, DevOps engineers, and CLI enthusiasts across global and local developer channels.
>
> Live Repository: [https://github.com/umutgungorr/logshrink](https://github.com/umutgungorr/logshrink)  
> GitHub Marketplace Action: `uses: umutgungorr/logshrink@v1`

---

## 📅 High-Impact Launch Schedule (Timing Blueprint)

To maximize visibility and ride algorithm momentum across platforms, launch in this order:

| Platform | Recommended Day & Time (EST) | Turkey Time (TRT / UTC+3) | Target Audience & Tone |
|---|---|---|---|
| **Hacker News (Show HN)** | Tuesday or Wednesday, 08:30–09:00 AM EST | 15:30–16:00 | Engineering purists, zero-dependency enthusiasts, CLI architects |
| **Reddit (r/commandline, r/Python)** | Tuesday or Wednesday, 10:30 AM EST | 17:30 | Hands-on developers, terminal lovers, Python builders |
| **Reddit (r/devops)** | Wednesday or Thursday, 09:30 AM EST | 16:30 | SREs, CI/CD maintainers, Kubernetes operators |
| **X / Twitter (Global)** | Simultaneous with HN (Tue 09:00 AM EST) | 16:00 | Visual thread, side-by-side GIF/terminal ASCII comparison |
| **LinkedIn (Global & TR)** | Wednesday, 11:00 AM EST | 18:00 | Engineering leads, DevOps professionals, open-source supporters |
| **Dev.to / Hashnode** | Thursday morning | 15:00 | In-depth tutorial & architectural writeup |
| **Product Hunt** | Tuesday or Thursday 00:01 AM PST | 10:01 TRT | Startup founders, productivity tool hunters |

---

## 1. 🟠 Hacker News (Show HN)

### Title Options (Pick One)
1. **Recommended**: `Show HN: LogShrink – Zero-dependency CLI to collapse polling noise in live terminal & CI logs`
2. **Alternative A**: `Show HN: LogShrink – Turn 5,000 repetitive /healthz logs into live badges, box real stack traces`
3. **Alternative B**: `Show HN: LogShrink – A Unix pipe stream filter for noisy Docker, K8s, and CI logs`

---

### First Comment (OP Introduction — Post Immediately After Submitting)

```markdown
Hey HN! I built LogShrink because I was tired of scrolling through thousands of lines of polling noise to find the one traceback that actually mattered.

Whenever I stream logs from Docker Compose, Kubernetes pods, or CI pipelines, my terminal buffer gets flooded with:
- 100s of identical `GET /healthz 200 (0.3ms)`
- Prometheus `/metrics` scrapes every 2 seconds
- Database connection pool heartbeats (`SELECT 1`)

When a real database deadlock or 500 error occurs, it scrolls off the terminal buffer in 300ms. Chaining `grep -v "health"` is brittle—it blind-deletes genuine errors occurring on health endpoints, drops multi-line Python/Go/Java tracebacks, and requires maintaining complex regex scripts.

LogShrink (`logshrink`) is a lightweight Unix-style stream filter designed to solve this:
1. **Dynamic Noise Suppression**: Collapses recurring lines into live counter badges like `[-] [x480 suppressed]` while always printing the first occurrence so you retain timing and context.
2. **Multi-Line Incident Boxing**: Detects tracebacks (Python, Go panics, Java stack traces, Rust panics, Node.js) and boxes them in ANSI borders so critical errors never get lost in the scroll.
3. **Instant Postmortems**: `--export incident_report.md` creates a clean GitHub-flavored Markdown postmortem, and `--copy` sends it straight to your clipboard for 1-click Slack sharing.
4. **GitHub Marketplace Action (`uses: umutgungorr/logshrink@v1`)**: Zero-config composite action that drops into your CI pipelines in 3 lines of YAML and populates `$GITHUB_STEP_SUMMARY`.
5. **Zero External Dependencies**: Implemented entirely in Python standard library (`sys`, `re`, `dataclasses`, `argparse`). Cold start is sub-15ms and memory usage is capped under 35 MB regardless of stream length.

You can pipe anything into it:
`docker compose logs -f | logshrink`
`kubectl logs -f deployment/api | logshrink`
`pytest -v 2>&1 | logshrink --summary`

Or run without installing:
`uvx --from git+https://github.com/umutgungorr/logshrink.git logshrink demo.log`

Code & GitHub Action: https://github.com/umutgungorr/logshrink

I'd love feedback on your experience with log parsing or edge cases you deal with daily!
```

---

### Anticipated HN Skepticism & Answers Cheatsheet

- **"Why not just use `grep -v`?"**  
  *Answer*: `grep -v` is destructive—if your health endpoint fails with a 500 or throws a DB exception, `grep -v "health"` silently deletes your actual bug! Furthermore, grep only operates line-by-line, mutilating multi-line stack traces. LogShrink inspects log levels, preserves the initial occurrence, collapses repetitions, and boxes multi-line error traces intact.
- **"Why not use `lnav`?"**  
  *Answer*: `lnav` is fantastic for interactive post-analysis in a curses/TUI interface. LogShrink is designed as a headless Unix pipe filter that outputs to standard stdout, fits seamlessly into shell aliases (`alias dcl='docker compose logs -f | logshrink'`), and runs headless in CI pipelines.
- **"How does memory scale on infinite streams?"**  
  *Answer*: LogShrink uses sliding time/frequency windows with bounded caches. Old normalizer hashes are pruned, keeping RSS resident memory under 35 MB even across millions of streamed lines.

---

## 2. 🔴 Reddit Launch Posts

### A. Subreddit: `r/Python`
**Title**: `I built LogShrink: A zero-dependency CLI stream filter that collapses noisy polling logs and auto-boxes multi-line errors`  
**Flair**: `Project` / `Showcase`

**Body**:
```markdown
Hi r/Python!

Like many of you, I spend hours staring at `docker compose logs -f` or running local microservices with FastAPI/Django/Flask. The terminal is always flooded with hundreds of identical `/healthz` 200 checks, database heartbeat queries, and Prometheus scrapes.

I built **LogShrink** (https://github.com/umutgungorr/logshrink) as an open-source, zero-dependency stream filter to fix this.

### What it does:
- **Zero Dependencies**: Pure Python 3.9+ standard library. No Rich, no Click, no requests. Instant cold start (<15ms).
- **Dynamic Folding**: Identical or template-matching polling messages are collapsed into live counter badges like `[-] [x350 suppressed]`.
- **First Line Preserved**: Unlike naive grepping, the first occurrence is always printed so you know the service is alive.
- **Multi-Line Incident Detection**: Detects and visually boxes Python tracebacks, Go panics, Java exceptions, Rust panics, and Node.js errors.
- **CI & GitHub Actions Ready**: Includes an official GitHub Action (`uses: umutgungorr/logshrink@v1`) that publishes a rich Markdown incident report straight to `$GITHUB_STEP_SUMMARY`.
- **Markdown & Clipboard Export**: `--export report.md --copy` lets you paste a structured crash report directly into Slack or Jira.

### Try it with uvx (no installation):
```bash
uvx --from git+https://github.com/umutgungorr/logshrink.git logshrink demo.log
```

Or install with pipx / pip:
```bash
pipx install git+https://github.com/umutgungorr/logshrink.git
```

GitHub: https://github.com/umutgungorr/logshrink

Would love your thoughts on the code architecture or features you'd like to see!
```

---

### B. Subreddit: `r/devops`
**Title**: `Stop scrolling through 10,000 /healthz logs: We built a zero-dep CLI filter & GitHub Action for CI/CD and K8s logs`  
**Flair**: `Tool` / `Open Source`

**Body**:
```markdown
Hey r/devops!

One of the most frustrating things during a CI failure or live Kubernetes debug session is log flood. You open a GitHub Actions run or tail a pod, and you're met with 20 MB of:
```
[INFO] GET /healthz 200 OK
[INFO] GET /healthz 200 OK
[INFO] GET /healthz 200 OK
```
And the actual OOMKilled error or DB connection timeout scrolled off the screen 2 minutes ago.

We built **LogShrink** to solve this once and for all:

1. **In the Terminal**:
   `kubectl logs -f deployment/backend | logshrink`
   Collapses repetitive polling bursts into `[-] [x420 suppressed]` badges and boxes real multi-line errors with ANSI highlighters.

2. **In GitHub Actions (CI Integration)**:
   GitHub Actions truncates logs after 5,000 lines. Plug LogShrink into your CI workflow with 3 lines:
   ```yaml
   - name: Clean & Summarize CI Logs
     uses: umutgungorr/logshrink@v1
     with:
       log-file: integration-test.log
   ```
   It cleans the log, catches errors, and writes an instant incident report to `$GITHUB_STEP_SUMMARY` with zero extra dependencies.

3. **Benchmarks**:
   - 100,000+ lines/sec throughput
   - < 15ms cold start
   - Pure Python standard library, cross-platform (Linux, macOS, Windows)

Repo: https://github.com/umutgungorr/logshrink

Feedback and PRs are very welcome!
```

---

### C. Subreddit: `r/commandline`
**Title**: `LogShrink – A zero-dependency Unix pipe stream filter to deduplicate polling noise and highlight stack traces`

**Body**:
```markdown
A lightweight Unix pipe filter that sits cleanly between noisy daemons and your terminal.

```bash
journalctl -u my-service -f | logshrink
docker compose logs -f | logshrink
curl -s http://log-stream | logshrink --errors-only
```

Features:
- Respects POSIX pipe mechanics and `NO_COLOR`
- Sub-15ms cold start
- Zero external dependencies
- Dynamic suppression with occurrence counters
- Boxed multi-line tracebacks for Python, Go, Java, Rust, Node.js

GitHub: https://github.com/umutgungorr/logshrink
```

---

## 3. 🐦 X (Twitter) & LinkedIn Posts

### X / Twitter Viral Thread (English)

**Tweet 1 (Hook + Visual)**:
```text
I got tired of terminal log flood scrolling my actual errors away.

So I built LogShrink: a zero-dependency CLI stream filter that deduplicates repetitive polling noise and auto-boxes real multi-line tracebacks.

Before: 5,000 lines of /healthz flood 💀
After: Clean live counter badges + boxed errors 🚀

👇 Repo & GitHub Action in thread
```

**Tweet 2 (How it works & pipe friendly)**:
```text
It behaves like any Unix tool:

$ docker compose logs -f | logshrink
$ kubectl logs -f deployment/api | logshrink
$ pytest 2>&1 | logshrink --summary

Zero external dependencies. Sub-15ms cold start. Pure Python stdlib.
```

**Tweet 3 (GitHub Action integration)**:
```text
We also released the official GitHub Marketplace Action:

- 3 lines of YAML in your workflow
- Writes a formatted incident report to $GITHUB_STEP_SUMMARY
- Never lose tracebacks when GitHub Actions truncates raw logs

uses: umutgungorr/logshrink@v1
```

**Tweet 4 (Call to Action)**:
```text
Try it in 5 seconds with uvx (no install):
uvx --from git+https://github.com/umutgungorr/logshrink.git logshrink demo.log

⭐ Star on GitHub: https://github.com/umutgungorr/logshrink
Feedback and RTs appreciated! 💙
```

---

### LinkedIn Post (English)

```markdown
Logging in modern cloud environments has a signal-to-noise problem.

When developing microservices with Docker Compose or Kubernetes, terminal buffers are constantly inundated with thousands of identical Kubernetes liveness probes (`GET /healthz 200`), Prometheus scrapes, and database heartbeats.

When an unhandled exception or deadlock actually occurs, it scrolls off your terminal buffer in milliseconds. And naive `grep -v` pipelines are risky—they blindly delete real failures occurring on health routes.

To solve this, I built and open-sourced **LogShrink**:
👉 A zero-dependency CLI stream filter and GitHub Action that turns terminal log flood into clean signal.

Key Highlights:
✨ **Dynamic Suppression**: Collapses recurring lines into live counter badges while preserving the first line for context.
🛡️ **Multi-Line Incident Boxing**: Detects tracebacks (Python, Go, Java, Rust, Node) and visually highlights them.
🤖 **GitHub Actions CI Integration**: Plug into any CI workflow with `uses: umutgungorr/logshrink@v1` to publish clean postmortems directly to `$GITHUB_STEP_SUMMARY`.
⚡ **Zero External Dependencies**: Pure Python standard library, <15ms cold start, cross-platform.
📋 **Instant Postmortems**: 1-click Markdown export and system clipboard copy (`--copy`) for instant Slack/Jira sharing.

Check out the project on GitHub:
🔗 https://github.com/umutgungorr/logshrink

If you find it useful, a star ⭐ on the repository would mean a lot!

#DevOps #Python #OpenSource #SoftwareEngineering #CLI #DeveloperTools #GitHubActions #Kubernetes
```

---

## 4. 🇹🇷 Turkish Developer Community Launch Copy (Türkçe Paylaşımlar)

### X / Twitter (Türkçe Paylaşım)

```text
Terminalde Docker Compose veya Kubernetes loglarını açtığınızda ekrandan saniyede 500 tane "/healthz 200" akmasından ve aradaki gerçek hatayı kaçırmaktan sıkıldınız mı?

Bunu çözmek için sıfır bağımlılıklı açık kaynak bir CLI geliştirdim: **LogShrink** 🚀

Tek bir pipe ile terminali temizliyor:
docker compose logs -f | logshrink

Neler yapıyor?
🔹 Tekrar eden polling / heartbeat loglarını live badge olarak daraltıyor
🔹 İlk logu asla silmiyor, bağlamı koruyor
🔹 Python, Go, Java, Rust stack trace'lerini otomatik yakalayıp kutuluyor
🔹 GitHub Actions CI entegrasyonuyla ($GITHUB_STEP_SUMMARY) tek tıkla özet çıkarıyor
🔹 0 harici kütüphane, saf Python stdlib, anında çalışıyor

Kurmadan denemek için:
uvx --from git+https://github.com/umutgungorr/logshrink.git logshrink demo.log

Yıldızlayıp destek olursanız çok sevinirim ⭐
🔗 https://github.com/umutgungorr/logshrink
```

---

### LinkedIn (Türkçe Paylaşım)

```markdown
Yazılım geliştirirken ve mikroservisleri debug ederken karşılaştığımız en yaygın sorunlardan biri log gürültüsüdür.

Terminalde `docker compose logs -f` veya `kubectl logs` çalıştırdığımızda, Kubernetes liveness probe'ları, veritabanı heartbeat sorguları ve metrik scrape'leri dakikada binlerce satır üreterek terminali kilitler. Gerçek bir hata veya stack trace oluştuğunda ise saniyeler içinde yukarı kayıp kaybolur. `grep -v` kullanmak ise tehlikelidir; çünkü sağlık ucundaki gerçek 500 hatalarını körü körüne siler.

Bu sorunu çözmek amacıyla **LogShrink** projesini geliştirdim ve açık kaynak olarak yayınladım:

📌 **LogShrink Nedir?**
Tekrarlayan log gürültüsünü canlı sayım rozetlerine dönüştüren, çok satırlı hata izlerini otomatik kutulayan ve GitHub Actions iş akışlarına kusursuz entegre olan sıfır bağımlılıklı bir CLI akış filtresidir.

Öne Çıkan Özellikler:
✅ **Sıfır Harici Bağımlılık**: Yalnızca Python standart kütüphanesiyle yazıldı. Soğuk başlatma süresi < 15ms.
✅ **Akıllı Gruplama**: Tekrarlayan logları `[-] [x480 suppressed]` şeklinde katlar; ilk satırı bağlam için korur.
✅ **Hata Yakalama & Kutulama**: Python traceback, Go panic, Java, Rust ve Node.js istisnalarını ANSI çerçeveleriyle öne çıkarır.
✅ **GitHub Actions Entegrasyonu**: `uses: umutgungorr/logshrink@v1` ile CI özet sayfasına ($GITHUB_STEP_SUMMARY) doğrudan Markdown rapor ekler.
✅ **Tek Tuşla Raporlama**: `--copy` parametresi ile oluşan hata raporunu doğrudan panoya kopyalar, Slack veya Jira'ya anında yapıştırabilirsiniz.

Projeyi incelemek ve GitHub üzerinden yıldız vererek destek olmak isterseniz:
🔗 https://github.com/umutgungorr/logshrink

Geri bildirimlerinizi ve katkılarınızı duymaktan mutluluk duyarım!

#YazılımGeliştirme #AçıkKaynak #DevOps #Python #Terminal #GitHub #YazılımMühendisliği
```

---

### Yazılımcı Telegram & Discord Grupları Paylaşım Metni

```text
Selamlar herkese! 👋

Mikroservis, Docker ve Kubernetes loglarındaki gereksiz polling gürültüsünü (healthz, ping, SELECT 1) temizleyip gerçek hataları öne çıkaran açık kaynak bir CLI tool yazdım: **LogShrink**.

Sıfır dependency (sadece Python stdlib), terminalde pipe ile doğrudan çalışıyor:
`docker compose logs -f | logshrink`

Ayrıca GitHub Actions için Marketplace action'ı da hazır (`uses: umutgungorr/logshrink@v1`).

Repo: https://github.com/umutgungorr/logshrink

İnceleyip GitHub'da bir ⭐ bırakırsanız ve geri bildirim verirseniz çok mutlu olurum! 🚀
```

---

## 5. 📝 Dev.to / Medium / Hashnode Article Outline

**Article Title**: *How We Turned 50,000 Lines of CI and Docker Log Noise into Instant Postmortems with Zero Dependencies*

1. **The Agony of Log Scrolling**: The cognitive load of terminal noise in modern cloud setups.
2. **Why Grep Pipelines Fail**: The danger of dropping genuine 500s on health endpoints and truncating multi-line stack traces.
3. **Designing LogShrink**:
   - Stream processing with bounded memory.
   - Normalizing timestamps, UUIDs, IPs, and elapsed times into stable templates.
   - The State Machine: First line pass-through -> aggregation counter -> flush on drift.
4. **Multi-Language Stack Trace Detection**: Regex-based heuristic engines for Python, Go, Java, Rust, and Node.js.
5. **CI/CD Integration with GitHub Actions**:
   - Dropping `uses: umutgungorr/logshrink@v1` into workflows.
   - Populating `$GITHUB_STEP_SUMMARY`.
6. **Performance & Benchmarks**: Handling 100k lines/sec with Python stdlib.
7. **Get Started**: Quick installation via `uvx`, `pipx`, and `pip`.

---

## 6. 🏆 Product Hunt Launch Checklist

- **Name**: LogShrink
- **Tagline**: Turn terminal log flood into signal. Instantly.
- **Topics**: Developer Tools, Open Source, Command Line, Productivity, GitHub
- **Maker First Comment**:
  Introduce your background, why you created LogShrink, the zero-dependency architecture, and invite users to test the demo command:
  `uvx --from git+https://github.com/umutgungorr/logshrink.git logshrink demo.log`
- **Visuals to upload**:
  1. Side-by-side terminal comparison (Before vs After).
  2. GitHub Action Step Summary screenshot.
  3. Animated terminal GIF recording using `vhs` or `asciinema`.
