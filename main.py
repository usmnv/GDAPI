from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import Client
from supabase import create_client
from models import TelegramAuth
from utils import generate_customer_code
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # потом ограничим GitHub Pages
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/auth/telegram")
def auth_telegram(data: TelegramAuth):
    user = (
        supabase
        .table("users")
        .select("*")
        .eq("telegram_id", data.telegram_id)
        .execute()
        .data
    )

    if not user:
        code = generate_customer_code()
        new_user = (
            supabase
            .table("users")
            .insert({
                "telegram_id": data.telegram_id,
                "username": data.username,
                "first_name": data.first_name,
                "customer_code": code
            })
            .execute()
            .data[0]
        )

        return {
            "new": True,
            "customer_code": new_user["customer_code"],
            "balance": new_user["balance"]
        }

    user = user[0]
    return {
        "new": False,
        "customer_code": user["customer_code"],
        "balance": user["balance"]
    }

@app.get("/me/{telegram_id}")
def me(telegram_id: int):
    user = (
        supabase
        .table("users")
        .select("username, first_name, customer_code, balance")
        .eq("telegram_id", telegram_id)
        .execute()
        .data
    )
    if not user:
        return {"error": "User not found"}
    return user[0]

@app.get("/orders/{telegram_id}")
def orders(telegram_id: int):
    user = (
        supabase
        .table("users")
        .select("id")
        .eq("telegram_id", telegram_id)
        .execute()
        .data
    )
    if not user:
        return {"orders": []}

    orders = (
        supabase
        .table("orders")
        .select("track_code, status")
        .eq("user_id", user[0]["id"])
        .execute()
        .data
    )

    return {"orders": orders}

@app.get("/exchange-rates")
def exchange_rates():
    return {
        "rates": [
            {"code": "USD", "rate": 90, "name": "Доллар", "flag": "🇺🇸"},
            {"code": "RUB", "rate": 1, "name": "Рубль", "flag": "🇷🇺"},
            {"code": "CNY", "rate": 12.5, "name": "Юань", "flag": "🇨🇳"},
            {"code": "EUR", "rate": 98, "name": "Евро", "flag": "🇪🇺"}
        ]
    }