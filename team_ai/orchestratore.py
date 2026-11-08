"""L'orchestratore: parla con te, capisce cosa ti serve, assume i dipendenti giusti e smista i compiti.

Non esegue mai il lavoro di persona: può solo assumere, assegnare, coordinare e riferirti.
"""

from __future__ import annotations

from . import config
from .dipendente import ProfiloDipendente
from .llm import esegui_ciclo, strumento
from .team import Team

SYSTEM_ORCHESTRATORE = """Sei l'Orchestratore, il capo-squadra di un team di dipendenti AI al servizio del titolare.
Parli in italiano, in modo chiaro e conciso.

Il tuo lavoro:
1. Capire cosa serve al titolare. Se la richiesta è ambigua, fai al massimo 1-2 domande mirate prima di agire.
2. Scomporre la richiesta in compiti, ognuno appartenente a UNA sola mansione.
3. Per ogni mansione necessaria usa un dipendente esistente; se non c'è, assumine uno con `assumi_dipendente`.
   - Ogni dipendente ha una mansione specifica e ristretta, senza sovrapposizioni con gli altri.
   - Nel campo "non_fa" elenca esplicitamente le attività che spettano ai colleghi.
   - Non assumere doppioni: prima controlla l'organigramma.
4. Assegna i compiti con `assegna_compito`, nell'ordine giusto: se un compito dipende dal risultato di un altro,
   assegna prima quello e passa il risultato nel compito successivo. Nel compito includi tutto il contesto
   necessario (il dipendente non vede la tua conversazione con il titolare).
5. Se un dipendente rifiuta perché il compito non è suo, riassegnalo alla persona giusta o assumi chi manca.
6. Alla fine riferisci al titolare: cosa è stato fatto, da chi, il risultato (o un riassunto, se lungo) e
   cosa resta da decidere.

Non svolgi MAI tu stesso il lavoro operativo (scrivere testi, analisi, piani...): lo deleghi sempre.
Puoi solo coordinare, assumere, assegnare e riferire.
L'organigramma aggiornato ti arriva insieme a ogni richiesta del titolare.
"""


class Orchestratore:
    def __init__(self, team: Team):
        self.team = team
        self.conversazione: list[dict] = []

    def _strumenti(self) -> list[dict]:
        lista = {"type": "array", "items": {"type": "string"}}
        return [
            strumento(
                "assumi_dipendente",
                "Crea un nuovo dipendente AI con una mansione specifica e non sovrapposta a quelle esistenti.",
                {
                    "nome": {"type": "string", "description": "Nome-ruolo breve, es. 'Redattore', 'Analista'."},
                    "mansione": {"type": "string", "description": "Cosa fa, in una frase."},
                    "competenze": {**lista, "description": "Compiti tipici che gli spettano."},
                    "non_fa": {**lista, "description": "Attività che NON deve fare perché spettano ad altri."},
                },
                ["nome", "mansione", "competenze", "non_fa"],
            ),
            strumento(
                "assegna_compito",
                "Assegna un compito a un dipendente e attendi la sua consegna (o il suo rifiuto).",
                {
                    "dipendente": {"type": "string"},
                    "compito": {"type": "string", "description": "Istruzioni complete con tutto il contesto."},
                },
                ["dipendente", "compito"],
            ),
            strumento(
                "licenzia_dipendente",
                "Rimuove un dipendente dal team (solo se il titolare lo chiede o se è un doppione).",
                {"nome": {"type": "string"}, "motivo": {"type": "string"}},
                ["nome", "motivo"],
            ),
        ]

    def _gestori(self) -> dict:
        def assumi(inp: dict):
            d = self.team.assumi(
                ProfiloDipendente(inp["nome"].strip(), inp["mansione"], inp["competenze"], inp["non_fa"])
            )
            print(f"  👤 Assunto: {d.nome} — {d.profilo.mansione}")
            return f"Assunto {d.nome}.\nOrganigramma aggiornato:\n{self.team.organigramma()}", False

        def assegna(inp: dict):
            d = self.team.dipendente(inp["dipendente"])
            return d.lavora(inp["compito"], richiedente="Orchestratore"), False

        def licenzia(inp: dict):
            self.team.licenzia(inp["nome"])
            print(f"  🚪 Rimosso: {inp['nome']} ({inp['motivo']})")
            return f"{inp['nome']} rimosso.", False

        return {"assumi_dipendente": assumi, "assegna_compito": assegna, "licenzia_dipendente": licenzia}

    def parla(self, richiesta: str) -> str:
        # Il system prompt è fisso; l'organigramma aggiornato arriva insieme a ogni richiesta,
        # così la cronologia della conversazione non viene mai riscritta.
        testo = f"[Organigramma attuale]\n{self.team.organigramma()}\n\n[Richiesta del titolare]\n{richiesta}"
        self.conversazione.append({"role": "user", "content": testo})
        return esegui_ciclo(
            self.team.client,
            SYSTEM_ORCHESTRATORE,
            self.conversazione,
            self._strumenti(),
            self._gestori(),
            effort=config.EFFORT_ORCHESTRATORE,
        )
