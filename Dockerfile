# Utilisation d'une image Python officielle avec Alpine pour réduire la taille
FROM python:3.11-alpine AS base

# Labels pour la documentation
LABEL org.opencontainers.image.title="AI Tournament Service"
LABEL org.opencontainers.image.description="Service de génération de planning de tournois avec IA"
LABEL org.opencontainers.image.authors="AI Tournament Team <team@ai-tournament.com>"
LABEL org.opencontainers.image.source="https://github.com/aminataCmd/ai-tournament-service"
LABEL org.opencontainers.image.version="1.0.0"

# Arguments non sensibles
ARG ENVIRONMENT=production
ARG CORS_ORIGIN=http://localhost:3000
ARG TRUSTED_HOSTS=localhost,127.0.0.1


# Installation des dépendances système nécessaires
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    && rm -rf /var/cache/apk/*

# Définition du répertoire de travail
WORKDIR /app

# Copie des fichiers de dépendances
COPY requirements.txt pyproject.toml ./

# Installation des dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage de développement pour les tests
FROM base AS development

# Installation des dépendances de développement
RUN pip install --no-cache-dir pytest pytest-cov pytest-mock black isort flake8 mypy bandit safety

# Copie du code source
COPY . .

# Variables d'environnement pour le développement
ENV ENVIRONMENT=development \
    CORS_ORIGIN=http://localhost:3000 \
    TRUSTED_HOSTS=localhost,127.0.0.1

# Exposition du port (8003 par défaut, sera configuré via la variable PORT)
EXPOSE 8003

# Commande par défaut pour le développement
CMD ["python", "main.py"]

# Stage de production
FROM base AS production

# Création d'un utilisateur non-root pour la sécurité
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# Copie du code source
COPY . .

# Changement des permissions
RUN chown -R appuser:appgroup /app

# Passage à l'utilisateur non-root
USER appuser

# Exposition du port (8003 par défaut, sera configuré via la variable PORT)
EXPOSE 8003

# Variables d'environnement pour la production
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Variables d'environnement non sensibles
ENV ENVIRONMENT=$ENVIRONMENT \
    CORS_ORIGIN=$CORS_ORIGIN \
    TRUSTED_HOSTS=$TRUSTED_HOSTS

# Commande de démarrage pour la production
CMD ["python", "main.py"]
