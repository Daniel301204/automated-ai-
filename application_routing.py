"""Deterministic route selection. Public listing APIs are never treated as submission credentials."""

def route_for(job, mandatory_status, score, threshold, verified_email):
    if mandatory_status != 'met' or score < threshold:
        return 'blocked'
    if verified_email:
        return 'email'
    if job.get('source') in ('greenhouse', 'lever') and job.get('url', '').startswith('https://'):
        return 'ats_review'
    return 'review'

def ats_submission_status(adapter, explicit_authorization, all_required_fields_present):
    """No live submission without an employer-provided adapter and explicit per-integration authorization."""
    if not explicit_authorization or not all_required_fields_present or adapter is None:
        return 'ats_review_required'
    return 'ats_adapter_ready'
