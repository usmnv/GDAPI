import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import db

app = FastAPI(title="Golden Dragon API")

# Разрешаем CORS (важно для запросов с GitHub Pages)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Golden Dragon API is running"}

@app.get("/api/user/{user_id}")
def get_user(user_id: int):
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    orders = db.get_user_track_codes(user_id)
    return {
        "customer_code": user["customer_code"],
        "balance": user["balance"],
        "orders_count": len(orders),
        "delivered_count": sum(1 for o in orders if o["status"] == "Доставлен")
    }

@app.get("/api/orders/{user_id}")
def get_orders(user_id: int):
    orders = db.get_user_track_codes(user_id)
    return {"orders": [
        {
            "track_code": o["track_code"],
            "description": o["description"],
            "status": o["status"],
            "date": str(o["created_date"]) if o["created_date"] else ""
        } for o in orders
    ]}

@app.get("/api/exchange_rates")
def get_exchange_rates():
    rates = db.get_exchange_rates()
    return {"rates": [
        {
            "code": r["currency_code"],
            "rate": r["rate"],
            "flag": r["flag"],
            "name": r["currency_name"]
        } for r in rates
    ]}

@app.get("/api/track/{track_code}")
def track_order(track_code: str):
    # Можно реализовать через прямой SQL-запрос, либо добавить метод в Database
    import psycopg2
    from psycopg2.extras import RealDictCursor
    conn = psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=RealDictCursor)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT track_code, status, description, created_date, u.customer_code
            FROM track_codes tc
            LEFT JOIN users u ON tc.user_id = u.user_id
            WHERE track_code = %s
        """, (track_code.upper(),))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Track code not found")
    return {
        "track_code": row["track_code"],
        "status": row["status"],
        "description": row["description"],
        "date": str(row["created_date"]) if row["created_date"] else "",
        "customer_code": row["customer_code"]
    }

# Для локального запуска
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)