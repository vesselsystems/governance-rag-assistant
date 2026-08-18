# AI Incident Response Guide

Document version: 1.0
Owner: AI Operations Team

## Trigger conditions

Open an incident when the system exposes restricted information, produces a materially misleading answer, loses source citations, shows a quality or latency regression, or behaves differently from the approved use case.

## First response

Record the time, user-visible behavior, request context, model and prompt version, retrieved sources, and relevant logs. Preserve evidence while avoiding unnecessary copies of sensitive content.

## Containment

Pause the affected workflow or route it to human review. Disable a problematic source, prompt, model, or integration only when the change is recorded and reversible. Do not silently delete evidence needed for investigation.

## Investigation and recovery

Reproduce the failure with a controlled test, identify whether the cause was data, retrieval, prompt, model, integration, or operations, and add a regression test. Restore service only after an owner accepts the remaining risk and the monitoring signal is in place.

## Communication

Communicate impact, scope, containment, owner, and next update time to the appropriate stakeholders. After recovery, document the root cause, corrective action, and prevention work.
