import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.game import ScopaGame

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates", autoescape=False)

games = {}  # game_id -> {"game": ScopaGame, "players": [id1,id2], "game_initialized": bool}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/new_game")
def new_game(player: dict):
    player_id = player.get("player_id")
    if not player_id:
        return JSONResponse({"error": "player_id richiesto"}, status_code=400)

    # Cerca partita con meno di 2 giocatori
    for game_id, g in games.items():
        if len(g["players"]) < 2:
            g["players"].append(player_id)
            if len(g["players"]) == 2 and not g.get("game_initialized"):
                g["game"].setup_game()
                g["game_initialized"] = True
            return {"game_id": game_id}

    # Crea nuova partita
    game_id = str(uuid.uuid4())
    games[game_id] = {"game": ScopaGame(), "players": [player_id], "game_initialized": False}
    return {"game_id": game_id}

@app.get("/state/{game_id}/{player_id}")
def get_state(game_id: str, player_id: str):
    g = games.get(game_id)
    if not g or player_id not in g["players"]:
        return JSONResponse({"error": "game not found"}, status_code=404)
    if not g.get("game_initialized"):
        return JSONResponse({"error": "waiting for second player"}, status_code=404)

    game = g["game"]
    player_index = g["players"].index(player_id)
    other_index = 1 - player_index

    return {
        "table": game.table,
        "hand": game.hands[player_index],
        "player_taken": game.taken[player_index],
        "opponent_taken": game.taken[other_index],
        "opponent_hand_size": len(game.hands[other_index]),
        "scopa": game.scopa[player_index],
        "opponent_scopa": game.scopa[other_index],
        "turn": game.turn,
        "game_over": game.game_over(),
        "score": game.score()
    }

@app.post("/play/{game_id}/{player_id}/{card_index}")
def play_card(game_id: str, player_id: str, card_index: int):
    g = games.get(game_id)
    if not g or player_id not in g["players"]:
        return JSONResponse({"error": "game not found"}, status_code=404)

    game = g["game"]
    player_index = g["players"].index(player_id)
    result = game.play_card(player_index, card_index)

    if "error" in result:
        return JSONResponse(result, status_code=400)

    other_index = 1 - player_index
    # Restituisci subito tutto lo stato aggiornato
    return {
        "table": game.table,
        "hand": game.hands[player_index],
        "player_taken": game.taken[player_index],
        "opponent_taken": game.taken[other_index],
        "opponent_hand_size": len(game.hands[other_index]),
        "scopa": game.scopa[player_index],
        "opponent_scopa": game.scopa[other_index],
        "turn": game.turn,
        "game_over": game.game_over(),
        "score": game.score()
    }

