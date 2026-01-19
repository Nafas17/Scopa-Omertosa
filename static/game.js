// /static/game.js

// =========================================
// Controllo login + nickname
// =========================================
let playerId = localStorage.getItem("player_id");
let username = localStorage.getItem("username") || playerId || "Ospite";

if (!playerId) {
    window.location.href = "/login";
}

// Mostra nickname
document.getElementById("pid").innerText = username;

let gameId = null;          // numero intero
let gameEnded = false;
let deckImages = [];
let pollingInterval = null;

// ==========================
// CARICAMENTO IMMAGINI CARTE
// ==========================
async function loadDeck() {
    try {
        const resp = await fetch("/static/cards.json");
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        deckImages = await resp.json();
    } catch (err) {
        console.error("Errore cards.json:", err);
        alert("Errore caricamento immagini carte.");
    }
}

function getCardImage(card) {
    if (!Array.isArray(card) || card.length < 2) return "/static/back.jpg";
    const [value, suit] = card;
    const found = deckImages.find(c => c.value === value && c.suit?.toLowerCase() === suit.toLowerCase());
    return found?.img || "/static/back.jpg";
}

// ==========================
// CREA O ENTRA IN PARTITA
// ==========================
async function joinOrCreateGame() {
    const preferredGameId = localStorage.getItem("preferred_game_id");
    let endpoint = "/create_game";
    let body = { player_id: playerId };

    // Se l'utente ha inserito un ID partita → tenta JOIN
    if (preferredGameId) {
        const parsed = parseInt(preferredGameId, 10);
        if (!isNaN(parsed) && parsed > 0) {
            gameId = parsed;
            document.getElementById("gid").innerText = gameId;
            localStorage.removeItem("preferred_game_id");

            endpoint = `/join_game/${gameId}`;
            console.log(`[JOIN] Tentativo di entrare in partita ${gameId} con nickname '${username}'`);
        }
    } else {
        console.log(`[CREATE] Creazione nuova partita per '${username}'`);
    }

    try {
        const resp = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });

        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            const msg = err.detail || `Errore ${resp.status}`;
            alert(msg);
            console.error("Errore join/crea:", msg, resp.status);

            // Se join fallito (es. partita piena/non trovata) → crea nuova
            if (endpoint.startsWith("/join_game")) {
                console.warn("Join fallito, fallback a creazione nuova partita");
                localStorage.removeItem("preferred_game_id");
                return joinOrCreateGame(); // solo una ricorsione
            }
            return;
        }

        const data = await resp.json();
        gameId = data.game_id;
        document.getElementById("gid").innerText = gameId;

        if (endpoint.startsWith("/join_game")) {
            console.log(`[JOIN OK] Entrato in partita ${gameId}`);
        } else {
            console.log(`[CREATE OK] Nuova partita ${gameId} creata`);
        }

    } catch (err) {
        console.error("Errore connessione:", err);
        alert("Errore di connessione al server. Riprova.");
    }
}

// ==========================
// RENDER CARTE
// ==========================
function renderCards(containerId, cards = [], clickable = false, onClick = null) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = "";

    cards.forEach((card, idx) => {
        const img = document.createElement("img");
        img.classList.add("card-img");
        img.src = getCardImage(card);
        img.alt = card.length === 2 ? `${card[0]} di ${card[1]}` : "Carta";
        img.dataset.index = idx;

        if (clickable) {
            img.classList.remove("disabled");
            img.onclick = () => onClick?.(idx);
        } else {
            img.classList.add("disabled");
        }

        container.appendChild(img);
    });
}

// ==========================
// MANO AVVERSARIO
// ==========================
function renderOpponentHand(count = 0) {
    let container = document.getElementById("opp_hand");
    if (!container) {
        container = document.createElement("div");
        container.id = "opp_hand";
        container.classList.add("board", "opponent");
        const section = document.querySelector(".opponent-hand-section") || document.body;
        section.appendChild(container);
    }

    renderCards("opp_hand", Array(count).fill([0, "hidden"]), false);
}

// ==========================
// AGGIORNA STATO (polling)
// ==========================
async function updateGameState() {
    if (!gameId || gameEnded) return;

    try {
        const resp = await fetch(`/state/${gameId}/${playerId}`);
        if (resp.status === 404) {
            document.getElementById("turn").innerText = "Partita non trovata o terminata";
            document.getElementById("turn").className = "turn-wait";
            return;
        }
        if (!resp.ok) {
            console.warn("Errore fetch stato:", resp.status);
            return;
        }

        const state = await resp.json();

        if (state.waiting === true) {
            document.getElementById("turn").innerText = `In attesa del secondo giocatore... (${state.players_count}/2)`;
            document.getElementById("turn").className = "turn-wait";
        } else {
            renderCards("table", state.table || [], false);
            renderCards("hand", state.hand || [], state.your_turn, playCard);
            renderOpponentHand(state.opponent_hand_size || 0);

            document.getElementById("taken_count").innerText = state.player_taken?.length || 0;
            document.getElementById("opp_taken_count").innerText = state.opponent_taken?.length || 0;
            document.getElementById("scopa").innerText = state.scopa || 0;
            document.getElementById("opp_scopa").innerText = state.opponent_scopa || 0;

            const turnEl = document.getElementById("turn");
            if (state.your_turn) {
                turnEl.innerText = "È il tuo turno!";
                turnEl.className = "turn-active";
            } else {
                turnEl.innerText = "Turno dell'avversario";
                turnEl.className = "turn-wait";
            }
        }

        if (state.game_over && !gameEnded) {
            gameEnded = true;
            clearInterval(pollingInterval);
            document.getElementById("turn").innerText = "Partita terminata! Preparo il punteggio...";

            // Debug forte
            console.log("=== FINE PARTITA ===");
            console.log("state.score dal server:", state.score);

            const scoreSafe = state.score || {
                player1: 0,
                player2: 0,
                scope: [0, 0],
                carte_p1: 0,
                carte_p2: 0,
                denari_p1: 0,
                denari_p2: 0
            };

            localStorage.setItem("lastGameScore", JSON.stringify(scoreSafe));
            console.log("Salvato in localStorage:", localStorage.getItem("lastGameScore"));

            // Delay più lungo per garantire salvataggio
            setTimeout(() => {
                console.log("Reindirizzamento a /final_score...");
                window.location.href = "/final_score";
            }, 2000);  // 2 secondi – aumenta a 3000 se ancora non va
        }

// ==========================
// GIOCA CARTA
// ==========================
async function playCard(cardIndex) {
    if (!gameId || gameEnded || !document.getElementById("turn").classList.contains("turn-active")) {
        return;
    }

    try {
        const resp = await fetch(`/play/${gameId}/${playerId}/${cardIndex}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
        });

        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            alert(err.detail || "Mossa non valida");
            return;
        }

        await new Promise(r => setTimeout(r, 400));
        await updateGameState();

    } catch (err) {
        console.error("Errore giocata:", err);
        alert("Errore di connessione.");
    }
}

// ==========================
// INIZIO
// ==========================
(async () => {
    await loadDeck();
    await joinOrCreateGame();

    if (gameId) {
        pollingInterval = setInterval(updateGameState, 1200);
        await updateGameState();
    }
})();