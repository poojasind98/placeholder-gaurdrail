# Guardrail - Project Status

**Project:** Guardrail - Unified Anomaly Detection via LLMs and Signature IDS
**Stage:** Phase 1 (Foundation + First Integration Checkpoint)
**Document owner:** Pooja Sindham
**Last updated:** April 20, 2026

---

## 1. What is Guardrail?

Guardrail is a research prototype for a **two-layer anomaly detection
system** that unifies:

- **A Log Engine** - an LLM-based analyzer that classifies sequences of
  system logs as *normal* or *anomalous*. Built on the LogLLM
  architecture (BERT + Llama-3-8B fine-tuned with LoRA).
- **A Network Engine** - a signature-based intrusion detection layer
  using Snort 3.

The novel contribution we are targeting is **not** either engine in
isolation - both are based on existing, well-understood components. The
contribution is the **orchestration + correlation layer** that fuses
their outputs into a single unified alert surface.

---

## 2. Problem statement

Modern attacks occur at two layers simultaneously, yet commercial tools
typically watch only one:

| Layer | Example attack | Tool that catches it today |
|---|---|---|
| Network | SQL injection, port scan, Shellshock | Snort / Suricata / Firewalls |
| Host / Application logs | Privilege escalation, data exfiltration, kernel panic cascade | SIEMs (rule-based), human analysts |

- **Network-only tools** miss anomalies that never touch the wire, or
  that use encrypted channels.
- **Log-only tools** miss in-flight attacks that are blocked or
  detected before they leave a log trail.
- **SIEMs** correlate alerts but rely on hand-written rules that do
  not generalize.

Guardrail proposes using a **Large Language Model** on the log side to
generalize beyond rules, while keeping a fast, deterministic Snort
layer on the network side for wire-speed coverage.

---

## 3. Proposed architecture

Guardrail is a **sequential pipeline** (not two parallel engines).
Every event - log line, HTTP request, kernel message - enters one front
door, passes through the log-engine stage, and only then hits the
Snort signature matcher as a **post-processing enrichment step**.

```text
                 INPUT (any event: log line, HTTP request, syslog)
                            │
                            ▼
                  ┌───────────────────────┐
                  │  [1] LOG ENGINE       │
                  │      (BERT + Llama)   │
                  │                       │
                  │  - classifies kind    │
                  │  - extracts content   │
                  │  - anomaly score      │
                  └──────────┬────────────┘
                             │  pipeline output
                             ▼
                 ┌────────────────────────┐
                 │ is kind network-based? │
                 └──────┬─────────┬───────┘
                        │ yes     │ no
                        ▼         ▼
           ┌────────────────────┐ │
           │ [2] SNORT MATCHER  │ │
           │                    │ │
           │ rules: local.rules │ │
           │ (DB-backed in P2)  │ │
           │                    │ │
           │ ->  matched SIDs   │ │
           └──────────┬─────────┘ │
                      │           │
                      ▼           ▼
                  ┌───────────────────────┐
                  │ [3] SUMMARIZER        │
                  │     (LLM, in P2)      │
                  │                       │
                  │  combines:            │
                  │    - anomaly score    │
                  │    - signature hits   │
                  │    - original context │
                  └──────────┬────────────┘
                             ▼
                 Unified human-readable alert
                 (BENIGN / SUSPICIOUS / MEDIUM / HIGH)
```

**Why this shape (and not parallel engines)?**

1. **Single entry point.** Callers do not have to classify input
   themselves - the pipeline decides what runs.
2. **Snort sees pre-extracted content.** Rather than raw packets, Snort
   receives the same content the log engine saw, so rule matches are
   aligned with the anomaly score.
3. **Non-network anomalies still flow through.** Kernel panics, file
   system corruption, etc. skip the Snort stage but still reach the
   summarizer - the log engine's anomaly score alone is enough.
4. **Composable.** Each stage is an independent function with a typed
   input/output. Phase 2 replaces the heuristic log engine with the
   real LLM; Phase 4 plugs the correlator in between stages 2 and 3.

### Rule storage

- **Today (Phase 1):** rules live in a flat text file in Snort's native
  syntax: `demo/local.rules`. Pros: directly consumed by the Snort
  binary; human-editable. Cons: no versioning, no metadata, no runtime
  updates.
- **Phase 2 plan:** move to a SQLite table
  `rules(sid, msg, pattern, nocase, priority, enabled, source,
  last_updated)` with a one-way export to Snort's flat format. Enables
  rule versioning, per-deployment enable/disable, and ingestion from
  upstream feeds (Talos, Emerging Threats) tagged by `source`.

---

## 4. Repository scope - files we have decided to work with

We have surveyed the LogLLM codebase and identified the files we plan to
adopt as our log-engine foundation and the new files we are authoring
for the Guardrail system layer.

### 4.1 Adopted from the LogLLM foundation (to be extended)

| File | Role in Guardrail | Planned changes |
|---|---|---|
| `model.py` | Core log-engine model (BERT + projector + Llama-3-8B) | Extend to run on Apple MPS / lower-end GPUs; decouple from CUDA hardcoding |
| `customDataset.py` | Log-sequence dataset + PyTorch collator | Reuse as-is for Phase 2 live inference |
| `train.py` | 3-phase LoRA fine-tuning script | Add checkpointing + evaluation hooks |
| `eval.py` | Test-set evaluation -> precision/recall/F1 | Wrap as a callable inside the orchestrator |
| `prepareData/sliding_window.py` | Sequence construction for BGL, Liberty, Thunderbird | Reuse |
| `prepareData/session_window.py` | Sequence construction for HDFS (session-based) | Reuse |
| `ft_model_<dataset>/`  (4 folders) | Fine-tuned LoRA adapters + projector weights for each dataset | Treated as baseline checkpoints |
| `requirements.txt` | Log-engine Python dependencies | Extend with Guardrail deps |
| `framework.png` | Reference architecture diagram | Cite in writeup |

### 4.2 New files authored for Guardrail (Phase 1)

| File | Purpose |
|---|---|
| `demo/run_demo.py` | Single entry point: banner, foundation metrics, pipeline run, Snort verification, summary, closing |
| `demo/local.rules` | Twenty hand-authored Snort 3 signature rules across six attack categories: SQL injection, XSS, path/sensitive-file access, recon scanners, RCE, and cloud metadata exfiltration (single source of truth for both the in-process matcher and the real Snort binary) |
| `demo/community-rules/community.rules` | Official **Snort 3 Community ruleset** (~4,017 rules, GPLv2, Cisco Talos). Fetched via `demo/fetch_community_rules.sh`. |
| `demo/community-rules/emerging.rules` | **Emerging Threats OPEN ruleset** (~47,424 rules, BSD-style, Proofpoint). Downloaded as Snort 2.9 syntax, auto-converted to Snort 3 via `snort2lua`, with broken-PCRE rules self-filtered. Fetched via `demo/fetch_et_open.sh`. |
| `demo/community-rules/snort.lua` | Minimal Snort 3 Lua config defining `HOME_NET` / `EXTERNAL_NET` / port variables required by both community rulesets |
| `demo/fetch_community_rules.sh` | One-shot script: downloads the Snort 3 Community ruleset from snort.org |
| `demo/fetch_et_open.sh` | One-shot script: downloads ET Open, runs it through `snort2lua`, iteratively filters rules Snort 3 cannot compile (typically 1–3 out of ~47K) |
| `demo/generate_pcap.py` | Synthesises `sample.pcap` with benign + malicious HTTP flows via scapy |
| `demo/sample.pcap` | Reference capture used by the Snort-verification section |
| `demo/requirements.txt` | Demo deps (rich, scapy) |
| `demo/README.md` | Setup + run instructions |
| `PROJECT_STATUS.md` | This document |

### 4.3 Files planned for Phase 2+ (not yet created)

| Planned file | Purpose | Target phase |
|---|---|---|
| `guardrail/orchestrator.py` | Top-level Guardrail coordinator calling both engines | Phase 2 |
| `guardrail/log_engine.py` | Wrapper exposing the LogLLM model as a callable service | Phase 2 |
| `guardrail/network_engine.py` | Python wrapper around Snort invocation + alert parsing | Phase 2 |
| `guardrail/correlator.py` | Fuses log verdicts + network alerts into a combined risk score | Phase 4 |
| `guardrail/dashboard/` | Real-time web dashboard (Streamlit / React) | Phase 5 |
| `data/pcaps/cicids2017/` | Real attack dataset (CIC-IDS2017) replacing synthetic pcap | Phase 3 |
| `tests/` | Unit + integration tests for the orchestration layer | Continuous |

---

## 5. What is working today (Phase 1 checkpoint)

This is what is demoable **right now** on a CPU-only laptop, via a
single command.

- **The Guardrail pipeline works end-to-end.** `demo/run_demo.py` walks
  the viewer through banner -> foundation metrics -> live pipeline run
  -> Snort verification -> summary, and produces unified verdicts
  (BENIGN / SUSPICIOUS / MEDIUM / HIGH) for every input event.
- **The pipeline correctly routes by event kind.** Web-access logs go
  through all three stages; kernel logs bypass the Snort matcher and
  go straight from log engine to summarizer. This validates the
  architecture in Section 3.
- **Snort 3 is installed and integrated two ways.** (a) The same
  `local.rules` file is loaded in-process by the pipeline's Stage 2
  matcher for zero-overhead per-event matching. (b) The real Snort
  binary is invoked as a subprocess on a reference pcap to verify the
  two matchers agree on rule IDs.
- **Twenty hand-authored Snort rules** across six attack categories
  (explainable, pipeline-integrated):
  - **SQL injection** (3): `UNION SELECT`, `OR 1=1` auth bypass, `SLEEP(` blind
  - **XSS** (3): `<script>` tag, `javascript:` URI, `onerror=` handler
  - **Path / sensitive files** (5): `../../` traversal, `/etc/passwd`,
    `/etc/shadow`, `.env`, `.git/config`
  - **Recon scanners** (4): sqlmap, Nmap, Nikto, WPScan User-Agents
  - **RCE** (3): Shellshock, PowerShell `-EncodedCommand`, PHP `<?php` tag
  - **Cloud / credential exfil** (2): AWS metadata endpoint
    `169.254.169.254`, `.aws/credentials` access
- **Snort 3 Community ruleset (4,017 rules, GPLv2, Cisco Talos)**
  downloaded via `demo/fetch_community_rules.sh`.
- **Emerging Threats OPEN ruleset (47,424 rules, BSD-style,
  Proofpoint)** downloaded and auto-converted from Snort 2.9 to
  Snort 3 syntax via `demo/fetch_et_open.sh` (uses `snort2lua` with an
  iterative self-healing filter for rules Snort 3's PCRE2 engine
  rejects — typically 1–3 rules out of ~47K).
- **Total loaded ruleset: 51,461 rules** (20 local + 4,017 community +
  47,424 ET Open) — production-scale coverage for a student project.
- **Synthetic pcap generation** via scapy produces a deterministic
  reference capture (4 benign + 15 attacks) covering 12 of the 20
  local signatures plus 5 community / ET Open signatures.
- **Live Snort verification run** loads all 51,461 rules, compiles
  18,457 of them into the PCRE2 engine, analyses the pcap in under
  6 seconds, and produces **20 alerts across 17 unique signatures**:
  - **12 from our local rules** (SQLi, XSS, traversal, /etc/passwd,
    .git/config, AWS metadata, etc.)
  - **5 from community + ET Open rules**: SID 648 (x86 NOP sled),
    SID 650 (x86 setuid(0) shellcode), SID 652 (Linux /bin/sh
    shellcode), SID 1394 (x86 heap-spray pattern), and SID 2100652
    (ET Open GPL SHELLCODE Linux).
- **Zero false positives on the benign flows**. All 20 alerts map to
  attack packets we authored; none fire on the 4 benign HTTP requests.

### How to reproduce this checkpoint

```bash
brew install snort                                 # one-time
python3 -m venv .venv                              # one-time
.venv/bin/pip install -r demo/requirements.txt     # one-time
.venv/bin/python demo/generate_pcap.py             # one-time (builds sample.pcap)
bash demo/fetch_community_rules.sh                 # one-time (~4,000 Snort community rules)
bash demo/fetch_et_open.sh                         # one-time (~47,000 Emerging Threats OPEN rules)

# Single entry point for the entire demo:
.venv/bin/python demo/run_demo.py
```

---

## 6. What is *not* yet working (honest gaps)

We are being explicit about the gaps so the roadmap is defensible.

| Gap | Why it is not yet done | Addressed in |
|---|---|---|
| **Live log-engine inference.** Today we display reported metrics, not live verdicts. | The log engine currently requires a CUDA GPU + 16 GB VRAM + Llama-3-8B base weights. Our laptop is Apple Silicon with no CUDA. | Phase 2 |
| **Real attack captures.** Today's pcap is synthetic. | We wanted reproducibility for Phase 1. Real captures require IRB / ethics review. | Phase 3 |
| **Demo pcap is synthetic, not a real attack capture.** 51,461 rules loaded, 17 fire (12 local + 5 community/ET Open). A real capture would fire 100s. | Intentional — the pcap is hand-crafted so every alert is traceable to a specific packet we authored. Phase 3 replaces it with CIC-IDS2017 to get realistic-scale coverage. | Phase 3 |
| **No correlation between engines.** Today they run in parallel, not coupled. | The correlation layer *is* the research contribution - we are staging up to it. | Phase 4 |
| **No quantitative end-to-end evaluation.** | We need Phase 2 + 3 complete first before we can evaluate the combined system. | Phase 5 |

---

## 7. Roadmap

| Phase | Weeks | Scope | Primary deliverable |
|---|---|---|---|
| **1. Foundation** (*done*) | 1-2 | Architecture sketched. Files scoped. Snort integration working end-to-end. Demo runnable on laptop. | This document + `demo/` folder |
| **2. Live log inference** | 3-5 | Port log engine off CUDA-only code path. Use Apple MPS or request GPU time on lab cluster. Wire the log engine into the orchestrator so it produces live verdicts during the demo. | `guardrail/log_engine.py`, `guardrail/orchestrator.py` |
| **3. Real network data** | 5-7 | Replace synthetic pcap with **CIC-IDS2017** academic attack dataset. Expand Snort ruleset to Emerging Threats OPEN. Add evaluation of the network engine alone. | `data/pcaps/`, expanded `rules/` |
| **4. Correlation layer** | 7-10 | Build the fusion engine: given a log-engine verdict and Snort alerts over a time window on the same host, compute a combined risk score. Define the fusion rule set. | `guardrail/correlator.py` |
| **5. Evaluation + writeup** | 10-12 | Construct combined benchmark where some attacks leave only network evidence, some only log evidence, some both. Measure Guardrail vs. Snort-alone vs. LogLLM-alone. Draft paper. | `eval/`, final report |

---

## 8. Risks and open questions

Transparent risks we are tracking:

1. **Compute access for Phase 2.** Apple MPS support for 4-bit
   quantization is still immature. Mitigation: request time on the lab
   GPU server by week 3; fall back to Colab Pro if unavailable.
2. **CIC-IDS2017 scale.** The full dataset is ~50 GB. We will work with
   a 5 GB subset for prototyping.
3. **Correlation rule design.** Rule-based correlation risks becoming
   another SIEM. We will explore a lightweight learned correlator
   (small MLP on engine outputs) as a secondary experiment in Phase 4.
4. **Reproducibility.** LoRA fine-tuning has stochastic outcomes. We
   will fix seeds and publish the full training manifest.

---

## 9. Immediate next steps (this week)

- [ ] Record a 3-minute Loom walkthrough of the Phase 1 demo for archival.
- [ ] Draft the `guardrail/` package skeleton (empty `__init__.py`,
      stubs for `orchestrator`, `log_engine`, `network_engine`).
- [ ] Migrate the Snort invocation logic from `demo/run_demo.py` into
      `guardrail/network_engine.py` so the orchestrator has a clean
      interface.
- [ ] Confirm GPU access for Phase 2 (submit cluster request).
- [ ] Begin surveying CIC-IDS2017 dataset structure for Phase 3.

---

## 10. Summary in one paragraph

> Guardrail is a unified anomaly-detection system combining LLM-based
> log analysis with signature-based network intrusion detection. We
> have just completed Phase 1: the architecture is defined, the
> Snort-based network engine is integrated end-to-end as a working
> CPU-only demo, and our log-engine foundation (LogLLM) is scoped for
> live integration in Phase 2. Our target research contribution is the
> **correlation layer** in Phase 4, which fuses verdicts from both
> engines into a single unified alert surface - a capability that no
> existing open-source tool provides cleanly today.
