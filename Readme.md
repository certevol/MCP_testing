# MCP Demo – “Chat” multi-sorgente (arXiv + OpenAlex) in VS Code + LLM (Ollama)

Questa repo mostra **come costruire un “chatbot” controllato** che:
- chiama **due sorgenti** (arXiv e OpenAlex) via **server MCP**
- fonde i risultati
- (opzionale) usa **Ollama** per una sintesi **con citazioni obbligatorie**

> Nota importante: **la “chat” qui è una cella interattiva nel notebook 02** (ti chiede la domanda e quali sorgenti usare). Non è una chat UI grafica stile ChatGPT: è una demo tecnica riproducibile.

---

## 1) Setup (una volta sola)

### 1.1 Crea e attiva venv
```bash
cd mcp-demo
python -m venv .venv
source .venv/bin/activate
````

### 1.2 Installa dipendenze

```bash
pip install fastmcp httpx arxiv
```

---

## 2) Ollama (opzionale, per usare LLM)

### 2.1 Installa Ollama

Vai su [https://ollama.com](https://ollama.com) e installa.

### 2.2 Avvia Ollama (in un terminale separato, lasciandolo aperto)

```bash
ollama serve
```

### 2.3 Scarica un modello

```bash
ollama pull llama3.2
```

---

## 3) Come aprire e usare tutto in Visual Studio Code

### 3.1 Apri la cartella progetto

* VS Code → **File → Open Folder…** → seleziona `mcp-demo`

### 3.2 Seleziona il Python interpreter del progetto

* Cmd+Shift+P → “**Python: Select Interpreter**”
* scegli quello dentro `mcp-demo/.venv/...`

### 3.3 Apri il notebook 02 (quello “vero”)

* apri `02_orchestrator_fusion.ipynb`

---

## 4) Cosa fa ogni notebook (molto chiaro)

### `00_setup_project.ipynb` (setup file)

* Serve a **generare/riscrivere** i file:

  * `servers/arxiv_server.py`
  * `servers/openalex_server.py`
  * (eventuali file CLI)
* **Lo esegui solo se devi (ri)creare i file** o hai incollato nuove versioni di server/client.

✅ Quando eseguirlo:

* prima volta (se i server non esistono)
* quando cambi codice “generator” nel notebook 00

---

### `01_test_cli_and_tools.ipynb` (test tool)

* È solo un banco prova: controlli che i server rispondano e vedi il formato delle risposte.
* **Non è necessario** per usare la chat del 02.

---

### `02_orchestrator_fusion.ipynb` (ORCHESTRATORE + CHAT)

* È **il notebook che userai ogni volta**.
* Dentro trovi:

  * `fetch()` → chiama i server MCP
  * `answer()` → costruisce la risposta (no LLM o con LLM)
  * una cella “chat” dove inserisci:

    * la domanda
    * quale sorgente usare (arXiv / OpenAlex / entrambe)
    * se usare il LLM

---

## 5) Come eseguire correttamente il notebook 02 
### 5.1 Prima volta (o dopo modifiche al codice): esegui “le celle di definizione”

1. **Restart Kernel** (consigliato)

2. Esegui in ordine le celle che definiscono funzioni (di solito sono le prime)

* Cell import
* `unpack()`
* `detect_domain()`
* `pick_sources()`
* `fetch()` e helper
* fusione senza LLM
* LLM (Ollama)
* `answer()`

✅ Metodo semplice: usa “Run All” (Esegui tutto) **una volta** dopo il restart.

> Perché: in notebook, se modifichi una funzione ma non riesegui la cella, il kernel continua a usare la versione vecchia.

---

## 6) Dov’è la fare la domanda e come scegliere la sorgente

Nel 02 devi avere (o creare) **UNA cella dedicata** tipo questa.
Questa è la “chat” interattiva:

```python
# --- CHAT CELL (VS Code Notebook) ---
q = input("Domanda: ").strip()

src = input("Sorgenti (a=arxiv, o=openalex, b=both) [b]: ").strip().lower() or "b"
use_arxiv = (src in ["a", "b"])
use_openalex = (src in ["o", "b"])

llm = input("Usare LLM? (y/n) [n]: ").strip().lower() or "n"
use_llm = (llm == "y")

k_str = input("Quanti risultati per sorgente? [3]: ").strip() or "3"
k = int(k_str)

model = "llama3.2"  # cambia se usi un altro modello Ollama

out = await answer(
    q,
    k=k,
    use_llm=use_llm,
    model=model,
    use_arxiv=use_arxiv,
    use_openalex=use_openalex
)
print(out)
```

### Come usarla:

1. premi ▶️ Run sulla cella
2. VS Code ti chiede:

   * **Domanda**
   * **Sorgente**:

     * `a` = solo arXiv
     * `o` = solo OpenAlex
     * `b` = entrambe
   * **LLM**: `y` o `n`
   * **k**: numero risultati

Esempio:

* Domanda: `agentic RAG evaluation`
* Sorgenti: `b`
* LLM: `y`
* k: `3`

---

## 7) Esempi di domande pronte

### AI (buona per entrambe le sorgenti)

* `How are agentic RAG systems evaluated, and what benchmarks and metrics are used?`

### General ma ancora “ricercabile” su entrambe

* `What are best practices for evaluating retrieval-augmented generation systems in real-world applications?`

### Business/management (tipicamente meglio OpenAlex)

* `product management`
* `innovation management`

---

## 8) Se “seleziono o ma usa sempre OpenAlex” (o viceversa)

Se scegli `o` (solo OpenAlex) è normale che risponda usando OpenAlex.
Se scegli `a` (solo arXiv) deve usare SOLO arXiv.

Se non succede:

* quasi sempre è perché **non hai rieseguito la cella che definisce `fetch()` / `answer()`**
* fai:

  1. Restart Kernel
  2. Run All
  3. riprova la chat cell

---

## 9) Troubleshooting (errori comuni)

### Errore: `asyncio.run() cannot be called from a running event loop`

In notebook non usare `asyncio.run(...)`.
Usa direttamente:

```python
out = await answer("...", k=3)
```

### Errore OpenAlex: `'NoneType' object has no attribute 'get'`

È un parsing non “null-safe” nel server OpenAlex.
Correggi `servers/openalex_server.py` rendendo robusti i campi (primary_location/source possono essere None).

### Errore arXiv: HTTP 429

È rate limit: il notebook ha retry/backoff. Se capita spesso:

* aspetta qualche secondo e riprova
* usa solo OpenAlex per test rapidi

---

## 10) Cosa hai costruito (in 1 frase)

Un orchestratore che fa “chat” in notebook e che può **attaccare/staccare sorgenti**, recuperare documenti e (opzionale) farli riassumere da un LLM **con citazioni verificabili**.

