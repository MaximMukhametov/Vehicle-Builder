from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

import settings
from db.models import Base, Feature, Group, Function, Component, Vehicle, FunctionComponent


async def pg_context(app):
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    app['db'] = engine
    await add_initial_data(engine)

    yield

    await app['db'].dispose()


async def add_initial_data(engine):
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        async with session.begin():
            group1 = Group(name="Group1")
            group2 = Group(name="Group2", is_set=True, parent=group1)
            group3 = Group(name="Group3", parent=group2)
            group4 = Group(name="Group4")

            feature1 = Feature(name="Feature1", group=group1)
            feature2 = Feature(name="Feature2", group=group3)
            feature3 = Feature(name="Feature3", group=group4)
            feature4 = Feature(name="Feature4", group=group2)
            feature5 = Feature(name="Feature5", group=group2)

            function1 = Function(name="Function1", feature=feature1)
            function2 = Function(name="Function2", feature=feature1)
            function3 = Function(name="Function3", feature=feature1)
            function4 = Function(name="Function4", feature=feature2)
            function5 = Function(name="Function5", feature=feature3)
            function6 = Function(name="Function6", feature=feature3)
            function7 = Function(name="Function7", feature=feature3)

            component1 = Component(
                name="Component1",
                cad_model="cad_model",
                vendor_code="vendor_code",
                provider_id=1,
                price=Decimal("10.50"),
                weight=Decimal("500.15"),
            )

            component2 = Component(
                name="Component2",
                cad_model="cad_model",
                vendor_code="vendor_code",
                provider_id=1,
                price=Decimal("10.50"),
                weight=Decimal("500.15"),
            )

            vehicle = Vehicle(name="Vehicle1", range=400, features=[feature1, feature2, feature3])

            function_component = FunctionComponent(
                vehicle=vehicle, function=function1, component=component1
            )

            session.add_all(
                [
                    group1, group2, group3, group4, feature1, feature2, feature3,
                    feature4, feature5, component1, component2,
                    function1, function2, function3, function4, function5,
                    function6, function7, vehicle, function_component,
                ]
            )

        await session.commit()
