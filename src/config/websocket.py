from typing import TypedDict

from fastapi import WebSocket, WebSocketDisconnect, Depends

from chat.models import ChatMessage
from chat.repository import ChatRepository

#
# class ConnectionContext(TypedDict):
#     websocket: WebSocket
#     user_id: int

class WebSocketConnectionManager:
    def __init__(self):
        self.connections: dict[WebSocket, tuple[int, int]] = dict()

    def __call__(self, chat_reop: ChatRepository = Depends()):
        self.chat_repo = chat_reop
        return self

    async def _send_message(self, websocket: WebSocket, message: ChatMessage, me_id: int):
        if message.user_id == me_id:
            await self._send_my_message(websocket=websocket, content=message.content)
        else:
            await self._send_friend_message(websocket=websocket, content=message.content)

    async def _send_my_message(self, websocket: WebSocket, content: str):
        await websocket.send_text(f"Me >> {content}")

    async def _send_friend_message(self, websocket: WebSocket, content: str):
        await websocket.send_text(f"Frined >> {content}")

    async def _get_context(self, websocket: WebSocket):
        room_id, user_id = self.connections[websocket]

    async def _init_messages(self, websocket: WebSocket):
        room_id, user_id = self.connections[websocket]

        messages = await self.chat_repo.get_messages_by_room(room_id=room_id)
        for message in messages:  # -> Rest API로 별도로 구현 가능
            await self._send_message(websocket=websocket, message=message, me_id=user_id)


    async def connect(self, websocket: WebSocket, room_id: int, user_id: int):
        await websocket.accept()  # 웹소켓 통신 허용
        self.connections[websocket] = room_id, user_id
        await self._init_messages(websocket=websocket)


    async def brodcast(self, websocket: WebSocket, content: str):
        room_id, user_id = self.connections[websocket]

        message = ChatMessage.create(room_id=room_id, user_id=user_id, content=content)
        await self.chat_repo.save(message=message)

        for conn, (conn_room_id, conn_user_id) in self.connections.items():
            if conn_room_id == room_id:
                if conn_user_id == user_id:
                    await self._send_my_message(websocket=conn, content=content)
                else:
                    await self._send_friend_message(websocket=conn, content=content)

    def disconnect(self, websocket: WebSocket):
        self.connections.pop(websocket)




ws_connection_manager = WebSocketConnectionManager()