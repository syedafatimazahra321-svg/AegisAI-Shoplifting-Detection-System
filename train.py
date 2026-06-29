import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset, random_split, Dataset
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import os
from model import AttentionLSTM

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
base_dir          = r"C:\JOB\AegisAI\data"
processed_X_path  = os.path.join(base_dir, "processed", "X.npy")
processed_y_path  = os.path.join(base_dir, "processed", "y.npy")

os.makedirs(r"C:\JOB\AegisAI\models", exist_ok=True)
os.makedirs(r"C:\JOB\AegisAI\logs",   exist_ok=True)

# ---------------------------------------------------------------------------
# Augmentation dataset wrapper
# Applies lightweight noise/scale jitter to feature vectors so the model
# cannot simply memorize DCSASS clip identities.
# ---------------------------------------------------------------------------
class AugmentedDataset(Dataset):
    """
    Wraps a TensorDataset and applies random augmentations to the
    [seq_len, feat_dim] feature tensors during training.

    Augmentations (all in feature space — no video needed):
      1. Gaussian noise       — simulates sensor/compression variation
      2. Random scale jitter  — simulates brightness / camera gain differences
      3. Temporal dropout     — randomly zeros out 1-2 frames so the model
                                cannot rely on fixed-position cues
    """
    def __init__(self, tensor_dataset, augment=True):
        self.dataset = tensor_dataset
        self.augment = augment

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        x, y = self.dataset[idx]          # x: [16, 1152], y: scalar

        if self.augment:
            # 1. Gaussian noise (std = 1% of typical feature range)
            x = x + torch.randn_like(x) * 0.01

            # 2. Scale jitter ±10%
            scale = 0.9 + torch.rand(1).item() * 0.2   # uniform [0.9, 1.1]
            x = x * scale

            # 3. Temporal dropout: zero out 1 random frame
            drop_idx = torch.randint(0, x.shape[0], (1,)).item()
            x[drop_idx] = 0.0

        return x, y


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
X_np = np.load(processed_X_path)
y_np = np.load(processed_y_path)

X = torch.tensor(X_np, dtype=torch.float32)
y = torch.tensor(y_np, dtype=torch.float32)

print(f"Dataset: {X.shape}, Labels: {y.shape}")
print(f"Positive ratio: {y.mean():.2%}")

# ---------------------------------------------------------------------------
# Split: 70% train / 15% val / 15% test
#
# Why three-way?
#   - val   : used during training to pick the best checkpoint (already done)
#   - test  : held-out, touched ONLY once at the very end to report real AUC
#
# Previously all data went into train+val so the reported AUC was inflated
# because the model had seen every clip at training time.
# ---------------------------------------------------------------------------
n_total = len(X)
n_test  = int(0.15 * n_total)
n_val   = int(0.15 * n_total)
n_train = n_total - n_val - n_test

full_dataset = TensorDataset(X, y)

train_ds_raw, val_ds_raw, test_ds_raw = random_split(
    full_dataset,
    [n_train, n_val, n_test],
    generator=torch.Generator().manual_seed(42)
)

print(f"Split → train: {n_train}  val: {n_val}  test: {n_test}")

# Wrap train split with augmentation; val/test get no augmentation
train_ds = AugmentedDataset(train_ds_raw, augment=True)
val_ds   = AugmentedDataset(val_ds_raw,   augment=False)
test_ds  = AugmentedDataset(test_ds_raw,  augment=False)

train_loader = DataLoader(train_ds, batch_size=32, shuffle=True,  num_workers=0)
val_loader   = DataLoader(val_ds,   batch_size=32, shuffle=False, num_workers=0)
test_loader  = DataLoader(test_ds,  batch_size=32, shuffle=False, num_workers=0)

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")
model = AttentionLSTM().to(device)

pos_weight = torch.tensor([(1 - y.mean()) / y.mean()]).to(device)
criterion  = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
optimizer  = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
scheduler  = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------
EPOCHS   = 20
best_auc = 0
train_losses, val_losses, val_aucs = [], [], []

for epoch in range(EPOCHS):
    # --- Train ---
    model.train()
    total_loss = 0
    for xb, yb in train_loader:
        xb, yb = xb.to(device), yb.to(device)
        optimizer.zero_grad()
        logit, _ = model(xb)
        loss = criterion(logit.squeeze(), yb)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        total_loss += loss.item()

    # --- Validate ---
    model.eval()
    val_loss, all_probs, all_true = 0, [], []
    with torch.no_grad():
        for xb, yb in val_loader:
            xb, yb = xb.to(device), yb.to(device)
            logit, _ = model(xb)
            loss = criterion(logit.squeeze(), yb)
            val_loss += loss.item()
            probs = torch.sigmoid(logit).squeeze().cpu().numpy()
            all_probs.extend(probs if probs.ndim > 0 else [probs.item()])
            all_true.extend(yb.cpu().numpy())

    auc       = roc_auc_score(all_true, all_probs)
    avg_train = total_loss / len(train_loader)
    avg_val   = val_loss   / len(val_loader)
    train_losses.append(avg_train)
    val_losses.append(avg_val)
    val_aucs.append(auc)

    print(f"Epoch {epoch+1:2d}/{EPOCHS} | Train: {avg_train:.4f} | "
          f"Val: {avg_val:.4f} | AUC: {auc:.4f}")

    if auc > best_auc:
        best_auc = auc
        torch.save(model.state_dict(),
                   r"C:\JOB\AegisAI\models\attention_lstm.pth")
        print(f"   -> Saved best model (AUC={best_auc:.4f})")

    scheduler.step()

# ---------------------------------------------------------------------------
# Final test-set evaluation  (run ONCE on held-out data)
# ---------------------------------------------------------------------------
print("\n=== Test Set Evaluation (held-out, never seen during training) ===")
model.load_state_dict(
    torch.load(r"C:\JOB\AegisAI\models\attention_lstm.pth",
               map_location=device))
model.eval()

test_probs, test_true = [], []
with torch.no_grad():
    for xb, yb in test_loader:
        xb = xb.to(device)
        logit, _ = model(xb)
        probs = torch.sigmoid(logit).squeeze().cpu().numpy()
        test_probs.extend(probs if probs.ndim > 0 else [probs.item()])
        test_true.extend(yb.numpy())

test_auc   = roc_auc_score(test_true, test_probs)
test_preds = [1 if p > 0.5 else 0 for p in test_probs]
print(f"Test AUC: {test_auc:.4f}")
print(classification_report(test_true, test_preds,
                             target_names=["Normal", "Shoplifting"]))
print("Confusion Matrix:")
print(confusion_matrix(test_true, test_preds))

# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

axes[0].plot(train_losses, label="Train Loss", color="#e94560")
axes[0].plot(val_losses,   label="Val Loss",   color="#0f3460")
axes[0].set_title("Training & Validation Loss")
axes[0].set_xlabel("Epoch")
axes[0].legend()

axes[1].plot(val_aucs, color="#27ae60", marker='o', markersize=4)
axes[1].set_title("Validation AUC over Epochs")
axes[1].set_xlabel("Epoch")
axes[1].set_ylabel("AUC")
axes[1].axhline(best_auc, ls='--', color='gray',
                label=f"Best val AUC: {best_auc:.4f}")
axes[1].axhline(test_auc, ls=':', color='red',
                label=f"Test AUC: {test_auc:.4f}")
axes[1].legend()

plt.tight_layout()
plt.savefig(r"C:\JOB\AegisAI\logs\training_plots.png",
            dpi=150, bbox_inches='tight')
print("\nSaved: C:\\JOB\\AegisAI\\logs\\training_plots.png")
print(f"Best Val AUC: {best_auc:.4f} | Test AUC: {test_auc:.4f}")

# ---------------------------------------------------------------------------
# Quick sanity check: if val AUC >> test AUC, model is still overfitting.
# You want them within ~0.05 of each other.
# ---------------------------------------------------------------------------
gap = best_auc - test_auc
if gap > 0.05:
    print(f"\n[WARNING] Val AUC vs Test AUC gap = {gap:.3f}  (> 0.05)")
    print("  Model may still be overfitting. Consider:")
    print("  - Increasing dropout in model.py (try 0.4-0.5)")
    print("  - Adding more augmentation noise in AugmentedDataset")
    print("  - Collecting more diverse training data")
else:
    print(f"\n[OK] Val/Test AUC gap = {gap:.3f} — model is generalising well.")