import os

dossier = r"C:\Windows\Temp"
fichiers = os.listdir(dossier)
for numero, fichier in enumerate(fichiers, start=1):
    print(f"{numero}. {fichier}")

if os.path.exists(r"C:\Windows\Prefetch"):  #[cite: 1]
  print("Le dossier Prefetch existe.")
else:
  print("Le dossier Prefetch n'existe pas.")
