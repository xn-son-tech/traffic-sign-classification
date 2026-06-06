import os
import time
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV
import joblib

def run_model_pipeline(data_dir="data", model_dir="outputs/models"):
    os.makedirs(model_dir, exist_ok=True)
    
    print("\n[*] Phase 3: Supervised Classification with PCA + SVM & Hyperparameter Optimization")
    
    # Load training data
    X_train_path = os.path.join(data_dir, "X_train.npy")
    y_train_path = os.path.join(data_dir, "y_train.npy")
    
    if not os.path.exists(X_train_path) or not os.path.exists(y_train_path):
        raise FileNotFoundError("Preprocessed training data not found. Please run preprocessing first!")
        
    X_train = np.load(X_train_path)
    y_train = np.load(y_train_path)
    
    print(f"Training data shape: {X_train.shape[0]} samples, {X_train.shape[1]} features.")
    
    # Define an end-to-end Machine Learning Pipeline
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('pca', PCA(n_components=0.95, svd_solver='full', random_state=42)),
        ('svm', SVC(probability=True, random_state=42))
    ])
    
    # Hyperparameter search grid
    param_grid = {
        'svm__C': [0.1, 1, 10],
        'svm__gamma': ['scale', 0.01],
        'svm__kernel': ['linear', 'rbf']
    }
    
    # To keep Grid Search computationally efficient and fast, we use a stratified subset of 5,000 samples for CV,
    # then retrain the winning pipeline on 100% of the training data.
    max_search_samples = 5000
    if len(X_train) > max_search_samples:
        print(f"[i] Subsampling {max_search_samples} stratified samples for fast Grid Search CV...")
        from sklearn.model_selection import train_test_split
        # Using train_test_split as a stratified sampler
        X_search, _, y_search, _ = train_test_split(
            X_train, y_train, 
            train_size=max_search_samples, 
            stratify=y_train, 
            random_state=42
        )
    else:
        X_search, y_search = X_train, y_train
        
    print("Starting Grid Search Cross-Validation (3-Fold Stratified CV)...")
    print(f"Grid parameters: {param_grid}")
    
    start_time = time.time()
    
    grid_search = GridSearchCV(
        pipeline, 
        param_grid=param_grid, 
        cv=3, 
        n_jobs=-1,  # use all available CPU cores for speed
        verbose=1,
        scoring='accuracy'
    )
    
    grid_search.fit(X_search, y_search)
    grid_search_time = time.time() - start_time
    print(f"[+] Grid Search CV completed in {grid_search_time:.2f} seconds ({grid_search_time/60:.2f} minutes).")
    
    # Print best parameters
    best_params = grid_search.best_params_
    best_score = grid_search.best_score_

    
    print(f"\n--- CV Optimization Results ---")
    print(f"Best CV Validation Accuracy: {best_score*100:.2f}%")
    print(f"Best Hyperparameters found:")
    print(f"  * SVM Regularization C: {best_params['svm__C']}")
    print(f"  * SVM Kernel Function: {best_params['svm__kernel']}")
    print(f"  * SVM Kernel Coefficient gamma: {best_params['svm__gamma']}")
    
    # Re-train the winning pipeline on the FULL training dataset for maximum final accuracy!
    print(f"\n[*] Retraining the winning pipeline on the FULL training set ({X_train.shape[0]} samples)...")
    refit_start = time.time()
    
    best_pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('pca', PCA(n_components=0.95, svd_solver='full', random_state=42)),
        ('svm', SVC(
            C=best_params['svm__C'],
            kernel=best_params['svm__kernel'],
            gamma=best_params['svm__gamma'],
            probability=True,
            random_state=42
        ))
    ])
    
    best_pipeline.fit(X_train, y_train)
    refit_time = time.time() - refit_start
    total_time = grid_search_time + refit_time
    
    n_components_selected = best_pipeline.named_steps['pca'].n_components_
    print(f"PCA Components selected for 95% variance on full data: {n_components_selected}")
    print(f"[+] Full retraining completed in {refit_time:.2f} seconds.")
    print("--------------------------------\n")
    
    # Save the best trained model pipeline
    model_path = os.path.join(model_dir, "best_pca_svm_pipeline.joblib")
    joblib.dump(best_pipeline, model_path)
    print(f"[+] Best Pipeline saved to '{model_path}' successfully.")
    
    # Save training time metadata for evaluation phase
    np.save(os.path.join(data_dir, "train_time.npy"), np.array([total_time]))
    
    return best_pipeline

if __name__ == "__main__":
    run_model_pipeline()
