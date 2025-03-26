from fastapi import APIRouter, Query

from app.core.deps import AdminJWTDep, UserJWTDep
from app.core.error import NotFoundException
from app.database import SessionDep

from . import responses as res
from .schemas import *
from .service import *

router = APIRouter(prefix="/report", tags=["Report"])


@router.get("", responses=res.get_report_list)
async def get_report_list(
    session: SessionDep,
    payload: AdminJWTDep,
    last_id: int = None,
    limit: int = Query(10, ge=1, le=100),
    user_id: int = None,
    review_id: int = None,
    order_by: ReportOrderBy = ReportOrderBy.id,
    direction: SortingOrder = 'desc'
):
    '''
    [Admin] ดูรายการรายงาน

    Parameters:
    ----------
    - **last_id** (int, optional): สำหรับการแบ่งหน้า
        กรอง report_id < last_id เมื่อ direction เป็น desc
        และ report_id > last_id เมื่อ direction เป็น asc
    - **limit** (int, optional): จำนวนรายการที่ต้องการ
    - **user_id** (int, optional): กรอง report ที่เขียนโดย user
    - **review_id** (int, optional): กรอง report ที่เกี่ยวข้องกับ review
    - **order_by** (ReportOrderBy, optional): วิธีการเรียงลำดับ
    - **direction** ('asc' | 'desc', optional): ทิศทางการเรียงลำดับ
    '''
    return await get_reports(
        session,
        last_id=last_id,
        limit=limit,
        user_id=user_id,
        review_id=review_id,
        order_by=order_by,
        direction=direction
    )


@router.get("/{report_id}", responses=res.get_report_detail)
async def get_report_detail(
    session: SessionDep,
    payload: AdminJWTDep,
    report_id: int
):
    '''
    [Admin] ดูรายงาน
    '''
    reports = await get_reports(session, report_id=report_id)
    if not reports:
        raise NotFoundException("Report not found.")
    return reports[0]


@router.post("", responses=res.make_a_report)
async def make_a_report(
    session: SessionDep,
    payload: UserJWTDep,
    report: ReportCreate
):
    '''
    [User] รายงานรีวิว
    '''
    report_id = await create_report(
        session,
        payload.sub,
        report.review_id,
        report.reason
    )
    return ReportId(report_id=report_id)
