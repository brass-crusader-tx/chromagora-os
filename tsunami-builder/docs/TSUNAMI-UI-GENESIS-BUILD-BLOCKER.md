# UI Genesis build-infrastructure blocker evidence

Date: 2026-09-25

The current UI Genesis source cannot obtain GitHub-hosted build/device evidence because GitHub Actions fails **before any workflow step begins**. This is not inferred from a failing Android, Gradle, Kotlin, font, or test step.

## Experiment 1 — isolated workflow inside TSUNAMI

A diagnostic branch was created from production main commit `2543cb39737557133a37d600050f9c4aa50a3fae`:

`diagnostic/actions-sanity-20260925`

Diagnostic commit:

`349f0f4b453201aa2fe542b71e496b2dc2273c79`

That commit removed the repository's existing workflow files from the diagnostic tree and installed one minimal workflow only:

```yaml
name: Actions sanity
on:
  push:
    branches:
      - diagnostic/actions-sanity-20260925
jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - run: echo ACTIONS_SANITY_PASS
```

GitHub created run **36124158309** for that exact commit. The run had:

- `event: push`
- `status: completed`
- `conclusion: startup_failure`
- `path: BuildFailed`
- an empty workflow name
- **zero jobs**; the echo step never started

This removed Android, Gradle, KVM, Python, checkout actions, repository tests, and the original workflow YAML from the experiment.

## Experiment 2 — independent public repository

To test whether the defect was specific to the private TSUNAMI repository, the current Genesis Android project was mirrored into the **public** repository `brass-crusader-tx/chromagora-os` on isolated branch:

`build/tsunami-ui-genesis-20260925`

The mirror was assembled without touching `chromagora-os` main. Relevant mirror commits include:

- `3b7d878816525632d4113126e362f2a42396525c` — Gradle project / manifest
- `d5ff6c8c60a862ea1b7aa0d0bc09a7e21e891614` — Android resources
- `3e2a9bf66c004f3449f72e96674a3997a3ef52d5` — shell core sources
- `abc7c2e56af2d22164366856f6fa285c2714caaf` — workspace sources
- `d05990e0e8f0471b2bdf2e76b41d81e829587f87` — remaining source, instrumentation test and font generator

A normal builder workflow was then added at commit `82cf50959f941affbc2e9a211c25e74a57902696`. Run **36125974081** registered the correct workflow name, but its only job, **108042060081**, terminated before any step existed; the job returned `steps=[]` and no usable step log.

## Experiment 3 — no actions, no checkout, no Android

To eliminate third-party/action-resolution policy as a cause, a second workflow used **only native shell steps** — no `uses:`, checkout, SDK setup, Gradle action, repository access, or Android command.

At commit `dbe63ca4c4f6347ee9851f1911d0c11691a39438`, run **36126525118** failed before its single shell step. Job **108043798723** again returned:

- `status: completed`
- `conclusion: failure`
- `steps: []`
- no usable job log

The full builder run created by the same push, **36126524905**, failed identically before steps.

## Experiment 4 — every GitHub-hosted runner family

The no-dependency probe was then expanded to three independent jobs at commit:

`ec361b2a82689dce39fd4cab37a1ce802ef1c86e`

The jobs requested only:

- `ubuntu-latest`
- `macos-latest`
- `windows-latest`

Each job contained a single native `echo`/PowerShell output statement.

Run **36126858910** completed as failure. All three jobs failed **before a step began**:

| Runner | Job ID | Result | Steps |
|---|---:|---|---|
| Windows | 108044862982 | failure | `[]` |
| macOS | 108044863184 | failure | `[]` |
| Ubuntu | 108044863189 | failure | `[]` |

This establishes that the present failure is not attributable to Linux/Ubuntu image selection, Android dependencies, Gradle, checkout, external actions, repository privacy, or the TSUNAMI repository itself. The available evidence localizes the blocker to pre-step Actions startup / workflow-association / account-or-platform infrastructure occurring before user workflow code executes.

## Experiment 5 — fresh current-PR event after source/evidence refresh

After the latest source and verification-document changes, pull request #16 produced a new Actions run at head `37ba4c7fa6b3dd22330e8856492f07368608f0ea`:

- run **36127395567**;
- event: `pull_request`;
- path: synthetic `BuildFailed`;
- workflow display name: empty;
- display title: `(Unknown event)`;
- conclusion: `startup_failure`;
- run start/update timestamp: **2026-09-25T11:04:22Z**;
- jobs endpoint result: **`jobs=[]`**.

Thus the current PR still does not reach checkout, Java setup, Android SDK setup, Gradle, the source verifier, font generation, compilation, tests, or artifact upload. This is fresh evidence on the current development lineage rather than merely historical evidence from earlier diagnostic commits.

## Consequence

A GitHub-hosted pass/fail result is presently unavailable as evidence for the shell. These infrastructure failures do **not** establish an Android compilation failure because no hosted runner executes source checkout or any shell command.

The UI Genesis acceptance gate remains `python3 tools/ui_shell_gate.py`; when runnable Android infrastructure is available it must still produce fresh evidence for:

1. TSUNAMI Sans generation and cmap/weight checks;
2. debug APK build;
3. forbidden-permission scan;
4. Compose instrumentation;
5. emulator/device boot and installation;
6. deterministic visual-state captures;
7. monochrome and squint derivatives;
8. crash/logcat scan;
9. packaged APK/evidence hashes.

No completion claim should substitute this infrastructure diagnosis for those missing Android/device results.

## Experiment 6 — current-head minimal runner probe

At current development head `a84faa4e6a8b643470995ab9991d104dcee1733a`, a temporary workflow containing only one `ubuntu-latest` job and a single native shell command, `echo "RUNNER_PROBE=PASS"`, was committed to the Genesis branch. GitHub created run **36160275870** for the resulting pull-request event.

The run again completed immediately with:

- `conclusion: startup_failure`;
- synthetic `path: BuildFailed`;
- empty workflow display name;
- **zero jobs** returned by the jobs endpoint.

Because the probe did not contain checkout, Java, Android, Gradle, Python, third-party actions, secrets, matrices, services, or artifact steps, this is a fresh current-lineage confirmation that the failure still precedes user code and runner allocation. The temporary probe workflow was removed immediately afterward so it does not become part of the product build surface.

## Experiment 7 — isolated self-hosted push trigger

The checked-in self-hosted acceptance workflow was extended on the Genesis branch so that pushes to `genesis/ui-shell-20260923` can request the repository's self-hosted runner directly, bypassing GitHub-hosted Ubuntu allocation. Commit `9e955e72e0ee7f13869e27062d8c4cbe8f77b9b7` triggered both push and pull-request events.

GitHub nevertheless emitted synthetic startup-failure runs **36160610352** (push) and **36160617226** (pull request) with `path: BuildFailed` before a named workflow or job was instantiated. Thus, in the present Actions state, selecting `runs-on: [self-hosted]` from the branch does not reach runner dispatch either. The self-hosted workflow remains useful once Actions dispatch is restored because it can execute the canonical host build and the attached-Motorola acceptance gate without depending on GitHub-hosted runners.


## Diagnostic precision

GitHub's public status page currently reports Actions operational and no incident for September 25, so there is no public evidence of a service-wide Actions outage at the time of these runs. Separately, contemporary GitHub Community reports document the same empty-name / synthetic `BuildFailed` / `startup_failure` / zero-job signature occurring before jobs exist. That signature can arise in workflow-startup or workflow-association infrastructure and does **not**, by itself, prove a runner-capacity failure.

Accordingly, the blocker is intentionally characterized only as **pre-step GitHub Actions infrastructure/startup**. The repository evidence rules out TSUNAMI Android source, Gradle, SDK setup, checkout, third-party Actions, and any one runner OS as the cause of the observed pre-step failures; it does not establish the exact GitHub account-side or backend root cause.

## Experiment 8 — current-head retry semantics

After the 37-state gate reconciliation and current-head evidence refresh, source head `e6d1360a50ae4850ae1903910cccf14163592060` produced fresh workflow runs **36168155010** and **36168239716**. Both completed with `startup_failure` before a workflow name or job was instantiated.

A direct attempt to re-run the failed current-lineage Actions run through GitHub's failed-jobs retry endpoint returned HTTP **403** with **"This workflow run cannot be retried"**. That behavior is consistent with the run having no retryable job object: the failure occurs before job allocation, not inside Gradle, Android, Java, Python, checkout, or a runner step.

The branch's source-side acceptance contracts were simultaneously rechecked after the capture matrix expanded to **37** states. `capture_verify.sh`, `visual_sanity_verify.py`, `ui_shell_gate.py`, `ui_shell_codespace_build.py`, `build_host.sh` and `ui_shell_static_check.py` now all require the same 37-state visual contract. This repairs a repository-internal count drift without weakening the outstanding executable acceptance boundary.

## Experiment 9 — current-head public mirror refresh and fresh push build

At private Genesis head `71f49a21681bf357cd32afcc0a04545e245a332a`, the public builder mirror on `brass-crusader-tx/chromagora-os:build/tsunami-ui-genesis-20260925` was re-synchronized against the private Git tree. A blob-by-blob comparison covered **40 UI-shell files + 8 support files** and returned **0 divergent blobs**. The mirror manifest was rebound at public commit `f18010517ac05466a99370edf11db1dabd6083f8` to private source head `71f49a21681bf357cd32afcc0a04545e245a332a`.

The public builder workflow was then given a branch-scoped push trigger at commit `adaea32834796e6247d857948d18a04bdec7e280`, producing fresh run **36170036683**. GitHub created job **108187058460**, but the job completed as failure before exposing any executable step list; the jobs API returned `steps=null`, and the job-log endpoint returned no materialized log blob (404). The run began at 2026-09-25T17:54:19Z and completed four seconds later.

This is fresh evidence against the exact current mirrored source. It still does **not** constitute an Android compile failure: checkout, Java setup, SDK setup, mirror binding, the canonical host build, Gradle, Kotlin/Compose compilation and artifact upload produced no step-level evidence. The current-head APK/device acceptance boundary therefore remains outstanding.


## Experiment 10 — 2026-09-26 current-source public mirror retry

After the v4.8 font manifest became part of the executable source contract, the public builder mirror was refreshed again rather than relying on the September 25 snapshot. Private head `11388f2ce43bb8c518a494e8044e5dba0f854e09` was compared against `brass-crusader-tx/chromagora-os:build/tsunami-ui-genesis-20260925` by Git blob SHA. The refreshed mirror contains **40 ui-shell files + 16 build/support files = 56 byte-identical blobs**, with **0 missing and 0 divergent paths**. Public commit `03d38e5a42587f9a2beb140aa132214954149d60` binds `MIRROR-MANIFEST.json` to that exact private head.

That push created:

- hosted builder run **36246923694**, job **108417723315**;
- public self-hosted run **36246923706**, job **108417724911**.

The hosted job first entered the queue and obtained a job object, then completed as failure without ever materializing a step list (`steps=null`). Fetching the job log returned HTTP 404 / `BlobNotFound`, so there is still no checkout, shell-command, Gradle or Android log to attribute the failure to repository code. The self-hosted job remains queued awaiting a matching runner.

This fresh run is useful for one reason: it eliminates stale mirror content—including the newly required TSUNAMI Sans v4.8 manifest and root gate—as a confounder. It still cannot satisfy the APK/device acceptance boundary because no user step ran.
