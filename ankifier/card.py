class Card:
    def __init__(self, front: str, back: str, pos: str):
        self.front = front
        self.back = back
        self.pos = pos

    def __str__(self):
        return f"{self.front}|{self.back}|{self.pos}"

    def __repr__(self):
        return self.__str__

    def __eq__(self, card):
        return (self.front == card.front) and (self.pos == card.pos)

    def as_tuple(self):
        return (self.front, self.back, self.pos)