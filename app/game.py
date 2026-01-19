import random
from itertools import combinations
from typing import List, Tuple, Dict, Any, Optional

SEMI = ["denari", "coppe", "spade", "bastoni"]
VALORI = list(range(1, 11))


class ScopaGame:
    def __init__(self):
        self.deck: List[Tuple[int, str]] = [(v, s) for s in SEMI for v in VALORI]
        random.shuffle(self.deck)

        self.table: List[Tuple[int, str]] = []                     # Carte sul tavolo
        self.hands: List[List[Tuple[int, str]]] = [[], []]         # Mani G1 e G2
        self.taken: List[List[Tuple[int, str]]] = [[], []]         # Prese G1 e G2
        self.scopa: List[int] = [0, 0]                             # Scope per giocatore
        self.turn: int = 0                                         # 0 = G1, 1 = G2
        self.game_finished: bool = False                           # Flag fine forzata

    def setup_game(self) -> None:
        """Inizializza partita: 4 carte sul tavolo + 3 a testa"""
        self.table = [self.deck.pop() for _ in range(4)]
        self.deal()
        print("[SETUP] Partita inizializzata")
        print(f"  Tavolo: {self._fmt_cards(self.table)}")
        print(f"  Mano G1: {self._fmt_cards(self.hands[0])}")
        print(f"  Mano G2: {self._fmt_cards(self.hands[1])}")

    def deal(self) -> None:
        """Distribuisce fino a 3 carte per giocatore"""
        if not self.deck:
            return
        for i in range(2):
            n = min(3, len(self.deck))
            if n == 0:
                break
            new_cards = [self.deck.pop() for _ in range(n)]
            self.hands[i].extend(new_cards)
            print(f"[DEAL] G{i+1} riceve {n} carte: {self._fmt_cards(new_cards)}")

    def _fmt_cards(self, cards: List[Tuple[int, str]]) -> str:
        """Formato leggibile per debug"""
        sym = {"denari": "♦", "coppe": "♥", "spade": "♠", "bastoni": "♣"}
        return " ".join(f"{v}{sym.get(s, s[0])}" for v, s in cards) or "(vuoto)"

    def possible_captures(self, card: Tuple[int, str], table: Optional[List[Tuple[int, str]]] = None) -> List[Tuple[Tuple[int, str], ...]]:
        if table is None:
            table = self.table

        results = []
        for r in range(1, len(table) + 1):
            for combo in combinations(table, r):
                if sum(c[0] for c in combo) == card[0]:
                    results.append(combo)

        if not results:
            results = [()]

        print(f"[CAPTURE] Per carta {card} → {len(results)} opzioni")
        return results

    def play_card(self, player_index: int, card_index: int, capture_index: int = 0) -> Dict[str, Any]:
        if player_index != self.turn:
            return {"error": "Non è il tuo turno"}

        hand = self.hands[player_index]
        if card_index < 0 or card_index >= len(hand):
            return {"error": "Indice carta non valido"}

        card = hand.pop(card_index)
        print(f"[PLAY] G{player_index+1} gioca {self._fmt_cards([card])} (indice {card_index})")

        captures = self.possible_captures(card)

        if capture_index < 0 or capture_index >= len(captures):
            return {"error": "Indice presa non valido"}

        chosen = captures[capture_index]
        print(f"[PLAY] Presa scelta: {self._fmt_cards(list(chosen)) if chosen else 'nessuna'}")

        scopa_made = False

        if chosen:
            try:
                for c in chosen:
                    self.table.remove(c)
            except ValueError:
                print("[ERROR] Carta non trovata nel tavolo durante remove!")
            taken_cards = list(chosen) + [card]
            self.taken[player_index].extend(taken_cards)
            print(f"[TAKEN] G{player_index+1} prende {len(taken_cards)} carte → totale prese: {len(self.taken[player_index])}")
            if len(self.table) == 0:
                scopa_made = True
                self.scopa[player_index] += 1
                print(f"[SCOPA] Scopa per G{player_index+1}! Totale: {self.scopa[player_index]}")
        else:
            self.table.append(card)
            print(f"[PLAY] Scartata sul tavolo: {self._fmt_cards([card])}")

        self.turn = 1 - self.turn

        if all(len(h) == 0 for h in self.hands) and self.deck:
            self.deal()
        elif not self.deck and all(len(h) == 0 for h in self.hands):
            self.game_finished = True
            print("[END] Partita finita: mazzo e mani vuote")

        return {
            "status": "ok",
            "card_played": card,
            "captured": chosen if chosen else None,
            "scopa": scopa_made,
            "table_after": list(self.table),
            "hands": [list(h) for h in self.hands],
            "remaining_deck": len(self.deck)
        }

    def game_over(self) -> bool:
        is_over = self.game_finished or (not self.deck and all(len(h) == 0 for h in self.hands))
        if is_over:
            print("[GAME_OVER] Fine partita rilevata")
            print(f"  Prese totali: G1 {len(self.taken[0])}, G2 {len(self.taken[1])}")
        return is_over

    def score(self) -> Dict[str, Any]:
        def primiera_value(v: int) -> int:
            return {7:21, 6:18, 1:16, 5:15, 4:14, 3:13, 2:12, 8:10, 9:10, 10:10}.get(v, 0)

        def best_primiera(taken: List[Tuple[int, str]]) -> int:
            best = {}
            for s in SEMI:
                vals = [primiera_value(v) for v, ss in taken if ss == s]
                if vals:
                    best[s] = max(vals)
            total = sum(best.values())
            print(f"[PRIMIERA] Somma: {total} (dettaglio: {best})")
            return total

        def calc(idx: int) -> int:
            taken = self.taken[idx]
            opp = self.taken[1 - idx]
            pts = self.scopa[idx]

            if len(taken) > len(opp):
                pts += 1
            denari = len([c for c in taken if c[1] == "denari"])
            den_opp = len([c for c in opp if c[1] == "denari"])
            if denari > den_opp:
                pts += 1
            if (7, "denari") in taken:
                pts += 1
            if best_primiera(taken) > best_primiera(opp):
                pts += 1

            print(f"[CALC G{idx+1}] Punti: {pts} (scope:{self.scopa[idx]}, carte:{len(taken)}>{len(opp)}, denari:{denari}>{den_opp}, settebello:{(7,'denari') in taken}, primiera:{pts- (self.scopa[idx] + (1 if len(taken)>len(opp) else 0) + (1 if denari>den_opp else 0) + (1 if (7,'denari') in taken else 0))})")
            return pts

        result = {
            "player1": calc(0),
            "player2": calc(1),
            "scope": self.scopa[:],
            "carte_p1": len(self.taken[0]),
            "carte_p2": len(self.taken[1]),
            "denari_p1": len([c for c in self.taken[0] if c[1] == "denari"]),
            "denari_p2": len([c for c in self.taken[1] if c[1] == "denari"])
        }

        print("[SCORE FINALE]")
        print(f"  G1: {result['player1']} punti")
        print(f"  G2: {result['player2']} punti")
        print(f"  Scope: {result['scope']}")
        print(f"  Carte: {result['carte_p1']} vs {result['carte_p2']}")
        print(f"  Denari: {result['denari_p1']} vs {result['denari_p2']}")

        return result

    def __str__(self) -> str:
        return (
            f"Turno: G{self.turn + 1}\n"
            f"Tavolo: {self._fmt_cards(self.table)}\n"
            f"G1 mano: {self._fmt_cards(self.hands[0])}\n"
            f"G2 mano: {self._fmt_cards(self.hands[1])}\n"
            f"Prese G1: {len(self.taken[0])} | Scope: {self.scopa[0]}\n"
            f"Prese G2: {len(self.taken[1])} | Scope: {self.scopa[1]}\n"
            f"Mazzo: {len(self.deck)} carte\n"
            f"Game finished: {self.game_finished}\n"
        )


if __name__ == "__main__":
    game = ScopaGame()
    game.setup_game()
    print(game)

    # Simulazione giocata per test
    print("\n=== Test giocata G1 ===")
    print(game.play_card(0, 0))

    print("\nStato dopo giocata:")
    print(game)

    # Forza fine per vedere punteggio
    game.game_finished = True
    print("\n=== Punteggio finale forzato ===")
    print(game.score())