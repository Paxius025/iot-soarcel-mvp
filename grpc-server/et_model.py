import os
import joblib
import pandas as pd
from pathlib import Path

class ETModel:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        model_path = os.path.join(base_dir, 'model', 'et_model.pkl')
        
        print(f"Loading model from: {model_path}")
        self.model = joblib.load(model_path)

    def predict(self, input_df: pd.DataFrame):
        if not isinstance(input_df, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")

        return self.model.predict(input_df)


