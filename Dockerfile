# Service de génération de la fiche Ming Gua (PDF 9 pages)
# Image pour Cloudflare Containers (ou tout hôte Docker).
FROM python:3.11-slim

# Polices : Noto Serif CJK (caractères chinois, traditionnel) + DejaVu (corps)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        fonts-noto-cjk \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code + données + polices bundlées (assets, data, fonts)
COPY . .

ENV PORT=8080
EXPOSE 8080

# Vérifie au build que les polices et la génération fonctionnent
RUN python -c "import generate_fiche; generate_fiche.generer_bytes(1, 'Test'); print('build self-test OK')"

CMD ["python", "server.py"]
