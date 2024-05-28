import logging 

class Card:
    def __init__(self, front: str, back: str):
        self.front = front
        self.back = back

    def __str__(self):
        return f"{self.front}; {self.back}"
    
    def __repr__(self):
        return self.__str__
    
    def __eq__(self, card):
        return self.front == card.front