// deck.js
const deck = [
  {id: 1, suit: "coins", value: 1}, {id: 2, suit: "coins", value: 2}, {id: 3, suit: "coins", value: 3},
  {id: 4, suit: "coins", value: 4}, {id: 5, suit: "coins", value: 5}, {id: 6, suit: "coins", value: 6},
  {id: 7, suit: "coins", value: 7}, {id: 8, suit: "coins", value: 8}, {id: 9, suit: "coins", value: 9},
  {id: 10, suit: "coins", value: 10},

  {id: 11, suit: "cups", value: 1}, {id: 12, suit: "cups", value: 2}, {id: 13, suit: "cups", value: 3},
  {id: 14, suit: "cups", value: 4}, {id: 15, suit: "cups", value: 5}, {id: 16, suit: "cups", value: 6},
  {id: 17, suit: "cups", value: 7}, {id: 18, suit: "cups", value: 8}, {id: 19, suit: "cups", value: 9},
  {id: 20, suit: "cups", value: 10},

  {id: 21, suit: "swords", value: 1}, {id: 22, suit: "swords", value: 2}, {id: 23, suit: "swords", value: 3},
  {id: 24, suit: "swords", value: 4}, {id: 25, suit: "swords", value: 5}, {id: 26, suit: "swords", value: 6},
  {id: 27, suit: "swords", value: 7}, {id: 28, suit: "swords", value: 8}, {id: 29, suit: "swords", value: 9},
  {id: 30, suit: "swords", value: 10},

  {id: 31, suit: "clubs", value: 1}, {id: 32, suit: "clubs", value: 2}, {id: 33, suit: "clubs", value: 3},
  {id: 34, suit: "clubs", value: 4}, {id: 35, suit: "clubs", value: 5}, {id: 36, suit: "clubs", value: 6},
  {id: 37, suit: "clubs", value: 7}, {id: 38, suit: "clubs", value: 8}, {id: 39, suit: "clubs", value: 9},
  {id: 40, suit: "clubs", value: 10}
];

// deck.js deve essere incluso prima
function cardImg(card) {
    // Trova la carta nel deck usando seme e valore
    const found = deck.find(c => c.suit === card.suit && c.value === card.value);
    
    // Se non trovi la carta, mostra il retro
    if (!found) return "/static/back.jpg";

    // Restituisci il percorso corretto dell'immagine
    return `/static/cards/${found.id}.jpg`;
}
