import { createServer } from "http";
import { parse } from "url";
import next from "next";
import { WebSocketServer } from "ws";
import { spawn } from "child_process";

const dev = process.env.NODE_ENV !== "production";
const app = next({ dev });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  const server = createServer((req, res) => {
    const parsedUrl = parse(req.url!, true);
    handle(req, res, parsedUrl);
  });

  // Use noServer to avoid intercepting Next.js HMR WebSocket connections
  const wss = new WebSocketServer({ noServer: true });

  server.on("upgrade", (request, socket, head) => {
    if (request.url === "/api/admin/terminal/ws") {
      wss.handleUpgrade(request, socket, head, (ws) => {
        wss.emit("connection", ws, request);
      });
    }
    // Let other upgrade requests (e.g. Next.js HMR) pass through
  });

  wss.on("connection", (ws) => {
    // TODO: Vérifier l'authentification et le rôle LEADER via le cookie de session
    console.log("Terminal WebSocket connecté");

    const shell = spawn("bash", [], {
      env: { ...process.env, TERM: "xterm-256color" },
    });

    const safeSend = (data: string) => {
      if (ws.readyState === ws.OPEN) ws.send(data);
    };

    shell.stdout.on("data", (data: Buffer) => safeSend(data.toString()));
    shell.stderr.on("data", (data: Buffer) => safeSend(data.toString()));

    ws.on("message", (message: Buffer) => {
      try {
        const { type, data } = JSON.parse(message.toString());
        if (type === "input" && shell.stdin.writable) {
          shell.stdin.write(data);
          if (data === "\r" || data === "\n") {
            // En production : enregistrer dans AdminLog
          }
        }
      } catch {}
    });

    ws.on("close", () => {
      shell.kill();
      shell.stdout.removeAllListeners("data");
      shell.stderr.removeAllListeners("data");
    });
    shell.on("close", () => {
      if (ws.readyState === ws.OPEN) ws.close();
    });
  });

  server.listen(3000, "0.0.0.0", () => {
    console.log("> Serveur démarré sur http://0.0.0.0:3000");
  });
});
