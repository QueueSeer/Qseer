from fastapi import APIRouter, Query

from app.core.deps import AdminJWTDep, SeerJWTDep, UserJWTDep
from app.core.schemas import RowCount
from app.database import SessionDep

from . import responses as res
from .schemas import *
from .service import *

router = APIRouter(prefix="/review", tags=["Review"])


@router.get("", responses=res.get_review_list)
async def get_review_list(
    session: SessionDep,
    payload: AdminJWTDep,
    last_id: int = None,
    limit: int = Query(10, ge=1, le=100),
    seer_id: int = None,
    client_id: int = None,
    min_score: int = None,
    max_score: int = None,
    order_by: ReviewOrderBy = ReviewOrderBy.id,
    direction: SortingOrder = 'asc'
):
    '''
    [Admin] ดูรายการรีวิวทั้งหมด

    Parameters:
    ----------
    - **last_id** (int, optional): สำหรับการแบ่งหน้า
        กรอง review_id < last_id เมื่อ direction เป็น desc
        และ review_id > last_id เมื่อ direction เป็น asc
    - **limit** (int, optional): จำนวนรายการที่ต้องการ
    - **seer_id** (int, optional): กรอง review ที่ seer_id ตรงกับที่กำหนด
    - **client_id** (int, optional): กรอง review ที่ client_id ตรงกับที่กำหนด
    - **min_score** (int, optional): กรอง review ที่ score มากกว่าหรือเท่ากับที่กำหนด
    - **max_score** (int, optional): กรอง review ที่ score น้อยกว่าหรือเท่ากับที่กำหนด
    - **order_by** (ReviewOrderBy, optional): วิธีการเรียงลำดับ
    - **direction** ('asc' | 'desc', optional): ทิศทางการเรียงลำดับ
    '''
    return await get_reviews(
        session=session,
        last_id=last_id,
        limit=limit,
        seer_id=seer_id,
        client_id=client_id,
        min_score=min_score,
        max_score=max_score,
        order_by=order_by,
        direction=direction
    )


@router.get("/me", responses=res.get_review_list)
async def get_my_reviews(
    session: SessionDep,
    payload: UserJWTDep,
    last_id: int = None,
    limit: int = Query(10, ge=1, le=100),
    order_by: ReviewOrderBy = ReviewOrderBy.id,
    direction: SortingOrder = 'desc'
):
    '''
    [User] ดูรายการรีวิวของตัวเอง

    Parameters:
    ----------
    - **last_id** (int, optional): สำหรับการแบ่งหน้า
        กรอง review_id < last_id เมื่อ direction เป็น desc
        และ review_id > last_id เมื่อ direction เป็น asc
    - **limit** (int, optional): จำนวนรายการที่ต้องการ
    - **order_by** (ReviewOrderBy, optional): วิธีการเรียงลำดับ
    - **direction** ('asc' | 'desc', optional): ทิศทางการเรียงลำดับ
    '''
    return await get_reviews(
        session=session,
        last_id=last_id,
        limit=limit,
        client_id=payload.sub,
        order_by=order_by,
        direction=direction
    )


@router.get("/received", responses=res.get_review_list)
async def get_received_reviews(
    session: SessionDep,
    payload: SeerJWTDep,
    last_id: int = None,
    limit: int = Query(10, ge=1, le=100),
    order_by: ReviewOrderBy = ReviewOrderBy.id,
    direction: SortingOrder = 'desc'
):
    '''
    [Seer] ดูรายการรีวิวที่เราถูกรีวิว

    Parameters:
    ----------
    - **last_id** (int, optional): สำหรับการแบ่งหน้า
        กรอง review_id < last_id เมื่อ direction เป็น desc
        และ review_id > last_id เมื่อ direction เป็น asc
    - **limit** (int, optional): จำนวนรายการที่ต้องการ
    - **order_by** (ReviewOrderBy, optional): วิธีการเรียงลำดับ
    - **direction** ('asc' | 'desc', optional): ทิศทางการเรียงลำดับ
    '''
    return await get_reviews(
        session=session,
        last_id=last_id,
        limit=limit,
        seer_id=payload.sub,
        order_by=order_by,
        direction=direction
    )


@router.get("/{review_id}", responses=res.review_detail)
async def get_review_detail(
    session: SessionDep,
    review_id: int
):
    '''
    [Public] ดูรายละเอียดรีวิว

    Parameters:
    ----------
    - **review_id** (int): รหัสรีวิว
    '''
    reviews = await get_reviews(session, review_id=review_id)
    if not reviews:
        raise NotFoundException("Review not found.")
    return reviews[0]


@router.get("/seer/{seer_id}", responses=res.get_review_list)
async def get_seer_reviews(
    session: SessionDep,
    seer_id: int,
    last_id: int = None,
    limit: int = Query(10, ge=1, le=100),
    min_score: int = None,
    max_score: int = None,
    order_by: ReviewOrderBy = ReviewOrderBy.id,
    direction: SortingOrder = 'desc'
):
    '''
    [Public] ดูรายการรีวิวของหมอ

    Parameters:
    ----------
    - **seer_id** (int): รหัสหมอ
    - **last_id** (int, optional): สำหรับการแบ่งหน้า
        กรอง review_id < last_id เมื่อ direction เป็น desc
        และ review_id > last_id เมื่อ direction เป็น asc
    - **limit** (int, optional): จำนวนรายการที่ต้องการ
    - **min_score** (int, optional): กรอง review ที่ score มากกว่าหรือเท่ากับที่กำหนด
    - **max_score** (int, optional): กรอง review ที่ score น้อยกว่าหรือเท่ากับที่กำหนด
    - **order_by** (ReviewOrderBy, optional): วิธีการเรียงลำดับ
    - **direction** ('asc' | 'desc', optional): ทิศทางการเรียงลำดับ
    '''
    return await get_reviews(
        session=session,
        last_id=last_id,
        limit=limit,
        seer_id=seer_id,
        min_score=min_score,
        max_score=max_score,
        order_by=order_by,
        direction=direction
    )


@router.post("", status_code=201, responses=res.review_service)
async def review_service(
    session: SessionDep,
    payload: UserJWTDep,
    review: ReviewCreate
):
    '''
    [User] เขียนรีวิว

    เงื่อนไข:
    - รีวิวซ้ำไม่ได้
    - ต้องรีวิว appointment ตัวเอง
    - appointment ต้องจบแล้ว
    - คะแนนหมอดูจะแสดงเมื่อถึง 10 รีวิว

    Parameters:
    ----------
    - **id** (int): id ของ appointment (appointment กับ review ใช้ id เดียวกัน)
    - **score** (int): คะแนนรีวิว 0-5 คะแนน
    - **text** (str): ข้อความรีวิว 1-1000 ตัวอักษร
    '''
    await create_review(
        session,
        review,
        user_id=payload.sub
    )
    return review


@router.delete("/{review_id}", responses=res.remove_review)
async def remove_review(
    session: SessionDep,
    payload: AdminJWTDep,
    review_id: int
):
    '''
    [Admin] ลบรีวิว
    '''
    rowcount = await delete_review(session, review_id)
    return RowCount(count=rowcount)
