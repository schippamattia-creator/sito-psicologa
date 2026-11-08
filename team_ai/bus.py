"""Bacheca dei messaggi: ogni comunicazione tra agenti passa da qui e viene registrata."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Messaggio:
    mittente: str
    destinatario: str
    tipo: str  # compito | richiesta | risposta | rifiuto | consegna
    contenuto: str
    ora: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class Bacheca:
    def __init__(self, cartella: Path):
        self.file = cartella / "registro_messaggi.jsonl"
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.sessione: list[Messaggio] = []

    def pubblica(self, mittente: str, destinatario: str, tipo: str, contenuto: str) -> Messaggio:
        msg = Messaggio(mittente, destinatario, tipo, contenuto)
        self.sessione.append(msg)
        with self.file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(msg), ensure_ascii=False) + "\n")
        anteprima = contenuto.replace("\n", " ")
        if len(anteprima) > 140:
            anteprima = anteprima[:140] + "…"
        print(f"  📨 [{tipo}] {mittente} → {destinatario}: {anteprima}")
        return msg

    def ultimi(self, n: int = 20) -> list[Messaggio]:
        return self.sessione[-n:]
