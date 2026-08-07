# Guide utilisateur — Topnet APM

Plateforme de gestion du patrimoine applicatif (Application Portfolio Management) pour la DSI Topnet.

## 1. Accès et connexion

1. Ouvrir l’URL de la plateforme (ex. `http://localhost:8000/`).
2. Se connecter avec identifiant + mot de passe.
3. Optionnel : onglet **Visage** si un identifiant facial a été enregistré dans le profil.
4. Mot de passe oublié : lien **Mot de passe oublié** sur la page de connexion.

Après connexion, une notification système est créée (une par jour maximum) et un toast de bienvenue s’affiche.

## 2. Rôles et droits

| Rôle | Acteur | Droits principaux |
|------|--------|-------------------|
| Administrateur DSI (`admin` / `dsi`) | Administrateur DSI | Utilisateurs, rôles, import/export CSV, paramètres globaux, CRUD patrimoine |
| Équipe DSI / Technicien (`manager`) | Technicien | CRUD patrimoine, tableaux de bord ; lecture de la liste utilisateurs |
| Lecteur (`viewer`) | Consultation | Lecture seule |

Le menu **Utilisateurs** et **Paramètres** n’apparaît que pour les profils autorisés.

## 3. Accueil et analyses

### Accueil (`/`)
- Score de santé SI (incidents + échéances).
- KPI : taux en production, pression échéances 30 j, incidents, apps critiques.
- Répartition des applications, horizon SSL, tendances 6 mois.
- Tableau des prochaines échéances (60 jours).
- Accès rapides vers certificats, incidents, documents, analyses.

### Analyses (`/dashboard/`)
Graphiques détaillés (statut apps, criticité, incidents, documents, SSL, contrats, tendances).

## 4. Catalogue SI

### Applications
1. Menu **Applications** → **Nouvelle application** (si droit d’écriture).
2. Renseigner nom, description, criticité, statut, dates, technologies.
3. Consulter la fiche pour environnements, docs et liens associés.
4. Archiver via le bouton d’archivage (soft-delete).

### Technologies
Référentiel technique (langages, BDD, frameworks…) lié aux applications.

### Dépendances
Cartographie App → App ou App → cible externe (AD, PostgreSQL, API…).

## 5. Infrastructure

### Environnements
Types : **DEV**, **RECETTE**, **PREPROD**, **PROD** (un type unique par application).  
Champs : URL, IP, OS, CPU/RAM, Docker/Kubernetes, serveur hébergeur.

### Serveurs
Inventaire Physique / VM / Cloud (IP, datacenter, ressources).

## 6. Ressources critiques

### Certificats SSL
- Créer un certificat (CN, type, CA, dates, app/env/domaine).
- Suivre le statut : Valide / Bientôt expiré / Expiré / Révoqué.
- Les alertes Celery mettent à jour le statut et notifient les managers.

### Domaines
- FQDN, registrar, DNS, dates, application/environnement.
- **Renouvellement automatique** : case à cocher sur le formulaire.
- Badge **Auto-renew** visible dans la liste.

### Fournisseurs & Contrats
Contrats de maintenance / support / licence / hébergement / SLA, liés à un fournisseur et éventuellement une application.

## 7. Documentation

1. Menu **Documents** → déposer un fichier.
2. Catégories : Architecture, Manuel utilisateur, Manuel exploitation, Contrat, Procédure.
3. Tags pour la recherche.
4. Lier le document à une application.

## 8. Incidents & notifications

- **Incidents** : déclarer un incident majeur (impact, cause, solution, statut).
- **Notifications** : alertes d’échéance, incidents, connexions ; badge non lu dans le menu.
- Marquer comme lue depuis la fiche notification.

## 9. Utilisateurs (Administrateur DSI)

### Créer un compte
**Utilisateurs** → **Nouvel utilisateur** → rôle, email, mot de passe.

### Exporter CSV
Bouton **Exporter CSV** (respecte les filtres recherche / rôle / statut).

Colonnes : `username,email,first_name,last_name,role,phone,department,is_active,password`

### Importer CSV
1. **Importer CSV**.
2. Choisir un fichier `.csv` (UTF-8).
3. Même `username` → mise à jour ; sinon création (email + password obligatoires).

Rôles acceptés : `admin`, `dsi`, `manager` / `technicien`, `viewer` / `lecteur`.

## 10. Paramètres globaux (Administrateur DSI)

Menu **Paramètres** (`/settings/`) :
- Seuil alerte J-60
- Seuil alerte J-30
- Alerte le jour d’expiration (J-0)
- Délai anti-doublon

Ces valeurs sont utilisées par la tâche Celery quotidienne `check_expiring_resources`.

## 11. Journal d’audit

Menu **Audit** : historique des actions (création, modification, archivage, connexion…).  
Couvre notamment : applications, environnements, serveurs, certificats, domaines, contrats, utilisateurs, documents, incidents, dépendances, login/logout.

## 12. Thème

Bouton **Clair / Sombre** dans la barre supérieure (préférence stockée localement).

## 13. Profil

Menu utilisateur (avatar) → **Mon profil** : identité, mot de passe, enrollment facial.  
**Déconnexion** depuis le même menu.

---

*Document livrable stage APM Topnet — guide utilisateur fonctionnel.*
