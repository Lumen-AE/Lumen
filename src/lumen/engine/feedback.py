"""Stage-specific public views of measured simulator feedback."""

def public_feedback(feedback, controller, catalog, arm, decision=None):
    result = dict(coverage=controller.report(), last_pc=feedback.get('last_pc'),
                  last_instruction=feedback.get('last_instruction'), new_bins=feedback.get('new_bins', []),
                  error=feedback.get('error'), decision=decision,
                  assigned_target=None if controller.current is None else catalog[controller.current])
    if arm == 'evidence' and 'evidence' in feedback:
        result['evidence'] = feedback['evidence']
    return result
