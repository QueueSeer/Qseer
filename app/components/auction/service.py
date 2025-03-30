import asyncio
from datetime import datetime
import json
from enum import Enum
import random
from string import ascii_uppercase, digits
from sqlalchemy import asc, delete, desc, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.appointment.service import create_appointment
from app.core.config import settings
from app.core.deps import SortingOrder, NullLiteral
from app.core.error import (
    BadRequestException,
    NotFoundException,
    InternalException,
)
from app.components.appointment.time_slots import get_busy_time_ranges
from app.components.transaction.service import (
    change_user_coins,
    cancel_bid_transactions,
    complete_bid_transactions,
)
from app.database.models import (
    Activity,
    Transaction,
    TxnStatus,
    TxnType,
    User,
    AuctionInfo,
    BidInfo
)
from app.trigger.service import trigger_auction
from .schemas import *


class AuctionOrderBy(str, Enum):
    id = 'id'
    date_created = 'date_created'
    start_time = 'start_time'
    end_time = 'end_time'
    appoint_start_time = 'appoint_start_time'


async def get_auctions(
    session: AsyncSession,
    seer_id: int = None,
    seer_display_name: str = None,
    name: str = None,
    exclude_ended: bool = True,
    order_by: AuctionOrderBy = AuctionOrderBy.id,
    direction: SortingOrder = 'desc',
    last_id: int = None,
    limit: int = 10,
):
    order = asc if direction == 'asc' else desc
    row_ordering = {
        AuctionOrderBy.id: AuctionInfo.id,
        AuctionOrderBy.date_created: AuctionInfo.date_created,
        AuctionOrderBy.start_time: AuctionInfo.start_time,
        AuctionOrderBy.end_time: AuctionInfo.end_time,
        AuctionOrderBy.appoint_start_time: AuctionInfo.appoint_start_time
    }
    stmt = (
        AuctionCard.select().
        order_by(order(row_ordering[order_by]))
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    if last_id is not None:
        if direction == 'asc':
            stmt = stmt.where(AuctionInfo.id > last_id)
        else:
            stmt = stmt.where(AuctionInfo.id < last_id)
    if seer_id is not None:
        stmt = stmt.where(AuctionInfo.seer_id == seer_id)
    if seer_display_name is not None:
        stmt = stmt.where(User.display_name.ilike(f'{seer_display_name}%'))
    if name is not None:
        stmt = stmt.where(AuctionInfo.name.ilike(f'{name}%'))
    if exclude_ended:
        stmt = stmt.where(AuctionInfo.end_time > func.now())
    return [
        AuctionCard.create_from(r)
        for r in (await session.execute(stmt))
    ]


async def get_auction_by_id(
    session: AsyncSession,
    auction_id: int
):
    stmt = (
        AuctionDetail.select().
        where(AuctionInfo.id == auction_id)
    )
    try:
        return AuctionDetail.create_from((await session.execute(stmt)).one())
    except NoResultFound:
        raise NotFoundException('Auction not found.')
    

async def get_auction_by_id_with_status(
    session: AsyncSession,
    auction_id: int,
) -> tuple[AuctionDetail, bool]:
    stmt = (
        AuctionDetail.select(
            (AuctionInfo.start_time <= func.now()).label("is_started"),
            (AuctionInfo.end_time <= func.now()).label("is_ended")
        ).
        where(AuctionInfo.id == auction_id)
    )
    try:
        auction_row = (await session.execute(stmt)).one()
        auction = AuctionDetail.create_from(auction_row)
        return auction, auction_row.is_started, auction_row.is_ended
    except NoResultFound:
        raise NotFoundException('Auction not found.')


async def get_auction_bidder(
    session: AsyncSession,
    auction_id: int,
    limit: int = 10
):
    stmt =  (
        select(
            BidInfo.auction_id,
            BidInfo.user_id,
            BidInfo.amount,
        ).
        where(BidInfo.auction_id == auction_id).
        order_by(desc(BidInfo.amount)).
        limit(limit)
    )
    return [
        Bidder.model_validate(r)
        for r in (await session.execute(stmt))
    ]


async def streaming_bids(
    session: AsyncSession,
    auction_id: int,
    times: int = 600
):
    last = None
    for _ in range(times):
        bids = await get_auction_bidder(session, auction_id)
        if bids != last:
            bidders = [b.model_dump(mode='json') for b in bids]
            yield json.dumps(bidders) + "\n\n"
            last = bids
        await asyncio.sleep(1)


async def get_highest_bidder(
    session: AsyncSession,
    auction_id: int
):
    stmt =  (
        select(
            BidInfo.auction_id,
            BidInfo.user_id,
            BidInfo.amount,
        ).
        where(BidInfo.auction_id == auction_id).
        order_by(desc(BidInfo.amount)).
        limit(1)
    )
    highest_bid = (await session.execute(stmt)).one_or_none()
    if highest_bid is not None:
        return Bidder.model_validate(highest_bid)
    return None


async def set_conclude_trigger(
    auction_id: int,
    end_time: datetime,
):
    success = await trigger_auction(
        auction_id,
        end_time + dt.timedelta(seconds=1),
        '/auction/conclude',
        settings.TRIGGER_SECRET
    )
    if not success:
        raise InternalException({"detail": "Trigger service failed."})


async def create_auction(
    session: AsyncSession,
    seer_id: int,
    data: AuctionCreate,
):
    busy = await get_busy_time_ranges(
        session,
        seer_id,
        data.appoint_start_time,
        data.appoint_end_time
    )
    if busy:
        raise BadRequestException("Seer is busy at this time.")

    stmt = insert(Activity).values(type="auctionInfo").returning(Activity.id)
    activity_id = (await session.scalars(stmt)).one()
    stmt = (
        insert(AuctionInfo).
        values(
            id=activity_id,
            seer_id=seer_id,
            name=data.name,
            short_description=data.short_description,
            description=data.description,
            start_time=data.start_time,
            end_time=data.end_time,
            appoint_start_time=data.appoint_start_time,
            appoint_end_time=data.appoint_end_time,
            initial_bid=data.initial_bid,
            min_increment=data.min_increment
        ).
        returning(AuctionInfo.id)
    )
    auction_id = (await session.scalars(stmt)).one()
    await set_conclude_trigger(auction_id, data.end_time)
    await session.commit()
    return auction_id


async def edit_auction(
    session: AsyncSession,
    auction_id: int,
    seer_id: int,
    data: AuctionUpdate
):
    auction, is_started, is_ended = await get_auction_by_id_with_status(
        session, auction_id
    )
    
    if is_started:
        raise BadRequestException("Auction has already started.")
    
    auction.start_time = data.start_time or auction.start_time
    auction.end_time = data.end_time or auction.end_time
    auction.appoint_start_time = data.appoint_start_time or auction.appoint_start_time
    auction.appoint_end_time = data.appoint_end_time or auction.appoint_end_time
    if not auction.is_valid_time():
        raise BadRequestException("Invalid time range.")
    
    busy = await get_busy_time_ranges(
        session,
        seer_id,
        auction.appoint_start_time,
        auction.appoint_end_time
    )
    if busy:
        raise BadRequestException("Seer is busy at this time.")

    data_dict = data.model_dump(exclude_unset=True)
    stmt = (
        update(AuctionInfo).
        where(AuctionInfo.id == auction_id).
        values(data_dict)
    )
    rowcount = (await session.execute(stmt)).rowcount
    await session.execute(stmt)
    await set_conclude_trigger(auction_id, auction.end_time)
    await session.commit()
    return rowcount


async def cancel_auction(
    session: AsyncSession,
    auction_id: int,
    seer_id: int = None
):
    stmt = (
        delete(AuctionInfo).
        where(
            AuctionInfo.id == auction_id,
            AuctionInfo.start_time > func.now()
        )
    )
    if seer_id is not None:
        stmt = stmt.where(AuctionInfo.seer_id == seer_id)
    rowcount = (await session.execute(stmt)).rowcount
    await session.commit()
    return rowcount


async def conclude_auction(
    session: AsyncSession,
    auction_id: int,
    *,
    seer_id: int = None,
    appoint_start_time: datetime = None,
    appoint_end_time: datetime = None,
    commit: bool = False
):
    if seer_id is None or appoint_start_time is None or appoint_end_time is None:
        stmt = (
            select(
                AuctionInfo.seer_id,
                AuctionInfo.appoint_start_time,
                AuctionInfo.appoint_end_time
            ).
            where(
                AuctionInfo.id == auction_id,
                AuctionInfo.end_time <= func.now()
            )
        )
        try:
            row = (await session.execute(stmt)).one()
        except NoResultFound:
            raise NotFoundException('Auction not found or not ended.')
        seer_id = row.seer_id
        appoint_start_time = row.appoint_start_time
        appoint_end_time = row.appoint_end_time

    highest_bid = await get_highest_bidder(session, auction_id)

    stmt = (
        select(Transaction.status).
        where(
            Transaction.activity_id == auction_id,
            Transaction.user_id == highest_bid.user_id,
            Transaction.type == TxnType.auction_bid,
            Transaction.status == TxnStatus.hold
        )
    )
    hold_status = (await session.scalars(stmt)).one_or_none()
    if hold_status is None:
        return None

    apmt_id = None
    if highest_bid is not None:
        # TODO: Set trigger to send notification for appointment
        code = ''.join(random.choices(ascii_uppercase + digits, k=6))
        apmt_id = await create_appointment(
            session,
            highest_bid.user_id,
            seer_id,
            None,
            appoint_start_time,
            appoint_end_time,
            confirmation_code=code, 
            commit=False
        )
        await complete_bid_transactions(
            session, auction_id, highest_bid.user_id, apmt_id, commit=False
        )
    
    if commit:
        await session.commit()
    return apmt_id


async def end_auction_early(
    session: AsyncSession,
    auction_id: int,
):
    stmt = (
        update(AuctionInfo).
        where(
            AuctionInfo.id == auction_id,
            AuctionInfo.end_time > func.now()
        ).
        values(end_time=func.now()).
        returning(
            AuctionInfo.seer_id,
            AuctionInfo.appoint_start_time,
            AuctionInfo.appoint_end_time,
            (AuctionInfo.start_time <= func.now()).label("is_started"),
        )
    )
    try:
        row = (await session.execute(stmt)).one()
    except NoResultFound:
        raise NotFoundException('Auction not found.')
    if not row.is_started:
        raise BadRequestException("Auction has not started yet.")
    
    apmt_id = await conclude_auction(
        session, auction_id,
        seer_id=row.seer_id,
        appoint_start_time=row.appoint_start_time,
        appoint_end_time=row.appoint_end_time
    )
    
    await session.commit()
    return apmt_id


async def bidding_auction(
    session: AsyncSession,
    user_id: int,
    auction_id: int,
    amount: float
):
    # Check if user has enough coins
    try:
        is_enough = (await session.scalars(
            select(User.coins >= amount).
            where(User.id == user_id)
        )).one()
    except NoResultFound:
        raise NotFoundException("User not found.")
    if not is_enough:
        raise BadRequestException("Insufficient coins.")

    # Check if auction is ongoing
    auction, is_started, is_ended = await get_auction_by_id_with_status(
        session, auction_id
    )
    if not is_started:
        raise BadRequestException("Auction has not started yet.")
    if is_ended:
        raise BadRequestException("Auction has already ended.")
    
    highest_bid = await get_highest_bidder(session, auction_id)

    # Check if user bid is valid
    if highest_bid is not None:
        if amount < highest_bid.amount + auction.min_increment:
            raise BadRequestException("Amount is too low.")
        if highest_bid.user_id == user_id:
            raise BadRequestException("Already the highest bidder.")
        await cancel_bid_transactions(
            session, auction_id, highest_bid.user_id, commit=False
        )
    elif amount < auction.initial_bid:
        raise BadRequestException("Amount is too low.")

    # Create or update bid
    stmt = (
        insert(BidInfo).
        values(
            user_id=user_id,
            auction_id=auction_id,
            amount=amount
        ).
        on_conflict_do_update(
            constraint=BidInfo.__table__.primary_key,
            set_={'amount': amount}
        )
    )
    await session.execute(stmt)

    await change_user_coins(
        session, user_id, -amount,
        TxnType.auction_bid,
        TxnStatus.hold,
        auction_id,
        commit=False
    )
    await session.commit()
    return Bidder(auction_id=auction_id, user_id=user_id, amount=amount)
