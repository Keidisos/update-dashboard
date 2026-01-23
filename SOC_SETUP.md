# SOC System - Setup Guide

## 🚀 Démarrage rapide

### 1. Lancer Ollama avec le modèle CyberLLM

```bash
# 1. Démarrer les services (avec Ollama)
cd /docker/update-dashboard
docker compose up -d

# 2. Vérifier qu'Ollama est démarré
docker ps | grep ollama

# 3. Télécharger le modèle de base llama3.1:8b
docker exec -it update-dashboard-ollama ollama pull llama3.1:8b

# 4. Créer le modèle custom CyberLLM
docker exec -it update-dashboard-ollama ollama create cybersec -f /app/ollama/Modelfile_cybersec

# 5. Vérifiern que le modèle est créé
docker exec -it update-dashboard-ollama ollama list
```

Vous devriez voir `cybersec` dans la liste des modèles !

---

## 🔍 Tester le SOC

### Vérifier la connexion Ollama

```bash
curl http://localhost:8080/api/v1/soc/health
```

### Lancer une analyse manuelle

```bash
# via curl
curl -X POST http://localhost:8080/api/v1/soc/analyze/1

# via UI
# Allez sur http://localhost:8080 et naviguez vers SOC
```

### Voir les incidents détectés

```bash
curl http://localhost:8080/api/v1/soc/incidents
```

### Obtenir les statistiques

```bash
curl http://localhost:8080/api/v1/soc/stats
```

---

## 🎯 Ce qui est analysé

Le SOC collecte et analyse :

- ✅ **auth.log** : Tentatives de connexion SSH
- ✅ Détection de **brute-force**
- ✅ Connexions depuis IPs inhabituelles
- ✅ Escalades de privilèges
- ✅ Commandes sudo suspectes

## 📊 Données renvoyées par l'IA

L'IA CyberLLM retourne pour chaque analyse :

- **Severity** : low, medium, high, critical
- **Threat type** : brute_force, ssh_intrusion, etc.
- **Description** détaillée technique
- **Recommendations** de remédiation
- **MITRE ATT&CK** techniques (T1078, T1110, etc.)
- **IPs sources** suspectes
- **Utilisateurs** affectés

---

## ⚙️ Configuration

Dans `.env` :

```env
# SOC Configuration
SOC_ENABLED=true
SOC_ANALYSIS_INTERVAL=10     # minutes entre chaque analyse auto
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=cybersec
```

---

## 🐛 Troubleshooting

### Ollama ne répond pas

```bash
# Vérifier les logs
docker logs update-dashboard-ollama

# Redémarrer
docker compose restart ollama
```

### Le modèle n'existe pas

```bash
# Recréer le modèle
docker exec -it update-dashboard-ollama ollama create cybersec -f /app/ollama/Modelfile_cybersec
```

### Pas assez de RAM

Le modèle llama3.1:8b nécessite ~8GB de RAM. Si vous n'avez pas assez :

```bash
# Utiliser un modèle plus léger
docker exec -it update-dashboard-ollama ollama pull llama3.2

# Modifier le Modelfile pour utiliser llama3.2 au lieu de llama3.1:8b
```

---

## 🎨 Prochaines étapes

- [ ] Page dashboard SOC UI (Phase 1 complete)
- [ ] Collecte logs containers Docker
- [ ] Analyse de logs multiples sources
- [ ] Corrélation d'événements
- [ ] Notifications Discord pour incidents critiques
