from flask import Flask, request, render_template
import asyncio
from know_client import run_agent

# Tell Flask to look inside "know/template" folder for HTML files
app = Flask(__name__, template_folder='template')

@app.route("/", methods=["GET"])
def index():
      return render_template("index.html")  # ✅ just "index.html"

@app.route("/ask", methods=["POST"])
def ask():
      query = request.form["query"]
      try:
            response = asyncio.run(run_agent(query))
            return render_template("index.html", response=response, query=query)
      except Exception as e:
            return render_template("index.html", response=f"Error: {str(e)}", query=query)

if __name__ == "__main__":
      app.run(debug=True)
