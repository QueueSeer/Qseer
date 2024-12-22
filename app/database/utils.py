import re
from psycopg.errors import NotNullViolation, UniqueViolation


def parse_unique_violation(error: UniqueViolation) -> dict:
    '''
    Parse a UniqueViolation error from psycopg into a dictionary.

    Return None if match is not found.
    '''
    pattern = re.compile(r'Key \((?P<field>.+?)\)=\((?P<value>.+?)\) already exists')
    match = pattern.search(str(error.diag.message_detail))
    if match is not None:
        match = match.groupdict()
        match['type'] = "UniqueViolation"
    return match


def parse_not_null_violation(error: NotNullViolation) -> dict:
    '''
    Parse a NotNullViolation error from psycopg into a dictionary.
    '''
    return {"field": error.diag.column_name, "type": "NotNullViolation"}
