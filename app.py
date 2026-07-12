from flask import Flask, Response

app = Flask(__name__)

DISABLED_MESSAGE = "This project deployment has been disabled by the repository owner."

@app.route("/")
def index():
    return Response(
        """<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Deployment Disabled</title>
<style>body{font-family:Arial,sans-serif;background:#111827;color:#f9fafb;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}.box{max-width:680px;padding:32px;border:1px solid #374151;border-radius:16px;background:#1f2937}h1{margin-top:0;color:#fca5a5}p{line-height:1.5;color:#d1d5db}</style></head>
<body><main class="box"><h1>Deployment Disabled</h1><p>This visitor notification system has been disabled by the repository owner.</p><p>No original app functions are available from this deployment.</p></main></body></html>""",
        mimetype="text/html",
    )

@app.route("/health")
def health():
    return {"status": "disabled"}, 410

@app.errorhandler(404)
def not_found(_error):
    return Response(DISABLED_MESSAGE, status=410, mimetype="text/plain")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
