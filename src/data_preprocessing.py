import os
import cv2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm

# Define the 10 selected classes
# 1: Speed limit 30km/h
# 2: Speed limit 50km/h
# 11: Right-of-way at the next intersection
# 12: Priority road
# 13: Yield
# 14: Stop
# 17: No entry
# 18: General caution
# 25: Road work
# 35: Ahead only
SELECTED_CLASSES = [1, 2, 11, 12, 13, 14, 17, 18, 25, 35]
CLASS_MAP = {original: new_idx for new_idx, original in enumerate(SELECTED_CLASSES)}
CLASS_NAMES = {
    1: "Speed limit 30km/h",
    2: "Speed limit 50km/h",
    11: "Right-of-way next intersection",
    12: "Priority road",
    13: "Yield",
    14: "Stop",
    17: "No entry",
    18: "General caution",
    25: "Road work",
    35: "Ahead only"
}

def preprocess_image(img_path, roi=None):
    """
    Applies the preprocessing pipeline:
    1. Read BGR image
    2. Crop to ROI (Region of Interest) if provided
    3. Resize to 32x32
    4. Convert to Grayscale
    5. Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    6. Normalize pixels to [0, 1]
    7. Flatten to 1024-dimensional vector
    """
    img = cv2.imread(img_path)
    if img is None:
        return None
    
    # 1. Crop to ROI to remove background noise
    if roi is not None:
        x1, y1, x2, y2 = roi
        # Make sure coordinates are valid
        h, w = img.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 > x1 and y2 > y1:
            img = img[y1:y2, x1:x2]
            
    # 2. Resize to uniform 32x32 pixels
    img = cv2.resize(img, (32, 32))
    
    # 3. Convert to Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 4. Apply CLAHE for local contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # 5. Normalize pixel values to [0, 1]
    normalized = enhanced.astype('float32') / 255.0
    
    # 6. Flatten to 1024 features
    return normalized.flatten()

def run_data_preprocessing(data_dir="data", output_dir="outputs/plots"):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("outputs/models", exist_ok=True)
    
    print("[*] Phase 1: Statistical Analysis and Exploratory Data Analysis (EDA)")
    
    # 1. Load Training Data Info
    train_images = []
    train_labels = []
    train_sizes = []
    
    train_base_path = os.path.join(data_dir, "GTSRB", "Final_Training", "Images")
    
    if not os.path.exists(train_base_path):
        raise FileNotFoundError(f"Dataset not found at {train_base_path}. Please run downloader first!")
        
    print("Reading and filtering training metadata...")
    class_counts = {c: 0 for c in SELECTED_CLASSES}
    
    for c in SELECTED_CLASSES:
        class_folder = f"{c:05d}"
        class_path = os.path.join(train_base_path, class_folder)
        csv_file = os.path.join(class_path, f"GT-{class_folder}.csv")
        
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file, sep=';')
            class_counts[c] = len(df)
            
            for _, row in tqdm(df.iterrows(), total=len(df), desc=f"Class {c:02d}"):
                img_path = os.path.join(class_path, row['Filename'])
                roi = (int(row['Roi.X1']), int(row['Roi.Y1']), int(row['Roi.X2']), int(row['Roi.Y2']))
                
                # Preprocess
                features = preprocess_image(img_path, roi)
                if features is not None:
                    train_images.append(features)
                    train_labels.append(CLASS_MAP[c])
                    train_sizes.append((row['Width'], row['Height']))
                    
    # Convert to numpy arrays
    X_train = np.array(train_images)
    y_train = np.array(train_labels)
    train_sizes = np.array(train_sizes)
    
    print(f"[+] Processed {len(X_train)} training images from 10 selected classes.")
    
    # 2. EDA: Visualizing Class Distribution
    plt.figure(figsize=(12, 6))
    sns.set_theme(style="whitegrid")
    
    # Map original classes to names
    labels_names = [f"Class {c}\n{CLASS_NAMES[c]}" for c in SELECTED_CLASSES]
    counts = [class_counts[c] for c in SELECTED_CLASSES]
    
    colors = sns.color_palette("viridis", len(SELECTED_CLASSES))
    bars = plt.bar(labels_names, counts, color=colors, edgecolor='black', linewidth=1)
    
    plt.title("Class Distribution of 10 Selected Traffic Signs (Training Set)", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Traffic Sign Classes", fontsize=12, labelpad=10)
    plt.ylabel("Number of Samples", fontsize=12, labelpad=10)
    plt.xticks(rotation=45, ha='right', fontsize=10)
    
    # Add values on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, height + 15, f'{int(height)}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
    plt.tight_layout()
    dist_plot_path = os.path.join(output_dir, "class_distribution.png")
    plt.savefig(dist_plot_path, dpi=300)
    plt.close()
    print(f"[+] Saved class distribution plot to {dist_plot_path}")
    
    # 3. Statistical Analysis of Image Dimensions
    widths = train_sizes[:, 0]
    heights = train_sizes[:, 1]
    
    print("\n--- Image Size Statistical Analysis ---")
    print(f"Total training samples: {len(X_train)}")
    print(f"Widths:  Min = {widths.min()}, Max = {widths.max()}, Mean = {widths.mean():.2f}, Median = {np.median(widths):.2f}, Std = {widths.std():.2f}")
    print(f"Heights: Min = {heights.min()}, Max = {heights.max()}, Mean = {heights.mean():.2f}, Median = {np.median(heights):.2f}, Std = {heights.std():.2f}")
    print("----------------------------------------\n")
    
    # 4. Load and Process Test Data
    print("Reading and filtering test metadata...")
    test_images = []
    test_labels = []
    
    test_csv_path = os.path.join(data_dir, "GT-final_test.csv")
    test_base_path = os.path.join(data_dir, "GTSRB", "Final_Test", "Images")
    
    if os.path.exists(test_csv_path) and os.path.exists(test_base_path):
        test_df = pd.read_csv(test_csv_path, sep=';')
        
        # Filter test dataframe for selected classes
        filtered_test_df = test_df[test_df['ClassId'].isin(SELECTED_CLASSES)]
        
        for _, row in tqdm(filtered_test_df.iterrows(), total=len(filtered_test_df), desc="Test Set"):
            img_path = os.path.join(test_base_path, row['Filename'])
            roi = (int(row['Roi.X1']), int(row['Roi.Y1']), int(row['Roi.X2']), int(row['Roi.Y2']))
            
            features = preprocess_image(img_path, roi)
            if features is not None:
                test_images.append(features)
                test_labels.append(CLASS_MAP[row['ClassId']])
                
    X_test = np.array(test_images)
    y_test = np.array(test_labels)
    
    print(f"[+] Processed {len(X_test)} testing images from 10 selected classes.")
    
    # 5. Save the preprocessed NumPy arrays
    np.save(os.path.join(data_dir, "X_train.npy"), X_train)
    np.save(os.path.join(data_dir, "y_train.npy"), y_train)
    np.save(os.path.join(data_dir, "X_test.npy"), X_test)
    np.save(os.path.join(data_dir, "y_test.npy"), y_test)
    print(f"[+] Preprocessed datasets saved to '{data_dir}/' directory.")
    
    return X_train, y_train, X_test, y_test

if __name__ == "__main__":
    run_data_preprocessing()
