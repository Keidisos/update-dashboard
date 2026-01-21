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
curl -O https://raw.githubusercontent.com/Keidisos/update-dashboard/main/docker-compose.yml

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
git clone https://github.com/Keidisos/update-dashboard.git
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

## 🖥️ Guide de Déploiement

### 1. Installation sur votre serveur (Hôte Dashboard)

Ce serveur hébergera l'interface web **Update Dashboard**.

**Prérequis :** Docker et Docker Compose installés (`curl -fsSL https://get.docker.com | sh`).

```bash
# 1. Créer le répertoire du projet
mkdir -p /opt/update-dashboard
cd /opt/update-dashboard

# 2. Créer le fichier docker-compose.yml
cat <<EOF > docker-compose.yml
services:
  update-dashboard:
    image: ghcr.io/keidisos/update-dashboard:latest
    container_name: update-dashboard
    ports:
      - "8081:8000"  # Port accessible : 8081 (modifiable)
    volumes:
      - ./data:/app/data
    environment:
      - SECRET_KEY=$(openssl rand -base64 32)
      # - DISCORD_WEBHOOK_URL=https://discord.com/... (optionnel)
    restart: unless-stopped
EOF

# 3. Lancer l'application
docker compose up -d

# 4. Vérifier les logs
docker compose logs -f
```

L'interface sera accessible sur `http://votre-ip:8081`.

---

## 🔧 Configuration des Hôtes Distants (SSH)

Pour que **Update Dashboard** puisse gérer un serveur distant (lister les conteneurs, mises à jour OS), vous devez configurer un accès SSH.

### Étape 1 : Créer un utilisateur dédié sur l'hôte distant

Connectez-vous à votre serveur **déjà existant** (celui que vous voulez monitorer) et exécutez :

```bash
# 1. Créer l'utilisateur 'update-manager'
sudo useradd -m -s /bin/bash update-manager

# 2. L'ajouter au groupe docker (pour gérer les conteneurs)
sudo usermod -aG docker update-manager

# 3. Configurer les permissions sudo pour les mises à jour système (apt/yum) sans mot de passe
# Ceci est CRITIQUE pour que le module "System Updates" fonctionne
echo "update-manager ALL=(ALL) NOPASSWD: /usr/bin/apt-get, /usr/bin/apt" | sudo tee /etc/sudoers.d/update-manager

# 4. Sécuriser le fichier sudoers
sudo chmod 440 /etc/sudoers.d/update-manager
```

### Étape 2 : Mettre en place la clé SSH

Vous devez générer une paire de clés SSH (sur votre machine personnelle ou le serveur dashboard) et fournir la **clé privée** à l'application.

```bash
# 1. Générer une paire de clés (si vous n'en avez pas)
ssh-keygen -t ed25519 -C "update-dashboard" -f ./dashboard-key -q -N ""

# 2. Copier la clé PUBLIQUE sur l'hôte distant
# Remplacer 'user@remote-host' par votre accès root ou admin actuel
ssh-copy-id -i ./dashboard-key.pub update-manager@votre-serveur-distant

# OU manuellement si ssh-copy-id n'est pas dispo :
# Sur le serveur distant :
# sudo mkdir -p /home/update-manager/.ssh
# echo "CONTENU_DE_DASHBOARD_KEY.PUB" | sudo tee /home/update-manager/.ssh/authorized_keys
# sudo chown -R update-manager:update-manager /home/update-manager/.ssh
# sudo chmod 700 /home/update-manager/.ssh
# sudo chmod 600 /home/update-manager/.ssh/authorized_keys
```

### Étape 3 : Ajouter l'hôte dans Update Dashboard

1. Allez sur **http://votre-serveur:8081**
2. Cliquez sur **Add Host**
3. Remplissez le formulaire :
   - **Name**: Nom de votre serveur (ex: `Prod-Database`)
   - **Hostname/IP**: IP du serveur distant
   - **Type**: `SSH`
   - **Username**: `update-manager`
   - **SSH Key**: Collez le contenu de votre **clé PRIVÉE** (`cat ./dashboard-key`)
   - **SSH Password**: Laisser vide (on utilise la clé)
4. Cliquez sur **Save**

Le statut devrait passer à **Connected** 🟢. Vous pouvez maintenant gérer les conteneurs et voir les mises à jour système !

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
