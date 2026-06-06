import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import seaborn as sns

SELECTED_CLASSES = [1, 2, 11, 12, 13, 14, 17, 18, 25, 35]
CLASS_NAMES = {
    0: "Speed limit 30km/h (C1)",
    1: "Speed limit 50km/h (C2)",
    2: "Right-of-way next intersection (C11)",
    3: "Priority road (C12)",
    4: "Yield (C13)",
    5: "Stop (C14)",
    6: "No entry (C17)",
    7: "General caution (C18)",
    8: "Road work (C25)",
    9: "Ahead only (C35)"
}

def run_data_visualization(data_dir="data", output_dir="outputs/plots"):
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n[*] Phase 2: Unsupervised Learning & Low-Dimensional Data Visualization")
    
    # Load preprocessed training data
    X_train_path = os.path.join(data_dir, "X_train.npy")
    y_train_path = os.path.join(data_dir, "y_train.npy")
    
    if not os.path.exists(X_train_path) or not os.path.exists(y_train_path):
        raise FileNotFoundError("Preprocessed training data not found. Please run preprocessing first!")
        
    X = np.load(X_train_path)
    y = np.load(y_train_path)
    
    print(f"Loaded {X.shape[0]} training samples of dimension {X.shape[1]}.")
    
    # Subsample data if it is too large for t-SNE (e.g., take 3000 samples for visualization speed and clarity)
    max_vis_samples = 3000
    if len(X) > max_vis_samples:
        indices = np.random.choice(len(X), max_vis_samples, replace=False)
        X_sub = X[indices]
        y_sub = y[indices]
        print(f"Subsampled {max_vis_samples} images for visualization clarity.")
    else:
        X_sub = X
        y_sub = y
        
    # Set a highly premium visual style
    sns.set_theme(style="white")
    palette = sns.color_palette("tab10", 10)
    
    # --- 1. PCA 2D Visualization ---
    print("Fitting PCA for 2D visualization...")
    pca_2d = PCA(n_components=2, random_state=42)
    X_pca_2d = pca_2d.fit_transform(X_sub)
    
    plt.figure(figsize=(10, 8))
    for i in range(10):
        mask = (y_sub == i)
        plt.scatter(X_pca_2d[mask, 0], X_pca_2d[mask, 1], label=CLASS_NAMES[i], 
                    color=palette[i], alpha=0.7, edgecolors='none', s=25)
                    
    plt.title("PCA 2D Projection of Traffic Signs", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel(f"PC1 (Explained Var: {pca_2d.explained_variance_ratio_[0]*100:.1f}%)", fontsize=12)
    plt.ylabel(f"PC2 (Explained Var: {pca_2d.explained_variance_ratio_[1]*100:.1f}%)", fontsize=12)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True, fontsize=10)
    plt.tight_layout()
    
    pca2d_path = os.path.join(output_dir, "pca_2d.png")
    plt.savefig(pca2d_path, dpi=300)
    plt.close()
    print(f"[+] Saved PCA 2D plot to {pca2d_path}")
    
    # --- 2. PCA 3D Visualization ---
    print("Fitting PCA for 3D visualization...")
    pca_3d = PCA(n_components=3, random_state=42)
    X_pca_3d = pca_3d.fit_transform(X_sub)
    
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    ax.view_init(elev=20, azim=45)
    
    for i in range(10):
        mask = (y_sub == i)
        ax.scatter(X_pca_3d[mask, 0], X_pca_3d[mask, 1], X_pca_3d[mask, 2], 
                   label=CLASS_NAMES[i], color=palette[i], alpha=0.7, s=20)
                   
    ax.set_title("PCA 3D Projection of Traffic Signs", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel(f"PC1 ({pca_3d.explained_variance_ratio_[0]*100:.1f}%)", fontsize=10)
    ax.set_ylabel(f"PC2 ({pca_3d.explained_variance_ratio_[1]*100:.1f}%)", fontsize=10)
    ax.set_zlabel(f"PC3 ({pca_3d.explained_variance_ratio_[2]*100:.1f}%)", fontsize=10)
    plt.legend(bbox_to_anchor=(1.15, 1), loc='upper left', frameon=True, fontsize=10)
    plt.tight_layout()
    
    pca3d_path = os.path.join(output_dir, "pca_3d.png")
    plt.savefig(pca3d_path, dpi=300)
    plt.close()
    print(f"[+] Saved PCA 3D plot to {pca3d_path}")
    
    # --- 3. t-SNE 2D Visualization ---
    print("Running t-SNE (using PCA initialization for stability and speed)...")
    # Using PCA reduction first to 50 dimensions before t-SNE is standard practice to reduce noise
    pca_50 = PCA(n_components=50, random_state=42)
    X_pca_50 = pca_50.fit_transform(X_sub)
    
    tsne = TSNE(n_components=2, perplexity=30, random_state=42)
    X_tsne = tsne.fit_transform(X_pca_50)
    
    plt.figure(figsize=(10, 8))
    for i in range(10):
        mask = (y_sub == i)
        plt.scatter(X_tsne[mask, 0], X_tsne[mask, 1], label=CLASS_NAMES[i], 
                    color=palette[i], alpha=0.8, edgecolors='none', s=25)
                    
    plt.title("t-SNE 2D Visualization of Traffic Signs (Highly Separable Clusters)", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("t-SNE Dimension 1", fontsize=12)
    plt.ylabel("t-SNE Dimension 2", fontsize=12)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True, fontsize=10)
    plt.tight_layout()
    
    tsne_path = os.path.join(output_dir, "tsne_2d.png")
    plt.savefig(tsne_path, dpi=300)
    plt.close()
    print(f"[+] Saved t-SNE 2D plot to {tsne_path}")
    
    # --- 4. PCA Cumulative Explained Variance ---
    print("Fitting comprehensive PCA to compute cumulative explained variance curve...")
    pca_full = PCA(random_state=42)
    pca_full.fit(X)
    
    cumulative_variance = np.cumsum(pca_full.explained_variance_ratio_)
    
    # Find components needed for 90% and 95% variance
    n_90 = np.argmax(cumulative_variance >= 0.90) + 1
    n_95 = np.argmax(cumulative_variance >= 0.95) + 1
    
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(cumulative_variance) + 1), cumulative_variance, 
             color='#2b5c8f', linewidth=2.5, label="Cumulative Explained Variance")
             
    plt.axhline(y=0.95, color='r', linestyle='--', alpha=0.7, label=f"95% Variance threshold ({n_95} comps)")
    plt.axhline(y=0.90, color='g', linestyle='-.', alpha=0.7, label=f"90% Variance threshold ({n_90} comps)")
    plt.axvline(x=n_95, color='r', linestyle='--', alpha=0.5)
    plt.axvline(x=n_90, color='g', linestyle='-.', alpha=0.5)
    
    plt.title("PCA Cumulative Explained Variance Curve", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Number of Principal Components", fontsize=12)
    plt.ylabel("Cumulative Explained Variance Ratio", fontsize=12)
    plt.xlim(0, min(X.shape[1], 300))  # focus on first 300 comps
    plt.ylim(0.4, 1.05)
    plt.legend(loc='lower right', frameon=True, fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    var_plot_path = os.path.join(output_dir, "pca_variance_curve.png")
    plt.savefig(var_plot_path, dpi=300)
    plt.close()
    print(f"[+] Saved PCA Variance Curve to {var_plot_path}")
    print(f"[i] To explain 90% variance: {n_90} components are needed.")
    print(f"[i] To explain 95% variance: {n_95} components are needed.")

if __name__ == "__main__":
    run_data_visualization()
