def test_upload_and_download_roundtrip(client):
    content = b"hello encrypted svipr\n" * 1000
    r = client.post("/upload", files={"file": ("test.txt", content)})
    assert r.status_code == 200
    file_id = r.json()["id"]
    assert r.json()["size"] == len(content)

    r2 = client.get(f"/download/{file_id}/raw")   # ← /raw for the stream
    assert r2.status_code == 200
    assert r2.content == content

def test_disk_stores_ciphertext_not_plaintext(client, upload_dir):
    content = b"TOP SECRET PLAINTEXT"
    r = client.post("/upload", files={"file": ("s.txt", content)})
    file_id = r.json()["id"]

    on_disk = (upload_dir / file_id).read_bytes()
    assert content not in on_disk          # plaintext not on disk
    assert len(on_disk) > len(content)     # ciphertext has overhead (nonce/tag)


def test_key_stored_separately(client, upload_dir):
    r = client.post("/upload", files={"file": ("a.txt", b"x")})
    file_id = r.json()["id"]
    assert (upload_dir / "keys" / f"{file_id}.key").exists()


def test_size_limit_returns_413(client, upload_dir):
    big = b"x" * (1024 * 1024 + 100)  # exceeds 1MB
    r = client.post("/upload", files={"file": ("big.bin", big)})
    assert r.status_code == 413
    # no residue
    assert not list(upload_dir.glob("*.part"))


def test_unknown_id_returns_404(client):
    r = client.get("/does-not-exist")
    assert r.status_code == 404

def test_download_page_renders(client):
    content = b"page test"
    r = client.post("/upload", files={"file": ("doc.txt", content)})
    file_id = r.json()["id"]
    page = client.get(f"/download/{file_id}")
    assert page.status_code == 200
    assert "doc.txt" in page.text
    assert f"/download/{file_id}/raw" in page.text

def test_unknown_id_page_404(client):
    assert client.get("/download/does-not-exist").status_code == 404
    assert client.get("/download/does-not-exist/raw").status_code == 404

def test_info_endpoint(client):
    r = client.post("/upload", files={"file": ("hello.txt", b"hi there")})
    file_id = r.json()["id"]

    info = client.get(f"/api/info/{file_id}").json()
    assert info["filename"] == "hello.txt"
    assert info["size"] == 8
    assert info["uploaded_at"] is not None
    assert info["expires_at"] == info["uploaded_at"] + 3 * 86400
    assert info["download_url"] == f"/download/{file_id}/raw"


def test_info_unknown_id_404(client):
    assert client.get("/api/info/nope").status_code == 404

def test_upload_rate_limit(client, monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "upload_rate_limit", "2/minute")
    
    from limiter import limiter
    limiter.reset()

    for i in range(2):
        r = client.post("/upload", files={"file": ("f.txt", b"x")})
        assert r.status_code == 200

    r = client.post("/upload", files={"file": ("f.txt", b"x")})
    assert r.status_code == 429
