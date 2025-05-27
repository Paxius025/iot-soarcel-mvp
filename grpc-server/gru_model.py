import os
import torch
import torch.nn as nn
import pickle
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn.base")

class GRUNet(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size):
        super(GRUNet, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.gru = nn.GRU(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        out, _ = self.gru(x, h0)
        out = out[:, -1, :]
        out = self.fc(out)
        return out


class GRUModel:
    def __init__(self, base_dir: str = None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        # Load scalers
        feature_scaler_path = os.path.join(base_dir, 'model', 'feature_scaler.pkl')
        target_scaler_path = os.path.join(base_dir, 'model', 'target_scaler.pkl')

        with open(feature_scaler_path, 'rb') as f:
            self.feature_scaler = pickle.load(f)
        with open(target_scaler_path, 'rb') as f:
            self.target_scaler = pickle.load(f)

        # Load model
        gru_model_path = os.path.join(base_dir, 'model', 'gru_model.pth')
        input_size = len(self.feature_scaler.scale_)
        output_size = len(self.target_scaler.scale_)
        hidden_size = 64
        num_layers = 1

        self.model = GRUNet(input_size, hidden_size, num_layers, output_size).to(self.device)
        self.model.load_state_dict(torch.load(gru_model_path, map_location=self.device))
        self.model.eval()

    def forecasting(self, input_df: pd.DataFrame) -> np.ndarray:
        """
        ทำการพยากรณ์ข้อมูลจาก GRU
        input_df: pd.DataFrame รูปแบบ (seq_len, input_size)
        return: np.ndarray ขนาด (output_size,)
        """
        scaled_input = self.feature_scaler.transform(input_df.values)
        x = torch.tensor(scaled_input, dtype=torch.float32).unsqueeze(0).to(self.device)

        with torch.no_grad():
            pred = self.model(x).cpu().numpy()

        pred_inverse = self.target_scaler.inverse_transform(pred)
        return pred_inverse.squeeze()
