from app.components.appointment.schemas import AppointmentId
from app.core.schemas import RowCount
from ..responses import *
from .schemas import *

search_auctions = {
    HTTP_200_OK: {
        "model": AuctionCard,
        "description": "List of auctions."
    }
}

get_seer_auctions = {
    HTTP_200_OK: {
        "model": AuctionCard,
        "description": "List of auctions."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

get_auction = {
    HTTP_200_OK: {
        "model": AuctionDetail,
        "description": "Auction retrieved."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {"detail": "Auction not found."}
            }
        },
        "description": "Auction not found."
    }
}

get_auction_bids = {
    HTTP_200_OK: {
        "model": list[Bidder],
        "description": "Top 10 bidders."
    }
}

get_my_bid = {
    HTTP_200_OK: {
        "model": Bidder,
        "description": "My bid."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {"detail": "Bid not found."}
            }
        },
        "description": "Bid not found."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

create_an_auction = {
    HTTP_201_CREATED: {
        "model": AuctionCreated,
        "description": "Auction created."
    },
    HTTP_400_BAD_REQUEST: {
        "content": {
            "application/json": {
                "example": {"detail": "Seer is busy at this time."}
            }
        },
        "description": "appoint_start_time & appoint_end_time\
            is overlapping with another appointment."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

update_auction = {
    HTTP_200_OK: {
        "model": AuctionUpdate,
        "description": "Auction updated."
    },
    HTTP_400_BAD_REQUEST: {
        "content": {
            "application/json": {
                "example": {"detail": "Auction has already started."}
            }
        },
        "description": "Auction has already started or Invalid time range\
            or Overlapping with another appointment."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {"detail": "Auction not found."}
            }
        },
        "description": "Auction not found."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

cancel_an_auction = {
    HTTP_200_OK: {
        "model": RowCount,
        "description": "Auction canceled."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

close_an_auction = {
    HTTP_200_OK: {
        "model": AppointmentId,
        "description": "Auction closed. Return apmt_id if there is a winner."
    },
    HTTP_400_BAD_REQUEST: {
        "content": {
            "application/json": {
                "example": {"detail": "Auction has not started yet."}
            }
        },
        "description": "Auction has not started yet."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {"detail": "Auction not found."}
            }
        },
        "description": "Auction not found."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}

bid_auction = {
    HTTP_200_OK: {
        "model": Bidder,
        "description": "Bid placed."
    },
    HTTP_400_BAD_REQUEST: {
        "content": {
            "application/json": {
                "example": {"detail": "Amount is too low."}
            }
        },
        "description": "Invalid bid amount or Not started or Ended."
    },
    HTTP_404_NOT_FOUND: {
        "content": {
            "application/json": {
                "example": {"detail": "Auction not found."}
            }
        },
        "description": "Auction not found."
    },
    **POSSIBLE_JWTCOOKIE_RESPONSE
}