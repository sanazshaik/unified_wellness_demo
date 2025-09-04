
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, pearsonr

# The Spearman correlation measures how strongly two variables move together based on their rank order 
# rather than exact values. It ranges from -1 to +1, where positive values mean the variables rise together, 
# negative values mean one decreases as the other increases, and values near 0 show little to no relationship. 
# It’s useful when data isn’t perfectly linear or may have outliers.


# --------------------------------------------
# Correlation Description function
# --------------------------------------------
def _corr_desc(r):
    if r is None or np.isnan(r):
        return "no clear correlation" # Describes correlations
    mag = abs(r)
    if mag < 0.2:
        return "very weak correlation"
    if mag < 0.4:
        return "weak correlation"
    if mag < 0.6:
        return "moderate correlation"
    if mag < 0.8:
        return "strong correlation"
    return "very strong correlation"

# --------------------------------------------
# Compute Correlation function
# --------------------------------------------
def compute_correlations(df: pd.DataFrame):
    res = []
    pairs = [
        ('sleep_hours','sugar_next_day'),
        ('sleep_hours','resting_hr'),
        ('workout_min','resting_hr'),
        ('steps','weight_lb'),
        ('calories','weight_lb'),
        ('carbs_g','systolic_bp'),
        ('sugar_g','systolic_bp')
    ]
    for x,y in pairs:
        if x in df.columns and y in df.columns:
            s = df[[x,y]].dropna()
            if len(s) > 10:
                r, p = spearmanr(s[x], s[y])
                res.append({'x': x, 'y': y, 'r_spearman': float(r), 'p_value': float(p), 'n': len(s)})
    return pd.DataFrame(res)

# --------------------------------------------
# Generate Narrative function
# --------------------------------------------
def generate_narrative(df: pd.DataFrame, corr_df: pd.DataFrame):
    lines = []
    # Insight for sleep < 6h -> next-day sugar
    subset = df[['sleep_hours','sugar_next_day']].dropna()
    if len(subset) > 10:
        low_sleep = subset[subset['sleep_hours'] < 6]
        high_sleep = subset[subset['sleep_hours'] >= 6]
        if len(low_sleep) > 5 and len(high_sleep) > 5:
            delta = low_sleep['sugar_next_day'].mean() - high_sleep['sugar_next_day'].mean()
            pct = 100*delta / (high_sleep['sugar_next_day'].mean()+1e-9)
            lines.append(f"On days after you slept < 6h, average sugar intake the next day was about {pct:.0f}% higher than on well-slept days.")
    
    # Heart rate trend
    if 'resting_hr_dev' in df.columns:
        elevated = (df['resting_hr_dev'] > 3).rolling(window=3).sum()
        if (elevated >= 3).any():
            lines.append("Your resting heart rate was elevated for 3+ consecutive days at least once—previously linked to stress or illness for many people. Consider additional rest and hydration.")
   
    # Calorie and weight correlation - insights to weight gain or weight loss
    if 'calories' in df.columns and 'weight_lb' in df.columns:
        last_14 = df[['calories','weight_lb']].dropna().tail(14)
        if len(last_14) >= 10:
            cal_trend = np.polyfit(range(len(last_14)), last_14['calories'], 1)[0]
            wt_trend = np.polyfit(range(len(last_14)), last_14['weight_lb'], 1)[0]
            if cal_trend > 0 and wt_trend > 0:
                lines.append("In the last ~2 weeks, both calories and weight trended up together.")
            elif cal_trend < 0 and wt_trend < 0:
                lines.append("In the last ~2 weeks, calories and weight both trended down.")
    
    # Correlation summary based off Spearman
    for _, row in corr_df.iterrows():
        desc = _corr_desc(row['r_spearman'])
        r = row['r_spearman']
        n = int(row['n'])
        lines.append(
            f"The relationship between **{row['x']}** and **{row['y']}** shows a {desc} "
        )

    # If there is not enough data
    if not lines:
        lines.append("Not enough data yet to surface robust insights. Keep logging for a few more days.")
    return lines