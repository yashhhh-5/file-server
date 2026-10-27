
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from email.parser import BytesParser
from email.policy import default
import os

UPLOAD_DIR = "received_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class FileHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Phone Transfer</title>
        </head>
        <body style="font-family:Arial;max-width:500px;margin:40px auto;padding:15px">
            <h2>📱 Phone → Laptop</h2>
            <p>Select photos, videos, or documents to transfer.</p>
            <form method="POST" enctype="multipart/form-data">
                <input type="file" name="files" multiple required>
                <br><br>
                <button type="submit">Upload Files</button>
            </form>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        try:
            content_type = self.headers.get("Content-Type", "")
            if not content_type.lower().startswith("multipart/form-data"):
                self.send_error(400, "Expected a file upload")
                return

            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                self.send_error(400, "No upload data received")
                return

            # Parse the multipart request without the removed cgi module.
            headers = (
                f"Content-Type: {content_type}\r\n"
                "MIME-Version: 1.0\r\n\r\n"
            ).encode("utf-8")

            message = BytesParser(policy=default).parsebytes(
                headers + self.rfile.read(length)
            )

            saved = 0

            for part in message.iter_parts():
                if part.get_param("name", header="content-disposition") != "files":
                    continue

                filename = part.get_filename()
                if not filename:
                    continue

                filename = os.path.basename(filename.replace("\\", "/"))
                if filename in ("", ".", ".."):
                    continue

                data = part.get_payload(decode=True)
                if data is None:
                    continue

                base, ext = os.path.splitext(filename)
                destination = os.path.join(UPLOAD_DIR, filename)
                counter = 1

                # Avoid overwriting files with the same name.
                while os.path.exists(destination):
                    destination = os.path.join(
                        UPLOAD_DIR, f"{base}_{counter}{ext}"
                    )
                    counter += 1

                with open(destination, "wb") as output:
                    output.write(data)

                print(f"Received: {destination} ({len(data)} bytes)")
                saved += 1

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                f"<h2>Uploaded {saved} file(s) successfully!</h2>"
                '<a href="/">Upload more files</a>'.encode("utf-8")
            )

        except Exception as error:
            print("Upload error:", error)
            self.send_error(500, "Upload failed. Check the laptop terminal.")


server = ThreadingHTTPServer(("0.0.0.0", 8000), FileHandler)

print("Server running on port 8000")
print("Open your laptop's local IP address on your phone.")
print("Keep this terminal open during transfers.")

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nServer stopped.")
    server.server_close()