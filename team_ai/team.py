"""Il team: anagrafica dei dipendenti (salvata su disco), bacheca dei messaggi e archivio dei lavori."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import anthropic

from .bus import Bacheca
from .dipendente import Dipendente, ProfiloDipendente


class Team:
    def __init__(self, cartella: Path, client: anthropic.Anthropic | None = None):
        self.cartella = cartella
        self.cartella.mkdir(parents=True, exist_ok=True)
        self.file_team = cartella / "team.json"
        self.cartella_lavori = cartella / "lavori"
        self.client = client or anthropic.Anthropic()
        self.bacheca = Bacheca(cartella)
        self._dipendenti: dict[str, Dipendente] = {}
        self._carica()

    # --- anagrafica -------------------------------------------------------
    def _carica(self) -> None:
        if self.file_team.exists():
            for d in json.loads(self.file_team.read_text(encoding="utf-8")):
                p = ProfiloDipendente(**d)
                self._dipendenti[p.nome.lower()] = Dipendente(p, self)

    def _salva(self) -> None:
        dati = [d.profilo.to_dict() for d in self._dipendenti.values()]
        self.file_team.write_text(json.dumps(dati, ensure_ascii=False, indent=2), encoding="utf-8")

    def assumi(self, profilo: ProfiloDipendente) -> Dipendente:
        if profilo.nome.lower() in self._dipendenti:
            raise ValueError(f"Esiste già un dipendente di nome '{profilo.nome}'.")
        if profilo.nome.lower() == "orchestratore":
            raise ValueError("'Orchestratore' è un nome riservato.")
        d = Dipendente(profilo, self)
        self._dipendenti[profilo.nome.lower()] = d
        self._salva()
        return d

    def licenzia(self, nome: str) -> None:
        self.dipendente(nome)
        del self._dipendenti[nome.lower()]
        self._salva()

    def dipendente(self, nome: str) -> Dipendente:
        try:
            return self._dipendenti[nome.lower()]
        except KeyError:
            raise ValueError(f"Nessun dipendente di nome '{nome}'. Presenti: {', '.join(self.nomi()) or 'nessuno'}")

    def nomi(self) -> list[str]:
        return [d.nome for d in self._dipendenti.values()]

    def profili(self) -> list[ProfiloDipendente]:
        return [d.profilo for d in self._dipendenti.values()]

    def organigramma(self) -> str:
        return "\n".join(p.scheda() for p in self.profili()) or "(nessun dipendente)"

    # --- archivio ---------------------------------------------------------
    def archivia_lavoro(self, autore: str, compito: str, risultato: str) -> Path:
        self.cartella_lavori.mkdir(parents=True, exist_ok=True)
        ora = datetime.now()
        slug = re.sub(r"[^a-z0-9]+", "-", compito.lower())[:40].strip("-") or "lavoro"
        file = self.cartella_lavori / f"{ora:%Y%m%d-%H%M%S}_{autore.lower()}_{slug}.md"
        file.write_text(
            f"# {autore} — {ora:%d/%m/%Y %H:%M}\n\n## Compito\n\n{compito}\n\n## Risultato\n\n{risultato}\n",
            encoding="utf-8",
        )
        return file
