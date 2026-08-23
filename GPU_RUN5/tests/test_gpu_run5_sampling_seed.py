from pathlib import Path


def test_vendored_wrapper_forwards_configurable_generation_seed():
    root = Path(__file__).resolve().parents[2]
    source = (root / "third_party/odeformer/odeformer/model/model_wrapper.py").read_text()
    assert "generation_seed=0" in source
    sampling = source.split('elif self.beam_type == "sampling":', 1)[1]
    search = source.split('if self.beam_type == "search":', 1)[1].split('elif self.beam_type == "sampling":', 1)[0]
    assert "seed=self.generation_seed" in sampling
    assert "seed=self.generation_seed" not in search
