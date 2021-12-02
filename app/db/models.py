from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Numeric,
    Boolean,
    Table,
    UniqueConstraint,
    inspect
)
from sqlalchemy.orm import backref, declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Feature(Base):
    """Feature is a container for functions.

    It needed  for the convenience of initial formation requirements for the vehicle.
    All vehicles are configured by features.

    """
    __tablename__ = 'feature'

    id = Column('id', Integer, primary_key=True)
    name = Column('name', String(200), nullable=False, unique=True)
    group_id = Column('group_id', Integer, ForeignKey('group.id', ondelete='CASCADE'))

    group = relationship("Group", backref="features")


class Group(Base):
    """Group is a container for other groups and features.

    A group can be a Set. The only difference of Set is that
    you can select (add to the Configuration) only one Feature. Sets can
    be within a Group or Subgroup.

    """
    __tablename__ = "group"

    id = Column('id', Integer, primary_key=True)
    name = Column('name', String(200), nullable=False, unique=True)
    is_set = Column("is_set", Boolean(), server_default="false")
    group_id = Column('group_id', Integer, ForeignKey('group.id', ondelete='CASCADE'))

    subgroups = relationship("Group", backref=backref('parent', remote_side=[id]))


class Component(Base):
    """The technical unit of supply required for the implementation of a specific function."""
    __tablename__ = 'component'

    id = Column('id', Integer, primary_key=True)
    name = Column('name', String(200), nullable=False, unique=True)
    cad_model = Column('cad_model', String(200), nullable=False)
    vendor_code = Column('vendor_code', String(200), nullable=False)
    provider_id = Column('provider_id', Integer)
    price = Column("price", Numeric(10, 2), nullable=False)
    weight = Column("weight", Numeric(10, 3), nullable=False)


class Function(Base):
    """Function is the basic vehicle unit.

    Indicates an entity to which in the configuration of the vehicle is bound by the Components.

    """
    __tablename__ = 'function'

    id = Column('id', Integer, primary_key=True)
    name = Column('name', String(200), nullable=False, unique=True)
    feature_id = Column('feature_id', Integer, ForeignKey('feature.id', ondelete='CASCADE'))

    feature = relationship("Feature", backref="functions")


# The association table between vehicles and features.
vehicle_feature = Table(
    'vehicle_feature', Base.metadata,
    Column('vehicle_id', ForeignKey('vehicle.id'), primary_key=True),
    Column('feature_id', ForeignKey('feature.id'), primary_key=True)
)


class Vehicle(Base):
    """Vehicle model containing all data about it."""
    __tablename__ = 'vehicle'

    id = Column('id', Integer, primary_key=True)
    name = Column('name', String(200), nullable=False, unique=True)
    range = Column('range', Integer, nullable=False)

    features = relationship("Feature", secondary=vehicle_feature, backref="vehicles")

    def to_dict(self) -> dict:
        """Return dict with vehicle data."""
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class FunctionComponent(Base):
    """Association Object to tie particular vehicle, function, and component."""
    __tablename__ = "function_component"

    id = Column('id', Integer, primary_key=True)
    vehicle_id = Column('vehicle_id', Integer, ForeignKey('vehicle.id', ondelete='CASCADE'))
    function_id = Column('function_id', Integer, ForeignKey('function.id', ondelete='CASCADE'))
    component_id = Column('component_id', Integer, ForeignKey('component.id', ondelete='CASCADE'))

    __table_args__ = (UniqueConstraint(vehicle_id, function_id, component_id),)

    vehicle = relationship("Vehicle", backref="function_components")
    function = relationship("Function", backref="function_components")
    component = relationship("Component", backref="function_components")
