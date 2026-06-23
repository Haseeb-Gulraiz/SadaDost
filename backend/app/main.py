"""FastAPI app — two endpoints the frontend uses.

  GET  /customers        -> list for the login dropdown (id + first name)
  POST /chat             -> { customer_id, message } -> guarded reply
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import data, chat

app = FastAPI(title="SadaDost — PayWallet Support")

# Allow the Vite dev server to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    customer_id: str
    message: str


@app.get("/customers")
def get_customers() -> list[dict]:
    return data.list_customers()


@app.post("/chat")
def post_chat(req: ChatRequest) -> dict:
    try:
        result = chat.answer(req.customer_id, req.message)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown customer")
    except RuntimeError as exc:  # e.g. missing API key
        raise HTTPException(status_code=503, detail=str(exc))
    return chat.result_dict(result)
