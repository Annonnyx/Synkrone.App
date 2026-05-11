"use client";

import { useEffect, useRef } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { AlertTriangle } from "lucide-react";

type TerminalType = import("xterm").Terminal;
type FitAddonType = import("xterm-addon-fit").FitAddon;

export default function TerminalPage() {
  const termRef = useRef<HTMLDivElement>(null);
  const { data: session } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (!session) return;
    if (!session.user.roles.includes("LEADER")) {
      router.replace("/dev");
      return;
    }

    let disposed = false;
    let ws: WebSocket | null = null;
    let resizeObserver: ResizeObserver | null = null;
    let term: TerminalType | null = null;

    async function init() {
      const [{ Terminal }, { FitAddon }] = await Promise.all([
        import("xterm"),
        import("xterm-addon-fit"),
        import("xterm/css/xterm.css"),
      ]);

      if (disposed || !termRef.current) return;

      term = new Terminal({ theme: { background: "#0a0a0a", foreground: "#00ff00" }, cursorBlink: true });
      const fitAddon = new FitAddon();
      term.loadAddon(fitAddon);
      term.open(termRef.current);
      fitAddon.fit();

      const protocol = window.location.protocol === "https:" ? "wss" : "ws";
      ws = new WebSocket(`${protocol}://${window.location.host}/api/admin/terminal/ws`);

      ws.onopen = () => term!.writeln("Connexion établie. Bienvenue Leader.");
      ws.onmessage = (e) => term!.write(e.data);
      ws.onclose = () => term!.writeln("\r\nConnexion fermée.");
      ws.onerror = () => term!.writeln("\r\nErreur de connexion au terminal.");

      term.onData((data: string) => ws!.send(JSON.stringify({ type: "input", data })));

      resizeObserver = new ResizeObserver(() => fitAddon.fit());
      resizeObserver.observe(termRef.current);
    }

    init();

    return () => {
      disposed = true;
      if (ws) ws.close();
      if (term) term.dispose();
      if (resizeObserver) resizeObserver.disconnect();
    };
  }, [session, router]);

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] p-6">
      <div className="bg-yellow-900/20 border border-yellow-700/50 text-yellow-400 text-sm p-3 rounded-lg mb-4 flex items-center gap-2">
        <AlertTriangle className="h-4 w-4 shrink-0" />
        Toutes les commandes exécutées dans ce terminal sont enregistrées avec votre identité et le timestamp.
      </div>
      <div ref={termRef} className="flex-1 rounded-lg overflow-hidden border border-neutral-800 bg-[#0a0a0a]" />
    </div>
  );
}
