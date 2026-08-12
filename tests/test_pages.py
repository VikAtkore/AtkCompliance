def test_placeholder_pages_render(app):
    client = app.test_client()
    for path, title in [('/certifications', 'My Certifications'), ('/reports', 'Reports'), ('/admin', 'Administration')]:
        resp = client.get(path)
        assert resp.status_code == 200
        text = resp.get_data(as_text=True)
        assert title in text
        assert 'Coming Soon' in text
        assert 'Back to Dashboard' in text
