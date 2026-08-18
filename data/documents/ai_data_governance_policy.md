# AI Data Governance Demo Policy

Document version: 1.0
Owner: Data Governance Working Group

## Purpose

This original demo policy describes minimum controls for using data in an AI project. It is a teaching artifact, not legal advice or a substitute for an organization's approved policy.

## Data inventory and ownership

Every AI project should record what data it uses, why it is needed, who owns it, where it came from, and how long it will be retained. A project may use only the minimum data needed for its stated purpose.

## Quality controls

Before modeling, the team should profile completeness, validity, uniqueness, timeliness, and consistency. Quality failures should be documented rather than silently removed. The owner should define thresholds for blocking a release and an escalation path for unresolved issues.

## Access and privacy

Access should follow least privilege. Sensitive fields should be masked, minimized, or excluded when they are not necessary. Development copies should not contain production secrets or unapproved personal information.

## Review evidence

A release review should include the data dictionary, quality results, lineage, intended use, known limitations, and the person responsible for accepting residual risk.
