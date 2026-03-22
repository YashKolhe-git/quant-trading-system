import joblib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "ml_models" / "random_forest.pkl"
FEATURES_PATH = BASE_DIR / "ml_models" / "features.pkl"

model = joblib.load(MODEL_PATH)
features = joblib.load(FEATURES_PATH)