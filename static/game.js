let player_id = localStorage.getItem("player_id") || crypto.randomUUID();
localStorage.setItem("player_id", player_id);
document.getElementById("pid").innerText = player_id;

let game_id = null;
let gameEnded = false;
let deck = [];

// Carica JSON delle carte
async function loadDeck() {
    const r = await fetch("/static/cards.json");
    deck = await r.json();
}

// Percorso immagine
function cardImg(card) {
    const found = deck.find(c => c.value === card[0] && c.suit === card[1]);
    return found ? found.img : "/static/back.jpg";
}

// Join partita
async function joinGame() {
    const r = await fetch("/new_game", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
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

        // Mostra chi è il turno
        document.getElementById("turn").innerText = d.your_turn ? "È il tuo turno" : "Turno avversario";

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
            const img = document.createElement("img");
            img.src = cardImg(c);
            img.classList.add("card-img");
            if (d.your_turn) img.addEventListener("click", () => play(i));
            else img.classList.add("disabled");
            handDiv.appendChild(img);
        });

        // Carte avversario (retro)
        const oppDiv = document.getElementById("opp_taken");
        oppDiv.innerHTML = "";
        for (let i = 0; i < d.opponent_hand_size; i++) {
            const img = document.createElement("img");
            img.src = "/static/back.jpg";
            img.classList.add("card-img");
            oppDiv.appendChild(img);
        }

        // Prese e scope
        document.getElementById("taken").innerText = d.player_taken.length;
        document.getElementById("scopa").innerText = d.scopa;
        document.getElementById("opp_scopa").innerText = d.opponent_scopa;

        if (d.game_over && !gameEnded) {
            gameEnded = true;
            document.getElementById("turn").innerText = "🎉 Partita finita!";
        }

    } catch (err) {
        console.error(err);
    }
}


// Gioca carta
async function play(i){
    await fetch(`/play/${game_id}/${player_id}/${i}`,{method:"POST"});
    loadState();
}

// Avvio
(async ()=>{
    await loadDeck();
    joinGame();
    setInterval(loadState,1000);
})();
