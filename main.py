import os
import sys
import argparse

# Import our custom pipeline modules
from src.data_downloader import setup_gtsrb_dataset
from src.data_preprocessing import run_data_preprocessing
from src.data_visualization import run_data_visualization
from src.model_pipeline import run_model_pipeline
from src.model_evaluation import run_model_evaluation

def main():
    parser = argparse.ArgumentParser(description="Traffic Sign Classification Pipeline using PCA + SVM")
    parser.add_argument("--skip-download", action="store_true", help="Skip downloading dataset")
    parser.add_argument("--skip-preprocess", action="store_true", help="Skip data preprocessing")
    parser.add_argument("--skip-visualize", action="store_true", help="Skip low-dimensional visualization")
    parser.add_argument("--skip-train", action="store_true", help="Skip training and model tuning")
    parser.add_argument("--skip-eval", action="store_true", help="Skip model evaluation")
    
    args = parser.parse_args()
    
    print("="*60)
    print("  TRAFFIC SIGN CLASSIFICATION SYSTEM (PCA + SVM)  ")
    print("="*60)
    
    data_dir = "data"
    plots_dir = "outputs/plots"
    models_dir = "outputs/models"
    
    # Phase 0: Data Collection
    if not args.skip_download:
        print("\n[Phase 0] Data Collection and Setup")
        setup_gtsrb_dataset(data_dir)
    else:
        print("\n[Phase 0] Skipped Data Collection")
        
    # Phase 1: Preprocessing & EDA
    if not args.skip_preprocess:
        print("\n[Phase 1] Preprocessing and EDA")
        run_data_preprocessing(data_dir, plots_dir)
    else:
        print("\n[Phase 1] Skipped Preprocessing")
        
    # Phase 2: Unsupervised Data Visualization
    if not args.skip_visualize:
        print("\n[Phase 2] Unsupervised Visualizations (PCA & t-SNE)")
        run_data_visualization(data_dir, plots_dir)
    else:
        print("\n[Phase 2] Skipped Visualization")
        
    # Phase 3: Model Pipeline Training
    if not args.skip_train:
        print("\n[Phase 3] Model Pipeline and Optimization")
        run_model_pipeline(data_dir, models_dir)
    else:
        print("\n[Phase 3] Skipped Model Pipeline Training")
        
    # Phase 4: Model Evaluation & Latency Analysis
    if not args.skip_eval:
        print("\n[Phase 4] Model Evaluation and Complexity Analysis")
        run_model_evaluation(data_dir, models_dir, plots_dir)
    else:
        print("\n[Phase 4] Skipped Evaluation")
        
    print("\n" + "="*60)
    print("  PIPELINE EXECUTION COMPLETE  ")
    print(f"  All outputs saved to 'outputs/' and plots in '{plots_dir}/'")
    print("="*60)

if __name__ == "__main__":
    main()
