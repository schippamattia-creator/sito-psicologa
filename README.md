# Team AI — i tuoi dipendenti AI

Un piccolo "ufficio" di agenti AI basati su Claude:

- **Orchestratore**: è l'unico con cui parli. Capisce cosa ti serve, scompone la richiesta in compiti,
  **assume i dipendenti necessari** e assegna a ciascuno il suo pezzo di lavoro. Non esegue mai il lavoro di persona.
- **Dipendenti**: creati dall'orchestratore secondo il bisogno (es. *Ricercatore*, *Redattore*, *Pianificatore*).
  Ognuno ha **una sola mansione**, con un elenco esplicito di cose che **non** fa perché spettano ai colleghi.
- **Comunicazione tra agenti**: un dipendente può chiedere a un collega un contributo che rientra nella mansione
  del collega (`chiedi_a_collega`), ma non può fare il suo lavoro. Se riceve un compito non suo lo **rifiuta**
  indicando a chi spetta, e l'orchestratore lo riassegna o assume chi manca.

```
Tu ──► Orchestratore ──assume──► Ricercatore, Redattore, ...
            │                         ▲   │
            └──assegna compito──► Redattore ──chiede dati──► Ricercatore
                                      │
            ◄────── consegna ─────────┘
```

Tutto viene registrato:

| Cosa | Dove |
|---|---|
| Elenco dipendenti e mansioni (resta tra una sessione e l'altra) | `dati_team/team.json` |
| Ogni messaggio tra agenti (compiti, richieste, consegne, rifiuti) | `dati_team/registro_messaggi.jsonl` |
| Ogni lavoro consegnato, in un file leggibile | `dati_team/lavori/*.md` |

## Installazione

Serve Python 3.10+ e una chiave API di Anthropic (https://console.anthropic.com).

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="la-tua-chiave"
```

## Uso

```bash
python -m team_ai
```

Esempio:

```
Tu › Ogni settimana devo pubblicare un articolo sul blog e un post Instagram sullo stesso tema.
     Questa settimana il tema è l'ansia da prestazione.
  👤 Assunto: Ricercatore — raccoglie e verifica informazioni sui temi richiesti
  👤 Assunto: Redattore — scrive articoli per il blog
  👤 Assunto: SocialMedia — adatta i contenuti per Instagram
  📨 [compito] Orchestratore → Ricercatore: ...
  📨 [consegna] Ricercatore → Orchestratore: ...
  📨 [compito] Orchestratore → Redattore: ...
  ...
Orchestratore › Ecco cosa è stato fatto ...
```

Comandi nella chat: `/team`, `/messaggi`, `/licenzia NOME`, `/nuova`, `/esci`, `/aiuto`.

## Personalizzare

In `team_ai/config.py`:

- `MODEL` — il modello Claude usato (default `claude-opus-5-5`).
- `EFFORT_ORCHESTRATORE` / `EFFORT_DIPENDENTE` — quanto ragionano (`low`, `medium`, `high`, `xhigh`, `max`):
  più alto = più accurato ma più lento e costoso.
- `MAX_PROFONDITA_DELEGA` — quante volte i dipendenti possono passarsi richieste a catena.
- `FALLBACKS` — se un modello rifiuta una richiesta per motivi di sicurezza, l'API la ripete in automatico su un
  modello di riserva. Per disattivarlo togli `betas`/`fallbacks` dalla chiamata in `team_ai/llm.py`.

Puoi anche modificare a mano `dati_team/team.json` per ritoccare le mansioni dei dipendenti.

## Struttura del codice

| File | Ruolo |
|---|---|
| `team_ai/orchestratore.py` | L'orchestratore e i suoi strumenti (assumi, assegna, licenzia) |
| `team_ai/dipendente.py` | Il dipendente: mansione, regole, strumenti (consegna, rifiuta, chiedi a collega) |
| `team_ai/team.py` | Anagrafica, salvataggio su disco, archivio lavori |
| `team_ai/bus.py` | Bacheca: registro di tutti i messaggi tra agenti |
| `team_ai/llm.py` | Ciclo agentico condiviso con l'API di Claude |
| `team_ai/__main__.py` | Chat da terminale |
