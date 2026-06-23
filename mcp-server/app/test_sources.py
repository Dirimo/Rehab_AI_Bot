import asyncio
import sys
import time
import shutil
from pathlib import Path

# Adjust path to import app modules correctly
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.sources.physiopedia import search_physiopedia_exercises
from app.sources.axomove import search_axomove_exercises
from app.sources.pmc import search_pmc_articles
from app.sources.ameli import get_ameli_advice
from app.sources.discovery import discover_guideline_sources, dynamic_search_available
from app.sources.registry import SOURCE_CATALOG, get_by_key
from app.sources.resolver import fetch_source_entry
from app.scraping.translator import translate_en_to_fr
from app.scraping.content_validation import is_content_sufficient

# Colors for terminal
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

async def test_physiopedia():
    print(f"\n{CYAN}--- Test Physiopedia (P0 - EN -> FR) ---{RESET}")
    start = time.perf_counter()
    try:
        results = await search_physiopedia_exercises("lombalgie", limit=1, translate=True)
        duration = time.perf_counter() - start
        if results:
            article = results[0]
            if article.get("content") and is_content_sufficient(article["content"]):
                print(f"{GREEN}[OK] Physiopedia a renvoyé des résultats en {duration:.2f}s.{RESET}")
                print(f"  Titre : {article.get('title')}")
                print(f"  URL   : {article.get('url')}")
                print(f"  Extrait : {article.get('content')[:200]}...")
                print(f"  Langue : {article.get('lang')}")
            else:
                print(f"{RED}[FAIL] Contenu Physiopedia insuffisant en {duration:.2f}s.{RESET}")
        else:
            print(f"{RED}[FAIL] Physiopedia n'a renvoyé aucun résultat en {duration:.2f}s.{RESET}")
    except Exception as e:
        print(f"{RED}[FAIL] Erreur lors du test Physiopedia : {e}{RESET}")

async def test_has():
    print(f"\n{CYAN}--- Test HAS (P0 - FR) ---{RESET}")
    start = time.perf_counter()
    try:
        entry = get_by_key("lombalgie")
        if not entry or entry.provider != "HAS":
            # Fallback to find any HAS source
            entry = next((e for e in SOURCE_CATALOG if e.provider == "HAS"), None)
        
        if entry:
            article = await fetch_source_entry(entry)
            duration = time.perf_counter() - start
            if article and article.get("content"):
                print(f"{GREEN}[OK] HAS a renvoyé des résultats en {duration:.2f}s.{RESET}")
                print(f"  Titre : {article.get('title')}")
                print(f"  URL   : {article.get('url')}")
                print(f"  Extrait : {article.get('content')[:200]}...")
            else:
                print(f"{RED}[FAIL] HAS n'a pas pu extraire de contenu depuis {entry.url} en {duration:.2f}s.{RESET}")
        else:
            print(f"{RED}[FAIL] Aucune entrée HAS trouvée dans le catalogue.{RESET}")
    except Exception as e:
        print(f"{RED}[FAIL] Erreur lors du test HAS : {e}{RESET}")

async def test_vidal():
    print(f"\n{CYAN}--- Test VIDAL (P1 - FR) ---{RESET}")
    start = time.perf_counter()
    try:
        entry = get_by_key("parkinson")
        if not entry or entry.provider != "VIDAL":
            # Fallback to find any VIDAL source
            entry = next((e for e in SOURCE_CATALOG if e.provider == "VIDAL"), None)
        
        if entry:
            article = await fetch_source_entry(entry)
            duration = time.perf_counter() - start
            if article and article.get("content"):
                print(f"{GREEN}[OK] VIDAL a renvoyé des résultats en {duration:.2f}s.{RESET}")
                print(f"  Titre : {article.get('title')}")
                print(f"  URL   : {article.get('url')}")
                print(f"  Extrait : {article.get('content')[:200]}...")
            else:
                print(f"{RED}[FAIL] VIDAL n'a pas pu extraire de contenu depuis {entry.url} en {duration:.2f}s.{RESET}")
        else:
            print(f"{RED}[FAIL] Aucune entrée VIDAL trouvée dans le catalogue.{RESET}")
    except Exception as e:
        print(f"{RED}[FAIL] Erreur lors du test VIDAL : {e}{RESET}")

async def test_ameli():
    print(f"\n{CYAN}--- Test Ameli.fr (P1 - FR) ---{RESET}")
    start = time.perf_counter()
    try:
        article = await get_ameli_advice("lombalgie")
        duration = time.perf_counter() - start
        if article and article.get("content"):
            print(f"{GREEN}[OK] Ameli.fr a renvoyé des résultats en {duration:.2f}s.{RESET}")
            print(f"  Titre : {article.get('title')}")
            print(f"  URL   : {article.get('url')}")
            print(f"  Extrait : {article.get('content')[:200]}...")
        else:
            print(f"{RED}[FAIL] Ameli.fr n'a renvoyé aucun résultat en {duration:.2f}s.{RESET}")
    except Exception as e:
        print(f"{RED}[FAIL] Erreur lors du test Ameli.fr : {e}{RESET}")

async def test_axomove():
    print(f"\n{CYAN}--- Test Axomove (P2 - FR) ---{RESET}")
    start = time.perf_counter()
    try:
        results = await search_axomove_exercises("lombalgie", limit=1)
        duration = time.perf_counter() - start
        if results:
            article = results[0]
            print(f"{GREEN}[OK] Axomove a renvoyé des résultats en {duration:.2f}s.{RESET}")
            print(f"  Titre : {article.get('title')}")
            print(f"  URL   : {article.get('url')}")
            print(f"  Extrait : {article.get('content')[:200]}...")
        else:
            print(f"{RED}[FAIL] Axomove n'a renvoyé aucun résultat en {duration:.2f}s.{RESET}")
    except Exception as e:
        print(f"{RED}[FAIL] Erreur lors du test Axomove : {e}{RESET}")

async def test_pmc():
    print(f"\n{CYAN}--- Test PMC (P2 - EN -> FR) ---{RESET}")
    start = time.perf_counter()
    try:
        results = await search_pmc_articles("lombalgie", limit=1, translate=True)
        duration = time.perf_counter() - start
        if results:
            article = results[0]
            print(f"{GREEN}[OK] PMC a renvoyé des résultats en {duration:.2f}s.{RESET}")
            print(f"  Titre : {article.get('title')}")
            print(f"  URL   : {article.get('url')}")
            print(f"  Extrait : {article.get('abstract')[:200]}...")
            print(f"  Langue : {article.get('lang')}")
        else:
            print(f"{RED}[FAIL] PMC n'a renvoyé aucun résultat en {duration:.2f}s.{RESET}")
    except Exception as e:
        print(f"{RED}[FAIL] Erreur lors du test PMC : {e}{RESET}")

async def test_translation():
    print(f"\n{CYAN}--- Test de Traduction avec Ollama ---{RESET}")
    test_text = "Standard physiotherapy programs are beneficial for chronic low back pain."
    print(f"Texte à traduire : '{test_text}'")
    start = time.perf_counter()
    try:
        translation = await translate_en_to_fr(test_text)
        duration = time.perf_counter() - start
        print(f"Traduction obtenue en {duration:.2f}s : '{translation}'")
        if translation != test_text:
            print(f"{GREEN}[OK] Ollama fonctionne pour la traduction.{RESET}")
        else:
            print(f"{YELLOW}[WARNING] La traduction a échoué ou a retourné le texte original (Ollama est peut-être éteint ou injoignable).{RESET}")
    except Exception as e:
        print(f"{RED}[FAIL] Erreur lors de la traduction : {e}{RESET}")

def clear_cache():
    cache_dir = Path(__file__).resolve().parents[1] / ".cache"
    if cache_dir.exists():
        print(f"{YELLOW}Suppression du cache local ({cache_dir})...{RESET}")
        shutil.rmtree(cache_dir, ignore_errors=True)
        print(f"{GREEN}Cache supprimé avec succès.{RESET}")
    else:
        print(f"Aucun cache détecté à {cache_dir}.")

async def test_has_cervicalgie():
    print(f"\n{CYAN}--- Test HAS cervicalgie (P0 - FR) ---{RESET}")
    start = time.perf_counter()
    try:
        entry = get_by_key("has_cervicalgie")
        if entry:
            article = await fetch_source_entry(entry)
            duration = time.perf_counter() - start
            if article and is_content_sufficient(article.get("content", "")):
                print(f"{GREEN}[OK] HAS cervicalgie en {duration:.2f}s.{RESET}")
                print(f"  Titre : {article.get('title')}")
                print(f"  Extrait : {article.get('content')[:200]}...")
            else:
                print(f"{RED}[FAIL] Contenu HAS cervicalgie insuffisant.{RESET}")
        else:
            print(f"{RED}[FAIL] Entrée HAS cervicalgie introuvable.{RESET}")
    except Exception as e:
        print(f"{RED}[FAIL] Erreur HAS cervicalgie : {e}{RESET}")

async def test_discovery():
    print(f"\n{CYAN}--- Test découverte dynamique (Firecrawl) ---{RESET}")
    if not dynamic_search_available():
        print(f"{YELLOW}[SKIP] Découverte dynamique désactivée (FIRECRAWL_API_KEY manquante).{RESET}")
        return
    start = time.perf_counter()
    try:
        results = await discover_guideline_sources("tendinite épaule", limit=2)
        duration = time.perf_counter() - start
        if results:
            hit = results[0]
            print(f"{GREEN}[OK] Découverte a renvoyé {len(results)} résultat(s) en {duration:.2f}s.{RESET}")
            print(f"  Titre : {hit.get('title')}")
            print(f"  URL   : {hit.get('url')}")
            print(f"  Source : {hit.get('provider')}")
        else:
            print(f"{YELLOW}[WARN] Découverte sans résultat en {duration:.2f}s.{RESET}")
    except Exception as e:
        print(f"{RED}[FAIL] Erreur découverte dynamique : {e}{RESET}")

async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--clear-cache", action="store_true", help="Supprime le cache avant le test")
    args = parser.parse_args()

    if args.clear_cache:
        clear_cache()

    print(f"{CYAN}=== Démarrage du test global des sources RehabBot ==={RESET}")
    print(f"Ollama URL configure: {settings.OLLAMA_BASE_URL}")
    print(f"Ollama Model configure: {settings.OLLAMA_TRANSLATION_MODEL}")

    print(f"Firecrawl activé : {settings.FIRECRAWL_ENABLED and bool(settings.FIRECRAWL_API_KEY)}")
    print(f"Découverte dynamique : {dynamic_search_available()}")

    # Run tests
    await test_discovery()
    await test_translation()
    await test_physiopedia()
    await test_has()
    await test_has_cervicalgie()
    await test_vidal()
    await test_ameli()
    await test_axomove()
    await test_pmc()

    print(f"\n{CYAN}=== Test global terminé ==={RESET}")

if __name__ == "__main__":
    asyncio.run(main())
