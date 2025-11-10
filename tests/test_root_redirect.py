def test_root_redirect(client):
    """GET / should redirect to /search/"""
    resp = client.get('/', follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers.get('Location') == '/search/'
