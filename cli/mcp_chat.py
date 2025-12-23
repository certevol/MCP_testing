import asyncio
import argparse
import json
import httpx
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

OLLAMA_URL = "http://localhost:11434/api/generate"

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question", help="Es: 'agentic RAG evaluation'")
    ap.add_argument("--k", type=int, default=3, help="Risultati per sorgente")
    ap.add_argument("--llm", action="store_true", help="Genera risposta finale con LLM locale (Ollama)")
    ap.add_argument("--model", type=str, default="llama3.2", help="Modello Ollama (es: llama3.2)")
    args = ap.parse_args()

    arxiv = Client(StdioTransport(command="python", args=["servers/arxiv_server.py"]))
    openalex = Client(StdioTransport(command="python", args=["servers/openalex_server.py"]))

    async with arxiv, openalex:
        tools_a = await arxiv.list_tools()
        tools_o = await openalex.list_tools()

        print("\n== Tools arXiv ==")
        for t in tools_a:
            print("-", t.name)

        print("\n== Tools OpenAlex ==")
        for t in tools_o:
            print("-", t.name)

        ax = await arxiv.call_tool("arxiv_search", {"topic": args.question, "max_results": args.k})
        ox = await openalex.call_tool("openalex_search_works", {"query": args.question, "per_page": args.k})

        def unpack(resp):
            content = None
            for key in ("data", "result", "content", "value"):
                if hasattr(resp, key):
                    v = getattr(resp, key)
                    if v is not None:
                        content = v
                        break
            if content is None:
                content = resp

            # lista di TextContent
            if isinstance(content, list) and content and hasattr(content[0], "text"):
                text = "\n".join(c.text for c in content if hasattr(c, "text"))
                try:
                    return json.loads(text)
                except Exception:
                    return text

            # singolo TextContent
            if hasattr(content, "text"):
                try:
                    return json.loads(content.text)
                except Exception:
                    return content.text

            if isinstance(content, (list, dict)):
                return content

            return content

        ax_items = unpack(ax)
        ox_items = unpack(ox)

        print("\n==============================")
        print("RISULTATI arXiv (preprint)")
        print("==============================")
        if isinstance(ax_items, str):
            print(ax_items)
        elif not ax_items:
            print("(nessun risultato)")
        else:
            for i, p in enumerate(ax_items, 1):
                print(f"{i}. {p.get('title')}")
                print(f"   PDF: {p.get('pdf_url')}\n")

        print("\n==============================")
        print("RISULTATI OpenAlex (panoramica + citazioni)")
        print("==============================")
        if isinstance(ox_items, str):
            print(ox_items)
        elif not ox_items:
            print("(nessun risultato)")
        else:
            for i, w in enumerate(ox_items, 1):
                print(f"{i}. {w.get('title')}")
                print(f"   Year: {w.get('publication_year')} | Cited by: {w.get('cited_by_count')}")
                print(f"   DOI: {w.get('doi')} | Source: {w.get('primary_location')}")
                print(f"   OpenAlex: {w.get('openalex_url')}\n")

        if not args.llm:
            print("\n=== Sintesi (senza LLM) ===")
            print("- arXiv: preprint molto recenti, abstract + PDF.")
            print("- OpenAlex: copertura più ampia + segnali come citazioni/anno.")
            print("Step successivo: usare un LLM (locale) nel client per fondere i risultati in una risposta unica.")
            return

        # --- LLM finale (Ollama) ---
        prompt = f"""
Sei un assistente di ricerca scientifica.

REGOLE OBBLIGATORIE:
1. Usa ESCLUSIVAMENTE le informazioni presenti nelle FONTI fornite.
2. OGNI affermazione fattuale nel testo DEVE avere una citazione inline
   nel formato [arXiv-1], [arXiv-2], [OpenAlex-1], ecc.
3. Se un'informazione NON è supportata dalle fonti, scrivi esplicitamente:
   "Non emergono evidenze dalle fonti fornite."
4. Non usare conoscenza generale o memoria esterna.

DOMANDA:
{args.question}

RISULTATI arXiv (lista, in ordine):
{json.dumps(ax_items, ensure_ascii=False, indent=2)}

RISULTATI OpenAlex (lista, in ordine):
{json.dumps(ox_items, ensure_ascii=False, indent=2)}

OUTPUT RICHIESTO:
- Un paragrafo di sintesi con CITAZIONI INLINE obbligatorie
- Una sezione finale "Fonti" che elenca:
  * [arXiv-i] titolo + link PDF
  * [OpenAlex-j] titolo + DOI o link OpenAlex

"""

        try:
            r = httpx.post(
                OLLAMA_URL,
                json={"model": args.model, "prompt": prompt, "stream": False},
                timeout=120.0
            )
            r.raise_for_status()
            data = r.json()
            answer = data.get("response", "").strip()
        except Exception as e:
            print("\n[ERRORE LLM] Non riesco a chiamare Ollama.")
            print("Assicurati che 'ollama serve' sia attivo e che il modello sia scaricato (es: ollama pull llama3.2).")
            print("Dettagli:", e)
            return

        print("\n==============================")
        print("RISPOSTA (LLM)")
        print("==============================")
        print(answer)

if __name__ == "__main__":
    asyncio.run(main())
