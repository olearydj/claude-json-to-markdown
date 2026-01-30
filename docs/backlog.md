# Backlog

Potential future enhancements, roughly prioritized.

## Medium Priority

### Skip Behavior CLI Flags
Currently, skipping conversations with empty names or no content is hardcoded. Add opt-out flags (`--no-skip-empty-names`, `--no-skip-empty-content`) to make this configurable. Follows the established `--no-*` pattern.

### Expand Integration Tests
Basic integration tests pass but coverage could improve:
- File system edge cases (permissions, missing directories)
- `--log-path` variations (file vs directory)
- Error condition logging

### Performance Testing
Verify scaling on very large exports. Current testing used ~1200 conversations; should validate with 5000+.

## Low Priority

### Project-to-Conversation Linking
Anthropic exports include project data, but only ~12% of conversations can be linked via document attachments. Could add optional metadata index if there's demand.

### Pydantic Input Validation
For robust validation of input JSON against expected schema. Likely overkill unless malformed exports become common.
