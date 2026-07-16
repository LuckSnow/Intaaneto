class ActionScopedThrottleMixin:
    """Apply DRF throttle scopes only to explicitly mapped ViewSet actions."""

    throttle_scope_by_action = {}

    def get_throttles(self):
        action = getattr(self, 'action', None)
        method = self.request.method.lower()
        self.throttle_scope = self.throttle_scope_by_action.get(
            (action, method),
            self.throttle_scope_by_action.get(action),
        )
        return super().get_throttles()
