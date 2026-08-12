def test_home_page_renders(app):
    client = app.test_client()
    resp = client.get('/')
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert 'Atkore Compliance Certification Portal' in text
    assert 'My Certifications' in text
    assert 'Create Certification' in text
    assert 'Reports' in text
    assert 'Administration' in text
