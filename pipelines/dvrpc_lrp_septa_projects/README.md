# DVRPC long-range plan: SEPTA projects

Reads the Pennsylvania transit projects (SEPTA) and their costs out of DVRPC's long-range plan appendix, and applies the cost revisions in its Amendment 1.

- **Run:** `python build.py ../../datasets/septa-region/dvrpc-lrp-septa-projects/dvrpc-lrp-septa-projects.csv [CACHE_DIR]`
- **Needs:** `pdftotext` from poppler (`brew install poppler` or `apt install poppler-utils`). No Python packages beyond the standard library.
- **Sources:** [Update: Connections 2050 Appendices](https://www.dvrpc.org/Reports/25140.pdf) (Table F-25, PDF pp. 251–256; Table F-30, PDF pp. 271–277) and [Amendment 1](https://www.dvrpc.org/Reports/26140.pdf) (Table 5). Both PDFs are downloaded to `CACHE_DIR`, or a temporary folder, and not committed.
- **Check:** the script stops if the row counts (39 funded, 45 unfunded, 6 amended) change or a scope does not end in a period (PAT087 excepted, as printed), since that means DVRPC changed the PDF layout or published a new version.
