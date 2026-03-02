from src.utils.config import CVConfig


def test_config_profile_path_exists():
    config = CVConfig.from_defaults()
    assert config.profile_path().exists(), f"Profile not found: {config.profile_path()}"


def test_config_pipeline_root_exists():
    config = CVConfig.from_defaults()
    assert config.pipeline_root.exists()


def test_config_cv_render_dir_format():
    config = CVConfig.from_defaults()
    path = config.cv_render_dir("tu_berlin", "201084")
    assert "tu_berlin" in str(path)
    assert "201084" in str(path)
    assert str(path).endswith("cv/rendered")
