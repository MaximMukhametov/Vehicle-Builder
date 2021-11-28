from os import environ

from sqlalchemy import (
    MetaData, Table, Column, ForeignKey,
    Integer, String, Date, Boolean
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import sessionmaker


DB_USER = environ.get("DB_USER", "postgres")
DB_PASSWORD = environ.get("DB_PASSWORD", "password")
DB_HOST = environ.get("DB_HOST", "localhost")
DB_NAME = "postgres"
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
)

Base = declarative_base()

meta = MetaData()


class Feature(Base):
    __tablename__ = 'feature'

    id = Column('id', Integer, primary_key=True)
    name = Column('name', String(200), nullable=False)
    group_id = Column(
        'group_id',
        Integer,
        ForeignKey('group.id', ondelete='CASCADE'))
    group = relationship("Group", backref="feature")


class Group(Base):
    __tablename__ = "group"

    id = Column('id', Integer, primary_key=True)
    name = Column('name', String(200), nullable=False)
    parent_id = Column(
        'group_id',
        Integer,
        ForeignKey('group.id', ondelete='CASCADE'))
    parent = relationship("Group", backref="group", remote_side="Group.id")
    # features = relationship("Feature", backref="feature")


async def pg_context(app):
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    app['db'] = engine
    await add_initial_data(engine)

    yield

    await app['db'].dispose()


async def add_initial_data(engine):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    async with async_session() as session:
        async with session.begin():
            session.add_all(
                [
                    Group(feature=[Feature(name="Feature1"), Feature(name="Feature2")], name="Group1", group=[Group(feature=[Feature(name="Feature33"), Feature(name="Feature33")], name="Group33")]),
                    Group(feature=[Feature(name="Feature3"), Feature(name="Feature5")], name="Group2"),
                    Group(feature=[Feature(name="Feature4"), Feature(name="Feature6")], name="Group3"),
                ]
            )

        # for relationship loading, eager loading should be applied.
        stmt = select(Group).options(selectinload(Group.feature))

        # AsyncSession.execute() is used for 2.0 style ORM execution
        # (same as the synchronous API).
        result = await session.execute(stmt)

        # result is a buffered Result object.
        for a1 in result.scalars():
            print(a1)
            for b1 in a1.feature:
                print(b1)
                print(b1)
        #
        # # for streaming ORM results, AsyncSession.stream() may be used.
        # result = await session.stream(stmt)
        #
        # # result is a streaming AsyncResult object.
        # async for a1 in result.scalars():
        #     print(a1)
        #     for b1 in a1.bs:
        #         print(b1)
        #
        # result = await session.execute(select(A).order_by(A.id))

        # a1 = result.scalars().first()
        #
        # a1.data = "new data"

        await session.commit()