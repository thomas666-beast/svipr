# tests/test_upload.py
def test_upload_and_download_roundtrip(client):
    content = b"hello encrypted svipr\n" * 1000
    r = client.post("/upload", files={"file": ("test.txt", content)})
    assert r.status_code == 200
    file_id = r.json()["id"]
    assert r.json()["size"] == len(content)

    # download should return exact original bytes
    r2 = client.get(f"/{file_id}")
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
