class Card:
    def __init__(self, front: str, back: str):
        self.front = front
        self.back = back

    def __str__(self):
        return f"{self.front}; {self.back}"
    
    def __eq__(self, card: Card):
        return self.front == card.front