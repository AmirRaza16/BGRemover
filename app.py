from flask import Flask, request, jsonify, send_file, render_template
from rembg import remove
from PIL import Image, ImageFilter
import os
import io
import zipfile
from threading import Lock

app = Flask(__name__)
output_files = {}  # Store processed file buffers for each client
lock = Lock()

# Hardcoded alpha threshold
ALPHA_THRESHOLD = 200

@app.route("/")
def index():
    return render_template("index.html")

def remove_and_sharpen_background(image_data, background_color):
    try:
        # Remove the background
        output_data = remove(image_data)

        # Load the image without background
        img = Image.open(io.BytesIO(output_data)).convert("RGBA")

        # Clean the alpha channel to remove black edges
        r, g, b, a = img.split()  # Separate channels

        # Enhance the alpha channel to make edges sharp
        alpha = a.point(lambda p: 255 if p > ALPHA_THRESHOLD else 0)
        img.putalpha(alpha)

        smoothed_alpha = alpha.filter(ImageFilter.GaussianBlur(radius=1))  # Adjust `radius` for smoother edges
        img.putalpha(smoothed_alpha)  # Replace the alpha channel with the refined one

        # Create a background image with the specified color
        background = Image.new("RGBA", img.size, background_color)

        # Composite the image onto the background using the alpha channel
        combined = Image.alpha_composite(background, img)

        # Save the processed image to a BytesIO buffer
        output_buffer = io.BytesIO()
        combined.save(output_buffer, format="PNG")
        output_buffer.seek(0)

        return output_buffer
    except Exception as e:
        raise ValueError(f"Error processing image: {e}")

@app.route("/process", methods=["POST"])
def process():
    if "images" not in request.files:
        return jsonify({"error": "No images uploaded"}), 400

    images = request.files.getlist("images")
    color_r = int(request.form.get("color_r", 255))
    color_g = int(request.form.get("color_g", 255))
    color_b = int(request.form.get("color_b", 255))
    color_alpha = int(request.form.get("alpha", 0))
    background_color = (color_r, color_g, color_b, color_alpha)

    client_id = request.form.get("client_id", "default")

    # Create a zip buffer for the processed images
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for image in images:
            if image.filename == "":
                continue
            image_data = image.read()
            processed_image = remove_and_sharpen_background(image_data, background_color)
            zip_file.writestr(f"processed_{image.filename}", processed_image.getvalue())

    zip_buffer.seek(0)

    # Store the zip file in memory for the client
    with lock:
        output_files[client_id] = zip_buffer
    return jsonify({"client_id": client_id})


@app.route("/download/<client_id>")
def download(client_id):
    with lock:
        if client_id not in output_files:
            return jsonify({"error": "File not found"}), 404

        # Duplicate the buffer for safe reuse
        zip_buffer = io.BytesIO(output_files[client_id].getvalue())

    return send_file(zip_buffer, mimetype="application/zip", as_attachment=True, download_name="processed_images.zip")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 if no PORT is specified
    app.run(host="0.0.0.0", port=port)
