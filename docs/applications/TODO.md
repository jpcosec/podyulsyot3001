# 📝 PhD Application TODO & Tracker

This document tracks all the necessary tasks and the status of your core application documents before you can start sending out emails to TU Berlin.

---

## 🏃 Action Items (Immediate Tasks)
- [ ] **Contact Referees for Recommendation Letters:** 
  - [ ] Email Prof. Miguel Alejandro Rodriguez (UPLA) asking if he would be willing to provide a letter of recommendation or act as a formal reference.
  - [ ] Email Juan Pablo Morales (Kwali) for a professional/technical reference.
- [x] **Collect/Organize Existing PDFs:**
  - [x] Locate and verify `Anabin Titelvalidierung.pdf` (Confirm it explicitly states equivalency to Master's / 300 ECTS).
  - [x] Locate and verify `Study certificate.pdf` (Transcripts + Diploma in English or German).
  - [x] Locate and verify `Language Certificate.pdf` (English C1/C2 or German).
- [x] **Prepare Publication Proofs:**
  - [x] Generate a 1-page PDF summarizing your accepted NeurIPS workshop paper (Title, Abstract, Link/DOI).
  - [x] Generate a 1-page PDF summarizing your ICITED paper.

## 📄 Document Creation & Editing
- [x] **Update Academic CV (LaTeX):**
  - [x] Move "Publications" section to the very top (after Education).
  - [x] Rewrite "Research Associate" experience at UPLA to include 3 detailed bullet points (ITS architecture, LAETEC-Vision-Module, Cartesian Playground).
  - [x] Add an explicit note under the Universidad de Chile Education section regarding the Anabin Validation / Master's equivalency.
  - [x] Compile the final `CV_Juan_Pablo_Ruiz.pdf`.
- [x] **Draft the Master Motivation Letter:**
  - [x] Finalize the "Degree Equivalency" paragraph to copy-paste into emails.
  - [x] Draft a strong base template using `/home/jp/phd/data/reference_data/agent_feedback/templates/application_master_template.md`.

## 🧠 Research Asset Reuse (Memoria Thesis: Distillation)
- [ ] **Position `jpcosec/Memoria` as a strategic research asset for 2026 applications:**
  - [ ] Write a concise project synopsis (6-10 lines) connecting 2019 thesis work to current LLM distillation relevance (teacher-student transfer, compression, efficiency).
  - [ ] Document the concrete methods used in the thesis so they are easy to reference in interviews and letters:
    - [ ] Logit distillation (`KD`, `KD_CE`, `CE`) and when each was used.
    - [ ] Feature distillation approaches (`hint`, `att_max`, `att_mean`, `PKT`, `NST`) and practical purpose.
    - [ ] Experimental setup breadth (CIFAR10/ImageNet/synthetic datasets) and what this says about research rigor.
  - [ ] Prepare one "bridge statement" (2-3 sentences) that links classic vision distillation to modern LLM distillation (same paradigm, different architectures/objectives).
- [ ] **Integrate Memoria evidence into CV and profile artifacts:**
  - [ ] Add one high-impact CV bullet under research/projects emphasizing distillation implementation + evaluation in PyTorch.
  - [ ] Add one supporting bullet focused on reproducibility/experiment management (scripts, losses, model variants, comparisons).
  - [ ] Update `docs/PROFILE.md` and `docs/PROFILE.json` with a dedicated "Distillation" competency entry tied to the thesis repository.
  - [ ] Ensure wording is role-adaptable (academic vs applied ML engineer framing).
- [ ] **Upgrade motivation-letter and email templates with distillation positioning:**
  - [ ] Create a reusable paragraph block in templates that frames distillation as long-term expertise (not trend-chasing).
  - [ ] Create a short variant (1-2 lines) for constrained application forms.
  - [ ] Create a technical variant for lab/research groups (method + expected contribution).
  - [ ] Create an industry variant for engineering teams (efficiency, deployment, cost/performance trade-offs).
- [ ] **Create a quick interview package for distillation discussions:**
  - [ ] Draft a 30-second verbal pitch.
  - [ ] Draft a 2-minute deep-dive answer (problem, method, result, modern relevance).
  - [ ] Prepare 3 likely follow-up Q&A pairs (e.g., "How does this map to LLMs?", "What would you improve now?", "What are distillation limitations?").
  - [ ] Add one "lessons learned" note on code quality/portability improvements since 2019 (to show growth).
- [ ] **Optional portfolio hardening (if time allows before applications):**
  - [ ] Refresh Memoria README with a modern overview and explicit legacy/archival note.
  - [ ] Add a minimal reproducibility path (single command + expected outputs) for at least one experiment.
  - [ ] Add a brief "Then vs Now" section explaining how the thesis approach can be adapted to LLM compression workflows.
  - [ ] Capture any refreshed benchmark/illustration in a simple markdown artifact that can be linked from applications.

## 🛠️ Application Assembly & Submission
- [x] **Setup PDF Merging Workflow:**
  - [x] Figure out a way to easily merge [Cover Letter + CV + Anabin + Transcripts + Language + Pubs] into a single PDF under 5 MB. *(Tip: ghostscript or a Python script can compress this easily later).*
- [ ] **Begin Applying (Iterate through `data/pipelined_data/tu_berlin/<job_id>/job.md`):**
  - [ ] Pick Job 1.
  - [ ] Tailor Cover Letter.
  - [ ] Merge PDF.
  - [ ] Send Email / Apply via portal.
  - [ ] Update Job Markdown file in Obsidian to `Status: Applied`.
