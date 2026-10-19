# ML training image (Linux x86_64 — matches Render deploy target).
# Native XGBoost works here (no macOS libomp issue).
FROM python:3.11-slim
RUN pip install --no-cache-dir pandas numpy scikit-learn joblib xgboost \
 && pip install --no-cache-dir tensorflow-cpu
WORKDIR /work
