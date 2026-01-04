# <img src="assets/images/logominipython.png" width="50" height="50"> MiniPython

Un interpréteur simple pour le langage **MiniPython**, développé en Python. Ce projet permet d'analyser lexicalement et syntaxiquement du code MiniPython, de générer un Arbre Syntaxique Abstrait (AST) et d'exécuter le code.

## Objectifs
Ce projet a pour but de :
- Comprendre le fonctionnement d'un analyseur lexical et syntaxique.
- Manipuler des Arbres Syntaxiques Abstraits (AST).
- Implémenter un interpréteur capable d'exécuter des scripts simples.
- Fournir une visualisation graphique de l'AST.

## Spécifications du Langage

Le langage MiniPython supporte les fonctionnalités suivantes :

- **Types de données** : `int`, `float`, `bool`, `string`.
- **Structures de données** : Tableaux (e.g., `int T[10]`, `float M[2][3]`).
- **Affectations** : `=` (e.g., `x = 3;`).
- **Opérateurs arithmétiques** : `+`, `-`, `*`, `/` et parenthèses `()`.
- **Opérateurs booléens** : `&&` (ET), `||` (OU), `!` (NON).
- **Comparaisons** : `<`, `>`, `==`, `!=`, `<=`, `>=`.
- **Structures de contrôle** :
  - `if (condition) { ... } else { ... }`
  - `while (condition) { ... }`
- **Entrées/Sorties** : `print(expression);`.
- **Commentaires** : `/* ... */`.

## Installation

### Prérequis
- Python 3.10+
- [Graphviz](https://graphviz.org/download/) (optionnel, pour l'AST visuel)

### Installation du package
Installez le projet en mode éditable pour pouvoir utiliser la commande `minipython` partout :

```bash
pip install -e .
```

### Branding Windows (Optionnel)
Pour associer les fichiers `.minipython` au logo et à l'interpréteur sur Windows :
1. Ouvrez PowerShell en tant qu'utilisateur.
2. Exécutez le script : `.\register_minipython.ps1`

## Utilisation

Une fois installé, vous pouvez lancer un script MiniPython simplement avec :

```bash
minipython test.minipython 
```
ou bien
```bash
.\minipython test.minipython
```
Le programme affichera :
1. Le code source.
2. Les tokens (phase lexicale).
3. L'AST textuel.
4. Le résultat de l'exécution.
5. Une image `ast_file.png` (si Graphviz est installé).
