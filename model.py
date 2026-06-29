import torch
import torch.nn as nn
import torch.nn.functional as F

class AttentionLSTM(nn.Module):
    def __init__(self, input_dim=1152, hidden_dim=256, num_layers=2, dropout=0.3):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout
        )
        # Attention mechanism: learns which frames to focus on
        self.attention_fc = nn.Linear(hidden_dim, 1)
        
        # Final classifier
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 1)  # Binary classification: shoplifting or normal
        )

    def forward(self, x):
        """
        x: [batch, seq_len, input_dim]  (seq_len = 16 frames)
        returns: logit [batch, 1], attention_weights [batch, seq_len]
        """
        lstm_out, _ = self.lstm(x)  # [batch, seq_len, hidden_dim]
        
        # Compute attention weights over time steps
        attn_scores = self.attention_fc(lstm_out).squeeze(-1)  # [batch, seq_len]
        attn_weights = F.softmax(attn_scores, dim=1)           # [batch, seq_len]
        
        # Weighted sum of LSTM outputs
        context = (lstm_out * attn_weights.unsqueeze(-1)).sum(dim=1)  # [batch, hidden_dim]
        logit = self.classifier(context)  # [batch, 1]
        
        return logit, attn_weights

# Test block
if __name__ == "__main__":
    model = AttentionLSTM()
    dummy = torch.randn(4, 16, 1152)  # batch=4, seq=16, feat=1152
    logit, weights = model(dummy)
    print(f"Output logit shape: {logit.shape}")        # [4, 1]
    print(f"Attention weights shape: {weights.shape}") # [4, 16]
    print(f"Weights sum : {weights[0].sum().item():.4f}")
    print("Model OK!")