from typing import List, Callable


class Publisher:
    def __init__(self, events: List[str]):
        self.subscribers: List = []
        self.events = events


    def add_subscriber(self, event, subscriber: Callable):
        self.subscribers.append((event, subscriber))

    def unsubscribe(self, subscriber: Callable):
        self.subscribers.remove(subscriber)

    def publish(self, event, data):
        for subscriber in self.subscribers:
            if subscriber[0] == event:
                try:
                    subscriber[1](data)
                except Exception as e:
                    print(e)
                    self.unsubscribe(subscriber)
