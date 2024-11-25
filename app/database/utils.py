import re
from psycopg.errors import UniqueViolation


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
