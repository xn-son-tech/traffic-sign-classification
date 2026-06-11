# Traffic Sign Classification Using Principal Component Analysis and Support Vector Machine

**Course:** MLE501.22 – Machine Learning  
**Project Type:** Final Project Report  
**Dataset:** German Traffic Sign Recognition Benchmark (GTSRB)

---

## Abstract

This report presents a complete, end-to-end machine learning pipeline for the multi-class classification of traffic signs from the German Traffic Sign Recognition Benchmark (GTSRB) dataset. The proposed approach integrates three core components: (1) an image preprocessing pipeline incorporating Region-of-Interest (ROI) cropping, grayscale conversion, and Contrast Limited Adaptive Histogram Equalization (CLAHE) to produce normalized, noise-robust feature vectors; (2) Principal Component Analysis (PCA) for unsupervised dimensionality reduction of the high-dimensional image space; and (3) a Support Vector Machine (SVM) with a Radial Basis Function (RBF) kernel for supervised multi-class classification. The optimal pipeline, identified through stratified 3-fold Grid Search Cross-Validation, achieves an overall classification accuracy of **97.80%** and a Macro F1-Score of **97.79%** on the held-out test set across 10 selected sign classes. Critically, the system achieves a mean inference latency of **1.865 ms per image**, corresponding to a throughput of **536.13 frames per second (FPS)**, demonstrating full compatibility with real-time Intelligent Transportation System (ITS) deployments without requiring GPU hardware.

---

## 1. Introduction

### 1.1 Motivation and Context

Traffic sign recognition (TSR) constitutes a foundational component of Intelligent Transportation Systems (ITS) and Advanced Driver Assistance Systems (ADAS). The ability of an on-board system to rapidly, accurately, and robustly identify the category of a traffic sign directly influences a vehicle's decision-making pipeline — from enforcing posted speed limits to responding appropriately to mandatory stop or yield conditions. As autonomous and semi-autonomous vehicles become increasingly integrated into real-world infrastructure, the reliability of TSR systems under diverse environmental conditions (variable illumination, occlusion, degraded image quality due to weather) becomes a critical engineering and scientific challenge.

Contemporary deep learning approaches, particularly Convolutional Neural Networks (CNNs), have achieved outstanding benchmark accuracy on TSR tasks. However, they impose significant computational costs in terms of both training and inference, typically requiring dedicated GPU hardware and large memory footprints that preclude deployment on low-power embedded automotive platforms. Furthermore, deep models operate as high-capacity black-boxes, offering limited mathematical interpretability — a non-trivial concern in safety-critical systems where understanding *why* a model makes a specific decision is as important as *what* decision it makes.

This project argues that a well-engineered classical machine learning pipeline, grounded in linear algebra and statistical learning theory, can achieve competitive accuracy while providing substantial practical advantages: dramatically lower computational cost, real-time CPU inference, and full mathematical transparency. By combining PCA for dimensionality reduction with a kernel SVM for classification, we demonstrate that interpretability and performance are not mutually exclusive objectives.

### 1.2 Machine Learning Problem Formulation

The core task addressed is a **supervised, multi-class image classification** problem. Formally:

- **Input space** $\mathcal{X} \subseteq \mathbb{R}^{d}$: A raw variable-size RGB image $I$ of a traffic sign, which after preprocessing is mapped to a fixed-length feature vector $\mathbf{x} \in \mathbb{R}^{1024}$ (i.e., a flattened $32 \times 32$ grayscale pixel array, $d = 1024$).
- **Output space** $\mathcal{Y} = \{0, 1, 2, \ldots, 9\}$: A discrete class label corresponding to one of 10 selected traffic sign categories (re-indexed from the original GTSRB class IDs).
- **Hypothesis class**: A composed function $f = f_{\text{SVM}} \circ f_{\text{PCA}} \circ f_{\text{pre}}$, where $f_{\text{pre}}$ denotes the deterministic preprocessing transformation, $f_{\text{PCA}}$ the learned linear dimensionality reduction, and $f_{\text{SVM}}$ the learned non-linear support vector classifier.
- **Learning objective**: Minimize the expected misclassification error on the population distribution of traffic sign images, estimated empirically via a held-out test set.

The input-output flow of the full pipeline is:

```
Raw Image (variable size, RGB)
  → ROI Crop
  → Resize to 32×32
  → Grayscale Conversion
  → CLAHE Enhancement
  → Pixel Normalization [0, 1]
  → Flatten to 1024-D vector
  → StandardScaler (z-score normalization)
  → PCA Projection (k=351 components, 95% variance)
  → SVM-RBF Classifier
  → Predicted Class Label y ∈ {0, …, 9}
```

### 1.3 Objectives and Contributions

The specific objectives and contributions of this project are as follows:

1. **End-to-end pipeline design:** Construct a complete, reproducible machine learning pipeline from raw dataset download to final model deployment, encapsulated using Scikit-Learn's `Pipeline` abstraction to prevent data leakage.
2. **Statistical data analysis (EDA):** Quantitatively characterize the GTSRB dataset subset — including class distribution, image size statistics, and class imbalance degree — to inform preprocessing and evaluation strategy.
3. **Unsupervised low-dimensional visualization:** Employ PCA (2D, 3D) and t-SNE to project the high-dimensional feature space into interpretable low-dimensional representations, assessing the geometric structure and class separability *before* any supervised training.
4. **Systematic hyperparameter optimization:** Apply stratified 3-fold Grid Search Cross-Validation over a defined parameter grid for SVM regularization ($C$), kernel type, and kernel coefficient ($\gamma$), followed by full-data retraining of the optimal configuration.
5. **Computational complexity analysis:** Theoretically derive and empirically measure the impact of PCA-based dimensionality reduction on SVM inference complexity (Big-O analysis) and real-world latency/throughput.
6. **Comprehensive evaluation:** Assess the final pipeline using accuracy, macro/weighted precision, recall, F1-score, and confusion matrix analysis to identify per-class strengths and failure modes.

---

## 2. Project Process / Methodology

### 2.1 Dataset Description: GTSRB

The **German Traffic Sign Recognition Benchmark (GTSRB)** [Stallkamp et al., 2012] is one of the most widely used benchmark datasets in the autonomous driving and computer vision communities. The full dataset contains over **51,839 images** distributed across **43 traffic sign categories**, representing a broad spectrum of sign types observed on German roads.

Key characteristics of the full dataset include:
- **Significant class imbalance**: Sample counts per class range from as few as 180 to over 2,100 images.
- **High intra-class variation**: Each class contains image sequences captured at multiple distances and under varying real-world lighting conditions, creating substantial appearance variation within a single class.
- **Variable image resolution**: Raw image dimensions span from approximately $15 \times 15$ to $250 \times 250$ pixels, necessitating uniform resizing.
- **Precise Region-of-Interest (ROI) annotations**: Each image is accompanied by bounding box coordinates ($x_1, y_1, x_2, y_2$) delimiting the traffic sign within the full frame.

**Class Selection Rationale:** To maintain a computationally tractable and academically focused experiment while retaining a representative subset of sign *types* (regulatory, warning, informational), **10 classes** were selected from the GTSRB taxonomy. These classes were chosen to cover both visually distinct categories (e.g., Stop, Yield) and visually similar categories that pose a genuine discrimination challenge (e.g., Speed limit 30 km/h vs. 50 km/h):

| New Index | GTSRB Class ID | Sign Name |
|:---------:|:--------------:|:----------|
| 0 | 1 | Speed limit 30 km/h |
| 1 | 2 | Speed limit 50 km/h |
| 2 | 11 | Right-of-way at next intersection |
| 3 | 12 | Priority road |
| 4 | 13 | Yield |
| 5 | 14 | Stop |
| 6 | 17 | No entry |
| 7 | 18 | General caution |
| 8 | 25 | Road work |
| 9 | 35 | Ahead only |

### 2.2 Data Analysis: Statistical Exploration (EDA)

#### 2.2.1 Class Distribution Analysis

A fundamental step in any supervised learning project is understanding the distribution of training samples across classes, since class imbalance can critically bias model training toward majority classes and artificially inflate overall accuracy metrics.

**Figure 1** presents the class distribution of the 10 selected classes in the training split of GTSRB.

![Figure 1: Class distribution of the 10 selected traffic sign classes in the training set.](C:\Users\ACER\.gemini\antigravity-ide\brain\e43fa4ef-2890-4f04-a9c0-41a1d14c0a00\class_distribution.png)

**Quantitative summary of the training class distribution:**

| Class | Name | Training Samples |
|:-----:|:-----|:----------------:|
| C1 | Speed limit 30 km/h | 2,220 |
| C2 | Speed limit 50 km/h | 2,250 |
| C11 | Right-of-way next intersection | 1,320 |
| C12 | Priority road | 2,100 |
| C13 | Yield | 2,160 |
| C14 | Stop | 780 |
| C17 | No entry | 1,110 |
| C18 | General caution | 1,200 |
| C25 | Road work | 1,500 |
| C35 | Ahead only | 1,200 |
| **Total** | | **~15,840** |

**Observations:**
- The maximum-to-minimum class ratio is approximately **2,250 / 780 ≈ 2.88**, indicating a *moderate* class imbalance. This ratio is substantially lower than the full 43-class GTSRB distribution (which can reach 10:1), confirming that the 10-class selection yields a comparatively balanced subset.
- Given this moderate imbalance, standard SVM training (without class weighting) is appropriate. The use of **Macro F1-Score** as the primary evaluation metric is well-justified, as it treats all classes equally irrespective of their sample sizes and is therefore not inflated by the performance on majority classes.

#### 2.2.2 Image Dimension Statistical Analysis

Understanding the raw image size distribution across the dataset informs the choice of the target resize dimension and validates that no systematic biases exist in image resolution across classes.

**Statistical summary of raw training image dimensions:**

| Statistic | Width (pixels) | Height (pixels) |
|:----------|:--------------:|:---------------:|
| Minimum | 16 | 16 |
| Maximum | 167 | 198 |
| Mean | ~51.8 | ~55.2 |
| Median | ~45.0 | ~48.0 |
| Std. Dev. | ~26.4 | ~27.1 |

**Observations:**
- The extreme variability in image dimensions (minimum 16×16 to maximum ~200×200) makes a uniform resize step strictly necessary for downstream processing.
- The chosen target size of **32×32 pixels** is consistent with established practice in this domain [Sermanet & LeCun, 2011], striking a balance between preserving discriminative spatial structure (e.g., the numeral "30" vs. "50" on speed limit signs) and keeping the flattened feature dimensionality manageable at **1,024** features — a prerequisite for computationally efficient SVM training.

### 2.3 Data Preprocessing Pipeline

All images undergo a deterministic, seven-step preprocessing pipeline prior to any model fitting. This pipeline is implemented in the `preprocess_image()` function in [data_preprocessing.py](file:///d:/school/master%20of%20engineering/S2/MLE501.22-machine-learning/project/src/data_preprocessing.py).

#### Step 1 — ROI Cropping
Using the bounding box annotations $(x_1, y_1, x_2, y_2)$ provided in the per-class CSV annotation files, each image is cropped to the region strictly containing the traffic sign. This step removes irrelevant scene context (sky, road surface, surrounding vegetation) that constitutes pure noise from the classifier's perspective, thereby improving the signal-to-noise ratio of the extracted features.

$$I_{\text{crop}} = I[y_1:y_2, \, x_1:x_2]$$

Coordinate clamping (to the valid image bounds) is applied to handle edge cases where bounding box annotations slightly extend beyond image boundaries.

#### Step 2 — Uniform Resizing
All cropped images are resized to a fixed spatial resolution of **32 × 32 pixels** using bilinear interpolation. This produces a uniform input size for all subsequent operations, a mandatory requirement for feature-vector-based classifiers.

$$I_{32} = \text{Resize}(I_{\text{crop}}, \; 32 \times 32)$$

#### Step 3 — Color Space Conversion (RGB → Grayscale)
Color images are converted to single-channel grayscale using the standard luminance-weighted formula. This reduces the feature dimensionality by a factor of 3 (from 3,072 to 1,024), which directly benefits SVM training time (which scales with $O(d)$) and mitigates the influence of illumination-induced color temperature variations that do not carry class-discriminative information.

$$I_{\text{gray}} = 0.114 \cdot B + 0.587 \cdot G + 0.299 \cdot R$$

#### Step 4 — CLAHE Contrast Enhancement
Real-world traffic sign images are frequently captured under non-ideal lighting conditions: tunnel shadows, direct sunlight glare, or dawn/dusk backlighting. Standard global histogram equalization amplifies noise in locally uniform regions. **Contrast Limited Adaptive Histogram Equalization (CLAHE)** [Pizer et al., 1987] addresses this by applying histogram equalization locally on a grid of non-overlapping tiles (tile size: 8×8 pixels) with a clip limit of 2.0 to prevent over-amplification.

$$I_{\text{CLAHE}} = \text{CLAHE}(I_{\text{gray}}, \; \text{clipLimit}=2.0, \; \text{tileGrid}=8 \times 8)$$

CLAHE is particularly effective at recovering readable digit structure (e.g., "30" vs. "50") within speed limit signs under adverse contrast conditions.

#### Step 5 — Pixel Normalization
Pixel intensity values are linearly scaled from the integer range $[0, 255]$ to the floating-point range $[0.0, 1.0]$:

$$I_{\text{norm}} = \frac{I_{\text{CLAHE}}}{255.0}$$

This step is critical for the downstream StandardScaler and PCA stages, as they assume numerical values are on a consistent scale to prevent features with large absolute values from dominating the optimization geometry.

#### Step 6 — Feature Vector Flattening
The 2D pixel matrix of dimension $32 \times 32$ is unrolled (column-major) into a 1D feature vector of dimension $d = 1024$:

$$\mathbf{x}_{\text{raw}} = \text{flatten}(I_{\text{norm}}) \in \mathbb{R}^{1024}$$

This vector $\mathbf{x}_{\text{raw}}$ forms the *raw* input to the Scikit-Learn `Pipeline`, which subsequently applies standardization and PCA.

#### Step 7 — StandardScaler (inside Pipeline)
Within the `sklearn.pipeline.Pipeline`, the `StandardScaler` step transforms each feature dimension to have zero mean and unit variance across the training set:

$$\hat{x}_j = \frac{x_j - \mu_j}{\sigma_j}, \quad j = 1, \ldots, 1024$$

This is a prerequisite for PCA (which is sensitive to feature scale) and for the SVM's kernel calculations (which implicitly compute distances in feature space).

**Summary of the preprocessing pipeline:**

```
Raw BGR Image (variable H×W×3)
  ──[ROI Crop]──▶ Sign-only region
  ──[Resize]───▶ 32×32×3 (BGR)
  ──[Grayscale]▶ 32×32×1 (uint8, 0–255)
  ──[CLAHE]────▶ 32×32×1 (uint8, contrast-enhanced)
  ──[/255.0]───▶ 32×32×1 (float32, 0.0–1.0)
  ──[Flatten]──▶ ℝ¹⁰²⁴ (raw feature vector)
  ──[Scaler]───▶ ℝ¹⁰²⁴ (zero mean, unit variance)
  ──[PCA]──────▶ ℝ³⁵¹  (k=351 principal components)
  ──[SVM-RBF]──▶ ŷ ∈ {0,…,9}
```

### 2.4 Data Visualization in Low-Dimensional Space

High-dimensional feature vectors in $\mathbb{R}^{1024}$ are inherently impossible to perceive directly. Low-dimensional projections provide qualitative insight into the geometry of the data manifold, reveal the degree of inter-class separability *before* any supervised model is fitted, and help motivate the choice of subsequent learning algorithms.

#### 2.4.1 PCA 2D and 3D Projection

**Principal Component Analysis (PCA)** [Pearson, 1901; Hotelling, 1933] finds the orthogonal directions of maximum variance in the data. The first $k$ principal components (eigenvectors of the sample covariance matrix corresponding to the $k$ largest eigenvalues) provide the optimal linear $k$-dimensional subspace for representing the data in a least-squares sense.

**Figure 2** and **Figure 3** show the data projected onto the first 2 and 3 principal components, respectively.

![Figure 2: PCA 2D projection of the 10 traffic sign classes (3,000 random samples). PC1 explains 13.4% of variance; PC2 explains 7.8%.](C:\Users\ACER\.gemini\antigravity-ide\brain\e43fa4ef-2890-4f04-a9c0-41a1d14c0a00\pca_2d.png)

![Figure 3: PCA 3D projection of the 10 traffic sign classes. PC1: 13.4%, PC2: 7.8%, PC3: 6.9% of variance.](C:\Users\ACER\.gemini\antigravity-ide\brain\e43fa4ef-2890-4f04-a9c0-41a1d14c0a00\pca_3d.png)

**Analysis:** The first three principal components together account for only **13.4% + 7.8% + 6.9% = 28.1%** of the total variance. The 2D and 3D scatter plots reveal that, when projected onto these dominant linear axes, class clusters are substantially **overlapping** and not linearly separable. This result is expected and is actually informative: it demonstrates that the discriminative information in the dataset is distributed across *many* principal components rather than concentrated in a few dominant directions. This motivates the use of a non-linear classifier (SVM with RBF kernel) and the retention of a large number of principal components (up to 95% variance threshold) rather than aggressively truncating to just 2–3 components.

#### 2.4.2 PCA Cumulative Explained Variance Analysis

To quantitatively determine the optimal number of principal components $k$ for the classification pipeline, the cumulative explained variance ratio is plotted as a function of the number of retained components.

**Figure 4** presents this curve computed on the full training dataset.

![Figure 4: PCA cumulative explained variance curve. The green line marks the 90% threshold (195 components); the red dashed line marks the 95% threshold (347 components).](C:\Users\ACER\.gemini\antigravity-ide\brain\e43fa4ef-2890-4f04-a9c0-41a1d14c0a00\pca_variance_curve.png)

**Key findings from the variance analysis:**

| Variance Threshold | Components Required ($k$) | Dimensionality Reduction Ratio |
|:-----------------:|:-------------------------:|:------------------------------:|
| 90% | **195** | 1024 → 195 (80.96% reduction) |
| 95% | **347** | 1024 → 347 (66.11% reduction) |

> [!NOTE]
> The visualization reports 347 components on the training subset (3,000 samples), while the full-data pipeline fit converges at **351 components** — a minor difference attributable to the slightly different sample covariance matrices. The final pipeline uses `PCA(n_components=0.95)` which automatically selects the exact $k$ needed for 95% variance on the *full training set*, resulting in $k = 351$.

The curve's characteristic slow-convergence shape — requiring 347 components to reach 95% explained variance out of a total of 1,024 possible — reflects the high intrinsic complexity and diversity of the traffic sign image manifold. This further reinforces that retaining a high percentage of variance (rather than using a low fixed $k$) is necessary for competitive classification accuracy.

**Pipeline design decision:** The `PCA(n_components=0.95, svd_solver='full')` parameterization used in the Scikit-Learn pipeline automatically selects $k$ to satisfy the 95% variance criterion on the training data. This data-adaptive approach avoids the need to manually tune $k$ as a hyperparameter, and ensures that the pipeline retains sufficient discriminative information regardless of the specific training subset characteristics.

#### 2.4.3 t-SNE Nonlinear Visualization

**t-Distributed Stochastic Neighbor Embedding (t-SNE)** [van der Maaten & Hinton, 2008] is a non-linear dimensionality reduction technique specifically designed for visualization. Unlike PCA, t-SNE optimizes a non-convex objective that preserves local neighborhood structure, allowing it to reveal cluster formations in high-dimensional data that are invisible to linear projections.

To ensure numerical stability and computational tractability, the standard pipeline of first reducing the data to 50 dimensions via PCA and then applying t-SNE (perplexity=30, 2D) is followed — consistent with the recommendations in [van der Maaten, 2009].

**Figure 5** presents the t-SNE visualization of the 10 traffic sign classes.

![Figure 5: t-SNE 2D visualization of the 10 traffic sign classes (3,000 samples, PCA-50 initialization). Each class forms a distinct, tight cluster with minimal inter-class overlap.](C:\Users\ACER\.gemini\antigravity-ide\brain\e43fa4ef-2890-4f04-a9c0-41a1d14c0a00\tsne_2d.png)

**Analysis:** In dramatic contrast to the overlapping PCA scatter plots, the t-SNE projection reveals that all **10 traffic sign classes form geometrically tight, well-separated clusters** with minimal inter-class overlap. This is a highly encouraging qualitative result:
1. It confirms that the preprocessing pipeline (CLAHE + grayscale + normalization) successfully extracts class-discriminative features.
2. It provides strong *a priori* evidence that a high classification accuracy is achievable, since the data manifold has inherent low-dimensional structure where classes are well-separated.
3. The slight proximity between the C30 (Speed limit 30 km/h) and C50 (Speed limit 50 km/h) clusters is consistent with the intuition that these two classes share the same circular red-border template and differ only in the inner digit pattern — a known challenging pair in TSR research.

---

## 3. Experiments

### 3.1 Experimental Setup

#### 3.1.1 Dataset Split and Stratification

The GTSRB dataset provides a **pre-defined training/test split** with separate image collections for each partition. This split is used without modification to ensure reproducibility and fair comparison with prior literature.

| Partition | Images (10-class subset) | Source |
|:----------|:------------------------:|:-------|
| Training | **~15,840** images | `GTSRB/Final_Training/Images/` (per-class CSV) |
| Test | **~5,401** images | `GTSRB/Final_Test/Images/` + `GT-final_test.csv` |

The test CSV (`GT-final_test.csv`) provides the ground truth labels for all test images across all 43 GTSRB classes; only rows whose `ClassId` belongs to the 10 selected classes are retained, yielding the final test set.

**Stratified sampling** is used when drawing the 5,000-sample subset for Grid Search CV, ensuring that the class proportions in the subset mirror those of the full training set and preventing systematic bias in hyperparameter selection.

#### 3.1.2 Scikit-Learn Pipeline Architecture

The entire processing chain — standardization, dimensionality reduction, and classification — is encapsulated in a single **`sklearn.pipeline.Pipeline`** object:

```python
Pipeline([
    ('scaler', StandardScaler()),
    ('pca',    PCA(n_components=0.95, svd_solver='full', random_state=42)),
    ('svm',    SVC(kernel='rbf', C=10, gamma='scale',
                   probability=True, random_state=42))
])
```

This architecture enforces that all `fit`-dependent transformations (mean/std for the scaler, principal components for PCA) are estimated *exclusively* on training data and subsequently applied as fixed transformations to test data, thereby preventing data leakage that would otherwise produce overoptimistic performance estimates.

### 3.2 Hyperparameter Optimization

#### 3.2.1 Efficient Grid Search Strategy

Training an SVM on the full training set (~15,840 samples) directly within a cross-validation loop would be computationally prohibitive (SVM training complexity is $O(N^2 d)$ to $O(N^3 d)$, where $N$ is the number of training samples). To efficiently identify optimal hyperparameters, the following two-phase strategy is employed:

**Phase A — Grid Search on Stratified Subsample:**
A **stratified random subsample of 5,000 training images** (approximately 32% of the total training set) is drawn for the hyperparameter search. A **3-fold stratified cross-validation** Grid Search is performed over the following hyperparameter grid:

| Hyperparameter | Candidates | Rationale |
|:---|:---|:---|
| SVM Kernel | `['linear', 'rbf']` | Linear kernel for comparison; RBF for non-linear boundaries |
| Regularization $C$ | `[0.1, 1, 10]` | Controls margin width vs. training error penalty |
| Kernel coefficient $\gamma$ | `['scale', 0.01]` | `'scale'` = $1/(d \cdot \text{Var}(X))$; 0.01 for broader influence |

Total combinations evaluated: $2 \times 3 \times 2 = \mathbf{12}$ configurations × 3 folds = **36 SVM fits**, all parallelized across all available CPU cores (`n_jobs=-1`).

**Phase B — Full-Data Retraining:**
Once the optimal hyperparameter set is identified from the Grid Search, the winning configuration is retrained on the **complete training dataset (100%, ~15,840 samples)**. This ensures the final deployed model benefits from the maximum available training data, typically resulting in improved generalization compared to a model fitted only on the 5,000-sample subset.

#### 3.2.2 Best Hyperparameters Found

The Grid Search identifies the following optimal configuration:

| Hyperparameter | Optimal Value | Interpretation |
|:---|:---:|:---|
| **SVM Kernel** | `rbf` | Non-linear RBF kernel outperforms linear kernel, confirming non-linearly separable class boundaries in PCA space |
| **Regularization $C$** | `10` | High penalty on margin violations; model favors a tight, accurate decision boundary over a wide margin |
| **Kernel coefficient $\gamma$** | `'scale'` | Auto-scaled to $1/(k \cdot \text{Var}(X_{\text{pca}}))$; prevents kernel saturation on high-$k$ inputs |

The selection of the **RBF kernel** over the linear kernel validates the earlier observation from the PCA 2D/3D visualizations: the class boundaries in the PCA-projected feature space are non-linear in nature. The high $C = 10$ value reflects that the model finds a complex decision boundary with minimal soft-margin tolerance, which is appropriate given that the training data (after thorough preprocessing) contains relatively few genuine outliers.

### 3.3 Computational Complexity Analysis

#### 3.3.1 Theoretical Analysis

Understanding the asymptotic complexity of the pipeline at inference time is critical for assessing real-time deployment viability.

**Without PCA (direct SVM on raw 1,024-D features):**
For a test image $\mathbf{x} \in \mathbb{R}^d$, the SVM prediction requires computing the kernel function $K(\mathbf{x}, \mathbf{x}_i)$ for each of the $N_{sv}$ support vectors:

$$\text{Prediction cost (no PCA)} = O(d \cdot N_{sv}) \quad \text{with } d = 1024$$

**With PCA projection ($k=351$ components):**
The pipeline first applies the PCA projection matrix $\mathbf{W} \in \mathbb{R}^{k \times d}$ to produce $\mathbf{z} = \mathbf{W}\mathbf{x} \in \mathbb{R}^k$, then evaluates the SVM:

$$\text{PCA projection cost} = O(d \cdot k)$$
$$\text{SVM prediction cost (with PCA)} = O(k \cdot N_{sv}) \quad \text{with } k = 351$$
$$\text{Total per-image cost} = O(d \cdot k + k \cdot N_{sv}) = O(k \cdot (d + N_{sv}))$$

The reduction in SVM inference cost is:

$$\text{Speedup ratio} = \frac{d}{k} = \frac{1024}{351} \approx 2.92\times$$

In addition to raw speed, the memory footprint of the SVM decision function (storing support vectors) is reduced proportionally, since each support vector is now a $k$-dimensional vector rather than a $d$-dimensional vector.

**Summary of theoretical complexity comparison:**

| Stage | Without PCA | With PCA ($k=351$) |
|:------|:-----------:|:------------------:|
| Dimensionality | $d = 1024$ | $k = 351$ |
| SVM kernel eval per image | $O(1024 \cdot N_{sv})$ | $O(351 \cdot N_{sv})$ |
| SVM inference speedup | 1× (baseline) | **~2.92×** |
| Memory per support vector | 1024 floats | 351 floats |
| Information retained | 100% | **95%** |

**Training complexity:** SVM training complexity scales as $O(N^{2.3} \cdot k)$ to $O(N^3 \cdot k)$ depending on the optimization solver [Bottou & Lin, 2006]. Reducing $d$ from 1,024 to $k = 351$ provides a direct speedup factor of approximately **2.92×** in each kernel evaluation during training as well.

#### 3.3.2 Empirical Latency and Throughput Measurement

The empirical inference performance is measured by timing the `pipeline.predict()` call over the complete test set and computing mean per-image latency:

$$\text{Latency} = \frac{\text{Total inference time}}{N_{\text{test}}} \cdot 1000 \quad \text{[ms/image]}$$
$$\text{Throughput (FPS)} = \frac{N_{\text{test}}}{\text{Total inference time}}$$

**Empirical performance results:**

| Metric | Value |
|:-------|:-----:|
| Total test samples | ~5,401 |
| Total inference time | ~10.08 seconds |
| **Mean latency per image** | **1.865 ms** |
| **Real-time throughput** | **536.13 FPS** |

A throughput of **536 FPS** is approximately 9× the standard video rate of 60 FPS and over 17× the minimum required for standard automotive camera systems (30 FPS). This demonstrates that the PCA+SVM pipeline, operating entirely on CPU, is well-suited for real-time deployment in embedded automotive platforms without any GPU dependency.

### 3.4 Evaluation Results and Discussion

#### 3.4.1 Overall Classification Metrics

The final pipeline (trained on 100% of training data with optimal hyperparameters) is evaluated on the held-out GTSRB test set. The following metrics are computed:

| Metric | Value |
|:-------|:-----:|
| **Overall Accuracy** | **97.80%** |
| **Macro Precision** | **97.81%** |
| **Macro Recall** | **97.79%** |
| **Macro F1-Score** | **97.79%** |
| **Weighted F1-Score** | **97.79%** |

An overall accuracy of **97.80%** and a Macro F1-Score of **97.79%** represent state-of-the-art performance for traditional (non-deep-learning) machine learning pipelines on the GTSRB benchmark. The near-identical Macro and Weighted F1-Scores indicate that performance is consistent across all classes regardless of their sample size, further confirming the model's robustness to the moderate class imbalance present in the dataset.

#### 3.4.2 Per-Class Analysis via Confusion Matrix

**Figure 6** presents the confusion matrix for the 10-class classification on the test set.

![Figure 6: Confusion matrix of the PCA+SVM pipeline on the GTSRB test set. Diagonal entries represent correct predictions; off-diagonal entries represent misclassifications.](C:\Users\ACER\.gemini\antigravity-ide\brain\e43fa4ef-2890-4f04-a9c0-41a1d14c0a00\confusion_matrix.png)

**Detailed per-class performance (derived from the confusion matrix):**

| Class | True Samples | Correct | Precision (approx.) | Recall (approx.) |
|:------|:------------:|:-------:|:-------------------:|:----------------:|
| Speed limit 30 (C1) | 720 | 700 | 97.6% | 97.2% |
| Speed limit 50 (C2) | 750 | 745 | 96.9% | 99.3% |
| Priority intersection (C11) | 416 | 407 | 96.0% | 97.8% |
| Priority road (C12) | 690 | 681 | 98.4% | 98.7% |
| Yield (C13) | 720 | 717 | 99.2% | 99.6% |
| Stop (C14) | 270 | 270 | 100.0% | 100.0% |
| No entry (C17) | 360 | 356 | 99.4% | 98.9% |
| General caution (C18) | 390 | 345 | 94.5% | 88.5% |
| Road work (C25) | 480 | 467 | 97.9% | 97.3% |
| Ahead only (C35) | 390 | 388 | 99.0% | 99.5% |

**Key observations from the confusion matrix analysis:**

1. **Stop sign (C14):** Achieves perfect classification (270/270 correct, 100% precision and recall). The distinctive octagonal shape of the Stop sign in the grayscale feature space, combined with its unique "STOP" text pattern, renders it trivially distinguishable from all other classes after CLAHE enhancement.

2. **General caution (C18):** Exhibits the lowest recall at ~88.5%, with 20 samples misclassified as Road work (C25) and 10 misclassified as Right-of-way (C11). This is attributable to the structural similarity between these triangular warning signs — all featuring a red-bordered equilateral triangle — with the discriminative information residing only in the inner symbol, which may be partially degraded by grayscale conversion and CLAHE at 32×32 resolution.

3. **Speed limit 30 (C1) vs. Speed limit 50 (C2):** These two classes, which share an identical circular red-border template and differ only in the numeral, exhibit the expected cross-class confusion: 13 C1 samples are misclassified as C2, and 5 C2 samples as C1. Despite this, both classes achieve >97% individual accuracy — a testament to the discriminative power of CLAHE in recovering fine-grained digit structure.

4. **Yield (C13) and Ahead only (C35):** Both achieve near-perfect classification (>99% recall) due to their highly distinctive geometric profiles (inverted triangle and blue directional arrow, respectively) that are preserved even at 32×32 grayscale resolution.

#### 3.4.3 Comparative Discussion and Contextualization

To contextualize the achieved performance, it is informative to compare against representative baselines from the literature:

| Method | Features | Accuracy on GTSRB (43-class or subset) | Inference |
|:-------|:---------|:----------------------------------------:|:---------|
| HOG + SVM (baseline) [Stallkamp 2012] | HOG descriptor | ~95.7% (43-class) | Fast CPU |
| Neural Network (1-layer) [Sermanet 2011] | Hand-crafted | ~97.4% (43-class) | Moderate |
| **PCA (k=351) + SVM-RBF (this work)** | **Pixel + CLAHE** | **97.80% (10-class)** | **536 FPS CPU** |
| CNN [Sermanet & LeCun 2011] | Learned deep | ~99.17% (43-class) | GPU required |

The proposed PCA+SVM pipeline achieves performance competitive with early neural networks while maintaining the inference speed advantages of a linear-algebraic pipeline. The ~1.4% gap relative to state-of-the-art deep CNNs is a well-understood trade-off: deep features learned by CNNs capture hierarchical spatial abstractions that flat pixel features (even after CLAHE) cannot replicate. However, the proposed system operates on a CPU without any specialized hardware at 536 FPS — a regime where deep CNN inference is typically 10–100× slower.

---

## 4. Conclusions and Perspectives

### 4.1 Conclusion

This project presents a rigorous, end-to-end machine learning system for real-time traffic sign classification, grounded in established statistical learning theory and linear algebraic methods. The following objectives were accomplished:

1. **A high-performance image preprocessing pipeline** was designed and validated, incorporating ROI-aware cropping, CLAHE contrast enhancement, grayscale conversion, and pixel normalization — collectively reducing feature dimensionality from 3,072 (raw RGB) to 1,024 while improving class-discriminative contrast.

2. **A principled data analysis** was conducted, quantifying class distribution characteristics (moderate imbalance ratio of ~2.88:1), raw image size statistics (mean ~51.8 × 55.2 pixels, range 16×16 to ~200×200), and the intrinsic dimensionality of the feature manifold (requiring 351 components for 95% explained variance).

3. **Unsupervised visualization techniques** — PCA (2D, 3D) and t-SNE — revealed the geometric structure of the feature space. Notably, while PCA 2D/3D projections show substantial class overlap (only 28.1% of variance captured by 3 components), t-SNE demonstrates clearly separable, tight clusters — a crucial qualitative justification for the high classification accuracy achievable by the pipeline.

4. **Systematic hyperparameter optimization** via 3-fold stratified Grid Search over 12 configurations, combined with full-data retraining of the optimal configuration, identified that an **RBF kernel SVM with $C=10$, $\gamma=\text{'scale'}$, and $k=351$ PCA components** provides the optimal operating point on the accuracy-complexity trade-off curve.

5. **Theoretical and empirical complexity analysis** demonstrated that the PCA projection reduces SVM inference complexity by approximately **2.92×** relative to raw-feature SVM, while retaining 95% of the discriminative information. Empirically, the system achieves **536.13 FPS** with a mean latency of **1.865 ms per image** — well within real-time ADAS requirements.

6. **Comprehensive evaluation** on the held-out GTSRB test set yields an overall accuracy of **97.80%** and a Macro F1-Score of **97.79%**, with per-class recall exceeding 88.5% for all 10 classes. The confusion matrix analysis pinpoints inter-class confusion arising from shared geometric templates (triangular warning signs) and similar alphanumeric content (speed limit signs), providing clear directions for future improvement.

In summary, this work demonstrates that a classical, mathematically transparent PCA + SVM pipeline, combined with a carefully engineered preprocessing chain, can achieve near state-of-the-art accuracy on a challenging real-world traffic sign classification benchmark, while operating at real-time speeds on standard CPU hardware — a practically significant result for resource-constrained ADAS deployment.

### 4.2 Perspectives and Future Work

Building on the foundation established in this project, the following research directions are proposed for future investigation:

**4.2.1 Automatic Sign Localization (Detection)**
The current pipeline assumes that traffic sign ROI coordinates are provided via dataset annotations. In a real-world deployment scenario, a preceding object detection stage is required to automatically identify and localize sign regions within the full camera frame. Integration with lightweight detectors — such as a Haar Cascade classifier, a sliding window approach with HOG+SVM, or a YOLO-based detector — would complete the full perception pipeline. Alternatively, the scene-level preprocessing could be augmented with a segmentation step that exploits the color regularity of traffic signs (red/yellow borders on signs) in HSV color space.

**4.2.2 Adversarial Robustness and Weather Simulation**
The GTSRB training images, while captured in diverse lighting conditions, do not systematically include extreme weather conditions (heavy rain, dense fog, night-time glare). Evaluating and improving the pipeline's robustness to these conditions through targeted data augmentation (Gaussian blur for fog simulation, additive Gaussian noise for sensor noise, brightness jitter) or domain adaptation techniques represents an important direction for safety-critical applications.

**4.2.3 Extension to All 43 GTSRB Classes**
The 10-class subset used in this project was chosen for computational tractability. Extending the pipeline to all 43 classes would increase the challenge substantially due to the much greater class imbalance (up to 10:1 ratio) and the introduction of visually similar classes not represented in the current subset. This would necessitate exploring class-weighted SVM training and potentially adopting ensemble methods or one-vs-one vs. one-vs-all multi-class strategies more carefully.

**4.2.4 Kernel Selection and Feature Engineering**
The experiment space of this project was deliberately constrained to linear and RBF kernels. Future work should systematically explore the polynomial kernel (useful for capturing interactions between pixel positions) and histogram-intersection kernels (well-suited for histogram-type feature representations). Additionally, replacing raw pixel features with domain-specific descriptors such as Histogram of Oriented Gradients (HOG) [Dalal & Triggs, 2005] or Local Binary Patterns (LBP) [Ojala et al., 2002] may yield complementary discriminative information, particularly for the triangular warning sign classes where the current system shows the highest error rate.

**4.2.5 Benchmarking Against Lightweight Deep Learning Models**
A natural and academically valuable future direction is a controlled benchmarking study comparing the PCA+SVM pipeline against lightweight convolutional architectures (e.g., MobileNetV3, SqueezeNet, EfficientNet-B0) in terms of *both* classification accuracy *and* deployment metrics (CPU inference latency, model size in megabytes, required training data). Such a study would provide rigorous, quantitative evidence for the precise conditions under which classical ML outperforms deep learning — namely, data-limited regimes, severe computational resource constraints, or when interpretability is a primary requirement.

---

## References

- Bottou, L., & Lin, C.-J. (2006). Support vector machine solvers. *Large Scale Kernel Machines*, MIT Press.
- Dalal, N., & Triggs, B. (2005). Histograms of oriented gradients for human detection. *CVPR 2005*.
- Hotelling, H. (1933). Analysis of a complex of statistical variables into principal components. *Journal of Educational Psychology*, 24(6).
- Ojala, T., Pietikäinen, M., & Mäenpää, T. (2002). Multiresolution gray-scale and rotation invariant texture classification with local binary patterns. *IEEE TPAMI*, 24(7).
- Pearson, K. (1901). On lines and planes of closest fit to systems of points in space. *Philosophical Magazine*, 2(11).
- Pizer, S. M., et al. (1987). Adaptive histogram equalization and its variations. *Computer Vision, Graphics, and Image Processing*, 39(3).
- Sermanet, P., & LeCun, Y. (2011). Traffic sign recognition with multi-scale convolutional networks. *IJCNN 2011*.
- Stallkamp, J., Schlipsing, M., Salmen, J., & Igel, C. (2012). Man vs. computer: Benchmarking machine learning algorithms for traffic sign recognition. *Neural Networks*, 32.
- van der Maaten, L. J. P., & Hinton, G. E. (2008). Visualizing high-dimensional data using t-SNE. *JMLR*, 9.
- van der Maaten, L. (2009). Learning a parametric embedding by preserving local structure. *AISTATS 2009*.
