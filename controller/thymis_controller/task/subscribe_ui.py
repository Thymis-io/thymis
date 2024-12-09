from fastapi import WebSocket


class TaskUISubscriptionManager:
    # manages websocket subscriptions
    def __init__(self):
        self.subscribers = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.subscribers.add(websocket)

    async def start(self):
        pass
