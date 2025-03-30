from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.components.appointment.schemas import AppointmentId
from app.core.deps import SeerJWTDep, UserJWTDep
from app.core.schemas import RowCount
from app.database import SessionDep

from . import responses as res
from .schemas import *
from .service import *

SSE_TYPE = "text/event-stream"

router = APIRouter(prefix="/auction", tags=["Auction"])


@router.get("/search", responses=res.search_auctions)
async def search_auctions(
    session: SessionDep,
    last_id: int = None,
    limit: int = Query(10, ge=1, le=100),
    seer_id: int = None,
    seer_display_name: str = None,
    name: str = None,
    order_by: AuctionOrderBy = AuctionOrderBy.id,
    direction: SortingOrder = 'desc',
):
    '''
    [Public] ค้นหาประมูล

    Parameters:
    ----------
    - **last_id** (int, optional): สำหรับการแบ่งหน้า
        กรอง auction_id < last_id เมื่อ direction เป็น desc
        และ auction_id > last_id เมื่อ direction เป็น asc
    - **limit** (int, optional): จำนวนรายการที่ต้องการ
    - **seer_id** (int, optional): กรอง auction ที่ seer_id ตรงกับที่กำหนด
    - **seer_display_name** (str, optional): 
        กรองชื่อหมอดูที่สร้าง auction ที่ขึ้นต้นตามที่กำหนด
    - **name** (str, optional): กรองชื่อ auction ที่ขึ้นต้นตามที่กำหนด
    - **exclude_ended** (bool, optional): กรอง auction ที่ยังไม่จบ
    - **order_by** (AuctionOrderBy, optional): ชื่อฟิลด์ที่ใช้เรียงลำดับ
    - **direction** ('asc' | 'desc', optional): ทิศทางการเรียงลำดับ
    '''
    return await get_auctions(
        session,
        seer_id,
        seer_display_name,
        name,
        True,
        order_by,
        direction,
        last_id,
        limit
    )


@router.get("/seer/me", responses=res.get_seer_auctions)
async def get_seer_auctions(
    session: SessionDep,
    payload: SeerJWTDep,
    last_id: int = None,
    limit: int = Query(10, ge=1, le=100),
    name: str = None,
    exclude_ended: bool = False,
    order_by: AuctionOrderBy = AuctionOrderBy.id,
    direction: SortingOrder = 'desc',
):
    '''
    [Seer] ดูรายการประมูลที่เราเป็นหมอดู

    Parameters:
    ----------
    - **last_id** (int, optional): สำหรับการแบ่งหน้า
        กรอง auction_id < last_id เมื่อ direction เป็น desc
        และ auction_id > last_id เมื่อ direction เป็น asc
    - **limit** (int, optional): จำนวนรายการที่ต้องการ
    - **name** (str, optional): กรองชื่อ auction ที่ขึ้นต้นตามที่กำหนด
    - **exclude_ended** (bool, optional): กรอง auction ที่ยังไม่จบ
    - **order_by** (AuctionOrderBy, optional): ชื่อฟิลด์ที่ใช้เรียงลำดับ
    - **direction** ('asc' | 'desc', optional): ทิศทางการเรียงลำดับ
    '''
    return await get_auctions(
        session=session,
        seer_id=payload.sub,
        name=name,
        exclude_ended=exclude_ended,
        order_by=order_by,
        direction=direction,
        last_id=last_id,
        limit=limit
    )


@router.get("/{auction_id}", responses=res.get_auction)
async def get_auction(
    session: SessionDep,
    auction_id: int
):
    '''
    [Public] ดูรายละเอียดประมูล
    '''
    return await get_auction_by_id(session, auction_id)


@router.get("/{auction_id}/bids", responses=res.get_auction_bids)
async def get_auction_bids(
    session: SessionDep,
    auction_id: int,
):
    '''
    [Public] ดูรายการเสนอราคาในประมูล top 10
    '''
    return await get_auction_bidder(session, auction_id)


@router.get("/{auction_id}/bids/stream")
async def streaming_auction_bids(
    session: SessionDep,
    auction_id: int,
    times: int = Query(600, ge=1, le=1200)
):
    '''
    [Public] ดูรายการเสนอราคาในประมูล top 10 (Server Sent Events)
    มี content-type คือ text/event-stream

    backend จะอัพเดทข้อมูลทุกๆ 1 วินาที ถ้ามีการเปลี่ยนแปลงจะส่งข้อมูลใหม่
    แต่ถ้าไม่มีการเปลี่ยนแปลงจะไม่ส่งอะไรกลับไป

    `times` คือกำหนดว่าจะให้ระบบอัพเดทข้อมูลกี่ครั้ง
    โดยค่าเริ่มต้นคือ 600 ครั้งหรือประมาณ 10 นาที
    ใช้ค่าน้อยๆ สำหรับการทดสอบ

    [ข้อมูลอ้างอิง](https://medium.com/@nandagopal05/server-sent-events-with-python-fastapi-f1960e0c8e4b)
    '''
    return StreamingResponse(
        streaming_bids(session, auction_id, times),
        media_type=SSE_TYPE
    )


@router.post(
    "/",
    status_code=201,
    responses=res.create_an_auction,
)
async def create_an_auction(
    session: SessionDep,
    payload: SeerJWTDep,
    auction: AuctionCreate
):
    '''
    [Seer] สร้างประมูล

    เงื่อนไข:
    - `start_time` < `end_time` < `appoint_start_time` < `appoint_end_time`
    - เวลา appoint ต้องไม่ชนกับเวลาที่มีการนัดหมายอยู่แล้ว

    Note:
    - `start_time` สามารถใส่เป็น 'now' เพื่อให้ระบบใช้เวลาปัจจุบัน
    - ระบบจะแปลง timeezone ให้เป็น UTC+7 การใส่เวลาต่อท้ายด้วย z จะถือว่าเป็น UTC+0
    '''
    auction_id = await create_auction(session, payload.sub, auction)
    return AuctionCreated.model_validate(
        auction.model_dump() | {"id": auction_id, "seer_id": payload.sub}
    )


@router.patch("/{auction_id}", responses=res.update_auction)
async def update_auction(
    session: SessionDep,
    payload: SeerJWTDep,
    auction_id: int,
    auction: AuctionUpdate
):
    '''
    [Seer] แก้ไขประมูล

    เงื่อนไข:
    - `start_time` < `end_time` < `appoint_start_time` < `appoint_end_time`
    - เวลา appoint ต้องไม่ชนกับเวลาที่มีการนัดหมายอยู่แล้ว
    - แก้ไขได้เฉพาะตอนประมูลยังไม่เริ่ม

    Note:
    - `start_time` สามารถใส่เป็น 'now' เพื่อให้ระบบใช้เวลาปัจจุบัน
    - ระบบจะแปลง timeezone ให้เป็น UTC+7 การใส่เวลาต่อท้ายด้วย z จะถือว่าเป็น UTC+0
    '''
    await edit_auction(session, auction_id, payload.sub, auction)
    return auction.model_dump(exclude_unset=True)


@router.patch("/{auction_id}/cancel", responses=res.cancel_an_auction)
async def cancel_an_auction(
    session: SessionDep,
    payload: SeerJWTDep,
    auction_id: int
):
    '''
    [Seer] ยกเลิกประมูลที่ยังไม่เริ่ม
    '''
    return RowCount(
        count=await cancel_auction(session, auction_id, payload.sub)
    )


@router.patch("/{auction_id}/close", responses=res.close_an_auction)
async def close_an_auction(
    session: SessionDep,
    payload: SeerJWTDep,
    auction_id: int
):
    '''
    [Seer] ปิดประมูลก่อนจบเวลาการประมูล

    หากมีการประมูลในช่วงเวลานี้ จะเลือกผู้ชนะแล้วสร้างการนัดหมาย
    หากไม่มีการประมูล จะปิดประมูลโดยไม่มีผู้ชนะ
    '''
    apmt_id = await end_auction_early(session, auction_id, payload.sub)
    return AppointmentId(apmt_id=apmt_id)


@router.put("/{auction_id}/bid", responses=res.bid_auction)
async def bid_auction(
    session: SessionDep,
    payload: UserJWTDep,
    auction_id: int,
    bid: Bidding
):
    '''
    [User] เสนอราคาในประมูล

    เงื่อนไข:
    - สามารถเสนอราคาได้เฉพาะในช่วงเวลาประมูล
    - ราคาเสนอต้องสูงกว่าราคาปัจจุบัน + min_increment
    - หากยังไม่มีการเสนอราคา ต้องเสนอราคา >= initial_bid
    - เสนอราคาแข่งกับตัวเองไม่ได้
    '''
    return await bidding_auction(session, payload.sub, auction_id, bid.amount)


@router.post("/conclude", include_in_schema=False)
async def conclude_an_auction(
    session: SessionDep,
    obj: AuctionCallback
):
    '''
    สรุปผลประมูลและสร้างการนัดหมาย Internal use
    '''
    if obj.security_key != settings.TRIGGER_SECRET:
        raise HTTPException(403, "Nuh uh.")

    return await conclude_auction(session, obj.auction_ID)
