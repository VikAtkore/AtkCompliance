from app.models import AppUser, UserRole
from app.models import Role
from app.extensions import db


def make_user(client, db_session, upn='dev.user@atkore.com'):
    # create AppUser and assign Submitter role
    user = AppUser(UserPrincipalName=upn, DisplayName='Dev User', Email=upn)
    db_session.add(user)
    db_session.flush()
    role = db_session.query(Role).filter(Role.RoleName == 'Submitter').first()
    if role is None:
        role = Role(RoleName='Submitter', Description='Submitter')
        db_session.add(role)
        db_session.flush()
    db_session.add(UserRole(UserId=user.UserId, RoleId=role.RoleId, IsActive=True, GrantedBy='test'))
    db_session.commit()
    # set session user_id
    with client.session_transaction() as sess:
        sess['user_id'] = user.UserId
    return user


def test_save_draft_creates_submission(app):
    client = app.test_client()
    # create user and session
    user = make_user(client, db.session)

    # create period and entity fixtures
    from app.models import CertificationPeriod, EntityMaster
    from datetime import date
    period = CertificationPeriod(QuarterLabel='Q1 2026', FiscalYear=2026, QuarterNumber=1,
                                 StartDate=date(2026,1,1), DueDate=date(2026,2,15), IsOpen=True, Enable404=False)
    db.session.add(period)
    entity = EntityMaster(Title='Test Entity', EntityNumber='9001', Region='NA', BusinessSegment='X', BusinessUnit='Y', Location='Z', IsGroup1=False, IsGroup2=True)
    db.session.add(entity)
    db.session.commit()

    payload = {'entityId': entity.EntityId, 'periodId': period.PeriodId, 'employeeName': 'Tester', 'preparerRole': 'Controller'}
    resp = client.post('/api/submissions', json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    assert 'submissionId' in data
    assert 'lastSavedUtc' in data

    # fetch submission
    sid = data['submissionId']
    resp2 = client.get(f'/api/submissions/{sid}')
    assert resp2.status_code == 200
    s = resp2.get_json()
    assert s['entityId'] == entity.EntityId
    assert s['periodId'] == period.PeriodId
    assert s['employeeName'] == 'Tester'


def test_update_draft_updates_header_and_last_saved(app):
    client = app.test_client()
    user = make_user(client, db.session, upn='another@atkore.com')

    # create period and entity
    from app.models import CertificationPeriod, EntityMaster
    from datetime import date
    period = CertificationPeriod(QuarterLabel='Q2 2026', FiscalYear=2026, QuarterNumber=2,
                                 StartDate=date(2026,4,1), DueDate=date(2026,5,15), IsOpen=True, Enable404=False)
    db.session.add(period)
    entity = EntityMaster(Title='Test Entity 2', EntityNumber='9002', Region='NA', BusinessSegment='X', BusinessUnit='Y', Location='Z', IsGroup1=False, IsGroup2=True)
    db.session.add(entity)
    db.session.commit()

    payload = {'entityId': entity.EntityId, 'periodId': period.PeriodId, 'employeeName': 'Initial', 'preparerRole': 'Controller'}
    resp = client.post('/api/submissions', json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    sid = data['submissionId']

    # patch header
    patch = {'EmployeeName': 'Updated', 'PreparerRole': 'Reviewer'}
    resp2 = client.patch(f'/api/submissions/{sid}', json=patch)
    assert resp2.status_code == 200
    updated = resp2.get_json()
    assert updated['employeeName'] == 'Updated'
    assert updated['preparerRole'] == 'Reviewer'
    assert 'lastSavedUtc' in updated


def test_existing_draft_is_listed(app):
    client = app.test_client()
    user = make_user(client, db.session, upn='list@atkore.com')

    # create period/entity and submission
    from app.models import CertificationPeriod, EntityMaster
    from datetime import date
    period = CertificationPeriod(QuarterLabel='Q3 2026', FiscalYear=2026, QuarterNumber=3,
                                 StartDate=date(2026,7,1), DueDate=date(2026,8,15), IsOpen=True, Enable404=False)
    db.session.add(period)
    entity = EntityMaster(Title='List Entity', EntityNumber='9003', Region='NA', BusinessSegment='X', BusinessUnit='Y', Location='Z', IsGroup1=False, IsGroup2=True)
    db.session.add(entity)
    db.session.commit()

    payload = {'entityId': entity.EntityId, 'periodId': period.PeriodId, 'employeeName': 'Lister', 'preparerRole': 'Controller'}
    resp = client.post('/api/submissions', json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    sid = data['submissionId']

    # list mine and ensure draft is present
    resp2 = client.get('/api/submissions')
    assert resp2.status_code == 200
    items = resp2.get_json()['items']
    matches = [i for i in items if i['submissionId'] == sid]
    assert matches
