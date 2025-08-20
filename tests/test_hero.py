import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hero import Hero

heroes_data = [
    Hero(name="hero1", intelligence=10, strength=10, speed=120, power=175),
    Hero(name="hero2", intelligence=20, strength=20, speed=120, power=275),
    Hero(name="hero3", intelligence=30, strength=30, speed=130, power=375),
    Hero(name="hero4", intelligence=40, strength=40, speed=140, power=475),
    Hero(name="hero5", intelligence=50, strength=50, speed=150, power=575),
    Hero(name="hero6", intelligence=60, strength=60, speed=160, power=675),
    Hero(name="hero7", intelligence=70, strength=70, speed=170, power=775),
    Hero(name="hero8", intelligence=80, strength=80, speed=180, power=875),
    Hero(name="hero9", intelligence=90, strength=90, speed=190, power=975),
    Hero(name="hero10", intelligence=100, strength=100, speed=200, power=1075),
]


@pytest.mark.asyncio
class TestHero:

    async def test_create_hero(self, session_db: AsyncSession):
        """Создание героя в БД"""
        hero = Hero(name="spiderman", intelligence=90, strength=80, speed=70, power=85)
        session_db.add(hero)
        await session_db.commit()

        result = await session_db.execute(select(Hero).where(Hero.name == "spiderman"))
        hero_from_db = result.scalars().first()

        assert hero_from_db is not None
        assert hero_from_db.name == "spiderman"

    async def test_add_hero(
        self, mocker, client: AsyncClient, session_db: AsyncSession
    ):
        """Добавление героя по имени"""
        hero_data = {"name": "batman"}

        mock_data = (
            "batman",
            {
                "intelligence": 90,
                "strength": 80,
                "speed": 70,
                "power": 85,
            },
        )
        mocker.patch(
            "app.api.endpoints.hero.fetch_hero_by_name", return_value=mock_data
        )
        response = await client.post("/hero/", json=hero_data)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "batman"
        assert "intelligence" in data
        assert "strength" in data
        assert "speed" in data
        assert "power" in data

        result = await session_db.execute(select(Hero).where(Hero.name == "batman"))
        hero = result.scalars().first()
        assert hero is not None
        assert hero.name == "batman"

    async def test_add_hero_not_found(
        self, mocker, client: AsyncClient, session_db: AsyncSession
    ):
        """При добавлении имя героя неизвестно"""
        hero_data = {"name": "unkown"}
        mock_data = (None, None)

        # Мокаем внешний вызов, чтобы вернуть None — герой не найден
        mocker.patch(
            "app.api.endpoints.hero.fetch_hero_by_name", return_value=mock_data
        )

        response = await client.post("/hero/", json=hero_data)
        assert response.status_code == 404

        result = await session_db.execute(
            select(Hero).where(Hero.name == "unknown_hero")
        )
        hero = result.scalars().first()
        assert hero is None

    async def test_add_hero_duplicate(
        self, mocker, client: AsyncClient, session_db: AsyncSession
    ):
        """Проверяем дубдирование героя при добавлении"""
        hero_data = {"name": "ironman"}

        mock_data = (
            "ironman",
            {
                "intelligence": 95,
                "strength": 85,
                "speed": 75,
                "power": 90,
            },
        )
        mocker.patch(
            "app.api.endpoints.hero.fetch_hero_by_name", return_value=mock_data
        )

        response_1 = await client.post("/hero/", json=hero_data)
        assert response_1.status_code == 200

        response_2 = await client.post("/hero/", json=hero_data)
        assert response_2.status_code == 200

        result = await session_db.execute(select(Hero).where(Hero.name == "ironman"))
        heroes = result.scalars().all()
        assert len(heroes) == 1

    async def test_add_hero_invalid_data(self, client: AsyncClient):
        """Если передали пустое значение в имени"""
        hero_data = {"name": ""}

        response = await client.post("/hero/", json=hero_data)
        assert response.status_code == 422

        response2 = await client.post("/hero/", json={})
        assert response2.status_code == 422

        response3 = await client.post("/hero/", json={"name": 123})
        assert response3.status_code == 422

    async def test_get_all_heroes(self, client: AsyncClient, session_db: AsyncSession):
        """Если никакие фильтры не переданы, то возвращаем всем героев"""
        hero1 = Hero(name="batman", intelligence=90, strength=80, speed=70, power=85)
        hero2 = Hero(
            name="superman", intelligence=95, strength=100, speed=95, power=100
        )
        session_db.add_all([hero1, hero2])
        await session_db.commit()

        response = await client.get("/hero/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["heroes"]) == 2
        assert data["filters_no_results"] is None

    async def test_get_heroes_filter_by_name(
        self, client: AsyncClient, session_db: AsyncSession
    ):
        """Делаем фильтрацию по имени"""
        hero = Hero(name="ironman", intelligence=88, strength=85, speed=80, power=90)
        session_db.add(hero)
        await session_db.commit()

        response = await client.get("/hero/", params={"name": "ironman"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["heroes"]) == 1
        assert data["heroes"][0]["name"] == "ironman"

    @pytest.mark.parametrize(
        "params,expected_count",
        [
            ({"strength": 50, "strength_op": "gte"}, 6),  # >= 50
            ({"intelligence": 60, "intelligence_op": "lte"}, 6),  # <= 60
            ({"speed": 180, "speed_op": "eq"}, 1),  # == 180
            ({"power": 500, "power_op": "gte"}, 7),  # >= 500
            (
                {
                    "strength": 50,
                    "strength_op": "gte",
                    "intelligence": 50,
                    "intelligence_op": "gte",
                },
                6,
            ),
            ({"strength": 50, "strength_op": "lte", "speed": 150, "speed_op": "eq"}, 1),
        ],
    )
    async def test_get_heroes_filter_combinations(
        self, client: AsyncClient, session_db: AsyncSession, params, expected_count
    ):
        """Проверяем фильтры"""
        heroes_data = [
            Hero(
                name=f"hero{i}",
                intelligence=10 * i,
                strength=10 * i,
                speed=120 + 10 * i,
                power=175 + 100 * i,
            )
            for i in range(1, 11)
        ]
        session_db.add_all(heroes_data)
        await session_db.commit()

        response = await client.get("/hero/", params=params)

        assert response.status_code == 200, f"Unexpected status {response.status_code}"
        data = response.json().get("heroes")
        assert len(data) == expected_count
