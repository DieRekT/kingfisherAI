"use client";
import {useState, useRef} from "react";
import {motion, AnimatePresence} from "framer-motion";
import clsx from "clsx";

type Citation = { url:string; title:string; snippet?:string };
type ImageRef = { url:string; alt?:string; credit?:string; provider?:string };
type Step = { title:string; body:string; image?:ImageRef; citations?:Citation[] };
type Card = { 
  kind:"howto"|"concept"|"plan"|"reference"; 
  title:string; 
  theme:string; 
  summary?:string; 
  steps:Step[]; 
  images:ImageRef[];
  citations?:Citation[];
};

export default function Page(){
  const [q, setQ] = useState("");
  const [text, setText] = useState<string>("");
  const [cards, setCards] = useState<Card[]>([]);
  const [pending, setPending] = useState(false);
  const [status, setStatus] = useState<string>("");
  const eventSourceRef = useRef<EventSource | null>(null);

  const askStreaming = async () => {
    if(!q.trim()) return;
    setPending(true);
    setText("");
    setCards([]);
    setStatus("Thinking...");
    
    // Check if EventSource is available
    if(typeof EventSource === "undefined") {
      // Fallback to non-streaming
      return askNonStreaming();
    }
    
    try {
      // Close any existing connection
      if(eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      
      const url = `http://127.0.0.1:8000/api/chat/stream?message=${encodeURIComponent(q)}`;
      const es = new EventSource(url);
      eventSourceRef.current = es;
      
      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          switch(data.type) {
            case "status":
              setStatus(data.stage === "planning" ? "Planning..." : "Fetching data...");
              break;
            
            case "cards":
              setText(data.text || "");
              setCards(data.cards || []);
              setStatus("");
              break;
            
            case "tool":
              // Optionally show tool progress
              break;
            
            case "result":
              setText(data.payload.text || "");
              setCards(data.payload.lesson_cards || []);
              setStatus("");
              setPending(false);
              es.close();
              break;
            
            case "error":
              console.error("Stream error:", data.message);
              setStatus("");
              setPending(false);
              es.close();
              break;
          }
        } catch(e) {
          console.error("Parse error:", e);
        }
      };
      
      es.onerror = () => {
        setStatus("");
        setPending(false);
        es.close();
      };
      
    } catch(e) {
      console.error("Streaming error:", e);
      setPending(false);
      // Fallback to non-streaming
      await askNonStreaming();
    }
  };

  const askNonStreaming = async () => {
    if(!q.trim()) return;
    setPending(true);
    try{
      const r = await fetch("http://127.0.0.1:8000/api/chat",{
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        body: JSON.stringify({ message: q })
      });
      const data = await r.json();
      setText(data.text || "");
      setCards(data.lesson_cards || []);
    } finally{
      setPending(false);
    }
  };

  const ask = askStreaming;

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-3xl font-semibold text-white">Kingfisher 2465</h1>
        <div className="flex gap-2">
          <input className="px-3 py-2 rounded-xl border bg-white min-w-[360px]" placeholder="Ask anything… e.g. How to tie a uni knot"
            value={q} onChange={e=>setQ(e.target.value)} onKeyDown={e=>e.key==='Enter'&&ask()} />
          <button onClick={ask} disabled={pending} className={clsx("px-4 py-2 rounded-xl text-white",
            pending ? "bg-neutral-500" : "bg-indigo-600 hover:bg-indigo-700")}>{pending?(status||"Thinking…"):"Ask"}</button>
        </div>
      </header>

      {text && (
        <section className="card p-5">
          <div className="text-sm text-neutral-500 mb-2">Chat</div>
          <div className="prose max-w-none">{text}</div>
        </section>
      )}

      <AnimatePresence>
        {cards.length>0 && (
          <section className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {cards.map((c,idx)=>(
              <motion.div key={idx} layout initial={{opacity:0, y:8}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-8}}
                className="card overflow-hidden">
                <div className={clsx("h-2", {
                  "bg-river": c.theme==="river",
                  "bg-ocean": c.theme==="ocean",
                  "bg-earth": c.theme==="earth",
                  "bg-amber": c.theme==="amber",
                  "bg-slate": c.theme==="slate",
                  "bg-emerald": c.theme==="emerald",
                  "bg-indigo": c.theme==="indigo",
                })}/>
                <div className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold">{c.title}</h3>
                    <span className="chip">{c.kind}</span>
                  </div>
                  {c.images?.[0]?.url && (
                    <div className="mb-3">
                      <img src={c.images[0].url} alt={c.images[0].alt||""} className="rounded-xl w-full object-cover max-h-44" />
                      {c.images[0].credit && (
                        <div className="text-xs text-neutral-400 mt-1">Photo: {c.images[0].credit}</div>
                      )}
                    </div>
                  )}
                  {c.summary && <p className="text-sm text-neutral-600 mb-3">{c.summary}</p>}
                  <div className="space-y-3">
                    {c.steps?.map((s,i)=>(
                      <div key={i} className="rounded-xl border p-3">
                        <div className="font-medium mb-1">{i+1}. {s.title}</div>
                        <div className="text-sm text-neutral-700 whitespace-pre-wrap">{s.body}</div>
                        {s.image?.url && (
                          <div className="mt-2">
                            <img src={s.image.url} alt={s.image.alt||""} className="rounded-lg w-full object-cover max-h-40" />
                            {s.image.credit && (
                              <div className="text-xs text-neutral-400 mt-1">Photo: {s.image.credit}</div>
                            )}
                          </div>
                        )}
                        {s.citations && s.citations.length > 0 && (
                          <div className="mt-2 pt-2 border-t text-xs text-neutral-500">
                            Source: {s.citations.map((cit, ci) => (
                              <a key={ci} href={cit.url} target="_blank" rel="noopener noreferrer" 
                                className="text-indigo-600 hover:underline">
                                {cit.title || cit.url}
                              </a>
                            )).reduce((prev: any, curr) => [prev, ', ', curr] as any)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                  {c.citations && c.citations.length > 0 && (
                    <div className="mt-3 pt-3 border-t text-xs text-neutral-500">
                      Sources: {c.citations.map((cit, ci) => (
                        <a key={ci} href={cit.url} target="_blank" rel="noopener noreferrer" 
                          className="text-indigo-600 hover:underline mr-2">
                          {cit.title || cit.url}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </section>
        )}
      </AnimatePresence>
    </div>
  );
}

