import os
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report, confusion_matrix
import joblib

SELECTED_CLASSES = [1, 2, 11, 12, 13, 14, 17, 18, 25, 35]
CLASS_NAMES = [
    "Speed limit 30 (C1)",
    "Speed limit 50 (C2)",
    "Priority intersection (C11)",
    "Priority road (C12)",
    "Yield (C13)",
    "Stop (C14)",
    "No entry (C17)",
    "General caution (C18)",
    "Road work (C25)",
    "Ahead only (C35)"
]

def run_model_evaluation(data_dir="data", model_dir="outputs/models", output_dir="outputs/plots"):
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n[*] Phase 4: Model Evaluation and Computational Complexity Analysis")
    
    # Load test dataset and model pipeline
    X_test_path = os.path.join(data_dir, "X_test.npy")
    y_test_path = os.path.join(data_dir, "y_test.npy")
    model_path = os.path.join(model_dir, "best_pca_svm_pipeline.joblib")
    
    if not os.path.exists(X_test_path) or not os.path.exists(y_test_path):
        raise FileNotFoundError("Preprocessed test data not found. Please run preprocessing first!")
    if not os.path.exists(model_path):
        raise FileNotFoundError("Trained pipeline model not found. Please run training pipeline first!")
        
    X_test = np.load(X_test_path)
    y_test = np.load(y_test_path)
    pipeline = joblib.load(model_path)
    
    print(f"Loaded test dataset: {X_test.shape[0]} samples.")
    print("Evaluating model pipeline...")
    
    # Measure total prediction time (inference latency)
    start_inf = time.time()
    y_pred = pipeline.predict(X_test)
    end_inf = time.time()
    
    total_inf_time = end_inf - start_inf
    avg_inf_latency_ms = (total_inf_time / len(X_test)) * 1000
    fps = len(X_test) / total_inf_time
    
    # 1. Compute Standard Metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(y_test, y_pred, average='macro')
    precision_weighted, recall_weighted, f1_weighted, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted')
    
    print("\n================== EVALUATION REPORT ==================")
    print(f"Overall Accuracy:       {accuracy*100:.2f}%")
    print(f"Macro Precision:        {precision_macro*100:.2f}%")
    print(f"Macro Recall:           {recall_macro*100:.2f}%")
    print(f"Macro F1-Score:         {f1_macro*100:.2f}%")
    print(f"Weighted F1-Score:      {f1_weighted*100:.2f}%")
    print("-------------------------------------------------------")
    print("\nDetailed Classification Report:")
    print(classification_report(y_test, y_pred, target_names=CLASS_NAMES))
    print("=======================================================\n")
    
    # 2. Confusion Matrix Plotting
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(12, 10))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES,
                cbar=True, square=True, annot_kws={"size": 10, "weight": "bold"})
                
    plt.title("Confusion Matrix of 10 Selected Traffic Signs (PCA + SVM)", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Predicted Labels", fontsize=12, labelpad=10)
    plt.ylabel("True Labels", fontsize=12, labelpad=10)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    cm_path = os.path.join(output_dir, "confusion_matrix.png")
    plt.savefig(cm_path, dpi=300)
    plt.close()
    print(f"[+] Saved Confusion Matrix plot to {cm_path}")
    
    # 3. Computational Complexity Analysis
    n_components = pipeline.named_steps['pca'].n_components_
    n_features_raw = X_test.shape[1]
    
    # Theoretical analysis
    print("\n--- Theoretical Computational Complexity ---")
    print("1. Without PCA (Direct SVM on raw 32x32 images):")
    print(f"   * Input Dimension (d): {n_features_raw} features (1024 dimensional)")
    print(f"   * SVM Inference Complexity per image: O(d * N_support_vectors)")
    print(f"   * Multiplication operations per image: ~{n_features_raw} * N_sv")
    
    print("2. With PCA (Dimensionality Reduction):")
    print(f"   * Compressed Dimension (k): {n_components} components (95% variance)")
    print(f"   * PCA projection complexity: O(d * k)")
    print(f"   * SVM Inference Complexity: O(k * N_support_vectors)")
    print(f"   * Total multiplication operations: ~({n_features_raw} * {n_components}) + ({n_components} * N_sv)")
    print(f"   * Since k ({n_components}) << d ({n_features_raw}), the SVM classifier operates on 10x smaller vectors, "
          "drastically speeding up prediction and reducing memory footprint!")
    
    # Empirical analysis
    print("\n--- Empirical Performance & Latency ---")
    print(f"Total Test Samples:             {len(X_test)} images")
    print(f"Total Inference Time:           {total_inf_time:.4f} seconds")
    print(f"Average Latency per image:      {avg_inf_latency_ms:.3f} milliseconds")
    print(f"Real-time Throughput (FPS):     {fps:.2f} Frames Per Second")
    if fps > 60:
        print("[+] Excellent performance! Model is easily compatible with real-time video processing (60+ FPS).")
    else:
        print("[i] Good performance! Model can process typical video feeds.")
    print("--------------------------------------------\n")
    
    # Write a text report of results for academic documentation
    results_report = (
        f"TRAFFIC SIGN CLASSIFICATION (PCA + SVM) RESULTS REPORT\n"
        f"======================================================\n"
        f"Selected classes: 10 types of GTSRB signs\n"
        f"Model: Standardized -> PCA (95% var, k={n_components}) -> SVM (RBF kernel)\n\n"
        f"Accuracy:          {accuracy*100:.2f}%\n"
        f"Macro F1-Score:    {f1_macro*100:.2f}%\n"
        f"Weighted F1-Score: {f1_weighted*100:.2f}%\n"
        f"Average Latency:   {avg_inf_latency_ms:.3f} ms\n"
        f"Throughput:        {fps:.2f} FPS\n"
    )
    with open(os.path.join(data_dir, "results.txt"), "w") as f:
        f.write(results_report)

if __name__ == "__main__":
    run_model_evaluation()
