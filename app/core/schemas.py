from pydantic import BaseModel


class Message(BaseModel):
    '''
    For returning only message.
    '''
    message: str

    def __init__(self, message: str):
        super().__init__(message=message)
