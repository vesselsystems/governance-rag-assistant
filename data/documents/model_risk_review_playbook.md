# Model Risk Review Playbook

Document version: 1.0
Owner: Applied AI Review Group

## Intended use

A model review asks whether the model is fit for a specific decision, population, time period, and operating process. A high score does not establish that a model should be used.

## Evaluation

The team should define a baseline, select metrics that reflect the decision cost, separate training and test data, and report uncertainty. For classification, review precision, recall, F1, ROC-AUC, calibration, subgroup performance, and error examples when they are relevant.

## Leakage and robustness

Review whether each feature would be available at prediction time. Check duplicates, target leakage, distribution shifts, missingness, adversarial inputs, and sensitivity to reasonable changes in the data or threshold.

## Human oversight

Document who can act on a prediction, what the model cannot decide, and how a person can override or appeal an output. Automation should not remove accountability from the responsible owner.

## Approval record

The approval record should state the intended use, excluded uses, data sources, evaluation results, residual risks, monitoring plan, review date, and owner for remediation.
