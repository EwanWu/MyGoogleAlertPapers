# Residual tail priority worklist (2026-05-07)

## Purpose

Turn the current residual tail into an explicit action queue after the regular fast-pass mainline was shown to be exhausted.

## Current residual baseline

- Source tail export after `tail57`: `data/exports/remaining_need_merge_after_tail57_20260507.json` (`48` candidates)
- Manual standard entries already inserted: `6` (`data/exports/manual_standard_entries_20260507.json`)
- Working current residual set: **42** candidates
- This worklist deliberately assumes **no more chunk08+ regular fast-pass**.

## Priority order

### P1 — already-downloaded thesis/dissertation-like PDFs (**13**)

These are the best next candidates **if** the library goal includes minimal thesis/dissertation records, because the PDFs are already local and the retrieval problem is solved. If the current policy is “download-only, no canonical thesis record”, then these can be marked externally completed and removed from the active merge queue by policy rather than by more provider work.

- `cand_5b392888405d7821` | 2026 | ualberta.scholaris.ca | PCA-based Future Image Frame Prediction Method for Real-Time MR-guided Radiotherapy — local PDF already saved
- `cand_8a91b7da0f8ba4ff` | n/a | dspace.umh.es | Diseño, implementación y entrenamiento de interfaces cerebro-máquina basadas en eventos de la marcha para control de exoesqueletos — local PDF already saved
- `cand_9708737171d69def` | 2026 | iris.unisr.it | Uncovering data-driven subtypes of depression based on neurobiological and environmental signatures: a machine learning approach — local PDF already saved
- `cand_ad4c3fe310d059c8` | 2026 | erepo.uef.fi | Koulutuksen ja työn luonteen yhteys kognitioon ja elintapainterventioon sitoutumiseen varhaisessa Alzheimerin taudissa — local PDF already saved
- `cand_edbeecbfb6c1b6e4` | 2025 | academicworks.cuny.edu | Characterization of the Intrinsic Neural Timescale Indices as a Reliable Fingerprint of Brain Dynamics — local PDF already saved
- `cand_f2de39cd8ff8d3a8` | 2025 | academicworks.cuny.edu | Advancing Electrical Stimulation: Full-Head MRI Segmentation for Abnormal Brain Anatomy with tDCS — local PDF already saved
- `cand_3b1bde59bb52ebaa` | n/a | medf.kg.ac.rs | РЕЗИЛИЈЕНТНОСТ И ПРОФЕСИОНАЛНО ИЗГАРАЊЕ КОД МЕДИЦИНСКИХ ТЕХНИЧАРА И СЕСТАРА КОЈЕ РАДЕ СА ОНКОЛОШКИМ ПАЦИЈЕНТИМА — local PDF already saved
- `cand_5aa65c129a742542` | 2026 | ucalgary.scholaris.ca | Mild Behavioural Impairment-Apathy as an Early Behavioural Marker of Alzheimer Disease — local PDF already saved
- `cand_65c00537f2bc31ef` | 2026 | gupea.ub.gu.se | Genetic factors and neurobiological markers in relation to ageing, with a specific focus on longevity and dementia — local PDF already saved
- `cand_304c6016ed3349f1` | n/a | openaccess.uoc.edu | Detecció d'àrees cerebrals alterades en TEA, mitjançant segmentació automatitzada i aprenentatge profund d'imatges MRI — local PDF already saved
- `cand_b41612a9334c885b` | n/a | bip.umlub.pl | Ocena wpływu deprywacji wzrokowej u pacjentów ze zwyrodnieniem barwnikowym siatkówki na zmiany strukturalne i funkcjonalne w drodze wzrokowej z użyciem … — local PDF already saved
- `cand_1bc0e7a69427a8f4` | 2026 | openaccess.city.ac.uk | Investigating Factors that Influence Face Perception — local PDF already saved
- `cand_212c4d15a79dcf70` | 2026 | opus4.kobv.de | Robust and Efficient Algorithms for Image Reconstruction with Applications to Magnetic Particle Imaging — local PDF already saved

**Recommended action:** batch-create a lightweight thesis/dissertation metadata path *or* formally declare these as out-of-band completed assets so they stop polluting the active residual queue.

### P2 — ResearchGate / repo-shadow ambiguous publication items (**6**)

These should only be worked case-by-case when an authoritative publisher / proceedings / DOI path can be found elsewhere. Do **not** spend mainline chunk compute on them.

- `cand_2d487272bab8a581` | n/a | www.researchgate.net | Informatics and Health — ResearchGate shadow; requires external confirmation
- `cand_2f6b4be6ab84d0ac` | 2026 | www.researchgate.net | BRAIN COMMUNICATIONS — ResearchGate shadow; requires external confirmation
- `cand_ff158b1e74de6ddb` | 2025 | www.researchgate.net | Chile entre velos: Filosofía de lo aparente y subyacente — ResearchGate shadow; requires external confirmation
- `cand_d0aac8d2cd76183e` | 2026 | www.researchgate.net | Active Breathing Part I: Modalities, Mathematical Model & Case Studies — ResearchGate shadow; requires external confirmation
- `cand_ed2c42753a6fd6a4` | 2026 | www.researchgate.net | BRAIN PLASTICITY DURING GESTATION AND POSTPARTUM PERIODS — ResearchGate shadow; requires external confirmation
- `cand_88f41d9c9a78d2ae` | n/a | www.researchgate.net | Graduate School of Sciences and Technology for Innovation Tokushima University — ResearchGate shadow; requires external confirmation

**Recommended action:** only rescue when an independent authoritative landing page exists; otherwise keep parked.

### P3 — explicit skip / archive buckets (**6**)

#### Books / book-chapter-like (**2**)

- `cand_41b0de1c248d5f2f` | 2026 | books.google.com | TECHNIQUES USING NANOPARTICLES MUTHUKUMARAN T1*, CHITRA VELLAPANDIAN2, SATHEESHKUMAR SELLAMUTHU³ — book/book-chapter-like; default skip
- `cand_a03d9863f6e54a31` | 2026 | books.google.com | The Implications of Neuroscience for What Works — book/book-chapter-like; default skip

#### Non-English out-of-scope under current policy (**4**)

- `cand_6a05865db3faf492` | 2026 | www.alba.ac.mz | IMPACTO ECONÓMICO E FINANCEIRO DO CICLONE FREDDY NO 2º MOMENTO — non-English / currently out of scope
- `cand_26f2330529d6065d` | 2025 | magres.apm.ac.cn | 抗逆转录病毒治疗相关的HIV 感染者脑功能动态改变 — non-English / currently out of scope
- `cand_8885d5e06333a6d5` | 2025 | elibrary.ru | ЛАТЕРАЛИЗАЦИЯ СИЛЫ КИСТИ КАК МАРКЕР КОГНИТИВНЫХ ФУНКЦИЙ У МУЖЧИН ПРАВШЕЙ С ХРОНИЧЕСКОЙ ИШЕМИЕЙ МОЗГА — non-English / currently out of scope
- `cand_0b74a043eb689872` | n/a | www.jsme.or.jp | 超高磁場7 テスラMRI 環境対応の全自動触覚機械刺激提示システムの開発 — non-English / currently out of scope

**Recommended action:** leave these out of the active build queue unless scope is explicitly widened.

### P4 — other nonstandard / low-confidence leftovers (**17**)

These are neither clean standard-entry wins nor already-rescued theses. They should stay parked unless a specific high-value rationale appears.

- `cand_96931996bddfec0f` | n/a | diposit.ub.edu | Smart Agricultural Technology — nonstandard / low-confidence
- `cand_91db400ad7a289f4` | 2026 | search.ebscohost.com | Digital first impressions: how personal branding on social platforms drives person-organization fit in Surabaya. — nonstandard / low-confidence
- `cand_70cbb35321d16b4b` | n/a | risingresearchers.com | The Role of Dopamine in Mania in Bipolar Disorder — nonstandard / low-confidence
- `cand_6edf5e9034e38097` | n/a | researchspace.auckland.ac.nz | and Frank Harry Bloomfield 1,* for the DIAMOND Study Group† 1 Liggins Institute, University of Auckland, 1142 Auckland, New Zealand; m. muelbert@ auckland. ac … — nonstandard / low-confidence
- `cand_f1953155dfc9d1a3` | n/a | jmcmpub.org | New Horizons in the Treatment and Management of Alzheimer's Disease: Managed Care Considerations on Role of New and Emerging Therapies — nonstandard / low-confidence
- `cand_5f2ca3562a275bb1` | 2026 | docta.ucm.es | Efectos del phubbing percibido y participación digital en el bienestar psicosocial de las personas mayores de las regiones de Ñuble y Bío-Bío, Chile — nonstandard / low-confidence
- `cand_5a7915c2ef9d0917` | n/a | www.diva-portal.org | Perspectives on income and health — nonstandard / low-confidence
- `cand_aa3aa5bb24f6ed1c` | 2026 | lajoe.org | ASSOCIATION BETWEEN KAPPA FREE LIGHT CHAINS, DISABILITY, AND MRI FINDINGS IN PREDICTING THE COURSE OF MULTIPLE SCLEROSIS — nonstandard / low-confidence
- `cand_38a739957e3e9daa` | n/a | www.math.unipd.it | Discovery of Latent Clinical Phenotypes Through Optimal Transport of Brain Dynamics — nonstandard / low-confidence
- `cand_8bc25f998a80d7f3` | 2025 | stax.strath.ac.uk | Depression-like behaviour in a mouse model of Alzheimer's disease: a reverse translational study. — nonstandard / low-confidence
- `cand_cc0222dc8c55cf6b` | 2026 | search.proquest.com | No Teacher Left Behind. Integrating Technology in Urban P-12 Classrooms Using the SAMR Model: A Qualitative Case Study of Urban Public Schools — nonstandard / low-confidence
- `cand_ad09e5bf2ddea2c7` | 2025 | minerva-access.unimelb.edu.au | Modelling neurobiological mechanisms of negative cognitions in binge eating — nonstandard / low-confidence
- `cand_ad67ee178f07ee23` | n/a | drdidwal.com | How to Reverse Brain Aging: The Science Behind Fitness, Brain Age, and Dementia Risk — nonstandard / low-confidence
- `cand_132d71553d6328d5` | n/a | www.jillcarnahan.com | Galectin-3: The Hidden Driver of Inflammation, Fibrosis, and Chronic Disease You are here — nonstandard / low-confidence
- `cand_a77c99b0e10b7adf` | 2025 | journal.bgcardio.org | Молекулни механизми на левокамерната систолна дисфункция: актуален преглед Molecular mechanisms of left ventricular systolic dysfunction: a current review — nonstandard / low-confidence
- `cand_263d188a54ad7cae` | n/a | pattern.eecs.tottori-u.ac.jp | Investigating temporal changes of impression formed by interviewers from the applicant's behavior — nonstandard / low-confidence
- `cand_f837e787dc0e1efa` | 2025 | docta.ucm.es | El valor intangible de la coproducción digital del sector público: El compromiso y la confianza ciudadana generada por Avisos Madrid — nonstandard / low-confidence

**Recommended action:** keep parked by default; only reopen one-by-one if topic value is high and a trustworthy metadata path is found.

## Operational reading

- If the goal is **reduce `need_merge` quickly**, the only high-ROI path left is to decide what to do with the **13 already-downloaded thesis/dissertation PDFs**.
- If the goal is **keep canonical library quality high**, then the correct move is *not* to brute-force the remaining 29 skipped candidates.
- If the goal is **maximize coverage regardless of cost**, then residual work becomes a manual curation project, not a pipeline project.

## Bottom line

1. `chunk08+` should not resume as regular automation.
2. The next real decision is policy on the **13 downloaded theses/dissertations**.
3. Everything else should remain case-by-case or explicitly parked.