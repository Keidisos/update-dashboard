# 🔄 Update Dashboard

Application web conteneurisée pour la gestion des mises à jour de conteneurs Docker et du système d'exploitation sur des hôtes distants.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![React](https://img.shields.io/badge/react-18-61dafb.svg)
![Docker](https://img.shields.io/badge/docker-ready-2496ed.svg)

## ✨ Fonctionnalités

- 🐳 **Gestion des conteneurs Docker**
  - Lister les conteneurs sur des hôtes distants
  - Détecter les mises à jour d'images (comparaison des digests)
  - Mettre à jour les conteneurs **en préservant TOUTE la configuration** (ports, volumes, env, networks, etc.)
  - Rollback automatique en cas d'échec

- 🖥️ **Mises à jour système**
  - Détection des mises à jour OS (Debian, Ubuntu, CentOS, RHEL, Fedora, Alpine)
  - Application des mises à jour via SSH sécurisé

- 🔔 **Notifications Discord**
  - Alertes automatiques lors de la détection de mises à jour
  - Notifications de succès/échec des mises à jour

- 🔐 **Connexions sécurisées**
  - SSH avec clé privée ou mot de passe
  - Docker TCP avec TLS

## 📸 Screenshots

| Dashboard | Containers | System Updates |
|-----------|------------|----------------|
| Vue d'ensemble | Liste et mise à jour | Paquets OS |

## 🚀 Déploiement Rapide

### Prérequis

- Docker et Docker Compose installés sur votre serveur
- Accès SSH ou Docker TCP aux hôtes que vous souhaitez gérer

### Option 1 : Depuis Docker Hub / GHCR

```bash
# Créer un répertoire pour l'application
mkdir update-dashboard && cd update-dashboard

# Télécharger docker-compose.yml
curl -O https://raw.githubusercontent.com/VOTRE_USERNAME/update-dashboard/main/docker-compose.yml

# Créer le fichier .env
cat > .env << EOF
SECRET_KEY=$(openssl rand -base64 32)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/votre-webhook
PORT=8080
EOF

# Lancer l'application
docker compose up -d

# Vérifier que l'application tourne
docker compose logs -f
```

### Option 2 : Build depuis les sources

```bash
# Cloner le dépôt
git clone https://github.com/VOTRE_USERNAME/update-dashboard.git
cd update-dashboard

# Configurer les variables d'environnement
cp .env.example .env
nano .env  # Modifier SECRET_KEY et DISCORD_WEBHOOK_URL

# Builder et lancer
docker compose up -d --build

# Vérifier le statut
docker compose ps
```

## 📋 Configuration

### Variables d'environnement

| Variable | Description | Requis | Défaut |
|----------|-------------|--------|--------|
| `SECRET_KEY` | Clé secrète pour le chiffrement des credentials | ✅ Oui | - |
| `DISCORD_WEBHOOK_URL` | URL du webhook Discord pour les notifications | Non | - |
| `PORT` | Port d'écoute de l'application | Non | `8080` |
| `DEBUG` | Mode debug (true/false) | Non | `false` |

### Génération d'une clé secrète

```bash
# Linux/macOS
openssl rand -base64 32

# ou avec Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Configuration du webhook Discord

1. Ouvrir les paramètres de votre serveur Discord
2. Aller dans **Intégrations** → **Webhooks**
3. Créer un nouveau webhook
4. Copier l'URL et la coller dans `DISCORD_WEBHOOK_URL`

## 🖥️ Déploiement sur un Serveur

### Avec Docker Compose (Recommandé)

```bash
# Sur votre serveur (SSH)
ssh user@votre-serveur

# Installer Docker si nécessaire
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Créer le répertoire
sudo mkdir -p /opt/update-dashboard
cd /opt/update-dashboard

# Créer docker-compose.yml
sudo tee docker-compose.yml > /dev/null << 'EOF'
services:
  update-dashboard:
    image: ghcr.io/VOTRE_USERNAME/update-dashboard:latest
    container_name: update-dashboard
    ports:
      - "8080:8000"
    volumes:
      - ./data:/app/data
      # Optionnel : monter vos clés SSH
      # - ~/.ssh:/app/.ssh:ro
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}
    restart: unless-stopped
EOF

# Créer le fichier .env
sudo tee .env > /dev/null << EOF
SECRET_KEY=$(openssl rand -base64 32)
DISCORD_WEBHOOK_URL=
EOF

# Lancer
sudo docker compose up -d

# Vérifier
sudo docker compose logs -f
```

### Avec un reverse proxy (Nginx + SSL)

```nginx
# /etc/nginx/sites-available/update-dashboard
server {
    listen 80;
    server_name update.votredomaine.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name update.votredomaine.com;

    ssl_certificate /etc/letsencrypt/live/update.votredomaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/update.votredomaine.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Activer le site
sudo ln -s /etc/nginx/sites-available/update-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Obtenir un certificat SSL avec Let's Encrypt
sudo certbot --nginx -d update.votredomaine.com
```

### Avec Traefik (Labels Docker)

```yaml
# docker-compose.yml avec Traefik
services:
  update-dashboard:
    image: ghcr.io/VOTRE_USERNAME/update-dashboard:latest
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.update-dashboard.rule=Host(`update.votredomaine.com`)"
      - "traefik.http.routers.update-dashboard.entrypoints=websecure"
      - "traefik.http.routers.update-dashboard.tls.certresolver=letsencrypt"
      - "traefik.http.services.update-dashboard.loadbalancer.server.port=8000"
    # ... reste de la config
```

## 🔧 Configuration des Hôtes Distants

### Préparer un hôte pour la connexion SSH

```bash
# Sur l'hôte distant
# 1. Créer un utilisateur dédié
sudo useradd -m -s /bin/bash update-manager
sudo usermod -aG docker update-manager

# 2. Configurer l'authentification par clé SSH
sudo mkdir -p /home/update-manager/.ssh
sudo chmod 700 /home/update-manager/.ssh

# 3. Ajouter votre clé publique
echo "votre-cle-publique-ssh" | sudo tee /home/update-manager/.ssh/authorized_keys
sudo chmod 600 /home/update-manager/.ssh/authorized_keys
sudo chown -R update-manager:update-manager /home/update-manager/.ssh
```

### Préparer un hôte pour Docker TCP

```bash
# Sur l'hôte distant - Activer Docker TCP avec TLS
# Voir: https://docs.docker.com/engine/security/protect-access/
```

## 📖 Utilisation

1. **Accéder à l'interface** : `http://votre-serveur:8080`

2. **Ajouter un hôte** :
   - Aller dans "Hosts" → "Add Host"
   - Renseigner le nom, l'adresse IP/hostname
   - Choisir le type de connexion (SSH ou TCP)
   - Configurer les credentials

3. **Gérer les conteneurs** :
   - Sélectionner un hôte dans le menu latéral
   - Aller dans "Containers"
   - Cliquer sur "Check Updates" pour détecter les mises à jour
   - Cliquer sur "Update" pour mettre à jour un conteneur

4. **Mises à jour système** :
   - Aller dans "System"
   - Voir les paquets disponibles
   - Cliquer sur "Update All" pour appliquer

## 🛠️ Développement

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Tests

```bash
# Backend
cd backend
pytest tests/ -v

# Frontend
cd frontend
npm run test
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Update Dashboard                      │
├─────────────────────────────────────────────────────────┤
│  Frontend (React + Vite + TailwindCSS)                  │
│  ├── Dashboard    - Vue d'ensemble                      │
│  ├── Hosts        - Gestion des hôtes                   │
│  ├── Containers   - Liste et mise à jour                │
│  └── System       - Mises à jour OS                     │
├─────────────────────────────────────────────────────────┤
│  Backend (FastAPI + Python 3.12)                        │
│  ├── DockerService    - Gestion conteneurs (⭐ core)    │
│  ├── SSHService       - Connexions SSH                  │
│  ├── RegistryService  - Comparaison digests             │
│  └── NotificationService - Webhooks Discord             │
├─────────────────────────────────────────────────────────┤
│  Database (SQLite)                                       │
│  └── Hosts, UpdateLogs                                   │
└─────────────────────────────────────────────────────────┘
```

## 📄 Licence

MIT License - voir [LICENSE](LICENSE)

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## ⚠️ Avertissement

Cette application effectue des opérations privilégiées (mise à jour de conteneurs, commandes système). Utilisez-la avec précaution et assurez-vous de comprendre les implications de chaque action.
