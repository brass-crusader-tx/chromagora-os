# Workers — Python Background Workers

Background workers for LLM calls, pipeline processing, and scheduled tasks.

## Stack
- Python 3.12+
- Supabase (supabase-py) for state access
- OpenRouter for LLM inference (free tiers only)
- httpx for HTTP calls

## Workers (planned)
- Agent runner — executes agent runs via LLM
- Pipeline processor — handles workflow step execution
- Scheduler — timers, retries, stale checks

## Running
```bash
cd apps/workers
pip install -r requirements.txt
python -m chromagora_workers.runner
```
