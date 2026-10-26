"""Allow running tidycsv as `python -m tidycsv`."""

import sys

from tidycsv.cli import main

sys.exit(main())
