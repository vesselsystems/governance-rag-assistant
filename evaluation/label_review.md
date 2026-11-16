# Challenge-set label review

The 32 questions in `evaluation/challenge_questions.json` and their expected chunks were
drafted with AI assistance. Until a person checks them, every result computed from them is
provisional. This review is the human evaluation step for the retrieval benchmark, and it is
yours to do: do not delegate it back to an AI.

**Time:** about 30-45 minutes. **Do not open `reports/retriever_comparison.md` until you
finish;** knowing what the system retrieved biases the judgment.

For each item below:

1. Read the question, then the quoted chunk text.
2. Answerable item: does the chunk directly answer the question? Does any *other* chunk also
   answer it? The full documents are in `data/documents/`.
   - Label right: set `"label_status": "human_verified"` for that item in the JSON.
   - Label wrong or incomplete: fix `expected_citations`, set
     `"label_status": "human_corrected"`, and add `"label_note"` saying what changed and why.
3. Unanswerable item: confirm that no document answers it. If one does, make it answerable:
   add the citation(s), set `"answerable": true`, and mark it `human_corrected` with a note.
4. If a question is itself ambiguous, say so in `label_note`; rewording is fine but record it.

When finished:

```bash
python scripts/label_worksheet.py      # refresh this file
python scripts/compare_retrievers.py   # recompute results with your labels
pytest
```

The comparison report then shows how many labels are human-verified and adds a
"human-verified only" result.

---

## ch-dev-01 (dev, paraphrase) - status: `ai_drafted_unverified`

**Question:** Who does this guidance apply to?

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#0]`:**

> Procurement Policy Note Improving Transparency of AI use in Procurement Information Note: 017 Originally issued: November 2023 Updated: February 2025 Issue 1. AI systems, tools and products are part of a rapidly growing and evolving market, and as such, there may be increased risks associated with their adoption. Care should be taken to ensure that AI is used appropriately, and with due regard to risks and opportunities. As the Government increases its adoption of AI, it is essential to take steps to identify and manage associated risks and opportunities, as part of the Government's commercial activities. Dissemination and scope 2. This Procurement Policy Note (PPN) applies to all central government departments, their executive agencies and non-departmental public bodies. Such bodies are referred to as ’in-scope organisation’. 3. Please circulate this PPN within your organisation, particularly to those with a commercial procurement and/or contract management role. It may also be relevant to those in finance, operational and sustainability roles. Other public sector contracting authorities may wish to apply the approach set out in this PPN. 4. This PPN has been updated

*Drafting rationale:* Chunk 0: the PPN applies to central government departments, their executive agencies and non-departmental public bodies.

---

## ch-dev-02 (dev, paraphrase) - status: `ai_drafted_unverified`

**Question:** Are bidders banned from using generative tools when writing proposals?

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#2]`:**

> date, please refer to PPN 02/24. 6. This update does not constitute a change in policy or a new call for action but in-scope organisation should continue to apply any ongoing obligations set out in the provisions of this PPN. Timing 7. In-scope organisation should note the provisions of this PPN from 24 February 2025. For information 8. There is a range of guidance available to support commercial teams to understand AI as a subject area, the appropriate use of AI within public services and how AI products should be procured. References to some of this guidance can be found in Annex A. 9. There are potential benefits to suppliers using AI to develop their bids, enabling them to bid for a greater number of public contracts. It is important to note that suppliers' use of AI is not prohibited during the commercial process but steps should be taken to understand the risks associated with the use of AI tools in this context, as would be the case if a bid writer has been used by the supplier. This may

*Drafting rationale:* Chunk 2: suppliers' use of AI is not prohibited during the commercial process.

---

## ch-dev-03 (dev, paraphrase) - status: `ai_drafted_unverified`

**Question:** Why might buyers need to plan for more questions and submissions?

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#4]`:**

> may be required to ensure suppliers have the appropriate capacity and capability to fulfil the requirements of the contract. Such due diligence should be proportionate to any additional specific risk posed by the use of AI, and could include site visits, clarification questions or supplier presentations. − Additional due diligence should help to establish the accuracy, robustness and credibility of suppliers' tenders through the use of clarifications or requesting additional supporting documentation in the same way contracting authorities would approach any uncertainty or ambiguity in tenders. ● Planning for a general increase in activity as suppliers may use AI to streamline or automate their processes and improve their bid writing capability and capacity leading to an increase in clarification questions and tender responses. ● Potentially allowing more time in the procurement to allow for due diligence and an increase in volumes of responses. ● Closer alignment with internal customers and delivery teams to bring greater expertise on the implications and benefits of AI, relative to the subject matter of the contract. 10. In certain procurements where there are national security

*Drafting rationale:* Chunk 4: suppliers may use AI to streamline bid writing, increasing clarification questions and tender responses.

---

## ch-dev-04 (dev, lexical_trap) - status: `ai_drafted_unverified`

**Question:** If a purchase raises defence or intelligence worries about supplier AI, who needs to be involved?

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#5]`:**

> volumes of responses. ● Closer alignment with internal customers and delivery teams to bring greater expertise on the implications and benefits of AI, relative to the subject matter of the contract. 10. In certain procurements where there are national security concerns in relation to use of AI by suppliers, there may be additional considerations and risk mitigations that are required. In such instances, commercial teams should engage with their Information Assurance and Security colleagues, before launching the procurement, to ensure proportionate risk mitigations are implemented. 11. Commercial teams should take note of existing guidance1 when purchasing AI services, however they should also be aware that AI and Machine Learning is becoming increasingly prevalent in the delivery of "non-AI" services. Where AI is likely to be used in the delivery of a service, commercial teams may wish to require suppliers to declare this, and provide further details (see Example Disclosure Question 3). This will enable commercial teams to consider any additional due diligence or contractual amendments to manage the impact of AI as part of the service delivery. An illustrative example:

*Drafting rationale:* Chunk 5: for national security concerns, engage Information Assurance and Security colleagues before launching. Trap: 'intelligence' also matches 'Artificial Intelligence' throughout Annex A.

---

## ch-dev-05 (dev, paraphrase) - status: `ai_drafted_unverified`

**Question:** Why can't text from a chatbot be trusted to be factually correct?

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#8]`:**

> restricted to use cases where risks can be effectively understood and managed. 14. AI has potential to accelerate and support decision making processes, especially through the use of large data sets. It is essential to ensure that decisions are made with the support of AI systems, not a reliance upon them, in accordance with the principles outlined in the Government's Data Ethics Framework and guidance on Understanding Artificial Intelligence Ethics and Safety. 15. Content created with the support of LLMs may include inaccurate or misleading statements; where statements, facts or references appear plausible, but are in fact false. LLMs are trained to predict a "statistically plausible" string of text, however statistical plausibility does not necessarily mean that the statements are factually accurate. As LLMs do not have a contextual understanding of the question they are being asked, or the answer they are proposing, they are unable to identify or correct any errors they make in their response. Care must be taken both in the use of LLMs, and in assessing returns that have used LLMs, in the form of additional

*Drafting rationale:* Chunk 8: LLMs predict statistically plausible text, and plausibility does not mean factual accuracy.

---

## ch-dev-06 (dev, paraphrase) - status: `ai_drafted_unverified`

**Question:** Who can I phone with questions about this note?

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#9]`:**

> they are proposing, they are unable to identify or correct any errors they make in their response. Care must be taken both in the use of LLMs, and in assessing returns that have used LLMs, in the form of additional due diligence. Contact 16. Enquiries about this PPN should be directed to the Crown Commercial Service Helpdesk on 0345 410 2222 or info@crowncommercial.gov.uk. Annex A - Guidance and Best Practice Introduction 1. Assessing if artificial intelligence is the right solution 2. Government Digital Service (GDS) and the Office for Artificial Intelligence (OAI) have published joint guidance2 for anyone responsible for choosing technology in a public sector organisation and will help you determine if the use of AI is appropriate for your specific use case. 3. Guidelines for AI Procurement 4. Cabinet Office, Office for Artificial Intelligence (OAI) and the World Economic Forum have published joint guidance3 to provide a set of guiding principles on how to buy AI technology, as well as insights on tackling challenges that may arise during procurement. 5. A guide to using artificial intelligence in the

*Drafting rationale:* Chunk 9: enquiries go to the Crown Commercial Service Helpdesk on 0345 410 2222.

---

## ch-dev-07 (dev, paraphrase) - status: `ai_drafted_unverified`

**Question:** Do suppliers' answers about AI use count toward their evaluation score?

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#14]`:**

> order to establish whether AI has been used by suppliers to develop responses to questions in the procurement, a disclosure question can be added to the Invitation to Tender. This requires suppliers to disclose their use of AI when responding to the tender questions, or as part of their proposed delivery of the service. There are a series of example disclosure questions set-out below which may be helpful. The questions included in this annex should not be scored or taken into account when assessing a tender and should be used for information only. Contracting authorities can however continue to ask and evaluate any further relevant questions about use of AI as part of their award process which are specific to their requirements and are compliant with procurement law. Whether, and if so how, any questions are to be scored should be set out in the tender notice or associated tender documents. These questions may be helpful in informing wider commercial strategy, defining how to undertake meaningful due diligence and manage risk. Note: It is important that contracting authorities do not

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#15]`:**

> be set out in the tender notice or associated tender documents. These questions may be helpful in informing wider commercial strategy, defining how to undertake meaningful due diligence and manage risk. Note: It is important that contracting authorities do not discriminate against particular suppliers in the use of these questions or in the interpretation of supplier responses. Example Disclosure Question 1: For Information Only (Not Scored) AI tools can be used to improve the efficiency of your bid writing process, however they may also introduce an increased risk of misleading statements via ‘hallucination’. Have you used AI or machine learning tools, including large language models, to assist in any part of your tender submission? This may include using these tools to support the drafting of responses to award questions. Yes ロ No ロ Please provide details: Where AI tools have been used to support the generation of Tender responses, please confirm that they have been checked and verified for accuracy: 12 Civil Service Learning AI Courses: https://learn.civilservice.gov.uk/search?q=artificial+intelligence Yes ロ No ロ Example Disclosure Question 2: For Information Only (Not Scored)

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#16]`:**

> been used to support the generation of Tender responses, please confirm that they have been checked and verified for accuracy: 12 Civil Service Learning AI Courses: https://learn.civilservice.gov.uk/search?q=artificial+intelligence Yes ロ No ロ Example Disclosure Question 2: For Information Only (Not Scored) AI tools can be used to improve the efficiency of your bid writing process, however they may also introduce an increased risk of misleading statements via ‘hallucination’. Please detail any instances where AI or machine learning tools, including large language models have been used to generate written content, or support your tender submission. Please provide details: Where AI tools have been used to support the generation of tender responses, please confirm that they have been checked and verified for accuracy: Yes ロ No ロ Example Disclosure Question 3: For Information Only (Not Scored) Are AI or machine learning technologies used as part of the products/services you intend to provide to [Insert Contracting Authority Name]? Yes ロ No ロ If Yes: Please describe how AI technologies are integrated into your service offerings. Please provide details:

*Drafting rationale:* Chunk 14 states the annex questions should not be scored; chunks 15 and 16 label each example question 'For Information Only (Not Scored)'.

---

## ch-dev-08 (dev, paraphrase) - status: `ai_drafted_unverified`

**Question:** What must a project write down about how long it holds onto its data?

**Labelled chunk `[ai_data_governance_policy.md#0]`:**

> # AI Data Governance Demo Policy Document version: 1.0 Owner: Data Governance Working Group ## Purpose This original demo policy describes minimum controls for using data in an AI project. It is a teaching artifact, not legal advice or a substitute for an organization's approved policy. ## Data inventory and ownership Every AI project should record what data it uses, why it is needed, who owns it, where it came from, and how long it will be retained. A project may use only the minimum data needed for its stated purpose. ## Quality controls Before modeling, the team should profile completeness, validity, uniqueness, timeliness, and consistency. Quality failures should be documented rather than silently removed. The owner should define thresholds for blocking a release and an escalation path for unresolved issues. ## Access and privacy Access should follow least privilege. Sensitive fields should be masked, minimized, or excluded when they are not necessary. Development copies should not contain production secrets or unapproved personal information. ## Review evidence A release review should include the data dictionary, quality results, lineage, intended use,

*Drafting rationale:* Chunk 0: every AI project should record how long its data will be retained.

---

## ch-dev-09 (dev, paraphrase) - status: `ai_drafted_unverified`

**Question:** Does a good accuracy number mean the model is ready to deploy?

**Labelled chunk `[model_risk_review_playbook.md#0]`:**

> # Model Risk Review Playbook Document version: 1.0 Owner: Applied AI Review Group ## Intended use A model review asks whether the model is fit for a specific decision, population, time period, and operating process. A high score does not establish that a model should be used. ## Evaluation The team should define a baseline, select metrics that reflect the decision cost, separate training and test data, and report uncertainty. For classification, review precision, recall, F1, ROC-AUC, calibration, subgroup performance, and error examples when they are relevant. ## Leakage and robustness Review whether each feature would be available at prediction time. Check duplicates, target leakage, distribution shifts, missingness, adversarial inputs, and sensitivity to reasonable changes in the data or threshold. ## Human oversight Document who can act on a prediction, what the model cannot decide, and how a person can override or appeal an output. Automation should not remove accountability from the responsible owner. ## Approval record The approval record should state the intended use, excluded uses, data sources, evaluation results, residual risks, monitoring plan, review date, and owner for

*Drafting rationale:* Chunk 0: a high score does not establish that a model should be used.

---

## ch-dev-10 (dev, in_domain_unanswerable) - status: `ai_drafted_unverified`

**Question:** What is the maximum fine for a data breach under this policy?

**Labelled unanswerable.** Confirm that no document in `data/documents/` answers this question.

*Drafting rationale:* No document sets fines or penalties.

---

## ch-dev-11 (dev, in_domain_unanswerable) - status: `ai_drafted_unverified`

**Question:** How often must models be retrained?

**Labelled unanswerable.** Confirm that no document in `data/documents/` answers this question.

*Drafting rationale:* No document specifies a retraining cadence.

---

## ch-dev-12 (dev, in_domain_unanswerable) - status: `ai_drafted_unverified`

**Question:** How long must video conference transcripts be retained?

**Labelled unanswerable.** Confirm that no document in `data/documents/` answers this question.

*Drafting rationale:* Chunk 6 discusses meeting transcripts and their use, but no retention period appears anywhere.

---

## ch-dev-13 (dev, in_domain_unanswerable) - status: `ai_drafted_unverified`

**Question:** Which AI vendors are on the government's approved supplier list?

**Labelled unanswerable.** Confirm that no document in `data/documents/` answers this question.

*Drafting rationale:* The PPN names no approved vendors or supplier list.

---

## ch-dev-14 (dev, in_domain_unanswerable) - status: `ai_drafted_unverified`

**Question:** What is the minimum contract value above which AI disclosure becomes mandatory?

**Labelled unanswerable.** Confirm that no document in `data/documents/` answers this question.

*Drafting rationale:* No value threshold appears; disclosure questions are described as optional examples.

---

## ch-dev-15 (dev, out_of_domain_unanswerable) - status: `ai_drafted_unverified`

**Question:** What is the boiling point of water at sea level?

**Labelled unanswerable.** Confirm that no document in `data/documents/` answers this question.

*Drafting rationale:* Unrelated to the corpus.

---

## ch-test-01 (test, paraphrase) - status: `ai_drafted_unverified`

**Question:** From what date do the updated rules take effect?

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#2]`:**

> date, please refer to PPN 02/24. 6. This update does not constitute a change in policy or a new call for action but in-scope organisation should continue to apply any ongoing obligations set out in the provisions of this PPN. Timing 7. In-scope organisation should note the provisions of this PPN from 24 February 2025. For information 8. There is a range of guidance available to support commercial teams to understand AI as a subject area, the appropriate use of AI within public services and how AI products should be procured. References to some of this guidance can be found in Annex A. 9. There are potential benefits to suppliers using AI to develop their bids, enabling them to bid for a greater number of public contracts. It is important to note that suppliers' use of AI is not prohibited during the commercial process but steps should be taken to understand the risks associated with the use of AI tools in this context, as would be the case if a bid writer has been used by the supplier. This may

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#1]`:**

> procurement and/or contract management role. It may also be relevant to those in finance, operational and sustainability roles. Other public sector contracting authorities may wish to apply the approach set out in this PPN. 4. This PPN has been updated to reflect new terminology introduced by the Procurement Act 2023 and the Procurement Regulations 2024. The Procurement Act 2023 and the Procurement Regulations 2024 apply to procurements commenced on or after 24 February 2025. For more detail on the meaning of 'commenced' please refer to the Procurement Act 2023 Guidance on Transitional and Savings Arrangements. 5. The Procurement Act 2023 does not apply to procurements commenced before 24 February 2025 or to contracts awarded prior to this date (including via frameworks, dynamic purchasing systems or qualification systems established under the previous legislation). For procurements commenced and contracts awarded before this date, please refer to PPN 02/24. 6. This update does not constitute a change in policy or a new call for action but in-scope organisation should continue to apply any ongoing obligations set out in the provisions of this PPN.

*Drafting rationale:* Chunk 2 (Timing): note the provisions from 24 February 2025. Chunk 1: the updated legislation applies to procurements commenced on or after 24 February 2025.

---

## ch-test-02 (test, paraphrase) - status: `ai_drafted_unverified`

**Question:** Can a vendor feed our non-public tender papers into a model to train it?

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#3]`:**

> during the commercial process but steps should be taken to understand the risks associated with the use of AI tools in this context, as would be the case if a bid writer has been used by the supplier. This may include: ● Asking suppliers to disclose their use of AI in the creation of their tender (See Annex B for an example of text that can be added to procurement documentation). ● Putting in place proportionate controls to ensure suppliers do not use confidential contracting authority information, or information not already in the public domain as training data for AI systems e.g. using confidential Government tender documents to train AI or Large Language Models (LLMs) to create future tender responses. ● Undertaking appropriate and proportionate due diligence: − If suppliers use AI tools to create tender responses, additional due diligence may be required to ensure suppliers have the appropriate capacity and capability to fulfil the requirements of the contract. Such due diligence should be proportionate to any additional specific risk posed by the use of AI, and could include site

*Drafting rationale:* Chunk 3: controls should stop suppliers using confidential or non-public authority information as AI training data.

---

## ch-test-03 (test, paraphrase) - status: `ai_drafted_unverified`

**Question:** What checks can a buyer use to confirm a supplier can actually deliver if the bid was AI-written?

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#3]`:**

> during the commercial process but steps should be taken to understand the risks associated with the use of AI tools in this context, as would be the case if a bid writer has been used by the supplier. This may include: ● Asking suppliers to disclose their use of AI in the creation of their tender (See Annex B for an example of text that can be added to procurement documentation). ● Putting in place proportionate controls to ensure suppliers do not use confidential contracting authority information, or information not already in the public domain as training data for AI systems e.g. using confidential Government tender documents to train AI or Large Language Models (LLMs) to create future tender responses. ● Undertaking appropriate and proportionate due diligence: − If suppliers use AI tools to create tender responses, additional due diligence may be required to ensure suppliers have the appropriate capacity and capability to fulfil the requirements of the contract. Such due diligence should be proportionate to any additional specific risk posed by the use of AI, and could include site

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#4]`:**

> may be required to ensure suppliers have the appropriate capacity and capability to fulfil the requirements of the contract. Such due diligence should be proportionate to any additional specific risk posed by the use of AI, and could include site visits, clarification questions or supplier presentations. − Additional due diligence should help to establish the accuracy, robustness and credibility of suppliers' tenders through the use of clarifications or requesting additional supporting documentation in the same way contracting authorities would approach any uncertainty or ambiguity in tenders. ● Planning for a general increase in activity as suppliers may use AI to streamline or automate their processes and improve their bid writing capability and capacity leading to an increase in clarification questions and tender responses. ● Potentially allowing more time in the procurement to allow for due diligence and an increase in volumes of responses. ● Closer alignment with internal customers and delivery teams to bring greater expertise on the implications and benefits of AI, relative to the subject matter of the contract. 10. In certain procurements where there are national security

*Drafting rationale:* Chunks 3-4: proportionate additional due diligence on capacity and capability, e.g. site visits, clarification questions or supplier presentations.

---

## ch-test-04 (test, paraphrase) - status: `ai_drafted_unverified`

**Question:** What should buyers do when a service that isn't marketed as AI will still rely on machine learning?

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#5]`:**

> volumes of responses. ● Closer alignment with internal customers and delivery teams to bring greater expertise on the implications and benefits of AI, relative to the subject matter of the contract. 10. In certain procurements where there are national security concerns in relation to use of AI by suppliers, there may be additional considerations and risk mitigations that are required. In such instances, commercial teams should engage with their Information Assurance and Security colleagues, before launching the procurement, to ensure proportionate risk mitigations are implemented. 11. Commercial teams should take note of existing guidance1 when purchasing AI services, however they should also be aware that AI and Machine Learning is becoming increasingly prevalent in the delivery of "non-AI" services. Where AI is likely to be used in the delivery of a service, commercial teams may wish to require suppliers to declare this, and provide further details (see Example Disclosure Question 3). This will enable commercial teams to consider any additional due diligence or contractual amendments to manage the impact of AI as part of the service delivery. An illustrative example:

*Drafting rationale:* Chunk 5: AI is increasingly used in 'non-AI' services; commercial teams may require suppliers to declare it and give details.

---

## ch-test-05 (test, paraphrase) - status: `ai_drafted_unverified`

**Question:** If a meeting tool automatically writes up minutes using AI, what should the contract say about that data?

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#6]`:**

> declare this, and provide further details (see Example Disclosure Question 3). This will enable commercial teams to consider any additional due diligence or contractual amendments to manage the impact of AI as part of the service delivery. An illustrative example: Video Conferencing A Contracting Authority is seeking to implement a new video conferencing suite in their offices. Key considerations for the functionality of this service may include the number of concurrent users, audio and visual call quality, integration with existing software and services. In such instances, a supplier may be able to provide a service that includes meeting transcription, or live translation using Generative AI. Additional consideration should therefore be given to how these meeting records will be used (e.g. for training of further AI models) and whether the information gathered is subject to Data Classification policies. In this example, departments will likely want to ensure that proposed contractual terms make it clear that data retrieved from the videoconference is appropriately managed, e.g. not used for training purposes unless this has been specifically agreed and approved in writing by the

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#7]`:**

> departments will likely want to ensure that proposed contractual terms make it clear that data retrieved from the videoconference is appropriately managed, e.g. not used for training purposes unless this has been specifically agreed and approved in writing by the client. Background 12. Generative AI is a form of Artificial Intelligence (AI) - a broad field which aims to use computers to emulate the products of human intelligence - or to build capabilities 1 Guidelines for AI Procurement: https://www.gov.uk/government/publications/guidelines-for-ai- procurement which go beyond human intelligence. Unlike previous forms of AI, Generative AI produces new content, such as images, text or music. 13. AI systems, tools and products are part of a rapidly growing and evolving market, and as such, there may be increased risks associated with their adoption. Care should be taken to ensure that the use of AI is restricted to use cases where risks can be effectively understood and managed. 14. AI has potential to accelerate and support decision making processes, especially through the use of large data sets. It is essential to ensure that decisions are made

*Drafting rationale:* Chunks 6-7: contractual terms should make clear that videoconference data is appropriately managed and not used for training unless agreed in writing.

---

## ch-test-06 (test, paraphrase) - status: `ai_drafted_unverified`

**Question:** Should officials let an AI system make the final call on decisions?

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#8]`:**

> restricted to use cases where risks can be effectively understood and managed. 14. AI has potential to accelerate and support decision making processes, especially through the use of large data sets. It is essential to ensure that decisions are made with the support of AI systems, not a reliance upon them, in accordance with the principles outlined in the Government's Data Ethics Framework and guidance on Understanding Artificial Intelligence Ethics and Safety. 15. Content created with the support of LLMs may include inaccurate or misleading statements; where statements, facts or references appear plausible, but are in fact false. LLMs are trained to predict a "statistically plausible" string of text, however statistical plausibility does not necessarily mean that the statements are factually accurate. As LLMs do not have a contextual understanding of the question they are being asked, or the answer they are proposing, they are unable to identify or correct any errors they make in their response. Care must be taken both in the use of LLMs, and in assessing returns that have used LLMs, in the form of additional

*Drafting rationale:* Chunk 8: decisions should be made with the support of AI systems, not a reliance upon them.

---

## ch-test-07 (test, lexical_trap) - status: `ai_drafted_unverified`

**Question:** What four values does the Turing Institute guidance name?

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#13]`:**

> produced guidance10 in partnership with The Alan Turing Institute. This guidance will help to ensure your project is fair and prevent bias or discrimination and to safeguard public trust in your project's capacity to deliver safe and reliable AI through the use of the 'FAST Track Principles'; Fairness, Accountability, Sustainability and Transparency. 20. Links to available training resources 21. There are a range of training resources related to AI available through the Government Campus and Civil Service Learning. ● Government Campus: Artificial Intelligence11 6 Generative AI Framework for HMG: https://www.gov.uk/government/publications/generative-ai-framework- for-hmg 7 Managing your artificial intelligence project: https://www.gov.uk/guidance/managing-your-artificial- intelligence-project 8 Artificial intelligence in public services: https://www.equalityhumanrights.com/guidance/artificial- intelligence-public-services 9 Data Ethics Framework: https://www.gov.uk/government/publications/data-ethics-framework 10 Understanding AI Ethics and Safety: https://www.gov.uk/guidance/understanding-artificial- intelligence-ethics-and-safety 11 Government Campus AI Courses: https://prospectus.governmentcampus.co.uk/04-artificial- intelligence/ ● Civil Service Learning: Artificial Intelligence12 Annex B – AI Disclosure Questions In order to establish whether AI has been used by suppliers to develop responses to questions in the procurement, a disclosure question can be added to the Invitation to Tender. This requires suppliers to disclose their use of AI when responding

*Drafting rationale:* Chunk 13 lists the FAST Track Principles: Fairness, Accountability, Sustainability and Transparency. Trap: chunk 12 also names the Turing Institute but not the four values.

---

## ch-test-08 (test, paraphrase) - status: `ai_drafted_unverified`

**Question:** Can buyers treat vendors differently based on how they answer the AI questions?

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#15]`:**

> be set out in the tender notice or associated tender documents. These questions may be helpful in informing wider commercial strategy, defining how to undertake meaningful due diligence and manage risk. Note: It is important that contracting authorities do not discriminate against particular suppliers in the use of these questions or in the interpretation of supplier responses. Example Disclosure Question 1: For Information Only (Not Scored) AI tools can be used to improve the efficiency of your bid writing process, however they may also introduce an increased risk of misleading statements via ‘hallucination’. Have you used AI or machine learning tools, including large language models, to assist in any part of your tender submission? This may include using these tools to support the drafting of responses to award questions. Yes ロ No ロ Please provide details: Where AI tools have been used to support the generation of Tender responses, please confirm that they have been checked and verified for accuracy: 12 Civil Service Learning AI Courses: https://learn.civilservice.gov.uk/search?q=artificial+intelligence Yes ロ No ロ Example Disclosure Question 2: For Information Only (Not Scored)

*Drafting rationale:* Chunk 15: contracting authorities must not discriminate against suppliers in using these questions or interpreting responses.

---

## ch-test-09 (test, paraphrase) - status: `ai_drafted_unverified`

**Question:** How is content-creating AI different from earlier kinds of AI?

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#7]`:**

> departments will likely want to ensure that proposed contractual terms make it clear that data retrieved from the videoconference is appropriately managed, e.g. not used for training purposes unless this has been specifically agreed and approved in writing by the client. Background 12. Generative AI is a form of Artificial Intelligence (AI) - a broad field which aims to use computers to emulate the products of human intelligence - or to build capabilities 1 Guidelines for AI Procurement: https://www.gov.uk/government/publications/guidelines-for-ai- procurement which go beyond human intelligence. Unlike previous forms of AI, Generative AI produces new content, such as images, text or music. 13. AI systems, tools and products are part of a rapidly growing and evolving market, and as such, there may be increased risks associated with their adoption. Care should be taken to ensure that the use of AI is restricted to use cases where risks can be effectively understood and managed. 14. AI has potential to accelerate and support decision making processes, especially through the use of large data sets. It is essential to ensure that decisions are made

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#10]`:**

> Economic Forum have published joint guidance3 to provide a set of guiding principles on how to buy AI technology, as well as insights on tackling challenges that may arise during procurement. 5. A guide to using artificial intelligence in the public sector 6. Government Digital Service (GDS) and the Office for Artificial Intelligence (OAI) have published joint guidance4 on how to build and use AI in the public sector. This guidance covers how: ● to assess if using AI will help you meet user needs ● the public sector can best use AI ● to implement AI ethically, fairly and safely 7. You can contact ai-guide@digital.cabinet-office.gov.uk for further information about using AI in the public sector. 8. Guidance to civil servants on use of Generative AI 9. Generative Artificial Intelligence (Gen AI) is a subset of AI that focuses on creating new data. Unlike traditional machine learning models that are designed for specific tasks, Gen AI models are capable of generating new content, such as images, text, music, and more. Central Digital and Data Office (CDDO) has developed internal guidance5

**Labelled chunk `[ppn_017_improving_transparency_of_ai_use_in_procurement.txt#11]`:**

> creating new data. Unlike traditional machine learning models that are designed for specific tasks, Gen AI models are capable of generating new content, such as images, text, music, and more. Central Digital and Data Office (CDDO) has developed internal guidance5 for the use of AI and LLMs across the Civil Service. 2 Assessing if artificial intelligence is the right solution: https://www.gov.uk/guidance/assessing-if- artificial- intelligence-is-the-right-solution 3 Guidelines for AI Procurement: https://www.gov.uk/government/publications/guidelines-for-ai- procurement 4 A guide to using artificial intelligence in the public sector: https://www.gov.uk/government/collections/a- guide-to-using-artificial-intelligence-in-the-public-sector 5 Guidance to civil servants on use of generative AI: https://www.gov.uk/government/publications/guidance-to- civil-servants-on-use-of-generative-ai 10. CDDO have published further, more detailed guidance6 on Generative AI. The Generative AI Framework for HMG is guidance on using Generative AI safely and securely for civil servants and people working in government organisations. The white paper A pro-innovation approach to AI regulation, sets out five principles to guide and inform AI development in all sectors. This framework builds on those principles to create ten core principles for generative AI use in government and public sector organisations. 11. Managing your artificial intelligence project 12.

*Drafting rationale:* Chunk 7: unlike previous forms of AI, generative AI produces new content. Chunks 10-11 repeat the contrast with traditional task-specific models.

---

## ch-test-10 (test, paraphrase) - status: `ai_drafted_unverified`

**Question:** What should happen once an incident is resolved?

**Labelled chunk `[incident_response_guide.md#0]`:**

> # AI Incident Response Guide Document version: 1.0 Owner: AI Operations Team ## Trigger conditions Open an incident when the system exposes restricted information, produces a materially misleading answer, loses source citations, shows a quality or latency regression, or behaves differently from the approved use case. ## First response Record the time, user-visible behavior, request context, model and prompt version, retrieved sources, and relevant logs. Preserve evidence while avoiding unnecessary copies of sensitive content. ## Containment Pause the affected workflow or route it to human review. Disable a problematic source, prompt, model, or integration only when the change is recorded and reversible. Do not silently delete evidence needed for investigation. ## Investigation and recovery Reproduce the failure with a controlled test, identify whether the cause was data, retrieval, prompt, model, integration, or operations, and add a regression test. Restore service only after an owner accepts the remaining risk and the monitoring signal is in place. ## Communication Communicate impact, scope, containment, owner, and next update time to the appropriate stakeholders. After recovery, document the root cause, corrective action, and prevention

**Labelled chunk `[incident_response_guide.md#1]`:**

> only after an owner accepts the remaining risk and the monitoring signal is in place. ## Communication Communicate impact, scope, containment, owner, and next update time to the appropriate stakeholders. After recovery, document the root cause, corrective action, and prevention work.

*Drafting rationale:* After recovery, document the root cause, corrective action and prevention work (end of chunk 0, all of chunk 1).

---

## ch-test-11 (test, paraphrase) - status: `ai_drafted_unverified`

**Question:** What should be written down about overruling a model's output?

**Labelled chunk `[model_risk_review_playbook.md#0]`:**

> # Model Risk Review Playbook Document version: 1.0 Owner: Applied AI Review Group ## Intended use A model review asks whether the model is fit for a specific decision, population, time period, and operating process. A high score does not establish that a model should be used. ## Evaluation The team should define a baseline, select metrics that reflect the decision cost, separate training and test data, and report uncertainty. For classification, review precision, recall, F1, ROC-AUC, calibration, subgroup performance, and error examples when they are relevant. ## Leakage and robustness Review whether each feature would be available at prediction time. Check duplicates, target leakage, distribution shifts, missingness, adversarial inputs, and sensitivity to reasonable changes in the data or threshold. ## Human oversight Document who can act on a prediction, what the model cannot decide, and how a person can override or appeal an output. Automation should not remove accountability from the responsible owner. ## Approval record The approval record should state the intended use, excluded uses, data sources, evaluation results, residual risks, monitoring plan, review date, and owner for

**Labelled chunk `[model_risk_review_playbook.md#1]`:**

> override or appeal an output. Automation should not remove accountability from the responsible owner. ## Approval record The approval record should state the intended use, excluded uses, data sources, evaluation results, residual risks, monitoring plan, review date, and owner for remediation.

*Drafting rationale:* Human oversight: document how a person can override or appeal an output (end of chunk 0, start of chunk 1).

---

## ch-test-12 (test, in_domain_unanswerable) - status: `ai_drafted_unverified`

**Question:** Which named official must sign off on using AI in a tender?

**Labelled unanswerable.** Confirm that no document in `data/documents/` answers this question.

*Drafting rationale:* No document names an approving official for AI use in tenders.

---

## ch-test-13 (test, in_domain_unanswerable) - status: `ai_drafted_unverified`

**Question:** What is the deadline for reporting an AI incident to the regulator?

**Labelled unanswerable.** Confirm that no document in `data/documents/` answers this question.

*Drafting rationale:* The incident guide covers internal stakeholders; no regulator or deadline appears.

---

## ch-test-14 (test, in_domain_unanswerable) - status: `ai_drafted_unverified`

**Question:** What encryption standard must suppliers use for training data?

**Labelled unanswerable.** Confirm that no document in `data/documents/` answers this question.

*Drafting rationale:* No encryption requirement appears anywhere.

---

## ch-test-15 (test, in_domain_unanswerable) - status: `ai_drafted_unverified`

**Question:** What budget is allocated for AI training courses for civil servants?

**Labelled unanswerable.** Confirm that no document in `data/documents/` answers this question.

*Drafting rationale:* Chunk 13 lists training resources but no budget.

---

## ch-test-16 (test, in_domain_unanswerable) - status: `ai_drafted_unverified`

**Question:** Which large language model does the Cabinet Office recommend for drafting bids?

**Labelled unanswerable.** Confirm that no document in `data/documents/` answers this question.

*Drafting rationale:* No model is recommended; the PPN only discusses risks of LLM use.

---

## ch-test-17 (test, out_of_domain_unanswerable) - status: `ai_drafted_unverified`

**Question:** Who won the 2018 football World Cup?

**Labelled unanswerable.** Confirm that no document in `data/documents/` answers this question.

*Drafting rationale:* Unrelated to the corpus.

---
