"""
E2E (сценарные) тесты — полные пользовательские сценарии

Проверяют сложные флоу (*потоки? - я не знаю как перевести*) согласно УСЛОВИЯМ задачи:
1. Полный цикл жизни PR: create → assign reviewers → merge
2. Деактивация пользователя влияет на новые PR
3. Переназначение из команды заменяемого ревьювера
"""

from httpx import AsyncClient


class TestFullPRLifecycle:
    """
    Полный цикл жизни Pull Request
    """

    async def test_pr_lifecycle_create_merge(self, client: AsyncClient):
        """
        Сценарий: создание команды -> создание PR -> проверка ревьюверов -> merge
        """
        # 1. Создаём команду
        team_response = await client.post(
            "/team/add",
            json={
                "team_name": "platform",
                "members": [
                    {"user_id": "p1", "username": "Pavel", "is_active": True},
                    {"user_id": "p2", "username": "Polina", "is_active": True},
                    {"user_id": "p3", "username": "Peter", "is_active": True},
                ],
            },
        )
        assert team_response.status_code == 201

        # 2. создаём PR
        pr_response = await client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": "pr-lifecycle",
                "pull_request_name": "Lifecycle test",
                "author_id": "p1",
            },
        )
        assert pr_response.status_code == 201

        pr = pr_response.json()["pr"]
        assert pr["status"] == "OPEN"
        assert len(pr["assigned_reviewers"]) == 2
        assert "p1" not in pr["assigned_reviewers"]  # автор не ревьювер

        # 3. проверяем что ревьюверы видят этот PR
        reviewer_id = pr["assigned_reviewers"][0]
        review_response = await client.get("/users/getReview", params={"user_id": reviewer_id})
        assert review_response.status_code == 200

        user_prs = review_response.json()["pull_requests"]
        assert len(user_prs) == 1
        assert user_prs[0]["pull_request_id"] == "pr-lifecycle"

        # 4. мерджим PR
        merge_response = await client.post(
            "/pullRequest/merge", json={"pull_request_id": "pr-lifecycle"}
        )
        assert merge_response.status_code == 200

        merged_pr = merge_response.json()["pr"]
        assert merged_pr["status"] == "MERGED"
        assert merged_pr["mergedAt"] is not None
        # ревьюверы сохранились
        assert merged_pr["assigned_reviewers"] == pr["assigned_reviewers"]


class TestDeactivationAffectsNewPRs:
    """
    Деактивация пользователя влияет на назначение в новые PR
    """

    async def test_deactivated_user_not_assigned_to_new_prs(self, client: AsyncClient):
        """
        Сценарий:
        1. Создаём команду с 3 активными участниками
        2. Деактивируем одного
        3. Создаём PR — деактивированный НЕ должен быть назначен
        """
        # 1. создаём команду
        await client.post(
            "/team/add",
            json={
                "team_name": "deactivation_test",
                "members": [
                    {"user_id": "d1", "username": "Active1", "is_active": True},
                    {"user_id": "d2", "username": "WillDeactivate", "is_active": True},
                    {"user_id": "d3", "username": "Active2", "is_active": True},
                ],
            },
        )

        # 2. деактивируем d2
        deactivate_response = await client.post(
            "/users/setIsActive",
            json={"user_id": "d2", "is_active": False},
        )
        assert deactivate_response.status_code == 200
        assert deactivate_response.json()["user"]["is_active"] is False

        # 3. создаём PR от d1
        pr_response = await client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": "pr-after-deactivation",
                "pull_request_name": "After deactivation",
                "author_id": "d1",
            },
        )
        assert pr_response.status_code == 201

        pr = pr_response.json()["pr"]
        # только d3 может быть ревьювером (d1 — автор, d2 — неактивен)
        assert pr["assigned_reviewers"] == ["d3"]
        assert "d2" not in pr["assigned_reviewers"]


class TestReassignFromReviewerTeam:
    """
    Переназначение берёт кандидата из команды ЗАМЕНЯЕМОГО ревьювера

    По условию (см. task.md):
    ---
    Переназначение заменяет одного ревьювера на случайного активного участника
    из команды заменяемого ревьювера
    ---
    """

    async def test_reassign_from_same_team(self, client: AsyncClient):
        """
        - Проверяем что reassign выбирает нового ревьювера из той же команды

        - В текущей реализации ревьюверы всегда из команды автора

        - При reassign новый ревьювер также берётся из команды заменяемого
        (которая совпадает с командой автора)

        -> Важно: автор PR МОЖЕТ стать ревьювером при reassign,
        т.к. условие не запрещает это явно
        """
        # создаём команду с 4 участниками
        await client.post(
            "/team/add",
            json={
                "team_name": "reassign_team",
                "members": [
                    {"user_id": "r1", "username": "Author", "is_active": True},
                    {"user_id": "r2", "username": "Reviewer1", "is_active": True},
                    {"user_id": "r3", "username": "Reviewer2", "is_active": True},
                    {"user_id": "r4", "username": "Candidate", "is_active": True},
                ],
            },
        )

        # создаём PR — назначаются 2 из r2, r3, r4 (автор r1 исключён при создании)
        pr_response = await client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": "pr-reassign-team",
                "pull_request_name": "Reassign team test",
                "author_id": "r1",
            },
        )

        pr = pr_response.json()["pr"]

        # переназначаем первого ревьювера
        old_reviewer = pr["assigned_reviewers"][0]
        other_reviewer = pr["assigned_reviewers"][1] if len(pr["assigned_reviewers"]) > 1 else None

        reassign_response = await client.post(
            "/pullRequest/reassign",
            json={"pull_request_id": "pr-reassign-team", "old_user_id": old_reviewer},
        )

        assert reassign_response.status_code == 200
        new_reviewer = reassign_response.json()["replaced_by"]

        # новый ревьювер должен быть из той же команды (r1, r2, r3, r4)
        # -> примечание: автор r1 МОЖЕТ стать ревьювером при reassign —
        # условие не запрещает это, говорит только "из команды заменяемого"
        assert new_reviewer in {"r1", "r2", "r3", "r4"}
        # не должен быть тем же, кого заменили
        assert new_reviewer != old_reviewer
        # не должен быть текущим вторым ревьювером (исключаем дубликаты)
        if other_reviewer:
            assert new_reviewer != other_reviewer


class TestEdgeCases:
    """
    Пограничные случаи
    """

    async def test_team_with_all_inactive_except_author(self, client: AsyncClient):
        """
        - Команда где все кроме автора неактивны
        - PR создаётся без ревьюверов
        """
        await client.post(
            "/team/add",
            json={
                "team_name": "mostly_inactive",
                "members": [
                    {"user_id": "mi1", "username": "Author", "is_active": True},
                    {"user_id": "mi2", "username": "Inactive1", "is_active": False},
                    {"user_id": "mi3", "username": "Inactive2", "is_active": False},
                ],
            },
        )

        pr_response = await client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": "pr-no-reviewers",
                "pull_request_name": "No reviewers available",
                "author_id": "mi1",
            },
        )

        assert pr_response.status_code == 201
        pr = pr_response.json()["pr"]
        assert pr["assigned_reviewers"] == []

    async def test_multiple_prs_same_team(self, client: AsyncClient):
        """
        - Несколько PR от разных авторов одной команды
        - Каждый PR получает своих ревьюверов
        """
        await client.post(
            "/team/add",
            json={
                "team_name": "multi_pr_team",
                "members": [
                    {"user_id": "m1", "username": "Member1", "is_active": True},
                    {"user_id": "m2", "username": "Member2", "is_active": True},
                    {"user_id": "m3", "username": "Member3", "is_active": True},
                ],
            },
        )

        # PR от m1
        pr1_response = await client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": "pr-multi-1",
                "pull_request_name": "First PR",
                "author_id": "m1",
            },
        )
        pr1 = pr1_response.json()["pr"]
        assert "m1" not in pr1["assigned_reviewers"]

        # PR от m2
        pr2_response = await client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": "pr-multi-2",
                "pull_request_name": "Second PR",
                "author_id": "m2",
            },
        )
        pr2 = pr2_response.json()["pr"]
        assert "m2" not in pr2["assigned_reviewers"]

        # проверяем что m1 может быть ревьювером в pr2 (он не автор там)
        # и m2 может быть ревьювером в pr1
        assert len(pr1["assigned_reviewers"]) == 2
        assert len(pr2["assigned_reviewers"]) == 2
