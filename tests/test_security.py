import sys, os, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import tools
import memory

INJECTIONS = [
    "__import__('os').system('ls')",
    "open('/etc/passwd').read()",
    "().__class__.__bases__[0].__subclasses__()",
    "eval('1+1')",
    "exec('import os')",
    "[x for x in range(10)]",
    "lambda: 1",
    "'a' * 1000000",
    "9**9**9",
    "os.popen('id')",
]

PROBES = [
    "http://en.wikipedia.org/wiki/X",                    # not https
    "https://evil.com/",                                 # unknown domain
    "https://169.254.169.254/latest/meta-data/",         # cloud metadata
    "https://localhost/admin",
    "https://127.0.0.1:8080/",
    "https://en.wikipedia.org.evil.com/",                # lookalike suffix
    "https://evil.com@en.wikipedia.org/",                # userinfo trick
    "https://en.wikipedia.org@evil.com/",
    "file:///etc/passwd",
    "https://en.wikipedia.org:8443/",                    # non-443 port
]


def test_calculator_blocks_injection():
    blocked = 0
    for p in INJECTIONS:
        try:
            tools.safe_calculate(p)
        except Exception:
            blocked += 1
    print(f"calculator blocked {blocked}/{len(INJECTIONS)}")
    assert blocked == len(INJECTIONS)


def test_calculator_correctness():
    cases = {"2+3*4": 14, "(10-4)/3": 2, "2**10": 1024, "-5+8": 3, "7//2": 3, "7%4": 3}
    for expr, want in cases.items():
        assert tools.safe_calculate(expr) == want


def test_allowlist_blocks_probes():
    blocked = sum(1 for u in PROBES if not tools.is_allowed(u))
    print(f"allowlist blocked {blocked}/{len(PROBES)}")
    assert blocked == len(PROBES)
    assert tools.is_allowed("https://en.wikipedia.org/api/rest_v1/page/summary/Python")


def test_memory_thread_isolation(tmp_path):
    memory.DB_PATH = str(tmp_path / "test.db")
    def worker(i):
        for j in range(40):
            memory.add(f"t{i}", "user", f"thread{i}-msg{j}")
    ts = [threading.Thread(target=worker, args=(i,)) for i in range(50)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert memory.count() == 50 * 40
    for i in range(50):
        rows = memory.history(f"t{i}", limit=1000)
        assert len(rows) == 40
        assert all(c.startswith(f"thread{i}-") for _, c in rows)   # no cross-thread leakage
