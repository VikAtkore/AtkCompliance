def test_certification_wizard_page(app):
    client = app.test_client()
    resp = client.get('/certifications/new')
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert 'Create Certification' in text
    assert 'Select Entity' in text
    assert 'Certification Info' in text
    assert 'Attestation Questions' in text
    assert 'Review' in text
    assert 'Submit' in text
    assert 'Save Draft' in text
