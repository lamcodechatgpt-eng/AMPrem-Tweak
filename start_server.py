import http.server
import socketserver
import socket
import sys

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

PORT = 8000

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Prevent caching so you always get the latest IPA
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        super().end_headers()

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

ip = get_ip()
print("="*50)
print(f"SERVER STARTED!")
print(f"Go to Safari on your iPhone and open:")
print(f"http://{ip}:{PORT}/")
print(f"")
print(f"Download 'AlightMotion_Premium_v23.ipa'")
print("="*50)

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
