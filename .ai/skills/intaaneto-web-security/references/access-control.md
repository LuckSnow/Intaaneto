# Access control

Use object-level authorization, not role checks alone. “Teacher” does not imply
ownership of every course, lesson, upload, assessment, or student record.

## Baseline access matrix

| Resource/action | Anonymous | Learner | Teacher | Admin |
|---|---|---|---|---|
| Published course metadata | Read | Read | Read | Manage |
| Enroll in published course | No | Self | Self if allowed | Manage |
| Authorized lesson content | No | Enrolled read | Owned-course read/write | Manage |
| Upload/reprocess lesson | No | No | Owned course only | Manage |
| Student submission | No | Own create/read | Assigned-course read | Manage |
| Solution/hidden tests | No | Never | Owned/assigned course | Manage |
| Own profile | No | Read/update safe fields | Read/update safe fields | Manage |
| Role/active status | No | No | No | Manage/audit |
| Chat/RAG session | No | Own authorized scope | Own/authorized scope | Audited support |
| Progress/AI assessment | No | Own read | Assigned learners | Manage |

Refine this matrix when product rules are decided, but never silently broaden it.

## Django/DRF implementation rules

- Prefer read-only public viewsets for published catalog data.
- Restrict `get_queryset()` by actor, ownership, enrollment, publication, and
  active/version state. Object permissions alone do not protect list endpoints.
- Use action-specific permission classes and serializers for create/update/
  custom actions.
- Set ownership in `perform_create()` from `request.user`; ignore client owners.
- Make privilege and evaluation fields read-only or omit them entirely.
- Use dedicated learner serializers that omit solutions, hidden tests, internal
  feedback, source internals, provider IDs, and processing errors.
- Verify related IDs belong to an authorized parent before saving nested or
  foreign-key objects.
- Return 404 instead of confirming existence when disclosure itself is unsafe.
- Use database constraints for uniqueness/invariants, but do not mistake them
  for authorization.

## Required negative tests

- Anonymous mutation of course data is rejected.
- Learner cannot list/update/delete another user.
- Learner cannot select or assign teacher/admin role.
- Teacher cannot edit another teacher's course or upload.
- Non-enrolled learner cannot retrieve lesson content or RAG chunks.
- Learner response never contains solution or hidden test fields.
- Learner cannot set score, status, completion, user, owner, or processing state.
- Custom actions enforce the same object scope as normal actions.
- List endpoints do not leak objects that detail endpoints would deny.

