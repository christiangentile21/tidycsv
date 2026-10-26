"""Pure cleaning functions: DataFrame in, new DataFrame out."""

import pandas as pd


def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy without fully duplicated rows, keeping the first one.

    Two rows count as duplicates only if every column matches; missing
    values in the same column are treated as equal. The index is reset
    to 0..n-1 so the result has no gaps.
    """
    return df.drop_duplicates(keep="first").reset_index(drop=True)
