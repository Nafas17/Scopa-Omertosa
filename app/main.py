import time
from typing import Dict, List
import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.game import ScopaGame

app = FastAPI(title="Scopa Online", description="Scopa multiplayer realtime")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Contatore ID partita
next_game_id: int = 1

# Storage partite
games: Dict[int, dict] = {}

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, game_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(game_id, []).append(websocket)

    def disconnect(self, game_id: int, websocket: WebSocket):
        if game_id in self.active_connections:
            self.active_connections[game_id] = [
                ws for ws in self.active_connections[game_id] if ws != websocket
            ]
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]

    async def broadcast(self, game_id: int, message: dict):
        if game_id not in self.active_connections:
            return
        for ws in self.active_connections[game_id][:]:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(game_id, ws)

manager = ConnectionManager()

def get_safe_state(game: ScopaGame, player_id: str, game_data: dict) -> dict:
    players = game_data["players"]
    if player_id not in players:
        raise HTTPException(403, "Non sei partecipante di questa partita")

    player_index = players.index(player_id)
    opp_index = 1 - player_index

    return {
        "your_turn": game.turn == player_index,
        "table": game.table,
        "hand": game.hands[player_index],
        "opponent_hand_size": len(game.hands[opp_index]),
        "player_taken": game.taken[player_index],
        "opponent_taken": game.taken[opp_index],
        "scopa": game.scopa[player_index],
        "opponent_scopa": game.scopa[opp_index],
        "game_over": game.game_over(),
        "score": game.score(),
        "player_index": player_index,
        "timestamp": time.time()
    }

# ────────────────────────────────────────────────
# PAGINE HTML
# ────────────────────────────────────────────────
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
# PAGINA DI VITTORIA / PUNTEGGIO FINALE
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
@app.get("/final_score", response_class=HTMLResponse)
async def final_score_page(request: Request):
    return templates.TemplateResponse("final_score.html", {"request": request})

# ────────────────────────────────────────────────
# CREA NUOVA PARTITA
# ────────────────────────────────────────────────
@app.post("/create_game")
async def create_game(data: dict):
    global next_game_id

    player_id = str(data.get("player_id") or "").strip()
    if not player_id:
        raise HTTPException(400, "player_id obbligatorio")

    game_id = next_game_id
    next_game_id += 1

    games[game_id] = {
        "game": ScopaGame(),
        "players": [player_id],
        "game_initialized": False,
        "created_at": time.time(),
        "last_activity": time.time()
    }

    print(f"[CREATE] Nuova partita {game_id} creata da '{player_id}'")
    return {"game_id": game_id}

# ────────────────────────────────────────────────
# ENTRA IN PARTITA ESISTENTE
# ────────────────────────────────────────────────
@app.post("/join_game/{game_id}")
async def join_game(game_id: int, data: dict):
    player_id = str(data.get("player_id") or "").strip()
    if not player_id:
        raise HTTPException(400, "player_id obbligatorio")

    g = games.get(game_id)
    if not g:
        raise HTTPException(404, "Partita non trovata")

    if len(g["players"]) >= 2:
        raise HTTPException(403, "Partita piena")

    if player_id not in g["players"]:
        g["players"].append(player_id)
        g["last_activity"] = time.time()
        print(f"[JOIN] Aggiunto '{player_id}' alla partita {game_id}")

    if len(g["players"]) == 2 and not g.get("game_initialized"):
        g["game"].setup_game()
        g["game_initialized"] = True
        print(f"[JOIN] Partita {game_id} inizializzata con 2 giocatori!")

    await manager.broadcast(game_id, {"type": "player_joined", "players": len(g["players"])})

    return {"game_id": game_id, "joined": True}

# ────────────────────────────────────────────────
# STATO PARTITA
# ────────────────────────────────────────────────
@app.get("/state/{game_id}/{player_id}")
async def get_state(game_id: int, player_id: str):
    g = games.get(game_id)
    if not g:
        raise HTTPException(404, "Partita non trovata")

    if not g["game_initialized"]:
        return {"waiting": True, "players_count": len(g["players"])}

    return get_safe_state(g["game"], player_id, g)

# ────────────────────────────────────────────────
# GIOCA CARTA
# ────────────────────────────────────────────────
@app.post("/play/{game_id}/{player_id}/{card_index}")
async def play_card(game_id: int, player_id: str, card_index: int):
    g = games.get(game_id)
    if not g or player_id not in g["players"]:
        raise HTTPException(404, "Partita non trovata o non partecipante")

    game = g["game"]
    player_index = g["players"].index(player_id)

    if game.turn != player_index:
        raise HTTPException(400, "Non è il tuo turno")

    result = game.play_card(player_index, card_index)
    if "error" in result:
        raise HTTPException(400, result["error"])

    g["last_activity"] = time.time()

    # Invia aggiornamento a entrambi i giocatori
    for pid in g["players"]:
        await manager.broadcast(game_id, {
            "type": "state_update",
            **get_safe_state(game, pid, g)
        })

    return get_safe_state(game, player_id, g)

# ────────────────────────────────────────────────
# WEBSOCKET
# ────────────────────────────────────────────────
@app.websocket("/ws/{game_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: int, player_id: str):
    g = games.get(game_id)
    if not g or player_id not in g["players"]:
        await websocket.close(4001)
        return

    await manager.connect(game_id, websocket)

    try:
        await websocket.send_json({
            "type": "connected",
            **get_safe_state(g["game"], player_id, g)
        })

        while True:
            await websocket.receive_json()
    except WebSocketDisconnect:
        manager.disconnect(game_id, websocket)
        await manager.broadcast(game_id, {"type": "player_disconnected", "player_id": player_id})

# ────────────────────────────────────────────────
# HEALTH
# ────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status": "ok",
        "games_count": len(games),
        "next_game_id": next_game_id,
        "active_ws": {gid: len(conns) for gid, conns in manager.active_connections.items()}
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)