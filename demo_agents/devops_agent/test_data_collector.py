from demo_agents.devops_agent.data_collector import available_topics, lookup_cheatsheet


def test_known_topic_returns_cheatsheet():
    assert "kubectl" in lookup_cheatsheet("kubernetes")


def test_lookup_is_case_and_space_insensitive():
    assert lookup_cheatsheet("  Kubernetes  ") == lookup_cheatsheet("kubernetes")


def test_alias_resolves_to_same_content():
    assert lookup_cheatsheet("k8s") == lookup_cheatsheet("kubernetes")
    assert lookup_cheatsheet("canary") == lookup_cheatsheet("deployment-patterns")
    assert lookup_cheatsheet("ci/cd") == lookup_cheatsheet("cicd-pipeline")


def test_unknown_topic_returns_none():
    assert lookup_cheatsheet("terraform") is None


def test_known_topics_exact_keys():
    assert lookup_cheatsheet("container-health") is not None
    assert lookup_cheatsheet("env-promotion") is not None
    assert lookup_cheatsheet("cicd-pipeline") is not None


def test_available_topics_matches_main_keys_not_aliases():
    topics = available_topics()
    assert "kubernetes" in topics
    assert "k8s" not in topics  # alias không tính là chủ đề chính
