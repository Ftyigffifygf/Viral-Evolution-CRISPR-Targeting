
# 🧬 Viral Evolution CRISPR Targeting

**Predict escape-resistant CRISPR targets in highly mutable viruses.** This tool allows researchers to upload viral genome sequences and identify optimal CRISPR guide RNA targets that are less likely to be evaded by mutation over time.

---

## 🌟 Features

- 🧫 Upload custom viral sequences in FASTA format
- 🔍 Analyze and identify CRISPR targets with escape-resistance profiling
- 🧪 Mutation simulation module for stress-testing targets
- 📊 Results visualization and downloadable output
- 🎯 Includes example support for **HIV-1** and **SARS-CoV-2**

---

## 🚀 Usage Guide

### 🖥️ Web Interface

1. Click **"Upload & Analyze"** to load your viral sequence.
2. Choose a virus type (e.g., HIV-1, SARS-CoV-2).
3. Paste your FASTA sequence into the input box.
4. Click **"Analyze CRISPR Targets"** to start the prediction.

### 📂 Example

- Sample Sequences provided:
  - HIV-1
  - SARS-CoV-2

You can test the app by loading one of these and running the analysis workflow.

---

## 📸 UI Preview

![App UI Screenshot](demo_ui_screenshot.png)

---

## 🛠️ Technologies Used

- Python 3.8+
- BioPython
- Streamlit (for frontend)
- pandas, numpy (data handling)
- Custom CRISPR target scoring logic

---

## 📌 Future Enhancements

- Add off-target prediction module using 3D genomic context
- Deploy backend to handle large-scale batch processing
- Export results in GenBank/GFF format

---

## 📜 License

MIT License

---

## 👨‍🔬 Authors

Developed for virology researchers and computational genome engineers.
with collabration of Girish G Shankar 

