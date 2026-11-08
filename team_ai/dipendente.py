"""Un dipendente AI: ha UNA mansione, la svolge, e rifiuta tutto ciò che spetta ad altri."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from . import config
from .llm import esegui_ciclo, strumento

if TYPE_CHECKING:
    from .team import Team


@dataclass
class ProfiloDipendente:
    nome: str            # es. "Redattore"
    mansione: str        # cosa fa, in una frase
    competenze: list[str]  # compiti tipici che gli spettano
    non_fa: list[str]    # cosa NON deve fare (spetta ad altri)
    creato_il: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))

    def scheda(self) -> str:
        return (
            f"- {self.nome}: {self.mansione}\n"
            f"    competenze: {', '.join(self.competenze)}\n"
            f"    non fa: {', '.join(self.non_fa) or '—'}"
        )

    def to_dict(self) -> dict:
        return asdict(self)


SYSTEM_DIPENDENTE = """Sei "{nome}", un dipendente AI di un piccolo team di lavoro.

LA TUA MANSIONE (l'unica): {mansione}
Ti spettano: {competenze}
NON ti spettano: {non_fa}

I colleghi del team e le loro mansioni:
{colleghi}

Regole di lavoro:
1. Svolgi SOLO la parte del compito che rientra nella tua mansione. Non improvvisarti in mestieri altrui,
   anche se sapresti farlo: il lavoro di un collega lo fa quel collega.
2. Se ti serve un contributo che spetta a un collega (un dato, un testo, una verifica), chiedilo con
   `chiedi_a_collega` e usa la sua risposta. Non rifare tu quel pezzo.
3. Se l'intero compito è fuori dalla tua mansione, usa `rifiuta_fuori_mansione` indicando chi dovrebbe farlo.
4. Quando hai finito la tua parte, usa `consegna_lavoro` con il risultato completo e pronto all'uso,
   scritto in italiano. Se hai fatto solo una parte, dichiara chiaramente cosa manca e a chi spetta.
5. Non inventare fatti, dati o numeri: se mancano informazioni, dillo nella consegna.
"""


class Dipendente:
    def __init__(self, profilo: ProfiloDipendente, team: "Team"):
        self.profilo = profilo
        self.team = team

    @property
    def nome(self) -> str:
        return self.profilo.nome

    def _system(self) -> str:
        colleghi = "\n".join(p.scheda() for p in self.team.profili() if p.nome != self.nome) or "(nessuno per ora)"
        p = self.profilo
        return SYSTEM_DIPENDENTE.format(
            nome=p.nome,
            mansione=p.mansione,
            competenze="; ".join(p.competenze),
            non_fa="; ".join(p.non_fa) or "tutto ciò che non è nella tua mansione",
            colleghi=colleghi,
        )

    def _strumenti(self) -> list[dict]:
        colleghi = [n for n in self.team.nomi() if n != self.nome]
        stringa_colleghi = {"type": "string", "description": "Nome esatto del collega."}
        if colleghi:
            stringa_colleghi["enum"] = colleghi
        strumenti = [
            strumento(
                "consegna_lavoro",
                "Consegna il risultato finale della TUA parte di lavoro. Chiude il compito.",
                {"risultato": {"type": "string", "description": "Il lavoro completo, pronto all'uso."}},
                ["risultato"],
            ),
            strumento(
                "rifiuta_fuori_mansione",
                "Usa questo se il compito non rientra nella tua mansione. Chiude il compito.",
                {
                    "motivo": {"type": "string"},
                    "collega_suggerito": {
                        "type": "string",
                        "description": "Chi dovrebbe occuparsene, oppure 'nessuno' se serve un nuovo dipendente.",
                    },
                },
                ["motivo", "collega_suggerito"],
            ),
        ]
        if colleghi:
            strumenti.append(
                strumento(
                    "chiedi_a_collega",
                    "Chiedi a un collega un contributo che rientra nella SUA mansione. Ricevi la sua risposta.",
                    {"collega": stringa_colleghi, "richiesta": {"type": "string"}},
                    ["collega", "richiesta"],
                )
            )
        return strumenti

    def lavora(self, compito: str, richiedente: str, profondita: int = 0) -> str:
        """Esegue un compito e restituisce l'esito (consegna o rifiuto) come testo."""
        bacheca = self.team.bacheca
        tipo_in = "compito" if richiedente == "Orchestratore" else "richiesta"
        bacheca.pubblica(richiedente, self.nome, tipo_in, compito)

        def consegna(inp: dict):
            bacheca.pubblica(self.nome, richiedente, "consegna", inp["risultato"])
            self.team.archivia_lavoro(self.nome, compito, inp["risultato"])
            return f"CONSEGNA di {self.nome}:\n{inp['risultato']}", True

        def rifiuta(inp: dict):
            testo = f"{inp['motivo']} (suggerito: {inp['collega_suggerito']})"
            bacheca.pubblica(self.nome, richiedente, "rifiuto", testo)
            return f"RIFIUTO di {self.nome}: {testo}", True

        def chiedi(inp: dict):
            collega = self.team.dipendente(inp["collega"])
            if profondita + 1 > config.MAX_PROFONDITA_DELEGA:
                return "Catena di richieste troppo lunga: completa con ciò che hai o segnala cosa manca.", False
            if collega.nome == richiedente:
                return f"{collega.nome} ti ha assegnato questo lavoro: non rimandarglielo, consegna ciò che puoi.", False
            esito = collega.lavora(inp["richiesta"], richiedente=self.nome, profondita=profondita + 1)
            return esito, False

        messaggi = [{"role": "user", "content": f"Compito da parte di {richiedente}:\n\n{compito}"}]
        return esegui_ciclo(
            self.team.client,
            self._system(),
            messaggi,
            self._strumenti(),
            {"consegna_lavoro": consegna, "rifiuta_fuori_mansione": rifiuta, "chiedi_a_collega": chiedi},
            effort=config.EFFORT_DIPENDENTE,
        )
