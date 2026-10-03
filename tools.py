"""Five tools: calculator, wikipedia, arxiv, weather, fetch_url.
Security: AST-only calculator (no eval) and an HTTPS domain allowlist for every outbound call."""
import ast
import operator
from urllib.parse import urlparse, quote
import requests

# ---------------- safe calculator ----------------
_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod, ast.Pow: operator.pow}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("Exponent too large")
        return _BIN[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_eval(node.operand))
    raise ValueError(f"Disallowed expression element: {type(node).__name__}")


def safe_calculate(expression: str) -> float:
    if len(expression) > 200:
        raise ValueError("Expression too long")
    return _eval(ast.parse(expression.strip(), mode="eval"))


# ---------------- allowlisted HTTP ----------------
ALLOWED_DOMAINS = {
    "en.wikipedia.org",
    "export.arxiv.org",
    "api.open-meteo.com",
    "geocoding-api.open-meteo.com",
}


def is_allowed(url: str) -> bool:
    try:
        p = urlparse(url)
        return (p.scheme == "https" and p.hostname in ALLOWED_DOMAINS
                and p.username is None and p.password is None
                and p.port in (None, 443))
    except Exception:
        return False


def safe_get(url: str, params=None, max_chars=4000) -> str:
    if not is_allowed(url):
        raise PermissionError(f"Blocked by allowlist: {url}")
    # redirects disabled so an allowed host cannot bounce us to an internal address
    r = requests.get(url, params=params, timeout=10, allow_redirects=False,
                     headers={"User-Agent": "research-agent/1.0"})
    r.raise_for_status()
    return r.text[:max_chars]


# ---------------- tool functions (wrapped for LangGraph in agent.py) ----------------
def calculator(expression: str) -> str:
    """Evaluate an arithmetic expression such as '(12.5 * 4) / 3 + 2**5'."""
    try:
        return str(safe_calculate(expression))
    except Exception as e:
        return f"Calculator error: {e}"


def wikipedia_search(query: str) -> str:
    """Get a short Wikipedia summary for a topic."""
    try:
        return safe_get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(query.replace(' ', '_'))}")
    except Exception as e:
        return f"Wikipedia error: {e}"


def arxiv_search(query: str) -> str:
    """Search arXiv for recent papers on a topic (returns Atom XML snippet)."""
    try:
        return safe_get("https://export.arxiv.org/api/query",
                        params={"search_query": f"all:{query}", "max_results": 3})
    except Exception as e:
        return f"arXiv error: {e}"


def weather(city: str) -> str:
    """Current weather for a city."""
    try:
        import json
        geo = json.loads(safe_get("https://geocoding-api.open-meteo.com/v1/search",
                                  params={"name": city, "count": 1}))
        if not geo.get("results"):
            return "City not found"
        g = geo["results"][0]
        return safe_get("https://api.open-meteo.com/v1/forecast",
                        params={"latitude": g["latitude"], "longitude": g["longitude"],
                                "current_weather": "true"})
    except Exception as e:
        return f"Weather error: {e}"


def fetch_url(url: str) -> str:
    """Fetch text from an https URL. Only allowlisted domains work."""
    try:
        return safe_get(url)
    except Exception as e:
        return f"Fetch error: {e}"
