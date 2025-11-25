"""
Интеграционные тесты для API PR-ов (/pullRequest/*)

Тестируемые эндпойнты по OpenAPI:
- POST /pullRequest/create — создание PR с автоматическим назначением ревьюверов
- POST /pullRequest/merge — merge PR (идемпотентная операция)
- POST /pullRequest/reassign — переназначение ревьювера
"""

from httpx import AsyncClient


class TestPRCreate:
    """
    Тесты POST /pullRequest/create
    """

    async def test_create_pr_success(self, client: AsyncClient, sample_team_data: dict):
        """
        Успешное создание PR — 201, назначены до 2 ревьюверов
        """
        # создаём команду с 3 участниками
        await client.post("/team/add", json=sample_team_data)

        # создаём PR
        response = await client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": "pr-1001",
                "pull_request_name": "Add search",
                "author_id": "u1",
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert "pr" in data
        pr = data["pr"]
        assert pr["pull_request_id"] == "pr-1001"
        assert pr["pull_request_name"] == "Add search"
        assert pr["author_id"] == "u1"
        assert pr["status"] == "OPEN"

        # должны быть assigned_reviewers
        assert "assigned_reviewers" in pr
        # до 2 ревьюверов из команды (3 участника - 1 автор = 2 кандидата)
        assert len(pr["assigned_reviewers"]) == 2

        # автор НЕ должен быть в ревьюверах
        assert "u1" not in pr["assigned_reviewers"]

        # ревьюверы должны быть из команды
        for reviewer_id in pr["assigned_reviewers"]:
            assert reviewer_id in ["u2", "u3"]

    async def test_create_pr_with_one_candidate(self, client: AsyncClient, sample_small_team: dict):
        """
        Создание PR в команде с 1 участником (он же автор)

        По условию: если кандидатов меньше 2, назначается доступное количество (0/1)
        """
        # команда с 1 участником
        await client.post("/team/add", json=sample_small_team)

        # создаём PR (автор = единственный участник)
        response = await client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": "pr-solo",
                "pull_request_name": "Solo PR",
                "author_id": "s1",
            },
        )

        assert response.status_code == 201
        pr = response.json()["pr"]

        # 0 ревьюверов (нет других участников)
        assert pr["assigned_reviewers"] == []

    async def test_create_pr_skips_inactive_reviewers(
        self, client: AsyncClient, sample_team_with_inactive: dict
    ):
        """
        Неактивные пользователи НЕ назначаются ревьюверами
        """
        # команда: f1 (active), f2 (inactive), f3 (active)
        await client.post("/team/add", json=sample_team_with_inactive)

        # создаём PR от f1
        response = await client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": "pr-front",
                "pull_request_name": "Frontend PR",
                "author_id": "f1",
            },
        )

        assert response.status_code == 201
        pr = response.json()["pr"]

        # должен быть только f3 (f2 неактивен, f1 — автор)
        assert len(pr["assigned_reviewers"]) == 1
        assert pr["assigned_reviewers"][0] == "f3"
        assert "f2" not in pr["assigned_reviewers"]  # неактивный

    async def test_create_pr_duplicate_returns_409(
        self, client: AsyncClient, sample_team_data: dict
    ):
        """
        Повторное создание PR с тем же ID — 409 PR_EXISTS\
        """
        await client.post("/team/add", json=sample_team_data)

        pr_data = {
            "pull_request_id": "pr-dup",
            "pull_request_name": "Duplicate PR",
            "author_id": "u1",
        }

        # первый раз — ок
        response1 = await client.post("/pullRequest/create", json=pr_data)
        assert response1.status_code == 201

        # второй раз — ошибка
        response2 = await client.post("/pullRequest/create", json=pr_data)

        assert response2.status_code == 409
        data = response2.json()
        assert data["detail"]["error"]["code"] == "PR_EXISTS"

    async def test_create_pr_author_not_found_returns_404(self, client: AsyncClient):
        """
        Создание PR с несуществующим автором — 404 NOT_FOUND
        """
        response = await client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": "pr-ghost",
                "pull_request_name": "Ghost PR",
                "author_id": "nonexistent",
            },
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"]["code"] == "NOT_FOUND"


class TestPRMerge:
    """
    Тесты POST /pullRequest/merge
    """

    async def test_merge_pr_success(self, client: AsyncClient, sample_team_data: dict):
        """
        Успешный merge PR — 200, статус MERGED
        """
        await client.post("/team/add", json=sample_team_data)

        # создаём PR
        await client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": "pr-merge",
                "pull_request_name": "Merge me",
                "author_id": "u1",
            },
        )

        # мерджим
        response = await client.post("/pullRequest/merge", json={"pull_request_id": "pr-merge"})

        assert response.status_code == 200
        pr = response.json()["pr"]

        assert pr["status"] == "MERGED"
        assert pr["mergedAt"] is not None
        assert "assigned_reviewers" in pr

    async def test_merge_pr_idempotent(self, client: AsyncClient, sample_team_data: dict):
        """
        Повторный merge — идемпотентность

        - По условию: повторный вызов не приводит к ошибке и возвращает актуальное состояние.
        """
        await client.post("/team/add", json=sample_team_data)

        await client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": "pr-idemp",
                "pull_request_name": "Idempotent",
                "author_id": "u1",
            },
        )

        # первый merge
        response1 = await client.post("/pullRequest/merge", json={"pull_request_id": "pr-idemp"})
        assert response1.status_code == 200
        merged_at_1 = response1.json()["pr"]["mergedAt"]
        assert merged_at_1 is not None

        # второй merge — должен вернуть то же самое, без ошибки
        response2 = await client.post("/pullRequest/merge", json={"pull_request_id": "pr-idemp"})

        assert response2.status_code == 200
        pr = response2.json()["pr"]
        assert pr["status"] == "MERGED"
        # mergedAt должен быть тот же (идемпотентность — не обновляется при повторном вызове)
        # сравниваем без учёта timezone suffix
        merged_at_2 = pr["mergedAt"]
        assert merged_at_1.rstrip("Z") == merged_at_2.rstrip("Z")

    async def test_merge_pr_not_found_returns_404(self, client: AsyncClient):
        """Merge несуществующего PR — 404."""
        response = await client.post("/pullRequest/merge", json={"pull_request_id": "nonexistent"})

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"]["code"] == "NOT_FOUND"


class TestPRReassign:
    """
    Тесты POST /pullRequest/reassign
    """

    async def test_reassign_success(self, client: AsyncClient):
        """
        Успешное переназначение ревьювера:
        - Создаём команду из 4 человек, чтобы был кандидат для замены
        """
        # команда с 4 участниками
        team_data = {
            "team_name": "big_team",
            "members": [
                {"user_id": "b1", "username": "One", "is_active": True},
                {"user_id": "b2", "username": "Two", "is_active": True},
                {"user_id": "b3", "username": "Three", "is_active": True},
                {"user_id": "b4", "username": "Four", "is_active": True},
            ],
        }
        await client.post("/team/add", json=team_data)

        # создаём PR (будет назначено 2 ревьювера из b2, b3, b4)
        create_response = await client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": "pr-reassign",
                "pull_request_name": "Reassign test",
                "author_id": "b1",
            },
        )

        pr = create_response.json()["pr"]
        original_reviewers = pr["assigned_reviewers"]
        old_reviewer = original_reviewers[0]

        # переназначаем
        response = await client.post(
            "/pullRequest/reassign",
            json={"pull_request_id": "pr-reassign", "old_user_id": old_reviewer},
        )

        assert response.status_code == 200
        data = response.json()

        assert "pr" in data
        assert "replaced_by" in data

        new_reviewer = data["replaced_by"]
        new_reviewers = data["pr"]["assigned_reviewers"]

        # старый ревьювер заменён
        assert old_reviewer not in new_reviewers
        # новый ревьювер добавлен
        assert new_reviewer in new_reviewers
        # всё ещё 2 ревьювера
        assert len(new_reviewers) == 2

    async def test_reassign_on_merged_pr_returns_409(
        self, client: AsyncClient, sample_team_data: dict
    ):
        """
        Переназначение на merged PR — 409 PR_MERGED.

        По условию: после MERGED менять список ревьюверов нельзя.
        """
        await client.post("/team/add", json=sample_team_data)

        # создаём и мерджим PR
        await client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": "pr-merged",
                "pull_request_name": "Already merged",
                "author_id": "u1",
            },
        )
        await client.post("/pullRequest/merge", json={"pull_request_id": "pr-merged"})

        # пытаемся переназначить
        response = await client.post(
            "/pullRequest/reassign",
            json={"pull_request_id": "pr-merged", "old_user_id": "u2"},
        )

        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["error"]["code"] == "PR_MERGED"

    async def test_reassign_not_assigned_reviewer_returns_409(
        self, client: AsyncClient, sample_team_data: dict
    ):
        """
        Переназначение пользователя, который не является ревьювером — 409 NOT_ASSIGNED
        """
        await client.post("/team/add", json=sample_team_data)

        # создаём PR
        await client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": "pr-not-assigned",
                "pull_request_name": "Not assigned test",
                "author_id": "u1",
            },
        )

        # ищем пользователя, который НЕ ревьювер (u1 — автор, остальные — ревьюверы)
        # автор u1 точно не ревьювер
        response = await client.post(
            "/pullRequest/reassign",
            json={"pull_request_id": "pr-not-assigned", "old_user_id": "u1"},
        )

        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["error"]["code"] == "NOT_ASSIGNED"

    async def test_reassign_no_candidate_returns_409(self, client: AsyncClient):
        """
        Переназначение когда нет кандидатов — 409 NO_CANDIDATE

        - Команда из 2 человек: автор (неактивен после создания PR) + 1 ревьювер
        - После деактивации автора, некому заменять ревьювера
        """
        team_data = {
            "team_name": "tiny",
            "members": [
                {"user_id": "t1", "username": "Tiny1", "is_active": True},
                {"user_id": "t2", "username": "Tiny2", "is_active": True},
            ],
        }
        await client.post("/team/add", json=team_data)

        # PR от t1, ревьювер = t2
        await client.post(
            "/pullRequest/create",
            json={
                "pull_request_id": "pr-tiny",
                "pull_request_name": "Tiny PR",
                "author_id": "t1",
            },
        )

        # деактивируем t1 (автора) — теперь при reassign t2 некого выбрать
        await client.post("/users/setIsActive", json={"user_id": "t1", "is_active": False})

        # пытаемся переназначить t2 — но t1 неактивен, кандидатов нет
        response = await client.post(
            "/pullRequest/reassign",
            json={"pull_request_id": "pr-tiny", "old_user_id": "t2"},
        )

        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["error"]["code"] == "NO_CANDIDATE"

    async def test_reassign_pr_not_found_returns_404(self, client: AsyncClient):
        """
        Переназначение на несуществующем PR — 404 NOT_FOUND
        """
        response = await client.post(
            "/pullRequest/reassign",
            json={"pull_request_id": "nonexistent", "old_user_id": "u1"},
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"]["code"] == "NOT_FOUND"
