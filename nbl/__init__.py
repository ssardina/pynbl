print(f'Invoking __init__.py for {__name__}')

__all__ = [
        'nbl_scrapper',
        'bball_stats',
        'tools'
        ]

from . import config
from . import nbl

# import nbl.bball_stats
# import nbl.tools
