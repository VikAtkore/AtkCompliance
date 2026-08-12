import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("ACC_ENV", "testing")

from app import create_app          # noqa: E402
from app.extensions import db as _db  # noqa: E402
from app.models import (Role, CertificationPeriod, EntityMaster, AppUser,  # noqa: E402
                        UserRole)
from app.constants import RoleName  # noqa: E402


@pytest.fixture()
def app():
    application = create_app("testing")
    with application.app_context():
        _db.create_all()
        for name in RoleName:
            _db.session.add(Role(RoleName=name.value, Description=name.value))
        _db.session.commit()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def db(app):
    return _db


@pytest.fixture()
def open_period(db):
    from datetime import date
    period = CertificationPeriod(QuarterLabel="Q1 2026", FiscalYear=2026,
                                 QuarterNumber=1, StartDate=date(2026, 1, 1),
                                 DueDate=date(2026, 2, 15), IsOpen=True, Enable404=False)
    db.session.add(period)
    db.session.commit()
    return period


@pytest.fixture()
def group2_entity(db):
    entity = EntityMaster(Title="Atkore Test Entity", EntityNumber="1001",
                          Region="North America", BusinessSegment="Electrical",
                          BusinessUnit="Conduit", Location="Mokena",
                          IsGroup1=False, IsGroup2=True)
    db.session.add(entity)
    db.session.commit()
    return entity
