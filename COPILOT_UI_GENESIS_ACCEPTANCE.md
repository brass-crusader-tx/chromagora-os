# Copilot UI Genesis acceptance rescue

This branch is rooted directly at immutable mirror commit `467b09041018099814c1b7d92a33cdf5b494cebd`.

The mirror manifest binds private TSUNAMI Genesis source head `1e65095a651394be923a7aa875cfc3b83a8254f6`.

This file is an execution marker only. Do not alter the 58 manifest-bound source/support files unless a genuine product defect is discovered by executable acceptance.

Required cloud-agent work:
- run the canonical build;
- produce app + AndroidTest APKs;
- require 39 instrumentation tests;
- capture 46 visual states on emulator;
- derive monochrome/squint review images;
- run visual sanity and crash/logcat gates;
- preserve APKs/evidence under `tsunami-builder/copilot-acceptance/`;
- do not merge;
- do not claim Motorola evidence unless ZY22L2PTS5 was actually used.
