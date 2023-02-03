from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


class User(BaseModel):
    __root__: str


class Message(BaseModel):
    user: str
    text: str
    timestamp: datetime = Field(default_factory=datetime.now)


app = FastAPI()

app.state.users: list[User] = []
app.state.messages: list[Message] = []


@app.get("/")
async def index():
    with open("index.htm") as f:
        return HTMLResponse(f.read())


@app.post("/users/join")
async def join(user: User):
    app.state.users.append(user)


@app.get("/users", response_model=list[User])
async def users():
    return app.state.users


@app.get("/messages", response_model=list[Message])
async def messages():
    return app.state.messages


@app.post("/messages")
async def post_message(message: Message):
    app.state.messages.append(message)
