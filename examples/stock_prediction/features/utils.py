import pandas as pd
import numpy as np

def compute_factor_tri(df_factor, df_stock, quantile_size=.2, resample='W-THU'):
    """
    takes parameter top quantile size, bottom quantile size.
    resample the factor to weekly, or monthly.
    computes the total return series of the factor based on the returns dataframe
    """
    df_factor_re = df_factor.resample(resample).ffill()
    # shift to make the return correspond to holding a position for that week
    df_stock_c = df_stock.resample(resample).ffill().pct_change().shift(-1)  
    
    all_pos_vecs = {}
    for row in df_factor_re.iterrows():
        cur_dt = row[0]
        not_null = row[1].dropna()
        num_not_null = len(not_null)
        num_pos = round(quantile_size * num_not_null)

        # setting the factors based on quantile
        cur_idx = list(not_null.index)
        np.random.shuffle(cur_idx)  # shuffling will randomly break ties
        sorted_factors = not_null.loc[cur_idx].sort_values(ascending=False)
        cur_top = sorted_factors[:num_pos].copy()
        cur_top.values.fill(1.)

        cur_bot = sorted_factors[-num_pos:].copy()
        cur_bot.values.fill(-1.)

        cur_nofact = sorted_factors[num_pos:-num_pos].copy()
        cur_nofact.values.fill(0.)
        cur_pos_vec = pd.concat([cur_top, cur_nofact, cur_bot])

        all_pos_vecs[cur_dt] = cur_pos_vec
        
    df_pos = pd.DataFrame(all_pos_vecs).T
    df_pos.columns = [x.replace('_factor', '') for x in df_pos.columns]
    pos_tickers = df_pos.columns
    
    df_rt = (df_stock_c[pos_tickers] * df_pos).mean(axis=1)
    return np.exp(np.log(df_rt + 1).cumsum())



def compute_sharpe(tri_series, resample='W-THU'):
    s_vol = tri_series.resample(resample).ffill().pct_change().std() * np.sqrt(52)
    y = (tri_series.index[-1] - tri_series.index[0]).days / 365.25
    s_rt = tri_series.values[-1] ** (1 / y) - 1
    return s_rt / s_vol
