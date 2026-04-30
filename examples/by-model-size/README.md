# Examples by Model Size

ADD document examples optimized for specific AI model classes. The same physical device — a garden irrigation valve — is described three ways to show how document complexity must match model capability.

| Model class | File | Rules | ethic_url | doc_url |
|---|---|---|---|---|
| Small (1B–13B) | [small-models/irrigation-valve-standard-small.json](small-models/irrigation-valve-standard-small.json) | 8 | No — uses ethic_core | No |
| Medium (13B–70B) | [medium-models/irrigation-valve-standard-medium.json](medium-models/irrigation-valve-standard-medium.json) | 12 | Yes | Yes |
| Large / Frontier | [large-models/irrigation-valve-standard-large.json](large-models/irrigation-valve-standard-large.json) | 15 | Yes | Yes |

The [multi-model validation example](irrigation-valve-multi-model-validation.json) shows the same document validated with three different models — one passes, one passes with warnings, one fails. The findings explain why and point to the correct alternative.

The [small-models](small-models/) folder also contains a minimal universal device example — a generic switched outlet with just two actions and no deployment-specific rules. This is the starting point for universal devices where context belongs to the agent task, not the ADD document.

For the full explanation of model classes and document design, see the [ADD Developer Guide](../../ADD_Developer_Guide_v1_0.md).
