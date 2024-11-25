from pydantic import BaseModel


class MessageModel(BaseModel):
    '''
    For returning only message.
    '''
    message: str

    def __init__(self, message: str):
        super().__init__(message=message)
