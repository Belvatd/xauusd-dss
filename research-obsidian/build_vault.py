import os
import shutil
import re

source_docs_dir = "../docs"
source_theory_dir = "../data-theory"
target_dir = "."

folders = {
    "01_Konsep_Dasar": [
        "00_base_knowledge.md",
        "01_arsitektur_dan_ide_riset.md",
        "10_glosarium_dan_identitas_data.md"
    ],
    "02_Data_Engineering": [
        "03_data_engineering_medallion.md",
        "09_implementasi_script_medallion.md",
        "14_kamus_data_gold.md",
        ("modul_1_raw_data_onboarding.md", source_theory_dir),
        ("modul_2_data_quality_assurance.md", source_theory_dir),
        ("modul_3_gold_aggregations.md", source_theory_dir),
        ("modul_4_pipeline_automation.md", source_theory_dir)
    ],
    "03_Metodologi_Riset_ML": [
        "04_fase_1_deskriptif.md",
        "05_fase_2_diagnostik.md",
        "06_fase_3_prediktif_dss.md",
        "11_algoritma_machine_learning.md",
        "13_alur_proses_training_ml.md",
        ("modul_5_genai_analytics.md", source_theory_dir)
    ],
    "04_Evaluasi_Hasil": [
        "12_alur_evaluasi_model_ml.md",
        "15_laporan_komprehensif_pemodelan_ml.md"
    ],
    "05_Dokumen_Formal": [
        "02_decision_log.md",
        "07_catatan_review_dan_perbaikan_desain.md",
        "08_draft_proposal_skripsi.md",
        "16_kajian_literatur_dan_relevansi_riset.md"
    ]
}

# Create folders
for folder in folders:
    os.makedirs(os.path.join(target_dir, folder), exist_ok=True)

def process_content(content, tags):
    # Add YAML frontmatter
    frontmatter = f"---\ntags: {tags}\n---\n\n"
    
    # Optional: convert markdown links to wikilinks if they point to local md files
    # [Link text](./00_base_knowledge.md) -> [[00_base_knowledge]]
    def link_replacer(match):
        text = match.group(1)
        link = match.group(2)
        if link.endswith('.md') and not link.startswith('http'):
            filename = os.path.basename(link).replace('.md', '')
            return f"[[{filename}|{text}]]"
        return match.group(0)
        
    content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link_replacer, content)
    return frontmatter + content

for folder, files in folders.items():
    for item in files:
        if isinstance(item, tuple):
            filename, src_dir = item
        else:
            filename, src_dir = item, source_docs_dir
            
        src_path = os.path.join(src_dir, filename)
        if os.path.exists(src_path):
            with open(src_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple tag generation based on folder
            tag = f"[{folder.split('_', 1)[1].lower().replace('_', '-')}]"
            
            processed = process_content(content, tag)
            
            target_path = os.path.join(target_dir, folder, filename)
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(processed)

# Create a master Dashboard MOC
dashboard_content = """---
tags: [dashboard, MOC]
---

# 📊 Dashboard Riset: Klasifikasi Liquidity Sweep XAUUSD

Selamat datang di *Knowledge Base* (Obsidian Vault) untuk riset:
**"Sistem Pendukung Keputusan Klasifikasi Liquidity Sweep dan Breakout pada Level Likuiditas PDH/PDL Instrumen XAUUSD Menggunakan Machine Learning"**.

Vault ini menstrukturkan seluruh dokumen ke dalam beberapa area inti (MOC - Map of Content).

## 🗺️ Peta Konten (Map of Content)

### 📘 1. Konsep Dasar & Arsitektur
Fondasi pengetahuan tentang trading XAUUSD, likuiditas, dan arsitektur awal riset.
- [[00_base_knowledge|Base Knowledge: Pasar & Likuiditas]]
- [[01_arsitektur_dan_ide_riset|Arsitektur dan Ide Riset]]
- [[10_glosarium_dan_identitas_data|Glosarium & Identitas Data]]

### ⚙️ 2. Data Engineering & Pipeline
Segala sesuatu tentang infrastruktur data, pipeline PySpark Databricks, dan Arsitektur Medallion.
- [[03_data_engineering_medallion|Arsitektur Medallion Utama]]
- [[09_implementasi_script_medallion|Implementasi Script Databricks]]
- [[14_kamus_data_gold|Kamus Data Gold (Data Dictionary)]]
- [[modul_1_raw_data_onboarding|Modul 1: Raw Data Onboarding]]
- [[modul_2_data_quality_assurance|Modul 2: Data Quality Assurance]]
- [[modul_3_gold_aggregations|Modul 3: Gold Aggregations]]
- [[modul_4_pipeline_automation|Modul 4: Pipeline Automation]]

### 🤖 3. Metodologi Riset & Machine Learning
Metodologi 3 fase dan pengenalan konsep ML yang digunakan dalam riset.
- [[04_fase_1_deskriptif|Fase 1: Analitik Deskriptif]]
- [[05_fase_2_diagnostik|Fase 2: Analitik Diagnostik]]
- [[06_fase_3_prediktif_dss|Fase 3: Analitik Prediktif & DSS]]
- [[11_algoritma_machine_learning|Konsep Algoritma Machine Learning]]
- [[13_alur_proses_training_ml|Alur Proses Training Model ML]]
- [[modul_5_genai_analytics|Modul 5: GenAI Analytics]]

### 📈 4. Evaluasi & Hasil
Hasil pengujian, evaluasi model, dan kalibrasi probabilitas.
- [[12_alur_evaluasi_model_ml|Alur Evaluasi Model ML]]
- [[15_laporan_komprehensif_pemodelan_ml|Laporan Komprehensif Rekayasa Fitur & Pemodelan]]

### 📑 5. Dokumen Formal & Log
Kumpulan catatan keputusan, log review, kajian literatur, dan naskah proposal.
- [[02_decision_log|Decision Log (Catatan Keputusan)]]
- [[07_catatan_review_dan_perbaikan_desain|Catatan Review & Perbaikan]]
- [[16_kajian_literatur_dan_relevansi_riset|Kajian Literatur Komprehensif]]
- [[08_draft_proposal_skripsi|Draft Proposal Skripsi Lengkap]]

---
*Gunakan fitur Graph View (Ctrl/Cmd + G) di Obsidian untuk melihat keterhubungan antar dokumen riset ini!*
"""

with open(os.path.join(target_dir, "00_Dashboard.md"), 'w', encoding='utf-8') as f:
    f.write(dashboard_content)

print("Obsidian vault structure created successfully!")
