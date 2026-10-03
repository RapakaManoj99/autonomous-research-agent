# Autonomous Multi-Tool Research Agent

LangGraph ReAct agent (Groq LLM) served through Flask, with five tools, a hardened calculator,
an HTTPS domain allowlist, and SQLite episodic memory isolated per thread.

## Tools
`calculator` (AST-based, no `eval`), `wikipedia_search`, `arxiv_search`, `weather`, `fetch_url`

## Security
- Calculator parses to an AST and only permits numeric constants and arithmetic operators.
- All outbound requests: HTTPS only, hostname in allowlist, no userinfo, port 443, redirects disabled.

## Run
```bash
pip install -r requirements.txt
export GROQ_API_KEY=...
python app.py
curl -X POST localhost:5000/chat -H 'Content-Type: application/json' \
     -d '{"thread_id":"demo","message":"What is 15% of 2480?"}'
```

## Tests
```bash
pytest -s tests/
```
`-s` prints the real blocked counts (injections and SSRF-style probes) and the memory-isolation load test.
