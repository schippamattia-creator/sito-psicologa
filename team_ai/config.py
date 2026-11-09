"""Impostazioni condivise del team AI."""

from pathlib import Path

# Modello usato da orchestratore e dipendenti.
MODEL = "claude-opus-5-5"

# Livello di "impegno" (quanto ragiona il modello).
# L'orchestratore pianifica: impegno alto. I dipendenti eseguono: impegno medio.
EFFORT_ORCHESTRATORE = "high"
EFFORT_DIPENDENTE = "medium"

MAX_TOKENS = 16000

# Se un modello rifiuta una richiesta, l'API la ripete in automatico su un
# modello di riserva (fallback lato server).
BETAS = ["server-side-fallback-2026-07-01"]
FALLBACKS = "default"

# Quante volte un dipendente può passare la palla a un collega in catena
# (A chiede a B, B chiede a C...). Evita giri infiniti.
MAX_PROFONDITA_DELEGA = 3

# Numero massimo di giri strumento->risposta per singolo agente.
MAX_GIRI_AGENTE = 20

# Dove salvare team, registro dei messaggi e lavori consegnati.
CARTELLA_DATI = Path(__file__).resolve().parent.parent / "dati_team"
