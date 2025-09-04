
import numpy as np
import pandas as pd

# --------------------------------------------
# ZScore Anomalies function
# --------------------------------------------
def zscore_anomalies(series: pd.Series, window=14, z_thresh=2.0, min_points=10):
    """
    Detect anomalies in a time series using rolling Z-scores.

    Parameters
    ----------
    series : pd.Series
        Input numeric time-series data
    window : int, default=14
        Rolling window size for mean and standard deviation
    z_thresh : float, default=2.0
        Z-score threshold for flagging anomalies
    min_points : int, default=10
        Minimum points required before calculating stats

    Returns
    -------
    z : pd.Series
        Computed Z-scores
    flags : pd.Series (bool)
        Boolean where True = anomaly
    """
    s = series.copy().astype('float')
    roll_mean = s.rolling(window, min_periods=min_points).mean()
    roll_std = s.rolling(window, min_periods=min_points).std(ddof=0)
    z = (s - roll_mean) / (roll_std.replace(0, np.nan))
    flags = (z.abs() >= z_thresh)
    return z, flags

# ---------------------------------------------
# Exponentially Weighted Moving (EVM) function
# ---------------------------------------------
def ewm_anomalies(series: pd.Series, span=10, thresh=2.5, min_points=10):
    """
    Detect anomalies in a time series using exponentially weighted statistics.

    Parameters
    ----------
    series : pd.Series
        Input numeric time-series data
    span : int, default=10
        Span for the exponentially weighted mean and standard deviation
    thresh : float, default=2.5
        Threshold for flagging anomalies based on standardized score
    min_points : int, default=10
        Minimum points required before calculating stats

    Returns
    -------
    score : pd.Series
        Standardized scores relative to EWM mean and std
    flags : pd.Series (bool)
        Boolean where True = anomaly
    """
    s = series.copy().astype('float')
    mean = s.ewm(span=span, min_periods=min_points).mean()
    std = s.ewm(span=span, min_periods=min_points).std()
    score = (s - mean) / (std.replace(0, np.nan))
    flags = (score.abs() >= thresh)
    return score, flags