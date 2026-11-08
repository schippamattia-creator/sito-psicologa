"""Ciclo agentico condiviso: chiama Claude, esegue gli strumenti, ripete finché l'agente ha finito."""

from __future__ import annotations

import json
from typing import Any, Callable

import anthropic

from . import config

# Un gestore riceve l'input dello strumento e restituisce (testo_risultato, fine_lavoro).
# fine_lavoro=True chiude il ciclo (es. il dipendente ha consegnato o rifiutato).
Gestore = Callable[[dict], tuple[str, bool]]


class ErroreAgente(Exception):
    pass


def strumento(nome: str, descrizione: str, proprieta: dict, obbligatori: list[str]) -> dict:
    """Definizione di uno strumento con schema rigoroso (input sempre valido)."""
    return {
        "name": nome,
        "description": descrizione,
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": proprieta,
            "required": obbligatori,
            "additionalProperties": False,
        },
    }


def _testo(contenuto) -> str:
    return "\n".join(b.text for b in contenuto if getattr(b, "type", None) == "text").strip()


def esegui_ciclo(
    client: anthropic.Anthropic,
    system: str,
    messaggi: list[dict],
    strumenti: list[dict],
    gestori: dict[str, Gestore],
    effort: str,
) -> str:
    """Esegue il ciclo agentico. `messaggi` viene esteso sul posto (la conversazione resta valida).

    Restituisce l'ultimo testo prodotto, oppure il risultato dello strumento che ha chiuso il lavoro.
    """
    for _ in range(config.MAX_GIRI_AGENTE):
        risposta = client.beta.messages.create(
            model=config.MODEL,
            max_tokens=config.MAX_TOKENS,
            system=system,
            tools=strumenti,
            messages=messaggi,
            output_config={"effort": effort},
            betas=config.BETAS,
            fallbacks=config.FALLBACKS,
        )

        if risposta.stop_reason == "refusal":
            raise ErroreAgente("La richiesta è stata rifiutata dal modello per motivi di sicurezza.")
        if risposta.stop_reason == "max_tokens":
            raise ErroreAgente("La risposta è stata troncata (limite di lunghezza raggiunto).")

        # Si riaggiunge sempre il contenuto completo (inclusi i blocchi di ragionamento).
        messaggi.append({"role": "assistant", "content": risposta.content})

        if risposta.stop_reason == "pause_turn":
            continue

        chiamate = [b for b in risposta.content if b.type == "tool_use"]
        if not chiamate:
            return _testo(risposta.content)

        risultati = []
        chiusura: str | None = None
        for c in chiamate:
            gestore = gestori.get(c.name)
            try:
                if gestore is None:
                    raise ValueError(f"Strumento sconosciuto: {c.name}")
                ingresso = c.input if isinstance(c.input, dict) else json.loads(c.input)
                testo, fine = gestore(ingresso)
                risultati.append({"type": "tool_result", "tool_use_id": c.id, "content": testo})
                if fine:
                    chiusura = testo
            except Exception as e:  # l'errore torna all'agente, che può correggersi
                risultati.append(
                    {"type": "tool_result", "tool_use_id": c.id, "content": f"Errore: {e}", "is_error": True}
                )
        messaggi.append({"role": "user", "content": risultati})

        if chiusura is not None:
            return chiusura

    raise ErroreAgente("L'agente ha superato il numero massimo di passaggi senza concludere.")
