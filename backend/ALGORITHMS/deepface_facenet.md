# DeepFace with Facenet512 (Facial Recognition)

DeepFace is a facial analysis framework that provides access to multiple pre-trained face recognition models. We use **Facenet512**, which generates a **512-dimensional numerical vector** (called an embedding) that mathematically represents the unique features of a face.

## How it works
1. The cropped face image is passed through the Facenet512 deep neural network.
2. The network outputs a 512-dimensional float vector. Faces of the same person produce vectors that are mathematically close to each other, while different people produce vectors that are far apart.
3. The embedding is **L2-normalized** (divided by its Euclidean norm) so that its magnitude becomes 1.0. This is a critical step because it converts the distance metric to **Cosine Similarity**, which measures the angle between two vectors rather than their magnitude — making comparisons scale-invariant and more robust.
