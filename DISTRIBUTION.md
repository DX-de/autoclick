# Mettre Auto Clicker Pro en ligne (téléchargement public)

Ce guide explique **comment les gens pourront télécharger** ton app, comme pour n’importe quel logiciel gratuit.

## Vue d’ensemble (3 étapes)

```
1. Créer les .exe / binaires  →  PyInstaller (Windows + Linux)
2. Mettre le code sur GitHub  →  dépôt public ou privé
3. Publier une Release        →  fichiers téléchargeables par tout le monde
```

Les utilisateurs iront sur une page du type :

`https://github.com/TON-UTILISATEUR/autoclick/releases`

et téléchargeront **AutoClickerPro.exe** (Windows) ou **AutoClickerPro** (Linux).

---

## Étape 1 — Créer les fichiers installables

### Sur Windows (chez toi ou sur un PC Windows)

```bat
build_windows.bat
```

Fichier produit : `dist\AutoClickerPro.exe`

### Sur Linux

```bash
bash build_linux.sh
```

Fichier produit : `dist/AutoClickerPro`

**Important :** un `.exe` Windows ne se fabrique **que sur Windows**. Un binaire Linux se fabrique **sur Linux**. Pour tout proposer, il faut builder sur les deux OS (ou utiliser GitHub Actions, voir ci-dessous).

---

## Étape 2 — Mettre le projet sur GitHub

1. Crée un compte sur [https://github.com](https://github.com) si besoin.
2. Crée un nouveau dépôt, par exemple `autoclick`.
3. Dans le dossier du projet :

```bash
cd /home/bastin-romain/autoclick
git init
git add .
git commit -m "Auto Clicker Pro v1.0"
git branch -M main
git remote add origin https://github.com/TON-UTILISATEUR/autoclick.git
git push -u origin main
```

(Remplace `TON-UTILISATEUR` par ton pseudo GitHub.)

---

## Étape 3 — Publier une Release (téléchargement public)

### À la main (simple)

1. Sur GitHub → ton dépôt → **Releases** → **Create a new release**.
2. Tag : `v1.0.0` (exemple).
3. Titre : `Auto Clicker Pro 1.0.0`.
4. Glisse-dépose :
   - `AutoClickerPro.exe` (Windows)
   - `AutoClickerPro` (Linux, éventuellement dans un `.zip`)
5. **Publish release**.

Le lien de téléchargement sera public pour tout le monde.

### Automatique (recommandé)

Le fichier `.github/workflows/release.yml` build **Windows + Linux** à chaque tag :

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub crée la release et attache les exécutables automatiquement.

---

## Autres endroits pour héberger les téléchargements

| Plateforme | Intérêt |
|------------|---------|
| **GitHub Releases** | Gratuit, simple, lien direct, très utilisé |
| **itch.io** | Page de présentation + téléchargement (jeux/outils) |
| **Site perso** | Lien sur ton portfolio ; héberge les fichiers ou redirige vers GitHub |
| **Google Drive / Dropbox** | Possible mais moins pro (pas de versioning) |

Pour commencer, **GitHub Releases suffit** dans 99 % des cas.

---

## Page « Télécharger » pour les visiteurs

Ajoute en haut du `README.md` :

```markdown
## Télécharger

- [Windows (.exe)](https://github.com/TON-UTILISATEUR/autoclick/releases/latest)
- [Linux (binaire)](https://github.com/TON-UTILISATEUR/autoclick/releases/latest)
```

Ou crée une page GitHub Pages (optionnel) avec un bouton « Download ».

---

## Points à connaître avant de publier

1. **Antivirus Windows** : les `.exe` PyInstaller sont parfois signalés à tort. Signer le code (certificat payant) ou documenter que c’est un faux positif.
2. **Licence** : ajoute un fichier `LICENSE` (MIT, GPL, etc.) pour clarifier l’usage.
3. **Avertissement** : les auto-clickers peuvent être interdits sur certains jeux/sites — garde l’avertissement dans le README.
4. **macOS** : non inclus par défaut ; il faudrait builder sur un Mac avec PyInstaller.
5. **Mises à jour** : à chaque nouvelle version, tag `v1.0.1`, `v1.1.0`, etc. et republier une release.

---

## Checklist rapide

- [ ] `build_windows.bat` testé → `.exe` OK
- [ ] `build_linux.sh` testé → binaire OK
- [ ] Dépôt GitHub créé et code poussé
- [ ] Release `v1.0.0` avec les deux fichiers
- [ ] Lien « Télécharger » dans le README
- [ ] (Optionnel) Workflow GitHub Actions activé

Une fois la release publiée, **n’importe qui dans le monde** peut télécharger ton app via le lien GitHub.
