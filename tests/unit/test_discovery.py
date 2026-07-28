import jsonschema
import pytest
from x402.extensions.bazaar import (
    validate_discovery_extension,
    validate_discovery_extension_spec,
)

from onecent.services.discovery import (
    ENDPOINT_DESCRIPTIONS,
    INPUT_EXAMPLES,
    OUTPUT_EXAMPLES,
    discovery_extension,
)

OPERATIONS = ("pulse", "passport", "extract", "changed")


@pytest.mark.parametrize("operation", OPERATIONS)
def test_bazaar_extension_passes_current_sdk_validation(operation: str) -> None:
    bazaar = discovery_extension(operation)["bazaar"]
    consistency = validate_discovery_extension(bazaar)
    specification = validate_discovery_extension_spec(bazaar)
    assert consistency.valid, consistency.errors
    assert specification.valid, specification.errors


@pytest.mark.parametrize("operation", OPERATIONS)
def test_examples_match_exact_input_and_output_schemas(operation: str) -> None:
    bazaar = discovery_extension(operation)["bazaar"]
    input_schema = bazaar["schema"]["properties"]["input"]["properties"]["body"]
    output_schema = bazaar["schema"]["properties"]["output"]["properties"]["example"]
    jsonschema.validate(INPUT_EXAMPLES[operation], input_schema)
    jsonschema.validate(OUTPUT_EXAMPLES[operation], output_schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({**INPUT_EXAMPLES[operation], "unknown": True}, input_schema)


@pytest.mark.parametrize("operation", OPERATIONS)
def test_metadata_is_machine_readable_and_complete(operation: str) -> None:
    bazaar = discovery_extension(operation)["bazaar"]
    assert len(ENDPOINT_DESCRIPTIONS[operation]) >= 120
    assert bazaar["info"]["input"]["type"] == "http"
    assert bazaar["info"]["input"]["bodyType"] == "json"
    assert bazaar["info"]["input"]["method"] == "POST"
    assert "$defs" not in str(bazaar)
