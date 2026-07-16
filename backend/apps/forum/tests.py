import pytest

from apps.users.models import User

from .models import Comment, Post, Reaction, Report, Tag


@pytest.fixture
def forum_users(student_user):
    other = User.objects.create_user(
        email='forum-other@example.invalid',
        username='forum-other',
        full_name='Forum Other',
        password='LocalTestOnly-123!',
        is_verified=True,
        phone_number='0900000001',
    )
    teacher = User.objects.create_user(
        email='forum-teacher@example.invalid',
        username='forum-teacher',
        full_name='Forum Teacher',
        password='LocalTestOnly-123!',
        role='teacher',
        is_verified=True,
    )
    admin = User.objects.create_user(
        email='forum-admin@example.invalid',
        username='forum-admin',
        full_name='Forum Admin',
        password='LocalTestOnly-123!',
        role='admin',
        is_verified=True,
    )
    return student_user, other, teacher, admin


@pytest.fixture
def forum_posts(forum_users):
    owner, other, _, _ = forum_users
    first = Post.objects.create(
        author=owner,
        title='Bài của owner',
        content='Nội dung owner',
    )
    second = Post.objects.create(
        author=other,
        title='Bài của user khác',
        content='Nội dung user khác',
    )
    return first, second


@pytest.mark.django_db
def test_public_post_author_omits_private_account_fields(api_client, forum_posts):
    first, _ = forum_posts

    response = api_client.get(f'/api/forum/posts/{first.id}/')

    assert response.status_code == 200
    assert set(response.data['author']) == {
        'id', 'username', 'full_name', 'role', 'avatar', 'google_avatar',
    }
    assert 'email' not in response.data['author']
    assert 'phone_number' not in response.data['author']
    assert 'date_of_birth' not in response.data['author']


@pytest.mark.django_db
def test_post_owner_can_edit_content_but_not_privileged_status(
    api_client, forum_users, forum_posts
):
    owner, _, _, _ = forum_users
    first, _ = forum_posts
    api_client.force_authenticate(owner)

    response = api_client.patch(
        f'/api/forum/posts/{first.id}/',
        {
            'title': 'Tiêu đề mới',
            'is_pinned': True,
            'is_closed': True,
            'is_solved': True,
        },
        format='json',
    )

    assert response.status_code == 200
    first.refresh_from_db()
    assert first.title == 'Tiêu đề mới'
    assert first.is_pinned is False
    assert first.is_closed is False
    assert first.is_solved is False


@pytest.mark.django_db
def test_other_user_cannot_update_or_delete_post(
    api_client, forum_users, forum_posts
):
    _, other, _, _ = forum_users
    first, _ = forum_posts
    api_client.force_authenticate(other)

    changed = api_client.patch(
        f'/api/forum/posts/{first.id}/',
        {'title': 'Chiếm quyền'},
        format='json',
    )
    deleted = api_client.delete(f'/api/forum/posts/{first.id}/')

    assert changed.status_code == 403
    assert deleted.status_code == 403
    first.refresh_from_db()
    assert first.title == 'Bài của owner'


@pytest.mark.django_db
def test_comment_owner_boundary_and_server_owned_relations(
    api_client, forum_users, forum_posts
):
    owner, other, _, _ = forum_users
    first, second = forum_posts
    comment = Comment.objects.create(
        post=first,
        author=owner,
        content='Bình luận owner',
    )
    api_client.force_authenticate(other)

    changed = api_client.patch(
        f'/api/forum/comments/{comment.id}/',
        {'content': 'Chiếm bình luận', 'post': second.id, 'is_solution': True},
        format='json',
    )
    deleted = api_client.delete(f'/api/forum/comments/{comment.id}/')

    assert changed.status_code == 403
    assert deleted.status_code == 403
    api_client.force_authenticate(owner)
    own_change = api_client.patch(
        f'/api/forum/comments/{comment.id}/',
        {'content': 'Owner sửa', 'post': second.id, 'is_solution': True},
        format='json',
    )
    assert own_change.status_code == 200
    comment.refresh_from_db()
    assert comment.content == 'Owner sửa'
    assert comment.post == first
    assert comment.is_solution is False


@pytest.mark.django_db
def test_reply_parent_must_belong_to_same_post(
    api_client, forum_users, forum_posts
):
    owner, _, _, _ = forum_users
    first, second = forum_posts
    parent = Comment.objects.create(post=first, author=owner, content='Parent')
    api_client.force_authenticate(owner)

    response = api_client.post(
        '/api/forum/comments/',
        {'post': second.id, 'parent': parent.id, 'content': 'Cross post'},
        format='json',
    )

    assert response.status_code == 400
    assert Comment.objects.count() == 1


@pytest.mark.django_db
def test_only_role_admin_can_mutate_tags_or_pin_posts(
    api_client, forum_users, forum_posts
):
    owner, _, teacher, admin = forum_users
    first, _ = forum_posts
    api_client.force_authenticate(owner)
    learner_tag = api_client.post(
        '/api/forum/tags/',
        {'name': 'Security', 'slug': 'security', 'color': '#112233'},
        format='json',
    )
    api_client.force_authenticate(teacher)
    teacher_pin = api_client.post(f'/api/forum/posts/{first.id}/pin/')
    api_client.force_authenticate(admin)
    admin_tag = api_client.post(
        '/api/forum/tags/',
        {'name': 'Security', 'slug': 'security', 'color': '#112233'},
        format='json',
    )
    admin_pin = api_client.post(f'/api/forum/posts/{first.id}/pin/')

    assert learner_tag.status_code == 403
    assert teacher_pin.status_code == 403
    assert admin_tag.status_code == 201
    assert admin_pin.status_code == 200
    first.refresh_from_db()
    assert first.is_pinned is True


@pytest.mark.django_db
def test_invalid_reaction_is_rejected_without_database_write(
    api_client, forum_users, forum_posts
):
    owner, _, _, _ = forum_users
    first, _ = forum_posts
    api_client.force_authenticate(owner)

    response = api_client.post(
        f'/api/forum/posts/{first.id}/react/',
        {'reaction_type': 'not-a-reaction'},
        format='json',
    )

    assert response.status_code == 400
    assert Reaction.objects.count() == 0


@pytest.mark.django_db
def test_custom_report_target_and_status_cannot_be_forged(
    api_client, forum_users, forum_posts
):
    owner, _, _, _ = forum_users
    first, second = forum_posts
    api_client.force_authenticate(owner)

    response = api_client.post(
        f'/api/forum/posts/{first.id}/report/',
        {
            'reason': 'spam',
            'description': 'Nội dung spam',
            'post': second.id,
            'status': 'resolved',
        },
        format='json',
    )

    assert response.status_code == 201
    report = Report.objects.get()
    assert report.reporter == owner
    assert report.post == first
    assert report.comment is None
    assert report.status == 'pending'
    duplicate = api_client.post(
        f'/api/forum/posts/{first.id}/report/',
        {'reason': 'other'},
        format='json',
    )
    assert duplicate.status_code == 409
    assert Report.objects.count() == 1


@pytest.mark.django_db
def test_general_report_requires_exactly_one_target_and_admin_list(
    api_client, forum_users, forum_posts
):
    owner, _, _, admin = forum_users
    first, second = forum_posts
    api_client.force_authenticate(owner)

    invalid = api_client.post(
        '/api/forum/reports/',
        {'reason': 'other', 'post': first.id, 'comment': None},
        format='json',
    )
    # First payload is valid and proves learner create; second has two targets.
    assert invalid.status_code == 201
    comment = Comment.objects.create(post=second, author=owner, content='Comment')
    two_targets = api_client.post(
        '/api/forum/reports/',
        {'reason': 'spam', 'post': second.id, 'comment': comment.id},
        format='json',
    )
    learner_list = api_client.get('/api/forum/reports/')
    api_client.force_authenticate(admin)
    admin_list = api_client.get('/api/forum/reports/')

    assert two_targets.status_code == 400
    assert learner_list.status_code == 403
    assert admin_list.status_code == 200


@pytest.mark.django_db
def test_follow_target_is_validated(api_client, forum_users):
    owner, _, _, _ = forum_users
    api_client.force_authenticate(owner)

    malformed = api_client.post(
        '/api/forum/follows/toggle/', {'user_id': 'abc'}, format='json'
    )
    missing = api_client.post(
        '/api/forum/follows/toggle/', {'user_id': 999999}, format='json'
    )

    assert malformed.status_code == 400
    assert missing.status_code == 404
