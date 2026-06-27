from backend.app.services.storage import LocalStorage


def test_storage_ensures_directories(tmp_path):
    storage = LocalStorage(tmp_path)
    storage.ensure_directories("data/raw/mrms/reflectivity")

    target = storage.absolute_path("data/raw/mrms/reflectivity")
    assert target.is_dir()


def test_storage_write_text_and_exists(tmp_path):
    storage = LocalStorage(tmp_path)
    path = storage.write_text("data/raw/mrms/reflectivity/sample.stub", "hello stub")

    assert path == "data/raw/mrms/reflectivity/sample.stub"
    assert storage.path_exists(path)
    assert storage.absolute_path(path).read_text() == "hello stub"


def test_storage_sha256(tmp_path):
    storage = LocalStorage(tmp_path)
    path = storage.write_text("data/raw/mrms/reflectivity/hash.stub", "abc")

    assert storage.sha256(path) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_storage_normalized_paths(tmp_path):
    storage = LocalStorage(tmp_path)
    raw_path, processed_path = storage.mrms_reflectivity_paths("2026-06-27T20:25:00Z")

    assert raw_path == "data/raw/mrms/reflectivity/20260627T202500Z.grib2.stub"
    assert processed_path == "data/processed/mrms/reflectivity/20260627T202500Z.png.stub"
