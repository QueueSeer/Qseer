from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, GetCoreSchemaHandler
from pydantic_core.core_schema import (
    ValidatorFunctionWrapHandler,
    literal_schema,
    no_info_wrap_validator_function,
    plain_serializer_function_ser_schema
)


class Message(BaseModel):
    '''
    For returning only message.
    '''
    message: str

    def __init__(self, message: str):
        super().__init__(message=message)


class TokenPayload(BaseModel):
    exp: Any = Field(examples=[1800000000])
    sub: int
    roles: list[str] = Field(examples=[["seer"]])
    
    @property
    def is_seer(self) -> bool:
        return 'seer' in self.roles
    
    @property
    def is_admin(self) -> bool:
        return 'admin' in self.roles


class UserId(BaseModel):
    id: int = Field(examples=[1])


class RowCount(BaseModel):
    count: int


def pydantic_enum_by_name[E: Enum](enum_cls: type[E]) -> type[E]:
    """
    [source](https://github.com/pydantic/pydantic/discussions/2980#discussioncomment-9912210)
    """
    def __get_pydantic_core_schema__(
            cls: type[E],
            source_type: Any,
            handler: GetCoreSchemaHandler
        ):
        assert source_type is cls
        
        def get_enum(value: Any, validate_next: ValidatorFunctionWrapHandler):
            if isinstance(value, cls):
                return value
            else:
                name: str = validate_next(value)
                return enum_cls[name]

        def serialize(enum: E):
            return enum.name
        
        expected = [member.name for member in cls]
        name_schema = literal_schema(expected)
        
        return no_info_wrap_validator_function(
            get_enum, name_schema, 
            ref=cls.__name__,
            serialization=plain_serializer_function_ser_schema(serialize)
        )
    
    setattr(
        enum_cls,
        '__get_pydantic_core_schema__',
        classmethod(__get_pydantic_core_schema__)
    )
    return enum_cls
