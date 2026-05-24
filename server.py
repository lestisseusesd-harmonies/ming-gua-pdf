# -*- coding: utf-8 -*-
"""
Service HTTP minimal qui génère la fiche Ming Gua en PDF.
Tourne dans le conteneur Cloudflare. Aucune dépendance hors reportlab/Pillow.

Endpoints :
  GET  /health                      -> 200 "ok"
  GET  /pdf?gua=&prenom=&sexe=&naissance=   -> application/pdf

Sécurité : seul le Worker Cloudflare doit appeler ce service (réseau interne au
conteneur). Validation stricte des entrées. Pas d'exécution de contenu utilisateur.
"""
import os, re, json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import generate_fiche

GUAS_VALIDES = {1, 2, 3, 4, 6, 7, 8, 9}
PORT = int(os.environ.get("PORT", "8080"))

def _clean_prenom(s):
    s = (s or "").strip()[:40]
    # Lettres (accents), espaces, traits d'union, apostrophes uniquement
    s = re.sub(r"[^\w\s\-']", "", s, flags=re.UNICODE)
    return s or "toi"

def _clean_naissance(s):
    s = (s or "").strip()[:40]
    return re.sub(r"[^\w\s\-/]", "", s, flags=re.UNICODE) or None

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # silence
        pass

    def _send(self, code, body, ctype="text/plain; charset=utf-8", headers=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/health":
            return self._send(200, b"ok")
        if u.path != "/pdf":
            return self._send(404, b"not found")

        q = parse_qs(u.query)
        try:
            gua = int(q.get("gua", ["0"])[0])
        except ValueError:
            gua = 0
        if gua not in GUAS_VALIDES:
            return self._send(400, json.dumps({"error": "gua invalide"}).encode(),
                              "application/json")
        prenom = _clean_prenom(q.get("prenom", [""])[0])
        sexe = q.get("sexe", ["femme"])[0]
        sexe = "homme" if sexe == "homme" else "femme"
        naissance = _clean_naissance(q.get("naissance", [""])[0])

        try:
            pdf = generate_fiche.generer_bytes(gua, prenom, naissance, sexe=sexe)
        except Exception as e:
            return self._send(500, json.dumps({"error": str(e)}).encode(), "application/json")

        fname = f"Fiche_MingGua_{gua}_{prenom}.pdf".replace(" ", "_")
        return self._send(200, pdf, "application/pdf",
                          {"Content-Disposition": f'inline; filename="{fname}"',
                           "Cache-Control": "no-store"})

if __name__ == "__main__":
    print(f"PDF service en écoute sur :{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
