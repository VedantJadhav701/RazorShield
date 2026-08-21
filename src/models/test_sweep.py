import pandas as pd
import numpy as np
import joblib

df = pd.read_parquet('data/processed/dataset_b_features.parquet')
test = df[df['split'] == 'test'].copy()
feats = [
    'rolling_txn_15m','baseline_txn_15m','velocity_ratio',
    'estimated_fraud_rate_15m','baseline_fraud_rate','estimated_fraud_rate_deviation',
    'amount_deviation','fraud_signal_ratio','estimated_fraud_count_15m',
    'expected_fraud_count_15m','fraud_excess_ratio','volume_deviation',
    'fraud_excess_minus_velocity','amount_shift_indicator'
]
model = joblib.load('models/spike_model/xgboost_spike_model_v2.joblib')
probs = model.predict_proba(test[feats].values)[:, 1]
test['prob'] = probs

print('Test set threshold sweep:')
for t in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
    vol = test[test['scenario_type'] == 'volume_only_spike']
    vol_fpr = np.mean(vol['prob'] >= t)
    spk = test[(test['scenario_type'] == 'fraud_spike') & (test['fraud_spike'] == 1)]
    spk_rec = np.mean(spk['prob'] >= t)
    preds = test[test['prob'] >= t]
    prec = np.mean(preds['fraud_spike']) if len(preds) > 0 else 0.0
    f1 = 2 * prec * spk_rec / (prec + spk_rec) if (prec + spk_rec) > 0 else 0.0
    print(f'T={t:.2f} | Vol-only FPR={vol_fpr*100:6.2f}% | Fraud Spike Recall={spk_rec*100:6.2f}% | Precision={prec:6.4f} | F1={f1:6.4f}')
