from flask import Flask, render_template, request
import asyncio
from scraper.capture import capture_screenshot
from urllib.parse import urlparse

app = Flask(__name__)

def validate_and_correct_url(url: str) -> str:
    if not urlparse(url).scheme:
        # ถ้าไม่มี schema เพิ่ม "http://"
        url = f"http://{url}"
    return url

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        screenshot_path = asyncio.run(capture_screenshot(url))
        if not screenshot_path:
            # flash("Unable to capture screenshot. The page took too long to load.", "error")
            return render_template("index.html")
        return render_template("index.html", screenshot=screenshot_path, url=url)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=9000)
