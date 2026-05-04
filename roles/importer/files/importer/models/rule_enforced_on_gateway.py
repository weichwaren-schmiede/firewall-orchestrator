from pydantic import BaseModel


# normalized config without db ids
class RuleEnforcedOnGatewayNormalized(BaseModel):
    rule_uid: str
    dev_uid: str

    model_config = {"arbitrary_types_allowed": True}
