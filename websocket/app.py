import json
from datetime import datetime
from typing import Generic, TypeVar

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel


class User(BaseModel):
    __root__: str


class Message(BaseModel):
    user: str
    text: str
    timestamp: datetime = Field(default_factory=datetime.now)


DataT = TypeVar("DataT")


class Data(GenericModel, Generic[DataT]):
    type: str
    data: DataT


app = FastAPI()

app.state.users: list[User] = []
app.state.messages: list[Message] = []
app.state.connections: list[WebSocket] = []


async def broadcast(data: Data):
    for ws in app.state.connections:
        await ws.send_text(data.json())


@app.get("/")
async def index():
    with open("index.htm") as f:
        return HTMLResponse(f.read())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    app.state.connections.append(websocket)

    user = None

    try:
        while True:
            data = await websocket.receive_text()
            json_data = json.loads(data)
            match json_data["type"]:
                case "join_user":
                    user = User(__root__=json_data["data"])
                    app.state.users.append(user)
                    await broadcast(
                        Data[User].parse_obj({"type": "join_user", "data": user})
                    )
                case "post_message":
                    message = Message(**json_data["data"])
                    app.state.messages.append(message)
                    await broadcast(
                        Data[Message].parse_obj(
                            {"type": "post_message", "data": message}
                        )
                    )
                case "get_messages":
                    await broadcast(
                        Data[list[Message]].parse_obj(
                            {"type": "get_messages", "data": app.state.messages}
                        )
                    )
                case "get_users":
                    await broadcast(
                        Data[list[User]].parse_obj(
                            {"type": "get_users", "data": app.state.users}
                        )
                    )
    except WebSocketDisconnect:
        app.state.connections.remove(websocket)
        if user:
            app.state.users.remove(user)
            await broadcast(Data[User].parse_obj({"type": "leave_user", "data": user}))
