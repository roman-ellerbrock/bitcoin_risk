import pandas as pd
import numpy as np

def canonical_columns(df):
    """
    Converts the given DataFrame to a canonical format for Bitcoin price analysis.
    
    Parameters:
    - df (pd.DataFrame): The input DataFrame containing Bitcoin price data.
    
    Returns:
    - pd.DataFrame: A copy of the input DataFrame with the following modifications:
      - 'time' column converted to 'date' in datetime format, with time set to midnight.
      - Only 'date', 'time', and 'usd' (formerly 'open') columns are retained.
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['time'], unit='s')
    df['date'] = pd.to_datetime(df['date'].dt.date)
    df = df[['date', 'open']]
    # df = df[['date', 'time', 'open']]
    df = df.rename(columns={'open': 'usd'})
    return df
 
 
def extend_dates(df, start_date, last_date, end_date):
    """
    Extends the given DataFrame to include future dates and fills missing values with the last known value.
    
    Parameters:
    - df (pd.DataFrame): The input DataFrame containing Bitcoin price data.
    - start_date (pd.Timestamp): The start date for the extension.
    - end_date (pd.Timestamp): The end date for the extension.
    
    Returns:
    - pd.DataFrame: A copy of the input DataFrame with the following modifications:
      - The 'date' column is extended to include future dates.
      - Missing values in the 'usd' column are filled with the last known value.
    """
    df = df.copy()
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    df = pd.merge(df, pd.DataFrame({'date': date_range}), on='date', how='right')
    # df = pd.merge(df, pd.DataFrame({'date': date_range}), on='date')
    df.sort_values('date', inplace=True)

    # Use forward fill (ffill) to fill missing values with the last known value
    df['usd'] = df['usd'].ffill()
    # Set the condition to identify rows with dates larger than today
    condition = df['date'] > last_date

    # # Erase data in the 'DataColumn' for dates larger than today
    df.loc[condition, 'usd'] = None  # Replace with None or any other value you prefer

    return df


def _unix_to_btc_time(date):
    # first = 1.2625632e+09 # BTC
    # first = 1422133182 # ETH Jan 2015
    # first = 1435784113 # Eth July 2015
    # first = 1415784113 # Eth Nov 2014
    # first = 1406062513 # Eth July 2014 crowd sale
    # first = 1438289713 # Eth July 2015 first block
    delta = 1e7
    return date - first + delta


def _bitcoin_time(date):
    x = pd.to_datetime(date).copy()
    x = x.apply(lambda x: x.timestamp())
    return _unix_to_btc_time(x)


def _evaluate_fit(fit, date):
    # date -> btc-time
    x = pd.to_datetime(date)
    x = x.apply(lambda x: x.timestamp())
    x = _unix_to_btc_time(x)
    x = np.log(x)
    return np.exp(fit[0] * x + fit[1])


def btc_fit(btc, dates, price):
    """
    Performs a logscale linear fit on the Bitcoin price data to predict future prices.

    Parameters:
    - dates (pd.Series): A series of dates for which the Bitcoin prices are known.
    - price (pd.Series): A series of Bitcoin prices corresponding to the dates.

    Returns:
    - pd.Series: A series of predicted Bitcoin prices based on the logscale linear fit.
    """
    t = _bitcoin_time(dates)
    t = np.log(t)
    y = np.log(price)
    btc_fit = np.polyfit(t, y, 1)
    return _evaluate_fit(btc_fit, btc['date'])


def _evaluate_fit_time(fit, price, time):
    # date -> btc-time
    return (np.exp((np.log(price) - fit[1]) / fit[0]) - time) / (24 * 60 * 60)


def btc_fit_time(dates, price, price_full, dates_full):
    """
    This function calculates the time until the Bitcoin price reaches a certain value based on a logscale linear fit.
    
    Parameters:
    - dates (pd.Series): A series of dates for which the Bitcoin prices are known.
    - price (pd.Series): A series of Bitcoin prices corresponding to the dates.
    
    Returns:
    - pd.Series: A series of times until the Bitcoin price reaches the specified value.
    """
    t = _bitcoin_time(dates)
    t = np.log(t)
    y = np.log(price)
    btc_fit = np.polyfit(t, y, 1)
    t_full = _bitcoin_time(dates_full)
    return _evaluate_fit_time(btc_fit, price_full, t_full)


def log_fits(btc, last_included_date):
    # Create a copy of the original DataFrame
    df = btc.copy()
    # Limit the DataFrame to the specified date range
    df = df[df['date'] < pd.to_datetime(last_included_date)].copy()

    # Compute the main fit for the filtered range
    btc['fit'] = btc_fit(btc, df['date'], df['usd'])

    # Compute undervalued fit
    btc_undervalued = df[df['usd'] < btc.loc[df.index, 'fit']]  # Mask only for relevant indices
    btc['undervalued'] = btc_fit(btc, btc_undervalued['date'], btc_undervalued['usd'])

    # Compute overvalued fit
    btc_overvalued = df[df['usd'] > btc.loc[df.index, 'fit']]  # Mask only for relevant indices
    btc['overvalued'] = btc_fit(btc, btc_overvalued['date'], btc_overvalued['usd'])

    # Compute bubble fit
    btc_bubble = df[df['usd'] > btc.loc[df.index, 'overvalued']]  # Mask only for relevant indices
    btc['bubble'] = btc_fit(btc, btc_bubble['date'], btc_bubble['usd'])

    # Compute top fit
    btc_top = df[df['usd'] > btc.loc[df.index, 'bubble']]  # Mask only for relevant indices
    btc['top'] = btc_fit(btc, btc_top['date'], btc_top['usd'])

    return btc


def log_time_fits(btc, last_included_date):
    # Create a copy of the original DataFrame
    df = btc.copy()
    # Limit the DataFrame to the specified date range

    # Compute the main fit for the filtered range
    df = df[df['date'] < pd.to_datetime(last_included_date)].copy()
    btc['time-risk'] = btc_fit_time(df['date'], df['usd'], btc['usd'], btc['date'])
    return btc


def _compute_risks(btc):
    # Risk
    v0 = np.log(btc['undervalued'])
    v1 = np.log(btc['top'])
    btc['risk'] = (np.log(btc['usd']) - v0) / (v1 - v0)
    return btc


def prepare_and_compute_risk(name, start_date, end_date, future, last_date):
  # read and prepare 2 columns: date and price($)
  btc = pd.read_csv(name)
  btc = canonical_columns(btc)
  btc = extend_dates(btc, start_date, end_date, future)

  # logarithmic regression and compute risk
  btc = log_fits(btc, last_included_date=last_date)
  btc = log_time_fits(btc, last_date)
  btc = _compute_risks(btc)
  return btc
