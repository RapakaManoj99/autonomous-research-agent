from flask import Flask, request, jsonify
import agent as A
import memory

app = Flask(__name__)
_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = A.build_agent()
    return _agent


@app.post("/chat")
def chat():
    data = request.get_json(force=True)
    thread_id, message = data.get("thread_id"), data.get("message")
    if not thread_id or not message:
        return jsonify(error="thread_id and message are required"), 400
    return jsonify(thread_id=thread_id, reply=A.chat(get_agent(), thread_id, message))


@app.get("/history/<thread_id>")
def history(thread_id):
    return jsonify([{"role": r, "content": c} for r, c in memory.history(thread_id, 50)])


if __name__ == "__main__":
    app.run(port=5000)
