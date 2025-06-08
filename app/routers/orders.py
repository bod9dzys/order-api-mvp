from typing import List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app import crud, schemas
from app.services.eta import calculate_order_eta

router = APIRouter(prefix="/orders", tags=["orders"])
ErrorSchema = schemas.ErrorSchema


@router.post(
    "",
    response_model=schemas.OrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
    description="Creates an order with a list of items (product ID + quantity).",
    responses={
        400: {
            "model": ErrorSchema,
            "description": "Invalid product or customer ID",
            "content": {
                "application/json": {
                    "example": {"detail": "Product with id=99 does not exist"}
                }
            },
        },
        401: {
            "model": ErrorSchema,
            "description": "Missing or invalid JWT",
            "content": {
                "application/json": {
                    "examples": {
                        "missing": {
                            "summary": "No token",
                            "value": {"detail": "Not authenticated"},
                        },
                        "invalid": {
                            "summary": "Bad token",
                            "value": {"detail": "Could not validate credentials"},
                        },
                    }
                }
            },
        },
    },
)
def create_order(
    order_in: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> schemas.OrderRead:
    """
    Creates a new order.
    """
    try:
        return crud.create_order(db, order_in)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product or customer ID"
        )

@router.get(
    "",
    response_model=schemas.CursorPage[list[schemas.OrderRead]],
    summary="List orders (cursor-based)",
    description=(
        "Returns a cursor-paginated list of orders. "
        "`limit` – items per page (1–100). "
        "`cursor` – opaque string returned from previous page."
    ),
    responses={
        401: {"model": ErrorSchema, "description": "Authentication required"},
        422: {"description": "Invalid pagination parameters"},
    },
)
def list_orders(
    limit: int = Query(10, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
) -> schemas.CursorPage:
    """
    Retrieves orders using cursor-based pagination.
    """
    items, next_cur = crud.get_orders_cursor(db, limit, cursor)
    return {"data": items, "next_cursor": next_cur}


@router.get(
    "",
    response_model=List[schemas.OrderRead],
    summary="List all orders",
    description=(
        "Returns a paginated list of orders.\n"
        "Supports `limit` (int) and `cursor` (str) for cursor-based pagination."
    ),
    responses={401: {"model": ErrorSchema, "description": "Authentication required"}},
)
def read_orders(
    limit: int = Query(10, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Dict[str, Optional[List[schemas.OrderRead]]]:
    """
    Retrieves orders with cursor-based pagination.
    """
    orders, next_cursor = crud.get_orders_cursor(db, limit, cursor)
    return {"data": orders, "next_cursor": next_cursor}


@router.get(
    "/{order_id}",
    response_model=schemas.OrderRead,
    summary="Get order by ID",
    description="Fetches full order details including items and customer info.",
    responses={
        401: {"model": ErrorSchema, "description": "Authentication required"},
        404: {
            "model": ErrorSchema,
            "description": "Order not found",
            "content": {"application/json": {"example": {"detail": "Order not found"}}},
        },
    },
)
def read_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> schemas.OrderRead:
    """
    Retrieves a single order by its ID.
    """
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.put(
    "/{order_id}",
    response_model=schemas.OrderRead,
    summary="Replace an order",
    description="Fully updates status and items of an existing order.",
    responses={
        401: {"model": ErrorSchema, "description": "Authentication required"},
        404: {"model": ErrorSchema, "description": "Order not found"},
        400: {"model": ErrorSchema, "description": "Invalid update data"},
    },
)
def replace_order(
    order_id: int,
    order_in: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> schemas.OrderRead:
    """
    Fully replaces an order's data.
    """
    existing = crud.get_order(db, order_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return crud.update_order(db, order_id, order_in)


@router.patch(
    "/{order_id}",
    response_model=schemas.OrderRead,
    summary="Update order status",
    description="Partially updates an order's status (e.g., to 'completed', 'shipped').",
    responses={
        401: {"model": ErrorSchema, "description": "Authentication required"},
        404: {"model": ErrorSchema, "description": "Order not found"},
    },
)
def update_order_status(
    order_id: int,
    status_update: schemas.OrderUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> schemas.OrderRead:
    """
    Updates only the status field of an order.
    """
    existing = crud.get_order(db, order_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return crud.update_order(db, order_id, status_update)


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an order",
    description="Deletes an order and its items.",
    responses={
        401: {"model": ErrorSchema, "description": "Authentication required"},
        404: {"model": ErrorSchema, "description": "Order not found"},
    },
)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Deletes an order by ID.
    """
    existing = crud.get_order(db, order_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    crud.delete_order(db, order_id)
    return None


@router.post(
    "/{order_id}/cancel",
    response_model=schemas.OrderRead,
    summary="Cancel an order",
    description="Sets the order's status to 'cancelled'.",
    responses={
        401: {"model": ErrorSchema, "description": "Authentication required"},
        404: {"model": ErrorSchema, "description": "Order not found"},
    },
    dependencies=[Depends(get_current_user)],
)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
) -> schemas.OrderRead:
    """
    Cancels an existing order.
    """
    existing = crud.get_order(db, order_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    update = schemas.OrderUpdate(status="cancelled")
    return crud.update_order(db, order_id, update)


@router.patch(
    "/{order_id}/address",
    response_model=schemas.OrderETA,
    summary="Update delivery address",
    description="Updates the delivery coordinates (lat, lon) for the customer's order and returns new ETA.",
    responses={
        400: {"model": ErrorSchema, "description": "Invalid coordinates"},
        401: {"model": ErrorSchema, "description": "Authentication required"},
        404: {"model": ErrorSchema, "description": "Order not found"},
    },
    dependencies=[Depends(get_current_user)],
)
def update_order_address(
    order_id: int,
    lat: float = Query(..., description="New latitude"),
    lon: float = Query(..., description="New longitude"),
    db: Session = Depends(get_db),
) -> schemas.OrderETA:
    """
    Updates customer's coordinates for the given order and recalculates ETA.
    """
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    # update customer location
    cust_update = schemas.CustomerUpdate(lat=lat, lon=lon)
    crud.update_customer(db, order.customer_id, cust_update)
    # recalculate ETA
    return calculate_order_eta(order_id, db)


@router.get(
    "/{order_id}/eta",
    response_model=schemas.OrderETA,
    summary="Get ETA for an order",
    description=(
        "Returns:\n"
        "- distance_km: km from warehouse to customer\n"
        "- eta_minutes: estimated delivery time (min)\n"
        "- co2_grams: estimated CO₂ footprint (g)\n"
        "- suggested_merge_with: ID of another pending order within 3 km"
    ),
    dependencies=[Depends(get_current_user)],
    responses={
        401: {"model": ErrorSchema, "description": "Authentication required"},
        404: {
            "model": ErrorSchema,
            "description": "Order not found",
            "content": {"application/json": {"example": {"detail": "Order not found"}}},
        },
    },
)
def get_order_eta(
    order_id: int,
    db: Session = Depends(get_db),
) -> schemas.OrderETA:
    """
    Calculates ETA using warehouse coords and customer location.
    """
    try:
        return calculate_order_eta(order_id, db)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
