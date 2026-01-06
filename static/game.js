let player_id = localStorage.getItem("player_id");
if (!player_id) {
    player_id = crypto.randomUUID();
    localStorage.setItem("player_id", player_id);
}
document.getElementById("pid").innerText = player_id;

let game_id = null;
let lastScopa = 0;
let lastHandSize = 0;
let gameEnded = false;

// Percorso immagini
function cardImg(card) {
    const found = deck.find(c => c.suit === card.suit && c.value === card.value);
    if (!found) return "/static/back.jpg";
    return `/static/Cards/${found.id}.jpg`;
}

// Join partita
async function joinGame() {
    const r = await fetch("/new_game", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({player_id})
    });
    const d = await r.json();
    game_id = d.game_id;
    document.getElementById("gid").innerText = game_id;
}

// Aggiorna stato
async function loadState() {
    if (!game_id) return;

    try {
        const r = await fetch(`/state/${game_id}/${player_id}`);
        if (r.status === 404) {
            document.getElementById("turn").innerText = "In attesa dell'altro giocatore...";
            return;
        }

        const d = await r.json();

        document.getElementById("turn").innerText =
            d.turn === player_id ? "È il tuo turno" : "Turno avversario";

        // Tavolo
        const tableDiv = document.getElementById("table");
        tableDiv.innerHTML = "";
        d.table.forEach(c => {
            const img = document.createElement("img");
            img.src = cardImg(c);
            img.classList.add("card-img");
            tableDiv.appendChild(img);
        });

        // Mano del giocatore
        const handDiv = document.getElementById("hand");
        handDiv.innerHTML = "";
        d.hand.forEach((c, i) => {
            const cardDiv = document.createElement("div");
            cardDiv.classList.add("card");
            if (d.turn !== player_id) cardDiv.classList.add("disabled");

            const img = document.createElement("img");
            img.src = cardImg(c);
            img.alt = `${c.value} di ${c.suit}`;
            if (d.turn === player_id) img.addEventListener("click", () => play(i));

            cardDiv.appendChild(img);
            handDiv.appendChild(cardDiv);
        });

        // Carte avversario (retro)
        const oppDiv = document.getElementById("opponent");
        oppDiv.innerHTML = "";
        d.opponent_taken.forEach(() => {
            const img = document.createElement("img");
            img.src = "/static/back.jpg";
            img.classList.add("card-img");
            oppDiv.appendChild(img);
        });

        // Aggiorna prese e scopa
        document.getElementById("taken").innerText = d.player_taken.length;
        document.getElementById("scopa").innerText = d.scopa;
        document.getElementById("opp_scopa").innerText = d.opponent_scopa;

        if (d.game_over && !gameEnded) {
            gameEnded = true;
            document.getElementById("turn").innerText = "🎉 Partita finita!";
        }

    } catch (err) {
        console.error("Errore nel loadState:", err);
        document.getElementById("turn").innerText = "Errore di connessione al server...";
    }
}

// Gioca carta
async function play(i) {
    await fetch(`/play/${game_id}/${player_id}/${i}`, {method: "POST"});
    loadState();
}

// Avvio
joinGame();
setInterval(loadState, 1000);
