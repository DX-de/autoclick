# GitHub Pages — site de téléchargement

Le dossier `docs/` contient une page vitrine avec boutons de téléchargement.

## URL du site (après activation)

**https://dx-de.github.io/autoclick/**

## Activer GitHub Pages

Sur GitHub : **Settings → Pages → Source : Deploy from branch**
- Branche : `main`
- Dossier : `/docs`

Ou en terminal :

```bash
gh api -X POST repos/DX-de/autoclick/pages \
  -f build_type=legacy \
  -f source[branch]=main \
  -f source[path]=/docs
```

Le site se met à jour automatiquement à chaque push sur `main`.
