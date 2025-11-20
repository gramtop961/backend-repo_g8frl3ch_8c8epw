"""
Database Schemas for Online Clothing Store

Each Pydantic model represents a MongoDB collection. The collection name is the
lowercased class name.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product"
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Detailed product description")
    price: float = Field(..., ge=0, description="Price in PKR")
    category: str = Field(..., description="Category like Men, Women, Kids, Winter Collection, Summer Collection, Sale Items")
    images: List[HttpUrl] = Field(default_factory=list, description="One or more image URLs")
    sizes: List[str] = Field(default_factory=lambda: ["S","M","L","XL"], description="Available sizes")
    in_stock: bool = Field(True, description="Stock availability")
    is_trending: bool = Field(False, description="Show in Trending")
    is_new: bool = Field(False, description="Show in New Arrivals")
    is_best_seller: bool = Field(False, description="Show in Best Sellers")
    season: Optional[str] = Field(None, description="Season like Winter or Summer")
    on_sale: bool = Field(False, description="Is this a sale item")
    sale_price: Optional[float] = Field(None, ge=0, description="Discounted price if on sale")

class Banner(BaseModel):
    """
    Banners collection schema
    Collection name: "banner"
    """
    title: str
    subtitle: Optional[str] = None
    image: Optional[HttpUrl] = None
    slug: str = Field(..., description="Identifier like mega-sale, new-collection-2025, limited-stock")
