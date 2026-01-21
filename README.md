# 🔄 Update Dashboard

Dashboard de gestion centralisée pour vos serveurs Docker. Permet de mettre à jour les conteneurs et les paquets système (OS) de vos serveurs distants via une interface web unique.

![Python](https://img.shields.io/badge/backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/frontend-React-61DAFB?style=flat-square&logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/deploy-Docker-2496ED?style=flat-square&logo=docker&logoColor=white)

## ✨ Fonctionnalités

*   📋 **Liste des conteneurs** multi-hôtes
*   🚀 **Mise à jour des conteneurs** (pull + recreate) en préservant toute la configuration (env, ports, volumes...)
*   📦 **Mises à jour Système** (apt/yum) via SSH
*   🔔 **Notifications Discord**
*   🔐 **Sécurisé** (Clés SSH chiffrées en base de données)

---

## 🛠️ Installation (Serveur Dashboard)

Ce serveur hébergera l'interface web.

### 1. Télécharger le projet
```bash
git clone https://github.com/Keidisos/update-dashboard.git
cd update-dashboard
```

### 2. Configuration
Créez le fichier de configuration :
```bash
mkdir -p data
cp .env.example .env
```
Ouvrez le fichier `.env` et modifiez au moins `SECRET_KEY` (utilisé pour chiffrer vos clés SSH dans la base de données).

### 3. Démarrer
```bash
docker compose up -d --build
```

L'application est accessible sur : **http://votre-ip:8081**

---

## 🔗 Connecter un Serveur Distant

Pour piloter un serveur distant, vous devez préparer un accès SSH dédié.

**Sur le serveur distant à monitorer**, exécutez ces commandes :

### 1. Créer l'utilisateur "update-manager"
```bash
# Créer l'utilisateur
sudo useradd -m -s /bin/bash update-manager

# L'ajouter au groupe docker (pour gérer les conteneurs)
sudo usermod -aG docker update-manager
```

### 2. Configurer les droits Sudo (pour les mises à jour système)
Pour que le dashboard puisse lancer `apt-get` ou `apt` sans mot de passe :

```bash
echo "update-manager ALL=(ALL) NOPASSWD: /usr/bin/apt-get, /usr/bin/apt" | sudo tee /etc/sudoers.d/update-manager
sudo chmod 440 /etc/sudoers.d/update-manager
```

### 3. Installer la clé SSH

Cette étape se fait en deux temps : générer une clé, et l'installer sur le serveur distant.

**A. Sur votre PC ou le Serveur Dashboard (Génération de la clé)**
```bash
# Générer la clé (appuyez sur Entrée pour ne pas mettre de passphrase)
ssh-keygen -t ed25519 -C "update-dashboard" -f ./dashboard-key -q -N ""

# Afficher la clé PRIVÉE (à copier dans le dashboard plus tard)
cat ./dashboard-key

# Afficher la clé PUBLIQUE (à copier sur le serveur distant)
cat ./dashboard-key.pub
```

**B. Sur le Serveur Distant (Installation de la clé publique)**

```bash
# 1. Créer le dossier .ssh pour l'utilisateur
mkdir -p /home/update-manager/.ssh

# 2. Créer le fichier authorized_keys
nano /home/update-manager/.ssh/authorized_keys
# (🔴 COLLEZ ICI LE CONTENU DE VOTRE CLÉ PUBLIQUE 'dashboard-key.pub')
# (Sauvegardez avec Ctrl+O, Entrée, Ctrl+X)

# 3. Définir les bonnes permissions et le propriétaire (CRITIQUE)
chmod 700 /home/update-manager/.ssh
chmod 600 /home/update-manager/.ssh/authorized_keys
chown -R update-manager:update-manager /home/update-manager/.ssh
```

### 4. Ajouter dans le Dashboard
1. Allez sur le dashboard web (**http://votre-ip:8081**)
2. Menu **Hosts** > **Add Host**
3. Remplissez :
   *   **Username**: `update-manager`
   *   **SSH Key**: Collez votre **CLÉ PRIVÉE** correspondante (dashboard-key.pub)
4. Sauvegardez. La connexion doit passer au vert.
