# 📄 Publication Summary: NeurIPS LXAI 2025

**Title:** Exploration of Incremental Synthetic Non-Morphed Images for Single Morphing Attack Detection  
**Venue:** Latinx in AI (LXAI) Workshop @ NeurIPS 2025  
**Authors:** David Benavente-Rios, **Juan Ruiz Rodriguez**, Gustavo Gatica  

---

### 📝 Abstract
This research investigates the use of synthetic face data to enhance Single-Morphing Attack Detection (S-MAD), addressing the lack of large-scale bona fide datasets due to privacy concerns. We implemented an incremental testing protocol to assess generalization as synthetic images were added. Our results demonstrate that while incorporating controlled amounts of synthetic data can improve model performance, indiscriminate use leads to suboptimal results. The study establishes strong baselines using efficient architectures (EfficientNet, MobileNet) suitable for real-time biometric verification.

### 🛠️ Key Contributions
- **Methodology:** Evaluated the impact of integrating GAN-generated "non-morphed" images into training pipelines for biometric security.
- **Architectural Analysis:** Demonstrated that compact architectures (EfficientNet-B2, MobileNetV3-large) achieve high accuracy (~6% EER) in cross-dataset evaluations.
- **Data Engineering:** Developed a protocol for mixed training using digital and synthetic images to overcome privacy-driven data scarcity.

### 🎓 Relevance to PhD Research
This work showcases depth in **Computer Vision**, **Anomaly Detection**, and **Deep Learning**, specifically in high-stakes environments where model efficiency and data privacy are critical.
