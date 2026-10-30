---

## 2. Organisation du code selon ton diagramme

Pour que ton code reflète fidèlement la logique de ton diagramme, tu peux structurer ton script avec des fonctions et des boucles :
* **Un menu principal** : Qui affiche les options du diagramme (Mode automatique / Mode manuel).
* **Une fonction de nettoyage générique** : Elle prend un dossier en paramètre, boucle sur ses éléments avec `os.listdir()`, vérifie avec `os.path.isfile()` et supprime avec `os.remove()`[cite: 1]. N'oublie pas d'utiliser un bloc `try...except` pour attraper les erreurs quand un fichier est verrouillé par le système.
* **Les instructions finales** : Afficher le message de fin (corbeille, paramètres Windows, etc.) comme indiqué tout en bas de ton schéma.

---

## 3. Vérification et demande des privilèges Administrateur

Pour détecter si ton script s'exécute en mode normal ou administrateur (nécessaire pour `C:\Windows\Prefetch`), tu peux utiliser le module natif `ctypes` de Python. 

Voici comment l'intégrer au tout début de ton script avant d'afficher quoi que ce soit dans le terminal :

```python
import ctypes
import sys


def est_admin():
  try:
    return ctypes.windll.shell32.IsUserAnAdmin()
  except:
    return False


# Vérification avant d'afficher le menu
if not est_admin():
  print("Attention : Le programme tourne en mode 'normale' (pas en admin).")
  print("Le dossier Prefetch ne pourra pas être nettoyé.")
  input(
      "Appuyez sur [ENTRÉE] pour redémarrer le programme en mode Administrateur..."
  )

  # Demande l'élévation des privilèges à l'utilisateur via Windows (UAC)
  ctypes.windll.shell32.ShellExecuteW(
      None, "runas", sys.executable, " ".join(sys.argv), None, 1
  )
  sys.exit()

print("Mode Administrateur détecté ! Lancement du programme...")
# Ici, tu peux lancer la suite de ton code (ton menu principal)