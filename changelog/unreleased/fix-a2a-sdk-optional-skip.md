## fix(a2a): skip a2a SDK tests when package not installed

Tests in `TestAgentCardFetching`, `TestAgentCardCaching`, `TestSkillValidation`,
and `TestStreamingSupport` require the optional `a2a` SDK. Added `_skip_no_a2a`
`pytestmark` to each class so CI passes in environments without the SDK.
