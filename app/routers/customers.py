from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import SessionLocal
from .. import crud, schemas
from ..dependencies import get_db, get_current_user

router = APIRouter(prefix="/customers", tags=["customers"])
ErrorSchema = schemas.ErrorSchema


@router.get(
    "",
    response_model=List[schemas.CustomerRead],
    summary="List all customers",
    description="Returns a paginated list of customers. Supports `skip` and `limit` query parameters.",
    responses={
        401: {
            "model": ErrorSchema,
            "description": "Missing or invalid JWT",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        }
    },
)
def read_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> List[schemas.CustomerRead]:
    """
    Retrieves customers from the database.
    """
    return crud.get_customers(db, skip=skip, limit=limit)


@router.post(
    "",
    response_model=schemas.CustomerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new customer",
    description="Creates a customer with full_name, email (unique), and geographic coordinates (lat, lon).",
    responses={
        400: {
            "model": ErrorSchema,
            "description": "Duplicate email or validation error",
            "content": {
                "application/json": {
                    "example": {"detail": "Customer with this email already exists"}
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
def create_customer(
    customer_in: schemas.CustomerCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> schemas.CustomerRead:
    """
    Creates and returns a new customer.
    """
    try:
        return crud.create_customer(db, customer_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this email already exists",
        )


@router.get(
    "/{customer_id}",
    response_model=schemas.CustomerRead,
    summary="Get customer by ID",
    description="Retrieves a single customer by its ID.",
    responses={
        401: {"model": ErrorSchema, "description": "Missing or invalid JWT"},
        404: {
            "model": ErrorSchema,
            "description": "Customer not found",
            "content": {"application/json": {"example": {"detail": "Customer not found"}}},
        },
    },
)
def read_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> schemas.CustomerRead:
    """
    Retrieves a customer by ID.
    """
    customer = crud.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


@router.put(
    "/{customer_id}",
    response_model=schemas.CustomerRead,
    summary="Replace customer data",
    description="Fully replaces all fields of an existing customer.",
    responses={
        401: {"model": ErrorSchema, "description": "Missing or invalid JWT"},
        404: {"model": ErrorSchema, "description": "Customer not found"},
        400: {
            "model": ErrorSchema,
            "description": "Duplicate email or validation error",
            "content": {"application/json": {"example": {"detail": "Customer with this email already exists"}}},
        },
    },
)
def replace_customer(
    customer_id: int,
    customer_in: schemas.CustomerCreate,  # use CustomerCreate here
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> schemas.CustomerRead:
    """
    Fully updates a customer's information.
    """
    existing = crud.get_customer(db, customer_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    try:
        return crud.update_customer(db, customer_id, customer_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this email already exists",
        )


@router.patch(
    "/{customer_id}",
    response_model=schemas.CustomerRead,
    summary="Update customer fields",
    description="Partially updates one or more fields of a customer.",
    responses={
        401: {"model": ErrorSchema, "description": "Missing or invalid JWT"},
        404: {"model": ErrorSchema, "description": "Customer not found"},
    },
)
def update_customer(
    customer_id: int,
    customer_in: schemas.CustomerCreate,  # also using CustomerCreate for patch
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> schemas.CustomerRead:
    """
    Partially updates a customer's information.
    """
    existing = crud.get_customer(db, customer_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return crud.update_customer(db, customer_id, customer_in)


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a customer",
    description="Deletes a customer and all their orders.",
    responses={
        401: {"model": ErrorSchema, "description": "Missing or invalid JWT"},
        404: {
            "model": ErrorSchema,
            "description": "Customer not found",
            "content": {"application/json": {"example": {"detail": "Customer not found"}}},
        },
    },
)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Deletes a customer by ID.
    """
    existing = crud.get_customer(db, customer_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    crud.delete_customer(db, customer_id)
    return None
