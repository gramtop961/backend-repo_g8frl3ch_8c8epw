import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product as ProductSchema, Banner as BannerSchema

class ProductOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    price: float
    category: str
    images: List[str] = []
    sizes: List[str] = []
    in_stock: bool = True
    is_trending: bool = False
    is_new: bool = False
    is_best_seller: bool = False
    season: Optional[str] = None
    on_sale: bool = False
    sale_price: Optional[float] = None

class BannerOut(BaseModel):
    id: str
    title: str
    subtitle: Optional[str] = None
    image: Optional[str] = None
    slug: str

app = FastAPI(title="Clothing Store API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def serialize_product(doc) -> ProductOut:
    return ProductOut(
        id=str(doc.get("_id")),
        title=doc.get("title"),
        description=doc.get("description"),
        price=float(doc.get("price", 0)),
        category=doc.get("category"),
        images=[str(x) for x in doc.get("images", [])],
        sizes=[str(x) for x in doc.get("sizes", [])],
        in_stock=bool(doc.get("in_stock", True)),
        is_trending=bool(doc.get("is_trending", False)),
        is_new=bool(doc.get("is_new", False)),
        is_best_seller=bool(doc.get("is_best_seller", False)),
        season=doc.get("season"),
        on_sale=bool(doc.get("on_sale", False)),
        sale_price=float(doc.get("sale_price")) if doc.get("sale_price") is not None else None,
    )

def serialize_banner(doc) -> BannerOut:
    return BannerOut(
        id=str(doc.get("_id")),
        title=doc.get("title"),
        subtitle=doc.get("subtitle"),
        image=doc.get("image"),
        slug=doc.get("slug"),
    )

@app.get("/")
def read_root():
    return {"message": "Clothing Store Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            response["collections"] = db.list_collection_names()
        else:
            response["database"] = "⚠️ Not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:120]}"
    return response

@app.get("/api/categories")
def get_categories():
    return ["Men", "Women", "Kids", "Winter Collection", "Summer Collection", "Sale Items"]

@app.get("/api/banners", response_model=List[BannerOut])
def get_banners():
    docs = list(db["banner"].find()) if db else []
    return [serialize_banner(d) for d in docs]

@app.post("/api/banners", response_model=str)
def create_banner(payload: BannerSchema):
    banner_id = create_document("banner", payload)
    return banner_id

@app.get("/api/products", response_model=List[ProductOut])
def list_products(
    category: Optional[str] = None,
    trending: Optional[bool] = Query(None),
    new: Optional[bool] = Query(None),
    best: Optional[bool] = Query(None),
    season: Optional[str] = None,
    sale: Optional[bool] = Query(None),
    q: Optional[str] = None,
    limit: int = Query(24, ge=1, le=100),
):
    if db is None:
        return []
    filt = {}
    if category:
        filt["category"] = category
    if season:
        filt["season"] = season
    if trending is not None:
        filt["is_trending"] = trending
    if new is not None:
        filt["is_new"] = new
    if best is not None:
        filt["is_best_seller"] = best
    if sale is not None:
        filt["on_sale"] = sale
    if q:
        filt["title"] = {"$regex": q, "$options": "i"}
    docs = db["product"].find(filt).limit(limit)
    return [serialize_product(d) for d in docs]

@app.get("/api/products/{product_id}", response_model=ProductOut)
def get_product(product_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        doc = db["product"].find_one({"_id": ObjectId(product_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product id")
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return serialize_product(doc)

@app.post("/api/products", response_model=str)
def create_product(payload: ProductSchema):
    product_id = create_document("product", payload)
    return product_id

@app.get("/api/seed")
def seed_data():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    created = {"products": 0, "banners": 0}

    if db["banner"].count_documents({}) == 0:
        banners = [
            {
                "title": "Mega Sale",
                "subtitle": "Up to 60% OFF on top styles",
                "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=1600&q=80&auto=format&fit=crop",
                "slug": "mega-sale",
            },
            {
                "title": "New Collection 2025",
                "subtitle": "Fresh arrivals for the new season",
                "image": "https://images.unsplash.com/photo-1520975922203-b5d0b0d75136?w=1600&q=80&auto=format&fit=crop",
                "slug": "new-collection-2025",
            },
            {
                "title": "Limited Stock Available",
                "subtitle": "Grab your favorites before they’re gone",
                "image": "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?w=1600&q=80&auto=format&fit=crop",
                "slug": "limited-stock",
            },
        ]
        for b in banners:
            db["banner"].insert_one(b)
            created["banners"] += 1

    if db["product"].count_documents({}) == 0:
        sample_products = [
            {
                "title": "Classic Black Tee",
                "description": "Premium cotton, perfect fit.",
                "price": 2499,
                "category": "Men",
                "images": [
                    "https://images.unsplash.com/photo-1520975922203-b5d0b0d75136?w=1200&auto=format&fit=crop&q=80",
                ],
                "sizes": ["S", "M", "L", "XL"],
                "in_stock": True,
                "is_trending": True,
                "is_new": False,
                "is_best_seller": True,
                "season": "Summer",
                "on_sale": True,
                "sale_price": 1999,
            },
            {
                "title": "Gold Accent Hoodie",
                "description": "Cozy fleece with subtle gold detail.",
                "price": 4999,
                "category": "Women",
                "images": [
                    "https://images.unsplash.com/photo-1519741497674-611481863552?w=1200&auto=format&fit=crop&q=80",
                ],
                "sizes": ["S", "M", "L", "XL"],
                "in_stock": True,
                "is_trending": True,
                "is_new": True,
                "is_best_seller": False,
                "season": "Winter",
                "on_sale": False,
            },
            {
                "title": "Kids Summer Set",
                "description": "Light and comfy two-piece.",
                "price": 2999,
                "category": "Kids",
                "images": [
                    "https://images.unsplash.com/photo-1520975432204-8d8a9f9a9f3b?w=1200&auto=format&fit=crop&q=80",
                ],
                "sizes": ["S", "M", "L"],
                "in_stock": True,
                "is_trending": False,
                "is_new": True,
                "is_best_seller": False,
                "season": "Summer",
                "on_sale": False,
            },
        ]
        for p in sample_products:
            db["product"].insert_one(p)
            created["products"] += 1

    return {"status": "ok", **created}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
