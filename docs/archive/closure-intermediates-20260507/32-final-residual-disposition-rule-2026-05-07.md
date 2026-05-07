# Final residual disposition rule (2026-05-07)

## Decision

This document formalizes the final handling rule for the current residual tail after the regular library-build mainline was exhausted.

### Rule A — downloaded but not ingested

For the **13 thesis/dissertation-like PDFs already downloaded locally**, the official policy is:

- **keep the PDF files** under `~/NewCareer/Openclaw/resource/papers/google_scholar_pdf/`;
- treat them as **external archived assets**;
- **do not** create canonical paper records for them in the current library-build cycle;
- **do not** keep them in the active residual merge/build queue.

### Rule B — discard other active leftovers

For the remaining **29** unresolved leftovers, the official policy is:

- remove them from the **active processing queue**;
- do **not** continue regular chunk passes, title-lane rescue, or case-by-case salvage on this batch;
- keep historical exports and notes for auditability, but treat these items as **closed / intentionally abandoned** under the current scope.

## Important interpretation

Here, “discard / 扔掉” means **workflow discard**, not filesystem deletion:

- existing exported JSON/MD artifacts are retained;
- existing downloaded PDFs are retained;
- the items simply stop consuming further library-build effort.

## Counts

- `archive_downloaded_not_ingested`: 13
- `discard_from_active_queue`: 29

## Archive set (13)

- `cand_5b392888405d7821` | 2026 | ualberta.scholaris.ca | PCA-based Future Image Frame Prediction Method for Real-Time MR-guided Radiotherapy -> `/home/ewan/NewCareer/Openclaw/resource/papers/google_scholar_pdf/PCA-based Future Image Frame Prediction Method for Real-Time MR-guided Radiotherapy (2026).pdf`
- `cand_8a91b7da0f8ba4ff` | n/a | dspace.umh.es | Diseño, implementación y entrenamiento de interfaces cerebro-máquina basadas en eventos de la marcha para control de exoesqueletos -> `/home/ewan/NewCareer/Openclaw/resource/papers/google_scholar_pdf/Diseño, implementación y entrenamiento de interfaces cerebro-máquina basadas en eventos de la marcha para control de exoesqueletos.pdf`
- `cand_9708737171d69def` | 2026 | iris.unisr.it | Uncovering data-driven subtypes of depression based on neurobiological and environmental signatures: a machine learning approach -> `/home/ewan/NewCareer/Openclaw/resource/papers/google_scholar_pdf/Uncovering data-driven subtypes of depression based on neurobiological and environmental signatures_ a machine learning approach (2026).pdf`
- `cand_ad4c3fe310d059c8` | 2026 | erepo.uef.fi | Koulutuksen ja työn luonteen yhteys kognitioon ja elintapainterventioon sitoutumiseen varhaisessa Alzheimerin taudissa -> `/home/ewan/NewCareer/Openclaw/resource/papers/google_scholar_pdf/Koulutuksen ja työn luonteen yhteys kognitioon ja elintapainterventioon sitoutumiseen varhaisessa Alzheimerin taudissa (2026).pdf`
- `cand_edbeecbfb6c1b6e4` | 2025 | academicworks.cuny.edu | Characterization of the Intrinsic Neural Timescale Indices as a Reliable Fingerprint of Brain Dynamics -> `/home/ewan/NewCareer/Openclaw/resource/papers/google_scholar_pdf/Characterization of the Intrinsic Neural Timescale Indices as a Reliable Fingerprint of Brain Dynamics.pdf`
- `cand_f2de39cd8ff8d3a8` | 2025 | academicworks.cuny.edu | Advancing Electrical Stimulation: Full-Head MRI Segmentation for Abnormal Brain Anatomy with tDCS -> `/home/ewan/NewCareer/Openclaw/resource/papers/google_scholar_pdf/Advancing Electrical Stimulation_ Full-Head MRI Segmentation for Abnormal Brain Anatomy with tDCS (2025).pdf`
- `cand_3b1bde59bb52ebaa` | n/a | medf.kg.ac.rs | РЕЗИЛИЈЕНТНОСТ И ПРОФЕСИОНАЛНО ИЗГАРАЊЕ КОД МЕДИЦИНСКИХ ТЕХНИЧАРА И СЕСТАРА КОЈЕ РАДЕ СА ОНКОЛОШКИМ ПАЦИЈЕНТИМА -> `/home/ewan/NewCareer/Openclaw/resource/papers/google_scholar_pdf/РЕЗИЛИЈЕНТНОСТ И ПРОФЕСИОНАЛНО ИЗГАРАЊЕ КОД МЕДИЦИНСКИХ ТЕХНИЧАРА И СЕСТАРА КОЈЕ РАДЕ СА ОНКОЛОШКИМ ПАЦИЈЕНТИМА.pdf`
- `cand_5aa65c129a742542` | 2026 | ucalgary.scholaris.ca | Mild Behavioural Impairment-Apathy as an Early Behavioural Marker of Alzheimer Disease -> `/home/ewan/NewCareer/Openclaw/resource/papers/google_scholar_pdf/Mild Behavioural Impairment-Apathy as an Early Behavioural Marker of Alzheimer Disease (2026).pdf`
- `cand_65c00537f2bc31ef` | 2026 | gupea.ub.gu.se | Genetic factors and neurobiological markers in relation to ageing, with a specific focus on longevity and dementia -> `/home/ewan/NewCareer/Openclaw/resource/papers/google_scholar_pdf/Genetic factors and neurobiological markers in relation to ageing, with a specific focus on longevity and dementia.pdf`
- `cand_304c6016ed3349f1` | n/a | openaccess.uoc.edu | Detecció d'àrees cerebrals alterades en TEA, mitjançant segmentació automatitzada i aprenentatge profund d'imatges MRI -> `/home/ewan/NewCareer/Openclaw/resource/papers/google_scholar_pdf/Detecció d'àrees cerebrals alterades en TEA, mitjançant segmentació automatitzada i aprenentatge profund d'imatges MRI.pdf`
- `cand_b41612a9334c885b` | n/a | bip.umlub.pl | Ocena wpływu deprywacji wzrokowej u pacjentów ze zwyrodnieniem barwnikowym siatkówki na zmiany strukturalne i funkcjonalne w drodze wzrokowej z użyciem … -> `/home/ewan/NewCareer/Openclaw/resource/papers/google_scholar_pdf/Ocena wpływu deprywacji wzrokowej u pacjentów ze zwyrodnieniem barwnikowym siatkówki na zmiany strukturalne i funkcjonalne w drodze wzrokowej z użyciem. .pdf`
- `cand_1bc0e7a69427a8f4` | 2026 | openaccess.city.ac.uk | Investigating Factors that Influence Face Perception -> `/home/ewan/NewCareer/Openclaw/resource/papers/google_scholar_pdf/Investigating Factors that Influence Face Perception (2026).pdf`
- `cand_212c4d15a79dcf70` | 2026 | opus4.kobv.de | Robust and Efficient Algorithms for Image Reconstruction with Applications to Magnetic Particle Imaging -> `/home/ewan/NewCareer/Openclaw/resource/papers/google_scholar_pdf/Robust and Efficient Algorithms for Image Reconstruction with Applications to Magnetic Particle Imaging (2026).pdf`

## Discarded active leftovers (29)

- `cand_96931996bddfec0f` | n/a | diposit.ub.edu | Smart Agricultural Technology — nonstandard_or_low_confidence_leftover; not worth further active processing
- `cand_91db400ad7a289f4` | 2026 | search.ebscohost.com | Digital first impressions: how personal branding on social platforms drives person-organization fit in Surabaya. — nonstandard_or_low_confidence_leftover; not worth further active processing
- `cand_41b0de1c248d5f2f` | 2026 | books.google.com | TECHNIQUES USING NANOPARTICLES MUTHUKUMARAN T1*, CHITRA VELLAPANDIAN2, SATHEESHKUMAR SELLAMUTHU³ — book_or_book_chapter_like; out of active library-build scope
- `cand_2d487272bab8a581` | n/a | www.researchgate.net | Informatics and Health — researchgate_shadow_or_repo_copy_without_authoritative_metadata_path
- `cand_70cbb35321d16b4b` | n/a | risingresearchers.com | The Role of Dopamine in Mania in Bipolar Disorder — nonstandard_or_low_confidence_leftover; not worth further active processing
- `cand_6edf5e9034e38097` | n/a | researchspace.auckland.ac.nz | and Frank Harry Bloomfield 1,* for the DIAMOND Study Group† 1 Liggins Institute, University of Auckland, 1142 Auckland, New Zealand; m. muelbert@ auckland. ac … — nonstandard_or_low_confidence_leftover; not worth further active processing
- `cand_f1953155dfc9d1a3` | n/a | jmcmpub.org | New Horizons in the Treatment and Management of Alzheimer's Disease: Managed Care Considerations on Role of New and Emerging Therapies — nonstandard_or_low_confidence_leftover; not worth further active processing
- `cand_6a05865db3faf492` | 2026 | www.alba.ac.mz | IMPACTO ECONÓMICO E FINANCEIRO DO CICLONE FREDDY NO 2º MOMENTO — non_english_out_of_scope_under_current_policy
- `cand_2f6b4be6ab84d0ac` | 2026 | www.researchgate.net | BRAIN COMMUNICATIONS — researchgate_shadow_or_repo_copy_without_authoritative_metadata_path
- `cand_ff158b1e74de6ddb` | 2025 | www.researchgate.net | Chile entre velos: Filosofía de lo aparente y subyacente — researchgate_shadow_or_repo_copy_without_authoritative_metadata_path
- `cand_5f2ca3562a275bb1` | 2026 | docta.ucm.es | Efectos del phubbing percibido y participación digital en el bienestar psicosocial de las personas mayores de las regiones de Ñuble y Bío-Bío, Chile — nonstandard_or_low_confidence_leftover; not worth further active processing
- `cand_26f2330529d6065d` | 2025 | magres.apm.ac.cn | 抗逆转录病毒治疗相关的HIV 感染者脑功能动态改变 — non_english_out_of_scope_under_current_policy
- `cand_5a7915c2ef9d0917` | n/a | www.diva-portal.org | Perspectives on income and health — nonstandard_or_low_confidence_leftover; not worth further active processing
- `cand_aa3aa5bb24f6ed1c` | 2026 | lajoe.org | ASSOCIATION BETWEEN KAPPA FREE LIGHT CHAINS, DISABILITY, AND MRI FINDINGS IN PREDICTING THE COURSE OF MULTIPLE SCLEROSIS — nonstandard_or_low_confidence_leftover; not worth further active processing
- `cand_d0aac8d2cd76183e` | 2026 | www.researchgate.net | Active Breathing Part I: Modalities, Mathematical Model & Case Studies — researchgate_shadow_or_repo_copy_without_authoritative_metadata_path
- `cand_38a739957e3e9daa` | n/a | www.math.unipd.it | Discovery of Latent Clinical Phenotypes Through Optimal Transport of Brain Dynamics — nonstandard_or_low_confidence_leftover; not worth further active processing
- `cand_8bc25f998a80d7f3` | 2025 | stax.strath.ac.uk | Depression-like behaviour in a mouse model of Alzheimer's disease: a reverse translational study. — nonstandard_or_low_confidence_leftover; not worth further active processing
- `cand_cc0222dc8c55cf6b` | 2026 | search.proquest.com | No Teacher Left Behind. Integrating Technology in Urban P-12 Classrooms Using the SAMR Model: A Qualitative Case Study of Urban Public Schools — nonstandard_or_low_confidence_leftover; not worth further active processing
- `cand_0b74a043eb689872` | n/a | www.jsme.or.jp | 超高磁場7 テスラMRI 環境対応の全自動触覚機械刺激提示システムの開発 — non_english_out_of_scope_under_current_policy
- `cand_ad09e5bf2ddea2c7` | 2025 | minerva-access.unimelb.edu.au | Modelling neurobiological mechanisms of negative cognitions in binge eating — nonstandard_or_low_confidence_leftover; not worth further active processing
- `cand_8885d5e06333a6d5` | 2025 | elibrary.ru | ЛАТЕРАЛИЗАЦИЯ СИЛЫ КИСТИ КАК МАРКЕР КОГНИТИВНЫХ ФУНКЦИЙ У МУЖЧИН ПРАВШЕЙ С ХРОНИЧЕСКОЙ ИШЕМИЕЙ МОЗГА — non_english_out_of_scope_under_current_policy
- `cand_a03d9863f6e54a31` | 2026 | books.google.com | The Implications of Neuroscience for What Works — book_or_book_chapter_like; out of active library-build scope
- `cand_ed2c42753a6fd6a4` | 2026 | www.researchgate.net | BRAIN PLASTICITY DURING GESTATION AND POSTPARTUM PERIODS — researchgate_shadow_or_repo_copy_without_authoritative_metadata_path
- `cand_ad67ee178f07ee23` | n/a | drdidwal.com | How to Reverse Brain Aging: The Science Behind Fitness, Brain Age, and Dementia Risk — nonstandard_or_low_confidence_leftover; not worth further active processing
- `cand_88f41d9c9a78d2ae` | n/a | www.researchgate.net | Graduate School of Sciences and Technology for Innovation Tokushima University — researchgate_shadow_or_repo_copy_without_authoritative_metadata_path
- `cand_132d71553d6328d5` | n/a | www.jillcarnahan.com | Galectin-3: The Hidden Driver of Inflammation, Fibrosis, and Chronic Disease You are here — nonstandard_or_low_confidence_leftover; not worth further active processing
- `cand_a77c99b0e10b7adf` | 2025 | journal.bgcardio.org | Молекулни механизми на левокамерната систолна дисфункция: актуален преглед Molecular mechanisms of left ventricular systolic dysfunction: a current review — nonstandard_or_low_confidence_leftover; not worth further active processing
- `cand_263d188a54ad7cae` | n/a | pattern.eecs.tottori-u.ac.jp | Investigating temporal changes of impression formed by interviewers from the applicant's behavior — nonstandard_or_low_confidence_leftover; not worth further active processing
- `cand_f837e787dc0e1efa` | 2025 | docta.ucm.es | El valor intangible de la coproducción digital del sector público: El compromiso y la confianza ciudadana generada por Avisos Madrid — nonstandard_or_low_confidence_leftover; not worth further active processing

## Operational consequence

- The residual-tail program is considered **closed** for the current cycle.
- No `chunk08+` continuation should be scheduled.
- Future reopening requires an explicit scope change, not routine follow-up.