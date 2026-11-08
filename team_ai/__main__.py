"""Avvio: `python -m team_ai`"""

from __future__ import annotations

import anthropic

from . import config
from .llm import ErroreAgente
from .orchestratore import Orchestratore
from .team import Team

AIUTO = """Comandi:
  /team             mostra i dipendenti e le loro mansioni
  /messaggi         ultimi messaggi scambiati tra gli agenti
  /licenzia NOME    rimuove un dipendente
  /nuova            inizia una nuova conversazione (il team resta)
  /esci             termina
Qualsiasi altro testo viene inviato all'Orchestratore."""


def main() -> None:
    team = Team(config.CARTELLA_DATI)
    capo = Orchestratore(team)
    print("🤝 Team AI pronto. Dimmi cosa ti serve.  (/aiuto per i comandi)\n")
    print(team.organigramma(), "\n")

    while True:
        try:
            testo = input("Tu › ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not testo:
            continue
        if testo in ("/esci", "/exit"):
            break
        if testo == "/aiuto":
            print(AIUTO)
            continue
        if testo == "/team":
            print(team.organigramma())
            continue
        if testo == "/messaggi":
            for m in team.bacheca.ultimi():
                print(f"[{m.ora}] {m.tipo}: {m.mittente} → {m.destinatario}\n  {m.contenuto[:300]}")
            continue
        if testo.startswith("/licenzia "):
            try:
                team.licenzia(testo.split(maxsplit=1)[1])
                print("Fatto.")
            except ValueError as e:
                print(e)
            continue
        if testo == "/nuova":
            capo = Orchestratore(team)
            print("Nuova conversazione.")
            continue

        try:
            risposta = capo.parla(testo)
            print(f"\nOrchestratore › {risposta}\n")
        except ErroreAgente as e:
            print(f"\n⚠️  {e}\n")
            capo = Orchestratore(team)  # riparte pulito dopo un errore
        except anthropic.AuthenticationError:
            print("⚠️  Chiave API mancante o non valida. Imposta ANTHROPIC_API_KEY.")
            break
        except anthropic.RateLimitError:
            print("⚠️  Troppe richieste: attendi qualche secondo e riprova.")
        except anthropic.APIConnectionError:
            print("⚠️  Connessione all'API non riuscita. Controlla la rete e riprova.")
        except anthropic.APIStatusError as e:
            print(f"⚠️  Errore dell'API ({e.status_code}): {e.message}")


if __name__ == "__main__":
    main()
