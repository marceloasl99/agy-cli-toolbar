import os
import sys
import json
import base64
import hashlib
import secrets
import urllib.request
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

# Default Google OAuth Client ID for Antigravity / Gemini CLI
DEFAULT_CLIENT_ID = "681255809395-oo8ft2oprdrnp9e3aqf6av3hmdib135j.apps.googleusercontent.com"
FALLBACK_CLIENT_ID = "1071006060591-tmhssin2h21lcre235vtolojh4g403ep.apps.googleusercontent.com"
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/cloud-platform"
]

def generate_pkce_pair():
    """Generates code_verifier and code_challenge (S256)."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode('ascii')).digest()
    challenge = base64.urlsafe_b64encode(digest).decode('ascii').rstrip('=')
    return verifier, challenge

def decode_jwt_payload(token):
    """Decodes JWT payload without verifying signature for reading email claims."""
    try:
        parts = token.split('.')
        if len(parts) >= 2:
            payload_b64 = parts[1]
            payload_b64 += '=' * ((4 - len(payload_b64) % 4) % 4)
            return json.loads(base64.urlsafe_b64decode(payload_b64.encode('utf-8')).decode('utf-8'))
    except Exception:
        pass
    return {}

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    auth_code = None
    error = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)

        if "code" in query:
            OAuthCallbackHandler.auth_code = query["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Antigravity - Autenticado com Sucesso</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                    .card { background: #1e293b; padding: 40px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); text-align: center; max-width: 480px; border: 1px solid #334155; }
                    h1 { color: #38bdf8; font-size: 26px; margin-bottom: 12px; }
                    p { color: #94a3b8; font-size: 16px; line-height: 1.5; }
                    .badge { display: inline-block; background: #0369a1; color: #e0f2fe; padding: 6px 14px; border-radius: 9999px; font-size: 14px; font-weight: 600; margin-top: 15px; }
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>Autenticação Concluída!</h1>
                    <p>Sua conta do Google foi conectada com sucesso ao perfil do <strong>Antigravity</strong>.</p>
                    <div class="badge">Pode fechar esta janela e voltar ao terminal.</div>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        elif "error" in query:
            OAuthCallbackHandler.error = query.get("error_description", query["error"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"<h3>Erro na autenticacao: {OAuthCallbackHandler.error}</h3>".encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silence HTTP server logs
        return

def run_browser_oauth(client_id=DEFAULT_CLIENT_ID, client_secret="", port=8085):
    """Runs a local OAuth loopback server and opens the browser for authorization."""
    verifier, challenge = generate_pkce_pair()
    state = secrets.token_hex(16)
    redirect_uri = f"http://localhost:{port}/oauth/callback"

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
        "access_type": "offline",
        "prompt": "consent"
    }

    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

    print(f"\n[*] Iniciando servidor local na porta {port}...")
    try:
        server = HTTPServer(("localhost", port), OAuthCallbackHandler)
    except Exception as e:
        print(f"[!] Porta {port} ocupada, tentando porta {port + 1}...")
        port = port + 1
        redirect_uri = f"http://localhost:{port}/oauth/callback"
        params["redirect_uri"] = redirect_uri
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
        server = HTTPServer(("localhost", port), OAuthCallbackHandler)

    print(f"[*] Abrindo navegador para login Google:")
    print(f"    {auth_url}\n")
    webbrowser.open(auth_url)

    server.handle_request()

    if OAuthCallbackHandler.error:
        raise RuntimeError(f"Erro OAuth: {OAuthCallbackHandler.error}")

    auth_code = OAuthCallbackHandler.auth_code
    if not auth_code:
        raise RuntimeError("Codigo de autorizacao nao recebido.")

    print("[*] Codigo recebido com sucesso! Trocando por tokens...")
    token_url = "https://oauth2.googleapis.com/token"
    token_params = {
        "client_id": client_id,
        "code": auth_code,
        "code_verifier": verifier,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }
    if client_secret:
        token_params["client_secret"] = client_secret

    req_data = urllib.parse.urlencode(token_params).encode('utf-8')
    req = urllib.request.Request(token_url, data=req_data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req) as resp:
            token_json = json.loads(resp.read().decode('utf-8'))
            return token_json
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        raise RuntimeError(f"Falha ao obter tokens ({e.code}): {err_msg}")

def save_credentials_to_profile(profile_gemini_dir, token_data, email=None):
    """Saves oauth_creds.json and google_accounts.json into the profile's .gemini dir."""
    os.makedirs(profile_gemini_dir, exist_ok=True)
    oauth_file = os.path.join(profile_gemini_dir, "oauth_creds.json")
    accounts_file = os.path.join(profile_gemini_dir, "google_accounts.json")

    # Determine email from id_token or parameter
    detected_email = email
    id_tok = token_data.get("id_token")
    if id_tok and not detected_email:
        claims = decode_jwt_payload(id_tok)
        detected_email = claims.get("email")

    if not detected_email:
        detected_email = "user@gmail.com"

    # Structure oauth_creds.json exactly as Antigravity expects
    creds_payload = {
        "access_token": token_data.get("access_token", ""),
        "scope": token_data.get("scope", " ".join(SCOPES)),
        "token_type": token_data.get("token_type", "Bearer"),
        "id_token": token_data.get("id_token", ""),
        "expiry_date": int(token_data.get("expires_in", 3600) * 1000) + int(__import__("time").time() * 1000),
        "refresh_token": token_data.get("refresh_token", "")
    }

    with open(oauth_file, "w", encoding="utf-8") as f:
        json.dump(creds_payload, f, indent=2)

    with open(accounts_file, "w", encoding="utf-8") as f:
        json.dump({"active": detected_email, "old": []}, f, indent=2)

    return detected_email

if __name__ == "__main__":
    print("=== Antigravity Google OAuth Authenticator ===")
    target_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser("~"), ".gemini")
    print(f"Diretorio alvo: {target_dir}")
    try:
        tokens = run_browser_oauth()
        email = save_credentials_to_profile(target_dir, tokens)
        print(f"\n[✓] Autenticacao concluida com sucesso para: {email}")
        print(f"[✓] Credenciais salvas em: {target_dir}")
    except Exception as err:
        print(f"\n[!] Erro: {err}")
        sys.exit(1)
