"""Pytest identity spelling shared with historical Python 3.6 drivers."""


def normalize_pytest_id(identity):
    # Parameter text is opaque; it can itself contain ::():: or non-ASCII text.
    while identity.endswith('::()'):
        identity = identity[:-4]
    path, bracket, parameter = identity.partition('[')
    parts = [part for part in path.split('::') if part != '()']
    return '::'.join(parts) + bracket + parameter
