import random
from itertools import combinations

SEMI = ["denari", "coppe", "spade", "bastoni"]
VALORI = list(range(1, 11))

class ScopaGame:
    def __init__(self):
        self.deck = [(v, s) for s in SEMI for v in VALORI]
        random.shuffle(self.deck)

        self.table = []
        self.hands = [[], []]
        self.taken = [[], []]
        self.scopa = [0, 0]
        self.turn = 0

    def setup_game(self):
        """Inizializza tavolo e distribuisce le prime mani"""
        self.table = [self.deck.pop() for _ in range(4)]
        self.deal()

    def deal(self):
        """Distribuisce 3 carte a ciascun giocatore se il mazzo non è vuoto"""
        if self.deck:
            for i in range(2):
                n = min(3, len(self.deck))
                self.hands[i] = [self.deck.pop() for _ in range(n)]

    def possible_captures(self, card, table):
        """Restituisce combinazioni di carte sul tavolo che sommano al valore della carta giocata"""
        results = []
        for r in range(1, len(table)+1):
            for combo in combinations(table, r):
                if sum(c[0] for c in combo) == card[0]:
                    results.append(combo)
        return results

    def play_card(self, player_index, card_index):
        """Gioca una carta e gestisce catture e scopa"""
        if player_index != self.turn:
            return {"error": "non è il tuo turno"}

        hand = self.hands[player_index]
        if card_index >= len(hand):
            return {"error": "indice carta non valido"}

        card = hand.pop(card_index)
        captures = self.possible_captures(card, self.table)

        if captures:
            taken_combo = captures[0]
            for c in taken_combo:
                self.table.remove(c)
            self.taken[player_index].extend(taken_combo + (card,))
            if not self.table:
                self.scopa[player_index] += 1
        else:
            self.table.append(card)

        # Cambio turno
        self.turn = 1 - self.turn

        # Nuova mano se entrambe vuote e mazzo non vuoto
        if all(len(h) == 0 for h in self.hands) and self.deck:
            self.deal()

        return {"status": "ok"}

    def game_over(self):
        return not self.deck and all(len(h) == 0 for h in self.hands)

    def score(self):
        """Calcola punti finali basandosi sulle carte prese"""
        def calc(taken, scopa):
            pts = scopa
            if len(taken) > 20: pts += 1
            if len([c for c in taken if c[1] == "denari"]) > 5: pts += 1
            if (7, "denari") in taken: pts += 1
            return pts

        return {
            "player1": calc(self.taken[0], self.scopa[0]),
            "player2": calc(self.taken[1], self.scopa[1])
        }
