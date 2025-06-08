from typing import List, Optional           # ← додали Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..dependencies import get_db, get_current_user
from .. import crud, schemas

router = APIRouter(prefix="/products", tags=["products"])
ErrorSchema = schemas.ErrorSchema


@router.post(
    "",
    response_model=schemas.ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="Adds a product with a unique SKU and price.",
    responses={
        400: {
            "model": ErrorSchema,
            "description": "Duplicate SKU or validation error",
            "content": {
                "application/json": {
                    "example": {"detail": "Product with this SKU already exists"}
                }
            },
        },
        401: {
            "model": ErrorSchema,
            "description": "Missing or invalid JWT",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        },
    },
)
def create_product(
    product_in: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> schemas.ProductRead:
    """
    Creates and returns a new product.
    """
    try:
        return crud.create_product(db, product_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product with this SKU already exists"
        )


@router.get(
    "",
    response_model=schemas.CursorPage[List[schemas.ProductRead]],  # Generic page
    summary="List products (cursor-based)",
    description=(
        "Returns a cursor-paginated list of products. "
        "`limit` – items per page (1–100). `cursor` – opaque string for next page."
    ),
    responses={
        401: {"model": ErrorSchema, "description": "Missing or invalid JWT"},
        422: {"description": "Invalid pagination parameters"},
    },
)
def list_products(
    limit: int = Query(10, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> schemas.CursorPage:
    """
    Retrieves products using cursor-based pagination.
    """
    items, next_cur = crud.get_products_cursor(db, limit, cursor)
    return {"data": items, "next_cursor": next_cur}


@router.get(
    "/{product_id}",
    response_model=schemas.ProductRead,
    summary="Get product by ID",
    description="Fetches details for the specified product.",
    responses={
        401: {"model": ErrorSchema, "description": "Missing or invalid JWT"},
        404: {
            "model": ErrorSchema,
            "description": "Product not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Product not found"}
                }
            },
        },
    },
)
def read_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> schemas.ProductRead:
    """
    Retrieves a single product by its ID.
    """
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.put(
    "/{product_id}",
    response_model=schemas.ProductRead,
    summary="Replace product data",
    description="Fully updates all fields of a product.",
    responses={
        401: {"model": ErrorSchema, "description": "Missing or invalid JWT"},
        404: {"model": ErrorSchema, "description": "Product not found"},
        400: {
            "model": ErrorSchema,
            "description": "Duplicate SKU or validation error",
            "content": {
                "application/json": {
                    "example": {"detail": "Product with this SKU already exists"}
                }
            },
        },
    },
)
def replace_product(
    product_id: int,
    product_in: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> schemas.ProductRead:
    """
    Fully updates a product's information.
    """
    existing = crud.get_product(db, product_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    try:
        return crud.update_product(db, product_id, product_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product with this SKU already exists"
        )


@router.patch(
    "/{product_id}",
    response_model=schemas.ProductRead,
    summary="Update product fields",
    description="Partially updates one or more product attributes.",
    responses={
        401: {"model": ErrorSchema, "description": "Missing or invalid JWT"},
        404: {"model": ErrorSchema, "description": "Product not found"},
    },
)
def update_product(
    product_id: int,
    product_in: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> schemas.ProductRead:
    """
    Partially updates a product's information.
    """
    existing = crud.get_product(db, product_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return crud.update_product(db, product_id, product_in)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product",
    description="Deletes the specified product.",
    responses={
        401: {"model": ErrorSchema, "description": "Missing or invalid JWT"},
        404: {
            "model": ErrorSchema,
            "description": "Product not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Product not found"}
                }
            },
        },
    },
)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Deletes a product by ID.
    """
    existing = crud.get_product(db, product_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    crud.delete_product(db, product_id)
    return None
